"""Offline artifact and lifecycle tests; never evidence of deployed Foundry integration."""

from copy import deepcopy
import asyncio
from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import httpx
from agent.assurance_protocol import RequestContext, Message, MessageSendParams, Part, Role, TextPart

from agent.assurance_artifacts import ArtifactRejected, make_document, read_document, reference
from agent.assurance_runtime import A2ARemote, ContextUnavailable, PRINCIPAL, SpecialistCallFailed, SpecialistSessions
from agent.contract_specialist import RETRIEVED, SpecialistExecutor, create_app
from shared.contract_assurance import retrieve_terms


class ArtifactTests(unittest.TestCase):
    def setUp(self):
        self.artifact = make_document(retrieve_terms("contract"), "Synthetic contract findings.", "scope-alice")

    def test_complete_bytes_and_annotation_lineage(self):
        body, text = read_document(self.artifact, "scope-alice", reference(self.artifact))
        self.assertIn("99.5%", text)
        self.assertIn("DEMO-NS-CON-002", text)
        annotated = make_document(retrieve_terms("rfp"), "RFP annotations.", "scope-alice",
                                  original=self.artifact, original_body=body)
        result, _ = read_document(annotated, "scope-alice", reference(annotated))
        self.assertEqual(annotated["artifactId"], self.artifact["artifactId"])
        self.assertEqual(annotated["metadata"]["version"], 2)
        self.assertEqual(annotated["metadata"]["parent"], reference(self.artifact))
        self.assertEqual(len(result["rfp_annotation"]["comparisons"]), 4)
        self.assertEqual(len(annotated["metadata"]["source_ids"]), 8)

    def test_missing_stale_unauthorized_tampered_and_wrong_version(self):
        body, _ = read_document(self.artifact, "scope-alice", reference(self.artifact))
        annotated = make_document(retrieve_terms("rfp"), "Annotation", "scope-alice",
                                  original=self.artifact, original_body=body)
        with self.assertRaises(ArtifactRejected):
            read_document(None, "scope-alice", reference(self.artifact))
        with self.assertRaises(ArtifactRejected):
            read_document(self.artifact, "scope-bob", reference(self.artifact))
        with self.assertRaises(ArtifactRejected):
            read_document(self.artifact, "scope-alice", reference(annotated))
        with self.assertRaises(ArtifactRejected):
            read_document(self.artifact, "scope-alice", reference(self.artifact),
                          {self.artifact["artifactId"]: reference(annotated)})
        tampered = deepcopy(self.artifact)
        tampered["parts"][0]["file"]["bytes"] = "e30="
        with self.assertRaises(ArtifactRejected):
            read_document(tampered, "scope-alice", reference(tampered))


