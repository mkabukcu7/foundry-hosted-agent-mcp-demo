import unittest
import ast
import asyncio
from contextlib import redirect_stderr
from io import StringIO
import json
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import patch

from agent.assurance_runtime import A2ARemote, PRINCIPAL, SpecialistSessions, metadata_span, validate_endpoint, new_request_id
from agent.contract_specialist import RETRIEVED, CallerBoundary, SpecialistExecutor, create_app
from agent.assurance_protocol import RequestContext, Message, MessageSendParams, Part, Role, TextPart
import httpx

from shared.contract_assurance import compare_evidence, retrieve_terms


class EvidenceTests(unittest.TestCase):
    def test_three_discrepancies_and_matching_residency(self):
        result = compare_evidence(retrieve_terms("contract"), retrieve_terms("rfp"))
        self.assertEqual([item["topic"] for item in result if item["status"] == "discrepancy"],
                         ["uptime", "service_credit", "breach_notification"])
        self.assertEqual(result[-1]["status"], "match")
        self.assertTrue(all(len(item["source_ids"]) == 2 for item in result))

    def test_retrieval_is_read_only_scoped_and_missing_evidence_abstains(self):
        contract = retrieve_terms("contract", topic="service_credit")
        self.assertEqual(contract[0]["value"], "5%")
        self.assertEqual(contract[0]["source_id"], "DEMO-NS-CON-002")
        contract[0]["value"] = "changed"
        self.assertEqual(retrieve_terms("contract", topic="service_credit")[0]["value"], "5%")
        self.assertEqual(retrieve_terms("rfp", vendor_id="unknown"), [])
        self.assertTrue(all(item["status"] == "insufficient_evidence"
                            for item in compare_evidence([], retrieve_terms("rfp"))))


class OfflineRemote:
    def __init__(self):
        self.calls = []

    async def send(self, question, context_id=None, reset=False, **kwargs):
        self.calls.append((question, context_id, reset))
        return context_id or f"offline-context-{len(self.calls)}", {"evidence": [], "context_reset": reset,
                                      "context_reused": context_id is not None}


class SessionTests(unittest.IsolatedAsyncioTestCase):
    async def test_reuse_parent_user_specialist_isolation_and_reset(self):
        contract, rfp = OfflineRemote(), OfflineRemote()
        sessions = SpecialistSessions({"contract": contract, "rfp": rfp})
        first = await sessions.ask("alice", "parent-1", "contract", "Compare")
        second = await sessions.ask("alice", "parent-1", "contract", "Explain credit")
        self.assertFalse(first["session_reused"])
        self.assertTrue(second["session_reused"])
        self.assertEqual(contract.calls[1][1], "offline-context-1")
        await sessions.ask("alice", "parent-2", "contract", "Other session")
        await sessions.ask("bob", "parent-1", "contract", "Other user")
        await sessions.ask("alice", "parent-1", "rfp", "RFP only")
        self.assertIsNone(contract.calls[2][1])
        self.assertIsNone(contract.calls[3][1])
        self.assertIsNone(rfp.calls[0][1])
        await sessions.reset("alice", "parent-1")
        self.assertTrue(contract.calls[-1][2])
        self.assertTrue(rfp.calls[-1][2])
        restarted = await sessions.ask("alice", "parent-1", "contract", "New context")
        self.assertFalse(restarted["session_reused"])
        self.assertIsNone(contract.calls[-1][1])

    async def test_parallel_followups_serialize_context_creation(self):
        remote = OfflineRemote()
        sessions = SpecialistSessions({"contract": remote})
        await asyncio.gather(*(sessions.ask("alice", "parent", "contract", "Question") for _ in range(3)))
        self.assertEqual([call[1] for call in remote.calls], [None, "offline-context-1", "offline-context-1"])

    async def test_failure_does_not_claim_reuse_or_success(self):
        class BrokenRemote:
            async def send(self, *args, **kwargs):
                raise RuntimeError("Unavailable")
        sessions = SpecialistSessions({"contract": BrokenRemote()})
        with self.assertRaises(RuntimeError):
            await sessions.ask("alice", "parent", "contract", "Question")
        self.assertIsNone(sessions.contexts[("alice", "parent", "contract")].context_id)


