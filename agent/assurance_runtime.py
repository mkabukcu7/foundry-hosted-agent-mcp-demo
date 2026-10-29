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
from agent.assurance_telemetry import configure_metadata_export, export_metadata


TRACE = ContextVar("assurance_trace", default=None)
PRINCIPAL = ContextVar("assurance_principal", default=None)


class ContextUnavailable(RuntimeError):
    pass


class SpecialistCallFailed(RuntimeError):
    pass


def new_request_id():
    return f"{time.time_ns()}-{uuid4().hex}"


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
    configure_metadata_export()


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
    started_ns = time.time_ns()
    success = False
    failure = {}
    try:
        yield current
        success = current.get("http_status_code", 200) < 400 and "error_type" not in current
    except BaseException as error:
        chain = []
        cause = error
        while cause is not None and len(chain) < 6:
            chain.append(type(cause).__name__)
            cause = cause.__cause__ or cause.__context__
        failure = {"error_type": type(error).__name__, "error_chain": ",".join(chain)}
        raise
    finally:
        TRACE.reset(token)
        if os.getenv("CONTRACT_ASSURANCE_TRACE") == "1":
            event = {
                "event": "assurance.call", "role": role,
                "trace_id": current["trace_id"], "span_id": current["span_id"],
                "parent_span_id": parent.get("span_id"),
                "session_tag": session_tag(session_id), "session_reused": reused if success else False,
                "duration_ms": round((time.monotonic() - started) * 1000), "success": success,
                "status": "completed" if success else "failed",
                **failure,
                **({"error_type": current["error_type"]} if "error_type" in current else {}),
                **({"http_status_code": current["http_status_code"]} if "http_status_code" in current else {}),
                **({"artifact_ref": artifact_ref} if artifact_ref else {}),
            }
            print(json.dumps(event), file=sys.stderr, flush=True)
            export_metadata(event, started_ns, time.time_ns())


async def capture_http_status(response):
    current = TRACE.get()
    if current is not None:
        current["http_status_code"] = response.status_code


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

    async def _exchange(self, request):
        with metadata_span("a2a.token", "outbound-credential"):
            headers = await auth_headers(self.url)
        async with httpx.AsyncClient(headers=headers, params=api_version_params(self.url), timeout=120,
                                     follow_redirects=False, event_hooks={"response": [capture_http_status]}) as http_client:
            with metadata_span("a2a.card", "trusted-specialist-card"):
                card = await A2ACardResolver(http_client, self.url).get_agent_card()
                if card.protocol_version != "1.0.0" or card.preferred_transport != "JSONRPC":
                    raise RuntimeError("Specialist must advertise A2A 1.0 JSONRPC.")
                if card.url.rstrip("/") != self.url.rstrip("/"):
                    raise RuntimeError("Agent card URL differs from the configured trusted specialist URL.")
            client = A2AClient(http_client, agent_card=card)
            with metadata_span("a2a.send", "specialist-message"):
                response = await client.send_message(request)
        envelope = response.root
        if hasattr(envelope, "error"):
            raise RuntimeError("Specialist returned an A2A error; no comparison was inferred.")
        return envelope.result

    async def send(self, question, context_id=None, reset=False, *, request_id=None, action="query", artifact=None,
                   scope=None, abandon_request=None):
        operation_id = request_id or new_request_id()
        parts = [Part(root=TextPart(text=question))]
        if artifact is not None:
            parts.extend(Part.model_validate(part) for part in artifact["parts"])
        request = SendMessageRequest(id=operation_id, params=MessageSendParams(
            message=Message(role=Role.user, message_id=operation_id, context_id=context_id, parts=parts),
            metadata={"assurance_reset": reset, "assurance_resume": context_id is not None,
                      "assurance_trace": TRACE.get(), "assurance_action": action,
                      "assurance_scope": scope, "assurance_abandon_request": abandon_request,
                      "assurance_artifact": ({"artifactId": artifact["artifactId"],
                                               "metadata": artifact["metadata"]} if artifact else None)},
        ))
        message = await self._exchange(request)
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


class ResponsesRemote(A2ARemote):
    """Carry the existing structured specialist contract over hosted Responses."""

    def __init__(self, url):
        super().__init__(url)
        if urlsplit(url).hostname.endswith(".services.ai.azure.com") and not url.rstrip("/").endswith("/protocols/openai"):
            raise ValueError("Hosted specialist URLs must use the Responses /protocols/openai base.")
        self.continuations = {}

    async def _exchange(self, request):
        message = request.params.message
        metadata = request.params.metadata or {}
        abandoned = metadata.get("assurance_abandon_request") if metadata.get("assurance_reset") else None
        message.context_id = message.context_id or abandoned or message.message_id
        context_id = message.context_id
        with metadata_span("responses.token", "outbound-credential"):
            headers = await auth_headers(self.url)
        if authorization := headers.get("Authorization"):
            headers["x-client-assurance-authorization"] = authorization
        payload = {"input": request.model_dump_json(by_alias=True, exclude_none=True),
                   "store": True, "stream": False}
        if not metadata.get("assurance_reset") and (previous := self.continuations.get(context_id)):
            payload["previous_response_id"] = previous
        async with httpx.AsyncClient(headers=headers, params=api_version_params(self.url), timeout=180,
                                     follow_redirects=False, event_hooks={"response": [capture_http_status]}) as client:
            with metadata_span("responses.send", "specialist-message"):
                response = await client.post(self.url.rstrip("/") + "/responses", json=payload)
                response.raise_for_status()
                body = response.json()
                if body.get("status") != "completed" or not isinstance(body.get("id"), str) or not body["id"]:
                    raise RuntimeError("Specialist Responses request did not complete.")
                texts = [part["text"] for item in body.get("output", []) if item.get("type") == "message"
                         for part in item.get("content", []) if part.get("type") == "output_text"]
                if len(texts) != 1:
                    raise RuntimeError("Expected one structured specialist response.")
                result = Message.model_validate_json(texts[0])
                if result.role != Role.agent or result.context_id != context_id:
                    raise RuntimeError("Specialist Responses context or role differs from the requested context.")
                self.continuations[context_id] = body["id"]
                return result