class VerificationGateTests(unittest.TestCase):
    def test_separate_host_definitions_and_source_only_package(self):
        import yaml
        root = Path(__file__).resolve().parents[1]
        manifest = yaml.safe_load((root / "deployment/contract-assurance/azure.yaml").read_text())
        agents = [service for service in manifest["services"].values() if service["host"] == "azure.ai.agent"]
        self.assertEqual(len(agents), 3)
        self.assertEqual({service["env"]["CONTRACT_ASSURANCE_ROLE"] for service in agents}, {"orchestrator", "contract", "rfp"})
        self.assertEqual(len({service["name"] for service in agents}), 3)
        self.assertTrue(all(service["kind"] == "hosted" and service["env"]["CONTRACT_ASSURANCE_LOCAL"] == "0" for service in agents))
        self.assertTrue(all(service["codeConfiguration"]["runtime"] == "python_3_13" for service in agents))
        for service in agents:
            if service["env"]["CONTRACT_ASSURANCE_ROLE"] in {"contract", "rfp"}:
                self.assertEqual({protocol["protocol"]: protocol["version"] for protocol in service["protocols"]},
                                 {"responses": "2.0.0"})
                self.assertEqual(service["agentEndpoint"]["protocols"], ["responses"])
                self.assertNotIn("agentCard", service)
        from scripts.package_assurance import stage
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as temporary:
            package = stage(Path(temporary))
            self.assertTrue((package / "main.py").is_file())
            self.assertTrue((package / "agent/assurance_host.py").is_file())
            self.assertFalse(any(path.name == ".env" or path.suffix in {".pyd", ".dll"} for path in package.rglob("*")))

    def test_receipts_come_from_actual_tool_items_not_model_text(self):
        from frontend.assurance_client import execution_receipts
        content = {"status": "document_validated", "findings": {"version": 1}, "annotated": {"version": 2},
                   "read_artifact": {"version": 1}, "document_body": "never expose this"}
        response = SimpleNamespace(output_text="I claim validation", output=[
            SimpleNamespace(type="message", content="document_validated"),
            SimpleNamespace(type="function_call_output", output=str(content))])
        result = execution_receipts(response)
        self.assertEqual(len(result), 1)
        self.assertNotIn("document_body", json.dumps(result))
        self.assertEqual(execution_receipts(SimpleNamespace(output_text="document_validated")), [])
        self.assertEqual(execution_receipts(SimpleNamespace(output=[
            SimpleNamespace(type="function_call_output", output="not a structured receipt(")])), [])

    def test_unconfigured_hosted_demo_is_not_run(self):
        from scripts.verify_contract_assurance import main
        output = StringIO()
        with patch.dict("os.environ", {}, clear=True), patch("scripts.verify_contract_assurance.load_dotenv"), redirect_stdout(output):
            self.assertEqual(main([]), 2)
        self.assertEqual(json.loads(output.getvalue())["status"], "NOT RUN")

    def test_three_distinct_observed_hosted_endpoints_are_required(self):
        from scripts.verify_contract_assurance import configured_hosted_agents
        env = {"FOUNDRY_PROJECT_ENDPOINT": "https://example.services.ai.azure.com/api/projects/test"}
        for role, name_key, url_key in (("orchestrator", "CONTRACT_ORCHESTRATOR_AGENT_NAME", "CONTRACT_ORCHESTRATOR_BASE_URL"),
                                       ("contract", "CONTRACT_ANALYST_AGENT_NAME", "CONTRACT_ANALYST_URL"),
                                       ("rfp", "RFP_ANALYST_AGENT_NAME", "RFP_ANALYST_URL")):
            env[name_key] = role
            env[name_key + "_VERSION"] = "1"
            env[url_key] = f"{env['FOUNDRY_PROJECT_ENDPOINT']}/agents/{role}/endpoint/protocols/openai"
        configured, errors = configured_hosted_agents(env)
        self.assertEqual(len(configured), 3)
        self.assertEqual(errors, [])
        env["CONTRACT_ANALYST_URL"] = "http://127.0.0.1:8091/"
        self.assertTrue(configured_hosted_agents(env)[1])


class OfflineDocumentAnalyst:
    def __init__(self, role):
        self.role, self.calls, self.inputs = role, 0, []
        self.fail_once = False

    def create_session(self):
        return SimpleNamespace(history=[])

    async def run(self, question, session):
        self.calls += 1
        self.inputs.append(question)
        session.history.append(question)
        if self.fail_once:
            self.fail_once = False
            raise RuntimeError("Offline transient model failure")
        evidence = retrieve_terms(self.role)
        RETRIEVED.get().extend(evidence)
        return SimpleNamespace(text="Synthetic findings " + " ".join(item["source_id"] for item in evidence))


class Queue:
    def __init__(self):
        self.results = []

    async def enqueue_event(self, message):
        self.results.append(message.parts[0].root.data)


def invocation(request_id, context_id="context", metadata=None):
    return RequestContext(request=MessageSendParams(message=Message(role=Role.user, message_id=request_id,
        context_id=context_id, parts=[Part(root=TextPart(text="Synthetic review"))]), metadata=metadata or {}))


