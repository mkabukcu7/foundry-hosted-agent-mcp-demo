"""Server-owned browser sessions for the real Responses orchestrator only."""

import asyncio
import ast
from dataclasses import dataclass, field
import os
import json
import secrets
from threading import Lock

from openai import OpenAI

from agent.assurance_runtime import api_version_params, auth_headers, validate_endpoint


def execution_receipts(response):
    receipts = []
    for item in getattr(response, "output", []) or []:
        if getattr(item, "type", None) != "function_call_output":
            continue
        value = getattr(item, "output", None)
        try:
            if isinstance(value, str):
                try:
                    value = json.loads(value)
                except ValueError:
                    value = ast.literal_eval(value)
        except (ValueError, TypeError, SyntaxError):
            continue
        if not isinstance(value, dict):
            continue
        if value.get("status") == "comparison_completed":
            comparisons = value.get("comparisons", [])
            receipts.append({"status": "comparison_completed",
                "discrepancy_topics": [item["topic"] for item in comparisons if item["status"] == "discrepancy"],
                "matching_topics": [item["topic"] for item in comparisons if item["status"] == "match"],
                "insufficient_evidence": sum(item["status"] == "insufficient_evidence" for item in comparisons),
                "sessions": {
                name: {key: value.get(f"{name}_analyst", {}).get(key) for key in ("session_reused", "session_tag")}
                for name in ("contract", "rfp")}})
        elif value.get("status") == "document_validated":
            receipts.append({key: value.get(key) for key in
                ("status", "findings", "annotated", "read_artifact", "annotation_parent", "operation_replayed",
                 "source_ids", "rfp_reused", "rfp_session_tag")})
        elif value.get("specialist_contexts_reset") is True:
            receipts.append({"status": "contexts_reset"})
    return receipts


@dataclass
class BrowserSession:
    owner: str
    previous_response_id: str | None = None
    lock: Lock = field(default_factory=Lock)


class AssuranceGateway:
    def __init__(self):
        self.sessions = {}
        self.lock = Lock()

    def create_session(self, owner):
        session_id = secrets.token_urlsafe(32)
        with self.lock:
            self.sessions[session_id] = BrowserSession(owner)
        return session_id

    def respond(self, owner, session_id, prompt, reset=False):
        with self.lock:
            session = self.sessions.get(session_id)
        if not session or not secrets.compare_digest(session.owner, owner):
            raise PermissionError("This assurance session is not owned by this browser.")
        if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 8000:
            raise ValueError("Enter a question of at most 8000 characters.")
        url = os.environ.get("CONTRACT_ORCHESTRATOR_BASE_URL", "").strip()
        if not url:
            raise RuntimeError("Live orchestrator is not configured. No mock fallback is available.")
        validate_endpoint(url)
        headers = asyncio.run(auth_headers(url))
        with session.lock, OpenAI(base_url=url, api_key=headers.get("Authorization", "Bearer local-demo")[7:],
                                 timeout=180, max_retries=0, default_query=api_version_params(url)) as client:
            options = {"input": prompt, "store": True}
            if session.previous_response_id:
                options["previous_response_id"] = session.previous_response_id
            if reset:
                if session.previous_response_id is None:
                    return {"output_text": "Conversation reset.", "mode": "live", "reset": True}
                options["input"] = "Reset both specialist contexts now."
                options["tool_choice"] = {"type": "function", "name": "reset_assurance_context"}
            response = client.responses.create(**options)
            if response.status != "completed":
                raise RuntimeError("Live orchestrator did not complete; no mock result was substituted.")
            receipts = execution_receipts(response)
            if reset and not any(receipt["status"] == "contexts_reset" for receipt in receipts):
                raise RuntimeError("Reset was not confirmed by an execution receipt. Context has not been silently discarded.")
            session.previous_response_id = None if reset else response.id
            return {"output_text": response.output_text, "mode": "live", "reset": reset,
                    "execution_receipts": receipts}