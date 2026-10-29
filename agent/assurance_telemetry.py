"""Export only explicit assurance metadata; never install automatic instrumentation."""

import atexit
import json
import os
import sys

from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.trace import SpanContext, SpanKind, Status, StatusCode, TraceFlags


_processor = None
_resource = None


def configure_metadata_export():
    global _processor, _resource
    if os.getenv("CONTRACT_ASSURANCE_APPINSIGHTS") != "1" or _processor is not None:
        return
    if os.getenv("CONTRACT_ASSURANCE_TRACE") != "1":
        raise ValueError("Application Insights export requires metadata tracing.")
    connection_string = os.environ["APPLICATIONINSIGHTS_CONNECTION_STRING"]
    if not connection_string:
        raise ValueError("Configure the existing Application Insights connection before enabling export.")

    from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter
    from azure.identity import DefaultAzureCredential
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, SpanExportResult

    class MetadataExporter(AzureMonitorTraceExporter):
        def export(self, spans, **kwargs):
            try:
                result = super().export(spans, **kwargs)
            except Exception as error:
                print(json.dumps({"event": "assurance.telemetry_failed",
                                  "error_type": type(error).__name__}), file=sys.stderr, flush=True)
                raise
            if result != SpanExportResult.SUCCESS:
                print(json.dumps({"event": "assurance.telemetry_failed",
                                  "status": result.name}), file=sys.stderr, flush=True)
            return result

    names = {"orchestrator": "assurance-orchestrator", "contract": "contract-analyst", "rfp": "rfp-analyst"}
    _resource = Resource({"service.name": names[os.environ["CONTRACT_ASSURANCE_ROLE"]]})
    _processor = BatchSpanProcessor(
        MetadataExporter(connection_string=connection_string, credential=DefaultAzureCredential(),
                         disable_offline_storage=True),
        schedule_delay_millis=1000,
    )
    atexit.register(_processor.shutdown)
    print(json.dumps({"event": "assurance.telemetry_ready", "content_recording": False}),
          file=sys.stderr, flush=True)


def export_metadata(event, started_ns, finished_ns):
    if _processor is None:
        return
    flags = TraceFlags(TraceFlags.SAMPLED)
    context = SpanContext(int(event["trace_id"], 16), int(event["span_id"], 16), False, flags)
    parent = (SpanContext(context.trace_id, int(event["parent_span_id"], 16), True, flags)
              if event["parent_span_id"] else None)
    allowed = ("role", "session_tag", "session_reused", "duration_ms", "success", "status",
               "error_type", "error_chain", "http_status_code")
    attributes = {f"assurance.{key}": event[key] for key in allowed if key in event}
    if "error_type" in event:
        attributes["error.type"] = event["error_type"]
    if "http_status_code" in event:
        attributes["http.response.status_code"] = event["http_status_code"]
    _processor.on_end(ReadableSpan(
        name=event["role"], context=context, parent=parent, resource=_resource,
        attributes=attributes, kind=SpanKind.INTERNAL,
        status=Status(StatusCode.OK if event["success"] else StatusCode.ERROR),
        start_time=started_ns, end_time=finished_ns,
    ))
