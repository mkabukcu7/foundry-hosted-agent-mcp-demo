"""Verify the hosted specialist wire contract without cloud or model calls."""

from contextlib import AsyncExitStack, redirect_stderr
from io import StringIO
import json
import unittest
from unittest.mock import AsyncMock, patch

import httpx

from agent.assurance_runtime import ArtifactRejected, ResponsesRemote, SpecialistSessions, conversation_scope
from agent.contract_specialist import CallerBoundary, create_responses_app
from tests.test_assurance_handoff import OfflineDocumentAnalyst


class ResponsesTransportTests(unittest.IsolatedAsyncioTestCase):
    async def test_responses_roundtrip_reuse_handoff_retry_and_reset(self):
        contract, rfp = OfflineDocumentAnalyst("contract"), OfflineDocumentAnalyst("rfp")
        requests = []
        real_client = httpx.AsyncClient
        with patch.dict("os.environ", {"CONTRACT_ASSURANCE_LOCAL": "1"}):
            apps = {8091: create_responses_app(contract, "contract"),
                    8092: create_responses_app(rfp, "rfp")}

            class Transport(httpx.AsyncBaseTransport):
                async def handle_async_request(self, request):
                    requests.append(request)
                    return await httpx.ASGITransport(
                        app=apps[request.url.port], client=("127.0.0.1", 1234)).handle_async_request(request)

            def client(**kwargs):
                return real_client(transport=Transport(), **kwargs)

            async with AsyncExitStack() as stack:
                for app in apps.values():
                    await stack.enter_async_context(app.app.router.lifespan_context(app.app))
                with patch("agent.assurance_runtime.httpx.AsyncClient", side_effect=client):
                    sessions = SpecialistSessions({
                        "contract": ResponsesRemote("http://127.0.0.1:8091/"),
                        "rfp": ResponsesRemote("http://127.0.0.1:8092/")})
                    first = await sessions.ask("alice", "parent", "rfp", "Compare RFP")
                    second = await sessions.ask("alice", "parent", "rfp", "Explain credit")
                    self.assertFalse(first["session_reused"])
                    self.assertTrue(second["session_reused"])
                    self.assertEqual(first["session_tag"], second["session_tag"])
                    result = await sessions.handoff("alice", "parent")
                    self.assertEqual(result["status"], "document_validated")
                    self.assertEqual(result["findings"], result["read_artifact"])
                    self.assertEqual(result["annotation_parent"], result["findings"])
                    self.assertEqual(result["annotated"]["version"], 2)
                    self.assertEqual(len(result["source_ids"]), 8)
                    self.assertTrue(result["rfp_reused"])
                    self.assertIn('"contract_findings"', rfp.inputs[-1])
                    self.assertIn("DEMO-NS-CON-004", rfp.inputs[-1])
                    context_id = sessions.contexts[("alice", "parent", "rfp")].context_id
                    with self.assertRaises(ArtifactRejected):
                        await sessions.remotes["rfp"].send(
                            "Invalid findings", context_id, action="annotate_findings",
                            scope=conversation_scope("alice", "parent"))
                    again = await sessions.handoff("alice", "parent")
                    self.assertTrue(again["operation_replayed"])
                    self.assertEqual(rfp.calls, 3)
                    await sessions.reset("alice", "parent")
                    restarted = await sessions.ask("alice", "parent", "rfp", "Start fresh")
                    self.assertFalse(restarted["session_reused"])
                    bob = await sessions.ask("bob", "parent", "rfp", "Other user")
                    self.assertNotEqual(bob["session_tag"], restarted["session_tag"])
                    contract.fail_once = True
                    with self.assertRaises(RuntimeError):
                        await sessions.ask("alice", "retry", "contract", "Retry this")
                    retried = await sessions.ask("alice", "retry", "contract", "Retry this")
                    self.assertFalse(retried["context_reused"])
                    contract.fail_once = True
                    with self.assertRaises(RuntimeError):
                        await sessions.ask("alice", "reset-unresolved", "contract", "Unresolved first call")
                    await sessions.reset("alice", "reset-unresolved")
                    recovered = await sessions.ask("alice", "reset-unresolved", "contract", "New question")
                    self.assertFalse(recovered["session_reused"])
        self.assertTrue(all(request.url.path == "/responses" for request in requests))
        payloads = [json.loads(request.content) for request in requests]
        self.assertTrue(all(payload["store"] and payload["stream"] is False for payload in payloads))
        self.assertNotIn("previous_response_id", payloads[0])
        self.assertIn("previous_response_id", payloads[1])
        self.assertFalse(any("A2A-Version" in request.headers for request in requests))

    async def test_nonlocal_missing_authorization_never_reaches_model(self):
        analyst = OfflineDocumentAnalyst("contract")
        with patch.dict("os.environ", {
            "CONTRACT_ASSURANCE_LOCAL": "0", "CONTRACT_ASSURANCE_TENANT_ID": "tenant",
            "CONTRACT_ASSURANCE_AUDIENCE": "audience", "CONTRACT_ASSURANCE_ALLOWED_CALLER_IDS": "allowed",
        }):
            app = create_responses_app(analyst, "contract")
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                                     base_url="https://specialist.example") as client:
            response = await client.post("/responses", json={"input": "Untrusted question"})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(analyst.calls, 0)

    async def test_foundry_passthrough_still_requires_verified_allowlisted_bearer(self):
        analyst = OfflineDocumentAnalyst("contract")
        real_client = httpx.AsyncClient
        requests = []
        with patch.dict("os.environ", {
            "CONTRACT_ASSURANCE_LOCAL": "0", "CONTRACT_ASSURANCE_TENANT_ID": "tenant",
            "CONTRACT_ASSURANCE_AUDIENCE": "audience", "CONTRACT_ASSURANCE_ALLOWED_CALLER_IDS": "allowed",
        }):
            app = create_responses_app(analyst, "contract")

            class Transport(httpx.AsyncBaseTransport):
                async def handle_async_request(self, request):
                    requests.append(request)
                    del request.headers["authorization"]
                    request.url = request.url.copy_with(path="/responses")
                    return await httpx.ASGITransport(app=app).handle_async_request(request)

            def client(**kwargs):
                return real_client(transport=Transport(), **kwargs)

            async with app.app.router.lifespan_context(app.app):
                inner = app.app

                async def without_credentials(scope, receive, send):
                    self.assertNotIn(b"x-client-assurance-authorization", dict(scope.get("headers", [])))
                    self.assertNotIn(b"authorization", dict(scope.get("headers", [])))
                    await inner(scope, receive, send)

                app.app = without_credentials
                with patch("agent.assurance_runtime.auth_headers", new=AsyncMock(
                    return_value={"Authorization": "Bearer verified-caller"})), \
                     patch("agent.assurance_runtime.httpx.AsyncClient", side_effect=client), \
                     patch.object(CallerBoundary, "verify", return_value="tenant:allowed") as verify:
                    remote = ResponsesRemote("https://test.services.ai.azure.com/api/projects/test/agents/test/endpoint/protocols/openai")
                    _, result = await remote.send("Explain credit")
                    self.assertTrue(result["evidence"])
                    verify.assert_called_once_with("verified-caller")
                    self.assertNotIn("verified-caller", requests[0].content.decode())
                    self.assertNotIn("verified-caller", result["explanation"])
                with patch.object(CallerBoundary, "verify", side_effect=ValueError("Invalid caller")):
                    async with real_client(transport=httpx.ASGITransport(app=app),
                                           base_url="https://test.services.ai.azure.com") as rejected:
                        response = await rejected.post("/responses", headers={
                            "x-client-assurance-authorization": "Bearer unauthorized"})
                    self.assertEqual(response.status_code, 401)
                    self.assertEqual(analyst.calls, 1)

    async def test_http_failure_preserves_platform_context_and_exports_only_metadata(self):
        real_client = httpx.AsyncClient
        requests = []

        def respond(request):
            requests.append(request)
            return httpx.Response(403, json={"error": "private server detail"})

        def client(**kwargs):
            return real_client(transport=httpx.MockTransport(respond), **kwargs)

        output = StringIO()
        with patch.dict("os.environ", {"CONTRACT_ASSURANCE_TRACE": "1"}), \
             patch("agent.assurance_runtime.auth_headers", new=AsyncMock(return_value={
                 "Authorization": "Bearer private-token", "x-agent-foundry-call-id": "private-context"})), \
             patch("agent.assurance_runtime.httpx.AsyncClient", side_effect=client), redirect_stderr(output):
            remote = ResponsesRemote("https://test.services.ai.azure.com/api/projects/test/agents/test/endpoint/protocols/openai")
            with self.assertRaises(httpx.HTTPStatusError):
                await remote.send("private prompt", request_id="stable-request")
        self.assertEqual(requests[0].url.params["api-version"], "v1")
        self.assertTrue(requests[0].url.path.endswith("/protocols/openai/responses"))
        self.assertEqual(requests[0].headers["x-agent-foundry-call-id"], "private-context")
        self.assertEqual(requests[0].headers["x-client-assurance-authorization"], "Bearer private-token")
        self.assertEqual(remote.continuations, {})
        events = [json.loads(line) for line in output.getvalue().splitlines()]
        self.assertEqual([event["role"] for event in events], ["responses.token", "responses.send"])
        self.assertEqual(events[-1]["http_status_code"], 403)
        for sensitive in ("private-token", "private-context", "private prompt", "private server detail"):
            self.assertNotIn(sensitive, output.getvalue())

    def test_rejects_hosted_a2a_url_instead_of_falling_back(self):
        with self.assertRaises(ValueError):
            ResponsesRemote("https://test.services.ai.azure.com/api/projects/test/agents/test/endpoint/protocols/a2a")


if __name__ == "__main__":
    unittest.main()
