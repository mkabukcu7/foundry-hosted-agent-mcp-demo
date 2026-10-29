"""Regression coverage for PR #5 failure paths, without cloud calls."""

import asyncio
from contextlib import closing
from copy import deepcopy
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
import time
import unittest
from unittest.mock import patch

import httpx

from agent.assurance_runtime import PRINCIPAL, ResponsesRemote, new_request_id
from agent.contract_specialist import SpecialistExecutor
from frontend.assurance_client import AssuranceGateway
from frontend.server import DemoHandler
from scripts.package_assurance import ROOT, stage
from tests.test_assurance_handoff import OfflineDocumentAnalyst, Queue, invocation


class GatewayReviewTests(unittest.TestCase):
    def test_rebinding_host_rejected_before_gateway_for_both_routes(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), DemoHandler)
        worker = Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            port = server.server_port
            with patch("frontend.server.assurance_gateway") as gateway:
                for path in ("/api/assurance/session", "/api/assurance/respond"):
                    for hostname in ("attacker.example", "127.0.0.1.attacker.example"):
                        with self.subTest(path=path, host=hostname):
                            with closing(HTTPConnection("127.0.0.1", port)) as client:
                                host = f"{hostname}:{port}"
                                client.request("POST", path, "{}", {"Host": host, "Origin": "http://" + host})
                                response = client.getresponse()
                                self.assertEqual(response.status, 403)
                                response.read()
                gateway.assert_not_called()
                gateway.return_value.create_session.return_value = "owned-session"
                for hostname in ("127.0.0.1", "localhost", "[::1]"):
                    with closing(HTTPConnection("127.0.0.1", port)) as client:
                        host = f"{hostname}:{port}"
                        client.request("POST", "/api/assurance/session", "{}",
                                       {"Host": host, "Origin": "http://" + host})
                        response = client.getresponse()
                        self.assertEqual(response.status, 200)
                        self.assertEqual(json.loads(response.read())["session_id"], "owned-session")
                with closing(HTTPConnection("127.0.0.1", port)) as client:
                    client.request("POST", "/api/assurance/session", "{}",
                                   {"Origin": "http://attacker.example"})
                    response = client.getresponse()
                    self.assertEqual(response.status, 403)
                    response.read()
        finally:
            server.shutdown()
            server.server_close()
            worker.join()

    def test_first_call_timeout_blocks_reset_and_different_input(self):
        gateway = AssuranceGateway()
        session_id = gateway.create_session("owner")
        with patch.dict("os.environ", {"CONTRACT_ASSURANCE_LOCAL": "1",
                                      "CONTRACT_ORCHESTRATOR_BASE_URL": "http://127.0.0.1:8090/"}), \
             patch("frontend.assurance_client.OpenAI") as client:
            create = client.return_value.__enter__.return_value.responses.create
            create.side_effect = TimeoutError("Response lost after remote execution")
            with self.assertRaises(TimeoutError):
                gateway.respond("owner", session_id, "Compare")
            for reset in (True, False):
                with self.assertRaisesRegex(RuntimeError, "unresolved"):
                    gateway.respond("owner", session_id, "Reset" if reset else "Different question", reset=reset)
            self.assertEqual(create.call_count, 1)
            self.assertTrue(gateway.sessions[session_id].unresolved)
            self.assertIsNone(gateway.sessions[session_id].previous_response_id)

    def test_never_invoked_session_can_reset_without_claiming_remote_acknowledgement(self):
        gateway = AssuranceGateway()
        session_id = gateway.create_session("owner")
        with patch.dict("os.environ", {"CONTRACT_ASSURANCE_LOCAL": "1",
                                      "CONTRACT_ORCHESTRATOR_BASE_URL": "http://127.0.0.1:8090/"}), \
             patch("frontend.assurance_client.OpenAI") as client:
            result = gateway.respond("owner", session_id, "Reset", reset=True)
            self.assertTrue(result["reset"])
            self.assertNotIn("execution_receipts", result)
            client.return_value.__enter__.return_value.responses.create.assert_not_called()


class PackageReviewTests(unittest.TestCase):
    def test_restage_removes_obsolete_sources_and_binaries(self):
        with TemporaryDirectory() as temporary:
            destination = Path(temporary) / "agent-code"
            stage(destination)
            for name in ("obsolete.py", "leftover.pyd", "leftover.dll", ".env"):
                (destination / "agent" / name).write_text("obsolete", encoding="utf-8")
            stage(destination)
            self.assertFalse(any((destination / "agent" / name).exists()
                                 for name in ("obsolete.py", "leftover.pyd", "leftover.dll", ".env")))
            self.assertTrue((destination / "agent" / "assurance_runtime.py").is_file())
            expected = {Path(".agentignore"), Path("main.py"), Path("requirements.txt")}
            for package in ("agent", "shared"):
                expected.update(Path(package) / source.name for source in (ROOT / package).glob("*.py"))
            expected.update(Path("agent") / source.name for source in (ROOT / "agent").glob("requirements*.txt"))
            self.assertEqual({p.relative_to(destination) for p in destination.rglob("*") if p.is_file()}, expected)

    def test_broad_destination_is_refused(self):
        with TemporaryDirectory() as temporary:
            marker = Path(temporary) / "keep.txt"
            marker.write_text("keep", encoding="utf-8")
            with self.assertRaises(ValueError):
                stage(Path(temporary))
            self.assertTrue(marker.exists())


