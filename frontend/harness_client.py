"""Responses client for the managed Foundry Copilot Harness agent."""

import os
from typing import Any


ACTIVITY_TYPES = {
    "function_call",
    "mcp_approval_request",
    "mcp_call",
    "mcp_list_tools",
}


def _dict_value(item: Any) -> dict:
    if isinstance(item, dict):
        return item
    if hasattr(item, "model_dump"):
        return item.model_dump(exclude_none=True)
    values = {}
    for name in ("type", "id", "name", "server_label", "status", "tool_name"):
        if hasattr(item, name):
            values[name] = getattr(item, name)
    return values


def activity_receipts(response: Any) -> list[dict]:
    """Return metadata-only observations; never include model or tool content."""
    receipts = []
    for sequence, item in enumerate(getattr(response, "output", []) or [], start=1):
        values = _dict_value(item)
        item_type = values.get("type")
        if item_type not in ACTIVITY_TYPES:
            continue
        receipt = {"status": "harness_activity", "activity": item_type, "sequence": sequence}
        for key in ("id", "name", "server_label", "tool_name", "status"):
            if values.get(key) is not None:
                receipt[key] = values[key]
        receipts.append(receipt)
    return receipts


class HarnessAssuranceClient:
    """Invoke a declarative prompt agent without implementing an agent loop."""

    def __init__(self, project_factory=None, credential_factory=None):
        self.project_factory = project_factory
        self.credential_factory = credential_factory

    def _factories(self):
        if self.project_factory is not None and self.credential_factory is not None:
            return self.project_factory, self.credential_factory
        from azure.ai.projects import AIProjectClient
        from azure.identity import DefaultAzureCredential
        return AIProjectClient, DefaultAzureCredential

    def respond(self, prompt: str, conversation_id: str | None = None) -> dict:
        endpoint = os.getenv("FOUNDRY_PROJECT_ENDPOINT", "").strip()
        agent_name = os.getenv("HARNESS_AGENT_NAME", "").strip()
        if not endpoint or not agent_name:
            raise RuntimeError(
                "Harness mode requires FOUNDRY_PROJECT_ENDPOINT and HARNESS_AGENT_NAME; no fallback is used."
            )
        project_factory, credential_factory = self._factories()
        with credential_factory() as credential, project_factory(
            endpoint=endpoint, credential=credential, allow_preview=True
        ) as project:
            with project.get_openai_client(agent_name=agent_name) as client:
                if conversation_id is None:
                    conversation_id = client.conversations.create().id
                response = client.responses.create(conversation=conversation_id, input=prompt)
        if getattr(response, "status", None) != "completed":
            raise RuntimeError("The Foundry Copilot Harness did not complete; no mock result was substituted.")
        return {
            "output_text": response.output_text,
            "mode": "live",
            "backend": "harness",
            "conversation_id": conversation_id,
            "execution_receipts": activity_receipts(response),
            "response_id": response.id,
        }
