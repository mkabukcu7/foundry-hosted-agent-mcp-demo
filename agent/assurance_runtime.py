"""Remote A2A delegation, isolated context reuse, and content-free tracing."""

import asyncio
from contextlib import AsyncExitStack, contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
import hashlib
import json
import logging
import os
import sys
import time
from urllib.parse import urlsplit
from uuid import uuid4

import httpx
from agent.assurance_protocol import A2ACardResolver, A2AClient, Message, MessageSendParams, Part, Role, SendMessageRequest, TextPart
from azure.identity import DefaultAzureCredential

from agent.assurance_artifacts import ArtifactRejected, read_document, reference


TRACE = ContextVar("assurance_trace", default=None)
PRINCIPAL = ContextVar("assurance_principal", default=None)


class ContextUnavailable(RuntimeError):
    pass


class SpecialistCallFailed(RuntimeError):
    pass


def configure_privacy():
    from agent_framework.observability import disable_instrumentation

    os.environ["OTEL_SDK_DISABLED"] = "true"
    for name in (
        "ENABLE_SENSITIVE_TELEMETRY", "ENABLE_SENSITIVE_DATA", "ENABLE_MESSAGE_EVENTS",
        "ENABLE_CONSOLE_EXPORTERS", "AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED",
    ):
        os.environ[name] = "false"
    disable_instrumentation()
    logging.disable(logging.CRITICAL)