class TransportReviewTests(unittest.IsolatedAsyncioTestCase):
    async def test_reset_bypasses_expired_continuation_and_replaces_it(self):
        from agent.assurance_protocol import DataPart, Message, Part, Role

        payloads = []
        def respond(request):
            payload = json.loads(request.content)
            payloads.append(payload)
            if "previous_response_id" in payload:
                return httpx.Response(404, json={"error": "expired continuation"})
            message = Message(role=Role.agent, message_id=new_request_id(), context_id="app-context",
                              parts=[Part(root=DataPart(data={"context_reset": True, "evidence": []}))])
            return httpx.Response(200, json={"id": "reset-response", "status": "completed",
                "output": [{"type": "message", "content": [{"type": "output_text",
                    "text": message.model_dump_json(by_alias=True)}]}]})

        real_client = httpx.AsyncClient
        with patch.dict("os.environ", {"CONTRACT_ASSURANCE_LOCAL": "1"}), \
             patch("agent.assurance_runtime.httpx.AsyncClient",
                   side_effect=lambda **kw: real_client(transport=httpx.MockTransport(respond), **kw)):
            remote = ResponsesRemote("http://127.0.0.1:8091/")
            remote.continuations["app-context"] = "expired-response"
            with self.assertRaises(httpx.HTTPStatusError):
                await remote.send("Continue", "app-context")
            _, result = await remote.send("Reset", "app-context", reset=True)
        self.assertTrue(result["context_reset"])
        self.assertNotIn("previous_response_id", payloads[-1])
        self.assertEqual(remote.continuations["app-context"], "reset-response")


class CleanupReviewTests(unittest.IsolatedAsyncioTestCase):
    async def test_cleanup_releases_documents_and_history_but_old_replay_is_rejected(self):
        analyst = OfflineDocumentAnalyst("contract")
        executor = SpecialistExecutor(analyst, "contract", ttl_seconds=10)
        token = PRINCIPAL.set("alice")
        try:
            request = invocation(new_request_id(), metadata={"assurance_action": "generate_findings"})
            await executor.execute(request, Queue())
            self.assertTrue(next(iter(executor.requests.values())).result["artifact"])
            for replay in executor.requests.values():
                replay.created -= 11
            for state in executor.sessions.values():
                state.last_used -= 11
            executor.cleanup()
            self.assertEqual(executor.sessions, {})
            self.assertEqual(executor.requests, {})
            queue = Queue()
            with patch("agent.contract_specialist.time.time", return_value=time.time() + 11):
                await executor.execute(request, queue)
            self.assertEqual(queue.results[-1]["status"], "context_expired")
            self.assertEqual(analyst.calls, 1)
            resumed = invocation(new_request_id(), metadata={"assurance_resume": True})
            await executor.execute(resumed, queue)
            self.assertEqual(queue.results[-1]["status"], "context_expired")
        finally:
            PRINCIPAL.reset(token)

    async def test_cleanup_protects_inflight_and_waiting_replay(self):
        started, release = asyncio.Event(), asyncio.Event()
        class SlowAnalyst(OfflineDocumentAnalyst):
            async def run(self, question, session):
                started.set()
                await release.wait()
                return await super().run(question, session)

        analyst = SlowAnalyst("contract")
        executor = SpecialistExecutor(analyst, "contract", ttl_seconds=10)
        token = PRINCIPAL.set("alice")
        try:
            request = invocation(new_request_id())
            first = asyncio.create_task(executor.execute(request, Queue()))
            await started.wait()
            second = asyncio.create_task(executor.execute(deepcopy(request), Queue()))
            await asyncio.sleep(0)
            state = next(iter(executor.sessions.values()))
            replay = next(iter(executor.requests.values()))
            state.last_used -= 11
            replay.created -= 11
            executor.cleanup()
            self.assertIs(next(iter(executor.sessions.values())), state)
            self.assertIs(next(iter(executor.requests.values())), replay)
            release.set()
            await asyncio.gather(first, second)
            self.assertEqual(analyst.calls, 1)
            self.assertEqual(replay.users, 0)
        finally:
            release.set()
            PRINCIPAL.reset(token)

    async def test_capacity_is_explicit_and_expired_entries_free_space(self):
        executor = SpecialistExecutor(OfflineDocumentAnalyst("contract"), "contract", max_entries=1)
        token = PRINCIPAL.set("alice")
        try:
            await executor.execute(invocation(new_request_id()), Queue())
            with self.assertRaisesRegex(RuntimeError, "capacity"):
                await executor.execute(invocation(new_request_id(), "another"), Queue())
            for replay in executor.requests.values():
                replay.created -= 1801
            for state in executor.sessions.values():
                state.last_used -= 1801
            await executor.execute(invocation(new_request_id(), "another"), Queue())
            self.assertEqual(len(executor.requests), 1)
            self.assertEqual(len(executor.sessions), 1)
        finally:
            PRINCIPAL.reset(token)

    async def test_maintenance_cleans_idle_entries_without_more_calls(self):
        executor = SpecialistExecutor(OfflineDocumentAnalyst("contract"), "contract", ttl_seconds=0.1)
        token = PRINCIPAL.set("alice")
        maintenance = asyncio.create_task(executor.maintain())
        try:
            await executor.execute(invocation(new_request_id()), Queue())
            await asyncio.sleep(0.25)
            self.assertEqual(executor.requests, {})
            self.assertEqual(executor.sessions, {})
        finally:
            maintenance.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await maintenance
            PRINCIPAL.reset(token)


if __name__ == "__main__":
    unittest.main()