class OfflineAnalyst:
    def create_session(self):
        return SimpleNamespace(turns=[])

    async def run(self, question, session):
        session.turns.append(question)
        evidence = retrieve_terms("contract", topic="service_credit")
        RETRIEVED.get().extend(evidence)
        return SimpleNamespace(text=f"5% [DEMO-NS-CON-002]. Turn {len(session.turns)}")


class ProtocolTests(unittest.IsolatedAsyncioTestCase):
    async def test_foundry_uses_versioned_native_card_discovery(self):
        from agent.assurance_protocol import A2ACardResolver
        base = "https://example.services.ai.azure.com/api/projects/test/agents/contract/endpoint/protocols/a2a"
        requests = []

        def respond(request):
            requests.append(request)
            return httpx.Response(200, json={"name": "Contract Analyst", "version": "1.0.0",
                "description": "Read-only demo evidence", "capabilities": {}, "skills": [],
                "defaultInputModes": ["text/plain"], "defaultOutputModes": ["application/json"],
                "supportedInterfaces": [{"url": base, "protocolBinding": "JSONRPC", "protocolVersion": "1.0"}]})

        async with httpx.AsyncClient(transport=httpx.MockTransport(respond), params={"api-version": "v1"}) as client:
            card = await A2ACardResolver(client, base).get_agent_card()
        self.assertEqual(len(requests), 1)
        self.assertEqual(str(requests[0].url), base + "/agentCard/v1.0?api-version=v1")
        self.assertEqual(card.url, base)
        self.assertEqual(card.protocol_version, "1.0.0")

    async def test_unknown_resumed_context_requires_explicit_reset(self):
        executor = SpecialistExecutor(OfflineAnalyst(), "contract")
        results = []
        class Queue:
            async def enqueue_event(self, message):
                results.append(message.parts[0].root.data)
        token = PRINCIPAL.set("alice")
        try:
            request = MessageSendParams(message=Message(role=Role.user, message_id=new_request_id(),
                context_id="lost-context", parts=[Part(root=TextPart(text="Continue"))]),
                metadata={"assurance_resume": True})
            await executor.execute(RequestContext(request=request), Queue())
        finally:
            PRINCIPAL.reset(token)
        self.assertEqual(results[0]["status"], "context_expired")
        self.assertFalse(results[0]["context_reused"])
        self.assertEqual(executor.sessions, {})

    async def test_offline_sdk_client_server_roundtrip_and_reuse(self):
        with patch.dict("os.environ", {"CONTRACT_ASSURANCE_LOCAL": "1"}):
            app = create_app(OfflineAnalyst(), "contract", "http://127.0.0.1:8091/")
            transport = httpx.ASGITransport(app=app, client=("127.0.0.1", 12345))
            real_client = httpx.AsyncClient
            def client_factory(**kwargs):
                return real_client(transport=transport, **kwargs)
            with patch("agent.assurance_runtime.httpx.AsyncClient", side_effect=client_factory):
                remote = A2ARemote("http://127.0.0.1:8091/")
                context_id, first = await remote.send("Explain credit")
                next_id, second = await remote.send("What clause?", context_id)
                self.assertEqual(context_id, next_id)
                self.assertFalse(first["context_reused"])
                self.assertTrue(second["context_reused"])
                self.assertIn("Turn 2", second["explanation"])
                self.assertEqual(second["evidence"][0]["source_id"], "DEMO-NS-CON-002")
                _, reset = await remote.send("reset", context_id, reset=True)
                self.assertTrue(reset["context_reset"])

    async def test_specialist_history_is_isolated_by_authenticated_principal(self):
        executor = SpecialistExecutor(OfflineAnalyst(), "contract")
        results = []
        class Queue:
            async def enqueue_event(self, message):
                results.append(message.parts[0].root.data)
        for principal in ("alice", "alice", "bob"):
            token = PRINCIPAL.set(principal)
            try:
                context = RequestContext(request=MessageSendParams(message=Message(
                    role=Role.user, message_id=new_request_id(), context_id="same-id",
                    parts=[Part(root=TextPart(text="Question"))])))
                await executor.execute(context, Queue())
            finally:
                PRINCIPAL.reset(token)
        self.assertEqual([result["context_reused"] for result in results], [False, True, False])

    async def test_specialist_abstains_without_retrieval(self):
        class NoEvidenceAnalyst(OfflineAnalyst):
            async def run(self, question, session):
                return SimpleNamespace(text="An unsupported claim")
        results = []
        class Queue:
            async def enqueue_event(self, message):
                results.append(message.parts[0].root.data)
        token = PRINCIPAL.set("alice")
        try:
            context = RequestContext(request=MessageSendParams(message=Message(
                role=Role.user, message_id=new_request_id(), parts=[Part(root=TextPart(text="Missing clause?"))])))
            await SpecialistExecutor(NoEvidenceAnalyst(), "contract").execute(context, Queue())
        finally:
            PRINCIPAL.reset(token)
        self.assertEqual(results[0]["evidence"], [])
        self.assertIn("Insufficient cited evidence", results[0]["explanation"])