def session_tag(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def conversation_scope(principal, parent):
    return hashlib.sha256(json.dumps([principal, parent]).encode()).hexdigest()


@contextmanager
def metadata_span(role, session_id, reused=False, incoming=None, artifact_ref=None):
    parent = incoming or TRACE.get() or {}
    current = {"trace_id": parent.get("trace_id", uuid4().hex), "span_id": uuid4().hex[:16]}
    token = TRACE.set(current)
    started = time.monotonic()
    success = False
    try:
        yield current
        success = True
    finally:
        TRACE.reset(token)
        if os.getenv("CONTRACT_ASSURANCE_TRACE") == "1":
            print(json.dumps({
                "event": "assurance.call", "role": role,
                "trace_id": current["trace_id"], "span_id": current["span_id"],
                "parent_span_id": parent.get("span_id"),
                "session_tag": session_tag(session_id), "session_reused": reused if success else False,
                "duration_ms": round((time.monotonic() - started) * 1000), "success": success,
                "status": "completed" if success else "failed",
                **({"artifact_ref": artifact_ref} if artifact_ref else {}),
            }), file=sys.stderr, flush=True)


def local_mode():
    return os.getenv("CONTRACT_ASSURANCE_LOCAL") == "1"


def api_version_params(url):
    hostname = urlsplit(url).hostname or ""
    return {"api-version": os.getenv("CONTRACT_ASSURANCE_API_VERSION", "v1")} if hostname.endswith(".services.ai.azure.com") else {}


def validate_endpoint(url):
    parsed = urlsplit(url)
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("Agent URLs cannot contain credentials, query strings, or fragments.")
    if parsed.scheme == "https" and parsed.hostname:
        return
    if local_mode() and parsed.scheme == "http" and parsed.hostname in {"127.0.0.1", "localhost", "::1"}:
        return
    raise ValueError("Use HTTPS for agent endpoints, or explicit local mode with loopback HTTP.")


async def auth_headers(url):
    validate_endpoint(url)
    if local_mode() and urlsplit(url).hostname in {"127.0.0.1", "localhost", "::1"}:
        return {}
    scope = os.getenv("CONTRACT_ASSURANCE_SCOPE", "https://ai.azure.com/.default")
    def acquire():
        with DefaultAzureCredential() as credential:
            return credential.get_token(scope).token
    token = await asyncio.to_thread(acquire)
    headers = {"Authorization": f"Bearer {token}"}
    if urlsplit(url).hostname.endswith(".services.ai.azure.com"):
        from azure.ai.agentserver.core import get_request_context
        headers.update(get_request_context().platform_headers())
    return headers


class A2ARemote:
    def __init__(self, url):
        validate_endpoint(url)
        self.url = url

    async def send(self, question, context_id=None, reset=False, *, request_id=None, action="query", artifact=None,
                   scope=None, abandon_request=None):
        headers = await auth_headers(self.url)
        async with httpx.AsyncClient(headers=headers, params=api_version_params(self.url), timeout=120, follow_redirects=False) as http_client:
            card = await A2ACardResolver(http_client, self.url).get_agent_card()
            if card.protocol_version != "1.0.0" or card.preferred_transport != "JSONRPC":
                raise RuntimeError("Specialist must advertise A2A 1.0 JSONRPC.")
            if card.url.rstrip("/") != self.url.rstrip("/"):
                raise RuntimeError("Agent card URL differs from the configured trusted specialist URL.")
            client = A2AClient(http_client, agent_card=card)
            operation_id = request_id or uuid4().hex
            parts = [Part(root=TextPart(text=question))]
            if artifact is not None:
                parts.extend(Part.model_validate(part) for part in artifact["parts"])
            request = SendMessageRequest(id=operation_id, params=MessageSendParams(
                message=Message(role=Role.user, message_id=operation_id, context_id=context_id,
                                parts=parts),
                metadata={"assurance_reset": reset, "assurance_resume": context_id is not None,
                          "assurance_trace": TRACE.get(), "assurance_action": action,
                          "assurance_scope": scope, "assurance_abandon_request": abandon_request,
                          "assurance_artifact": ({"artifactId": artifact["artifactId"],
                                                   "metadata": artifact["metadata"]} if artifact else None)},
            ))
            response = await client.send_message(request)
        envelope = response.root
        if hasattr(envelope, "error"):
            raise RuntimeError("Specialist returned an A2A error; no comparison was inferred.")
        message = envelope.result
        if not isinstance(message, Message) or not message.context_id:
            raise RuntimeError("Expected a completed specialist Message with contextId.")
        data = [part.root.data for part in message.parts if part.root.kind == "data"]
        if len(data) != 1:
            raise RuntimeError("Specialist returned no structured evidence.")
        if data[0].get("status") == "context_expired":
            raise ContextUnavailable("Specialist context expired or was lost. Explicitly reset the review before continuing.")
        if data[0].get("status") == "call_failed":
            raise SpecialistCallFailed("Specialist call failed without committing history. Retry the same request or reset.")
        if data[0].get("status") in {"artifact_rejected", "scope_rejected"}:
            raise ArtifactRejected("Specialist rejected the artifact or conversation scope; no document was validated.")
        result = data[0]
        file_parts = [part.model_dump(mode="json", by_alias=True) for part in message.parts if part.root.kind == "file"]
        if result.get("artifact_manifest"):
            result["artifact"] = {**result.pop("artifact_manifest"), "parts": file_parts}
        return message.context_id, result


@dataclass
class RemoteContext:
    context_id: str | None = None
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    pending_id: str | None = None
    pending_digest: str | None = None
    reset_required: bool = False


class SpecialistSessions:
    def __init__(self, remotes):
        self.remotes = remotes
        self.contexts = {}
        self.artifacts = {}
        self.handoff_locks = {}

    async def ask(self, principal, parent_session, specialist, question, *, action="query", artifact=None):
        if not principal or not parent_session or specialist not in self.remotes:
            raise ValueError("Trusted principal, parent session, and specialist are required.")
        key = (principal, parent_session, specialist)
        state = self.contexts.setdefault(key, RemoteContext())
        async with state.lock:
            if state.reset_required:
                raise ContextUnavailable("Specialist continuity is unavailable. Explicitly reset the review.")
            digest = hashlib.sha256(json.dumps([question, action, artifact], sort_keys=True).encode()).hexdigest()
            if state.pending_id and state.pending_digest != digest:
                raise SpecialistCallFailed("Previous specialist outcome is unresolved. Retry the same request or explicitly reset.")
            state.pending_id = state.pending_id or uuid4().hex
            state.pending_digest = digest
            reused = state.context_id is not None
            with metadata_span(f"delegate.{specialist}", "|".join(key), reused):
                try:
                    context_id, result = await self.remotes[specialist].send(
                        question, state.context_id, request_id=state.pending_id, action=action, artifact=artifact,
                        scope=conversation_scope(principal, parent_session))
                except ContextUnavailable:
                    state.reset_required = True
                    raise
                if state.context_id is not None and context_id != state.context_id:
                    state.reset_required = True
                    raise RuntimeError("Specialist changed its context unexpectedly.")
                if reused and result.get("context_reused") is not True:
                    state.reset_required = True
                    raise ContextUnavailable("Specialist did not retain its context. Explicitly reset the review.")
                state.context_id = context_id
                state.pending_id = state.pending_digest = None
            return {**result, "session_reused": reused, "session_tag": session_tag(context_id)}

    async def reset(self, principal, parent_session):
        async with self.parent_lock(principal, parent_session):
            await self._reset(principal, parent_session)

    def parent_lock(self, principal, parent_session):
        return self.handoff_locks.setdefault((principal, parent_session), asyncio.Lock())

    async def _reset(self, principal, parent_session):
        states = [(specialist, self.contexts.get((principal, parent_session, specialist)))
                  for specialist in sorted(self.remotes)]
        async with AsyncExitStack() as stack:
            for _, state in states:
                if state is not None:
                    await stack.enter_async_context(state.lock)
                    state.reset_required = True
            for specialist, state in states:
                if state is None:
                    continue
                if state.context_id is not None or state.pending_id:
                    _, result = await self.remotes[specialist].send(
                        "Reset specialist context.", state.context_id, reset=True,
                        request_id=uuid4().hex, action="query", scope=conversation_scope(principal, parent_session),
                        abandon_request=state.pending_id)
                    if not result.get("context_reset"):
                        raise ContextUnavailable("Specialist reset was not acknowledged; continuity remains blocked.")
            for _, state in states:
                if state is None:
                    continue
                state.context_id = None
                state.pending_id = state.pending_digest = None
                state.reset_required = False
            self.artifacts.pop((principal, parent_session), None)

    async def handoff(self, principal, parent_session):
        key = (principal, parent_session)
        lock = self.parent_lock(principal, parent_session)
        async with lock:
            scope = conversation_scope(principal, parent_session)
            pending = self.artifacts.get(key)
            replayed = bool(pending and pending["output"] is not None)
            if pending is None:
                generated = await self.ask(principal, parent_session, "contract",
                    "Generate a synthetic findings document containing all four cited contract clauses.",
                    action="generate_findings")
                artifact = generated.get("artifact")
                if artifact is None:
                    raise ArtifactRejected("Contract Analyst did not return the actual findings document.")
                read_document(artifact, scope, reference(artifact))
                self.artifacts[key] = {"input": artifact, "output": None}
                pending = self.artifacts[key]
            original = pending["input"]
            if pending["output"] is None:
                with metadata_span("artifact.handoff", f"{principal}|{parent_session}", artifact_ref=reference(original)):
                    result = await self.ask(principal, parent_session, "rfp",
                        "Read the attached synthetic findings file completely and annotate it against all RFP commitments.",
                        action="annotate_findings", artifact=original)
                    annotated = result.get("artifact")
                    if annotated is None or result.get("read_artifact") != reference(original):
                        raise ArtifactRejected("RFP Analyst did not acknowledge reading the intended document version.")
                    body, _ = read_document(annotated, scope, reference(annotated))
                    if annotated["metadata"].get("parent") != reference(original):
                        raise ArtifactRejected("Annotated document does not descend from the transmitted findings.")
                    pending["output"] = annotated
                    pending["comparisons"] = body["rfp_annotation"]["comparisons"]
                    pending["session_receipt"] = {"rfp_reused": result["session_reused"],
                                                   "rfp_session_tag": result["session_tag"]}
                    with metadata_span("artifact.annotated", f"{principal}|{parent_session}", artifact_ref=reference(annotated)):
                        pass
            return {"status": "document_validated", "findings": reference(original),
                    "annotated": reference(pending["output"]), "read_artifact": reference(original),
                    "annotation_parent": pending["output"]["metadata"]["parent"], "operation_replayed": replayed,
                    "source_ids": pending["output"]["metadata"]["source_ids"],
                    "comparisons": pending["comparisons"],
                    **(pending["session_receipt"] if not replayed else {"rfp_reused": None,
                        "rfp_session_tag": pending["session_receipt"]["rfp_session_tag"]})}


def trusted_parent(ctx):
    from azure.ai.agentserver.core import get_request_context

    if ctx.session is None:
        raise RuntimeError("A hosted parent AgentSession is required.")
    identity = get_request_context().user_id
    if not identity and local_mode():
        identity = "loopback-demo"
    if not identity:
        raise RuntimeError("No trusted platform caller identity; refusing shared-session delegation.")
    return identity, ctx.session.session_id