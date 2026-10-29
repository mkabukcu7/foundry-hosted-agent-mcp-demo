"""Verify that explicit diagnostic export cannot capture application content."""

from contextlib import redirect_stderr
from io import StringIO
import json
import unittest
from unittest.mock import patch

import httpx
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import StatusCode, get_tracer_provider

from agent import assurance_telemetry
from agent.assurance_runtime import A2ARemote, metadata_span


class MetadataTests(unittest.TestCase):
    def test_explicit_export_is_correlated_and_content_free_with_global_sdk_disabled(self):
        exporter = InMemorySpanExporter()
        output = StringIO()
        provider = get_tracer_provider()
        with patch.dict("os.environ", {"CONTRACT_ASSURANCE_TRACE": "1", "OTEL_SDK_DISABLED": "true"}), \
             patch.object(assurance_telemetry, "_processor", SimpleSpanProcessor(exporter)), \
             patch.object(assurance_telemetry, "_resource", Resource({"service.name": "assurance-orchestrator"})), \
             redirect_stderr(output):
            with metadata_span("orchestrator.compare", "private-user-session") as parent:
                try:
                    with metadata_span("a2a.card", "private-session",
                                       artifact_ref={"document": "private document"}) as child:
                        child["http_status_code"] = 403
                        raise httpx.HTTPStatusError(
                            "secret token and prompt", request=httpx.Request("GET", "https://private.example"),
                            response=httpx.Response(403))
                except httpx.HTTPStatusError:
                    pass
        spans = exporter.get_finished_spans()
        self.assertEqual(len(spans), 2)
        failed, root = spans
        self.assertEqual(failed.context.trace_id, int(parent["trace_id"], 16))
        self.assertEqual(failed.parent.span_id, root.context.span_id)
        self.assertEqual(failed.context.span_id, int(child["span_id"], 16))
        self.assertEqual(failed.status.status_code, StatusCode.ERROR)
        self.assertEqual(failed.attributes["error.type"], "HTTPStatusError")
        self.assertEqual(failed.attributes["http.response.status_code"], 403)
        serialized = str([(span.attributes, span.events, span.status.description) for span in spans])
        for sensitive in ("secret token", "prompt", "private-user-session", "private.example", "private document"):
            self.assertNotIn(sensitive, serialized)
        self.assertNotIn("secret token", output.getvalue())
        self.assertIs(provider, get_tracer_provider())
        self.assertEqual(failed.events, ())

    def test_export_is_opt_in_and_missing_destination_fails_explicitly(self):
        with patch.object(assurance_telemetry, "_processor", None), \
             patch.dict("os.environ", {"CONTRACT_ASSURANCE_APPINSIGHTS": "0"}):
            assurance_telemetry.configure_metadata_export()
            self.assertIsNone(assurance_telemetry._processor)
        with patch.object(assurance_telemetry, "_processor", None), \
             patch.dict("os.environ", {"CONTRACT_ASSURANCE_APPINSIGHTS": "1",
                                      "CONTRACT_ASSURANCE_TRACE": "1",
                                      "APPLICATIONINSIGHTS_CONNECTION_STRING": ""}):
            with self.assertRaises(ValueError):
                assurance_telemetry.configure_metadata_export()


class StageTests(unittest.IsolatedAsyncioTestCase):
    async def test_card_failure_records_the_http_status_and_stage_without_sending_message(self):
        output = StringIO()
        requests = []

        def respond(request):
            requests.append(request)
            return httpx.Response(403, json={"error": "sensitive server detail"})

        real_client = httpx.AsyncClient

        def client_factory(**kwargs):
            return real_client(transport=httpx.MockTransport(respond), **kwargs)

        with patch.dict("os.environ", {"CONTRACT_ASSURANCE_LOCAL": "1", "CONTRACT_ASSURANCE_TRACE": "1"}), \
             patch("agent.assurance_runtime.httpx.AsyncClient", side_effect=client_factory), \
             redirect_stderr(output):
            with self.assertRaises(Exception):
                await A2ARemote("http://127.0.0.1:8091/").send("private prompt")
        events = [json.loads(line) for line in output.getvalue().splitlines()]
        self.assertEqual([event["role"] for event in events], ["a2a.token", "a2a.card"])
        self.assertTrue(events[0]["success"])
        self.assertFalse(events[1]["success"])
        self.assertEqual(events[1]["http_status_code"], 403)
        self.assertEqual(len(requests), 1)
        self.assertNotIn("private prompt", output.getvalue())
        self.assertNotIn("sensitive server detail", output.getvalue())


if __name__ == "__main__":
    unittest.main()