class LifecycleTests(unittest.IsolatedAsyncioTestCase):
    async def test_same_context_id_without_reuse_acknowledgement_is_not_continuity(self):
        class Remote:
            async def send(self, question, context_id=None, **kwargs):
                return "same-id", {}
        sessions = SpecialistSessions({"contract": Remote()})
        await sessions.ask("alice", "parent", "contract", "First")
        with self.assertRaises(ContextUnavailable):
            await sessions.ask("alice", "parent", "contract", "Follow-up")

    async def test_reset_does_not_invalidate_another_users_replay(self):
        executor = SpecialistExecutor(OfflineDocumentAnalyst("contract"), "contract")
        for principal in ("alice", "bob"):
            token = PRINCIPAL.set(principal)
            try:
                await executor.execute(invocation(principal + "-first", "shared-context-id"), Queue())
            finally:
                PRINCIPAL.reset(token)
        token = PRINCIPAL.set("alice")
        try:
            await executor.execute(invocation("reset", "shared-context-id", {"assurance_reset": True}), Queue())
        finally:
            PRINCIPAL.reset(token)
        token = PRINCIPAL.set("bob")
        queue = Queue()
        try:
            await executor.execute(invocation("bob-first", "shared-context-id"), queue)
        finally:
            PRINCIPAL.reset(token)
        self.assertNotEqual(queue.results[-1].get("status"), "context_expired")
        self.assertEqual(len(executor.sessions[("bob", "shared-context-id")].session.history), 1)

    async def test_partial_reset_failure_blocks_both_specialists_until_acknowledged(self):
        class Remote:
            def __init__(self):
                self.fail_reset = False
            async def send(self, question, context_id=None, reset=False, **kwargs):
                if reset and self.fail_reset:
                    raise TimeoutError("Offline reset failure")
                return context_id or "context", {"context_reset": reset, "context_reused": context_id is not None}
        contract, rfp = Remote(), Remote()
        sessions = SpecialistSessions({"contract": contract, "rfp": rfp})
        await sessions.ask("alice", "parent", "contract", "Question")
        await sessions.ask("alice", "parent", "rfp", "Question")
        rfp.fail_reset = True
        with self.assertRaises(TimeoutError):
            await sessions.reset("alice", "parent")
        for specialist in ("contract", "rfp"):
            with self.assertRaises(ContextUnavailable):
                await sessions.ask("alice", "parent", specialist, "Continue")
        rfp.fail_reset = False
        await sessions.reset("alice", "parent")
        self.assertTrue(all(state.context_id is None and not state.reset_required for state in sessions.contexts.values()))

    async def test_server_replay_does_not_repeat_model_and_failed_call_rolls_back(self):
        analyst = OfflineDocumentAnalyst("contract")
        executor = SpecialistExecutor(analyst, "contract")
        token = PRINCIPAL.set("alice")
        try:
            queue = Queue()
            analyst.fail_once = True
            await executor.execute(invocation("operation"), queue)
            self.assertEqual(queue.results[-1]["status"], "call_failed")
            self.assertEqual(executor.sessions[("alice", "context")].session.history, [])
            await executor.execute(invocation("operation"), queue)
            self.assertEqual(len(executor.sessions[("alice", "context")].session.history), 1)
            await executor.execute(invocation("operation", metadata={"assurance_trace": {"trace_id": "new-trace"}}), queue)
            self.assertEqual(analyst.calls, 2)
            self.assertEqual(queue.results[-1], queue.results[-2])
        finally:
            PRINCIPAL.reset(token)

    async def test_expiry_and_reset_do_not_silently_resume(self):
        analyst = OfflineDocumentAnalyst("contract")
        executor = SpecialistExecutor(analyst, "contract", ttl_seconds=1)
        token = PRINCIPAL.set("alice")
        try:
            queue = Queue()
            await executor.execute(invocation("first"), queue)
            executor.sessions[("alice", "context")].last_used -= 2
            await executor.execute(invocation("expired", metadata={"assurance_resume": True}), queue)
            self.assertEqual(queue.results[-1]["status"], "context_expired")
            self.assertEqual(analyst.calls, 1)
            await executor.execute(invocation("reset", metadata={"assurance_reset": True}), queue)
            self.assertTrue(queue.results[-1]["context_reset"])
            await executor.execute(invocation("first"), queue)
            self.assertEqual(queue.results[-1]["status"], "context_expired")
            await executor.execute(invocation("new"), queue)
            self.assertFalse(queue.results[-1]["context_reused"])
        finally:
            PRINCIPAL.reset(token)

    async def test_client_retries_exact_request_id_after_ambiguous_transport_failure(self):
        class Flaky:
            def __init__(self):
                self.request_ids = []
            async def send(self, question, context_id=None, **kwargs):
                self.request_ids.append(kwargs["request_id"])
                if len(self.request_ids) == 1:
                    raise TimeoutError("Offline ambiguous transport timeout")
                return "remote-context", {"context_reused": False}
        remote = Flaky()
        sessions = SpecialistSessions({"contract": remote})
        with self.assertRaises(TimeoutError):
            await sessions.ask("alice", "parent", "contract", "Question")
        with self.assertRaises(SpecialistCallFailed):
            await sessions.ask("alice", "parent", "contract", "Different question")
        result = await sessions.ask("alice", "parent", "contract", "Question")
        self.assertEqual(remote.request_ids[0], remote.request_ids[1])
        self.assertFalse(result["session_reused"])

    async def test_concurrent_users_and_conversations_remain_isolated(self):
        analyst = OfflineDocumentAnalyst("contract")
        executor = SpecialistExecutor(analyst, "contract")
        async def run(principal, context, request_id):
            token = PRINCIPAL.set(principal)
            queue = Queue()
            try:
                await executor.execute(invocation(request_id, context), queue)
            finally:
                PRINCIPAL.reset(token)
            return queue.results[-1]
        results = await asyncio.gather(run("alice", "one", "a1"), run("alice", "two", "a2"), run("bob", "one", "b1"))
        self.assertTrue(all(not result["context_reused"] for result in results))
        self.assertEqual(len(executor.sessions), 3)