class MCPTransportTests(unittest.IsolatedAsyncioTestCase):
    async def test_both_transports_retrieve_only_their_document_set(self):
        root = Path(__file__).resolve().parents[1]
        spec = importlib.util.spec_from_file_location("assurance_mcp_logic", root / "mcp-server/server.py")
        logic = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(logic)
        with patch.dict(sys.modules, {"server": logic}):
            modules = []
            for name in ("local_mcp", "function_app"):
                spec = importlib.util.spec_from_file_location(f"assurance_{name}", root / f"mcp-server/{name}.py")
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                modules.append(module)
        for module in modules:
            for name, document_set in (("retrieve_contract_clauses", "contract"), ("retrieve_rfp_commitments", "rfp")):
                handler = getattr(module, name)
                if module is modules[1]:
                    result = await handler(json.dumps({"arguments": {"topic": "service_credit"}}))
                    evidence = ast.literal_eval(result)
                else:
                    evidence = handler(topic="service_credit")
                self.assertEqual(len(evidence), 1)
                self.assertEqual(evidence[0]["document_set"], document_set)
                self.assertTrue(evidence[0]["fictional"])
        local_tools = {item.name for item in await modules[0].mcp.list_tools()}
        self.assertTrue({"retrieve_contract_clauses", "retrieve_rfp_commitments"} <= local_tools)