@dataclass
class RemoteContext:
    context_id: str | None = None
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    pending_id: str | None = None
    pending_digest: str | None = None
    reset_required: bool = False


class ParentLock:
    def __init__(self):
        self.lock = asyncio.Lock()
        self.users = 0

    async def __aenter__(self):
        self.users += 1
        try:
            await self.lock.acquire()
        except BaseException:
            self.users -= 1
            raise
        return self

    async def __aexit__(self, *_):
        self.lock.release()
        self.users -= 1


class SpecialistSessions:
    def __init__(self, remotes, *, ttl_seconds=1800, max_entries=1024):
        if ttl_seconds <= 0 or max_entries < 1:
            raise ValueError("Parent session TTL and capacity must be positive.")
        self.remotes = remotes
        self.contexts = {}
        self.artifacts = {}
        self.handoff_locks = {}
        self.parent_activity = {}
        self.expired_parents = set()
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries

    def _parent_key(self, principal, parent_session):
        return principal, parent_session

    def _busy(self, key):
        lock = self.handoff_locks.get(key)
        if lock is not None and lock.users:
            return True
        for context_key, state in self.contexts.items():
            if context_key[:2] == key and (state.lock.locked() or state.pending_id or state.reset_required):
                return True
        return False

    def _drop_parent_data(self, key):
        for context_key, state in list(self.contexts.items()):
            if context_key[:2] != key:
                continue
            remote = self.remotes[context_key[2]]
            continuations = getattr(remote, "continuations", None)
            if continuations is not None:
                for context_id in (state.context_id, state.pending_id):
                    if context_id:
                        continuations.pop(context_id, None)
            del self.contexts[context_key]
        self.artifacts.pop(key, None)

    def cleanup(self, now=None):
        now = time.monotonic() if now is None else now
        for key, last_used in list(self.parent_activity.items()):
            if key in self.expired_parents or now - last_used < self.ttl_seconds or self._busy(key):
                continue
            self._drop_parent_data(key)
            self.expired_parents.add(key)
        for key, lock in list(self.handoff_locks.items()):
            if not lock.users and key not in self.parent_activity:
                del self.handoff_locks[key]

    async def maintain(self):
        while True:
            await asyncio.sleep(min(60, self.ttl_seconds / 2))
            self.cleanup()

    def _touch_parent(self, principal, parent_session, *, allow_expired=False):
        self.cleanup()
        key = self._parent_key(principal, parent_session)
        if key in self.expired_parents and not allow_expired:
            raise ContextUnavailable("Parent session expired. Explicitly reset the review before continuing.")
        if key not in self.parent_activity and len(self.parent_activity) >= self.max_entries:
            raise RuntimeError("Parent session capacity is full; explicitly reset an expired review.")
        self.parent_activity[key] = time.monotonic()
        return key

    async def ask(self, principal, parent_session, specialist, question, *, action="query", artifact=None):
        if not principal or not parent_session or specialist not in self.remotes:
            raise ValueError("Trusted principal, parent session, and specialist are required.")
        self._touch_parent(principal, parent_session)
        key = (principal, parent_session, specialist)
        state = self.contexts.setdefault(key, RemoteContext())
        async with state.lock:
            if state.reset_required:
                raise ContextUnavailable("Specialist continuity is unavailable. Explicitly reset the review.")
            digest = hashlib.sha256(json.dumps([question, action, artifact], sort_keys=True).encode()).hexdigest()
            if state.pending_id and state.pending_digest != digest:
                raise SpecialistCallFailed("Previous specialist outcome is unresolved. Retry the same request or explicitly reset.")
            state.pending_id = state.pending_id or new_request_id()
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
                self.parent_activity[(principal, parent_session)] = time.monotonic()
            return {**result, "session_reused": reused, "session_tag": session_tag(context_id)}

    async def reset(self, principal, parent_session):
        key = self.parent_lock(principal, parent_session, allow_expired=True)
        was_expired = (principal, parent_session) in self.expired_parents
        async with key:
            await self._reset(principal, parent_session)
            parent_key = self._parent_key(principal, parent_session)
            self.parent_activity[parent_key] = time.monotonic()
            if was_expired:
                self.expired_parents.discard(parent_key)
                self.parent_activity.pop(parent_key, None)
        if was_expired and not key.users:
            self.handoff_locks.pop((principal, parent_session), None)

    def parent_lock(self, principal, parent_session, *, allow_expired=False):
        key = self._touch_parent(principal, parent_session, allow_expired=allow_expired)
        return self.handoff_locks.setdefault(key, ParentLock())

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
                        request_id=new_request_id(), action="query", scope=conversation_scope(principal, parent_session),
                        abandon_request=state.pending_id)
                    if not result.get("context_reset"):
                        raise ContextUnavailable("Specialist reset was not acknowledged; continuity remains blocked.")
                    continuations = getattr(self.remotes[specialist], "continuations", None)
                    if continuations is not None:
                        for context_id in (state.context_id, state.pending_id):
                            if context_id:
                                continuations.pop(context_id, None)
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