class OfflineHandoffProtocolTests(unittest.IsolatedAsyncioTestCase):
    async def test_nonlocal_handoff_rejects_missing_authorization_before_model(self):
        analyst = OfflineDocumentAnalyst("rfp")
        with patch.dict("os.environ", {"CONTRACT_ASSURANCE_LOCAL": "0", "CONTRACT_ASSURANCE_TENANT_ID": "test-tenant",
                                      "CONTRACT_ASSURANCE_AUDIENCE": "test-audience", "CONTRACT_ASSURANCE_ALLOWED_CALLER_IDS": "allowed"}):
            app = create_app(analyst, "rfp", "https://specialist.example/")
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="https://specialist.example") as client:
            response = await client.post("/", json={"method": "message/send"})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(analyst.calls, 0)

    async def test_real_sdk_file_roundtrip_with_offline_analysts(self):
        contract, rfp = OfflineDocumentAnalyst("contract"), OfflineDocumentAnalyst("rfp")
        with patch.dict("os.environ", {"CONTRACT_ASSURANCE_LOCAL": "1"}):
            apps = {8091: create_app(contract, "contract", "http://127.0.0.1:8091/"),
                    8092: create_app(rfp, "rfp", "http://127.0.0.1:8092/")}
            class Transport(httpx.AsyncBaseTransport):
                async def handle_async_request(self, request):
                    return await httpx.ASGITransport(app=apps[request.url.port], client=("127.0.0.1", 1234)).handle_async_request(request)
            real_client = httpx.AsyncClient
            def client(**kwargs):
                return real_client(transport=Transport(), **kwargs)
            with patch("agent.assurance_runtime.httpx.AsyncClient", side_effect=client):
                sessions = SpecialistSessions({"contract": A2ARemote("http://127.0.0.1:8091/"),
                                               "rfp": A2ARemote("http://127.0.0.1:8092/")})
                await sessions.ask("alice", "parent", "rfp", "Compare RFP")
                result = await sessions.handoff("alice", "parent")
                self.assertEqual(result["status"], "document_validated")
                self.assertEqual(result["findings"], result["read_artifact"])
                self.assertEqual(result["annotation_parent"], result["findings"])
                self.assertFalse(result["operation_replayed"])
                self.assertEqual(result["annotated"]["version"], 2)
                self.assertTrue(result["rfp_reused"])
                self.assertIn('"contract_findings"', rfp.inputs[-1])
                self.assertIn('"contract_narrative"', rfp.inputs[-1])
                self.assertIn("DEMO-NS-CON-004", rfp.inputs[-1])
                self.assertEqual(len(result["source_ids"]), 8)
                again = await sessions.handoff("alice", "parent")
                self.assertEqual(again["annotated"], result["annotated"])
                self.assertTrue(again["operation_replayed"])
                self.assertIsNone(again["rfp_reused"])
                self.assertEqual(rfp.calls, 2)
                original = sessions.artifacts[("alice", "parent")]["input"]
                unauthorized = deepcopy(original)
                unauthorized["metadata"]["scope"] = "someone-elses-conversation"
                context_id = sessions.contexts[("alice", "parent", "rfp")].context_id
                from agent.assurance_runtime import conversation_scope
                for invalid in (None, original, unauthorized):
                    with self.assertRaises(ArtifactRejected):
                        await sessions.remotes["rfp"].send("Validate attached findings", context_id,
                            action="annotate_findings", artifact=invalid, scope=conversation_scope("alice", "parent"))
                self.assertEqual(rfp.calls, 2)


if __name__ == "__main__":
    unittest.main()