class PrivacyTests(unittest.TestCase):
    def test_jwt_signature_tenant_audience_issuer_and_expiry_are_checked(self):
        import jwt
        import time
        from cryptography.hazmat.primitives.asymmetric import rsa

        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        with patch.dict("os.environ", {"CONTRACT_ASSURANCE_LOCAL": "0",
                                      "CONTRACT_ASSURANCE_TENANT_ID": "test-tenant",
                                      "CONTRACT_ASSURANCE_AUDIENCE": "test-audience",
                                      "CONTRACT_ASSURANCE_ALLOWED_CALLER_IDS": "object-1"}):
            boundary = CallerBoundary(None)
        boundary.key_client = SimpleNamespace(get_signing_key_from_jwt=lambda token: SimpleNamespace(key=private_key.public_key()))
        claims = {"sub": "user-1", "oid": "object-1", "tid": "test-tenant", "aud": "test-audience",
                  "iss": "https://login.microsoftonline.com/test-tenant/v2.0",
                  "iat": int(time.time()) - 10, "exp": int(time.time()) + 600}
        self.assertEqual(boundary.verify(jwt.encode(claims, private_key, algorithm="RS256")), "test-tenant:object-1")
        for field, value in (("tid", "other-tenant"), ("aud", "wrong-audience"),
                             ("iss", "https://untrusted.example/"), ("exp", int(time.time()) - 100),
                             ("oid", "unauthorized-caller")):
            with self.subTest(field=field), self.assertRaises((jwt.InvalidTokenError, ValueError)):
                boundary.verify(jwt.encode({**claims, field: value}, private_key, algorithm="RS256"))

    def test_trace_is_opt_in_and_contains_no_input_or_raw_session(self):
        output = StringIO()
        with patch.dict("os.environ", {"CONTRACT_ASSURANCE_TRACE": "0"}), redirect_stderr(output):
            with metadata_span("test", "private-session"):
                pass
        self.assertEqual(output.getvalue(), "")
        with patch.dict("os.environ", {"CONTRACT_ASSURANCE_TRACE": "1"}), redirect_stderr(output):
            with metadata_span("root", "private-session"):
                with metadata_span("child", "private-session", True):
                    pass
        child, root = [json.loads(line) for line in output.getvalue().splitlines()]
        self.assertNotIn("private-session", output.getvalue())
        self.assertEqual(child["trace_id"], root["trace_id"])
        self.assertEqual(child["parent_span_id"], root["span_id"])
        self.assertTrue(child["session_reused"])
        self.assertEqual(set(child), {"event", "role", "trace_id", "span_id", "parent_span_id",
                                     "session_tag", "session_reused", "duration_ms", "success", "status"})

    def test_non_loopback_http_is_never_allowed(self):
        with patch.dict("os.environ", {"CONTRACT_ASSURANCE_LOCAL": "1"}):
            with self.assertRaises(ValueError):
                validate_endpoint("http://untrusted.example/")


class BrowserOwnershipTests(unittest.TestCase):
    def test_browser_cannot_resume_another_owners_session(self):
        from frontend.assurance_client import AssuranceGateway
        gateway = AssuranceGateway()
        session = gateway.create_session("alice-cookie")
        with self.assertRaises(PermissionError):
            gateway.respond("bob-cookie", session, "Read another session")

    def test_gateway_reuses_only_server_owned_response_id(self):
        from frontend.assurance_client import AssuranceGateway
        gateway = AssuranceGateway()
        session = gateway.create_session("alice-cookie")
        with patch.dict("os.environ", {"CONTRACT_ASSURANCE_LOCAL": "1",
                                      "CONTRACT_ORCHESTRATOR_BASE_URL": "http://127.0.0.1:8090/"}), \
             patch("frontend.assurance_client.OpenAI") as client:
            responses = client.return_value.__enter__.return_value.responses
            responses.create.side_effect = [
                SimpleNamespace(id="server-response-1", status="completed", output_text="First"),
                SimpleNamespace(id="server-response-2", status="completed", output_text="Follow-up"),
                SimpleNamespace(id="server-response-3", status="completed", output_text="Reset", output=[
                    SimpleNamespace(type="function_call_output", output='{"specialist_contexts_reset": true}')]),
            ]
            first = gateway.respond("alice-cookie", session, "Compare")
            gateway.respond("alice-cookie", session, "Explain")
            gateway.respond("alice-cookie", session, "Reset", reset=True)
            self.assertNotIn("previous_response_id", responses.create.call_args_list[0].kwargs)
            self.assertEqual(responses.create.call_args_list[1].kwargs["previous_response_id"], "server-response-1")
            self.assertEqual(responses.create.call_args_list[2].kwargs["tool_choice"]["name"], "reset_assurance_context")
            self.assertIsNone(gateway.sessions[session].previous_response_id)
            self.assertNotIn("server-response-1", json.dumps(first))


if __name__ == "__main__":
    unittest.main()