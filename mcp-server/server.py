"""Governed HWC tool logic exposed by Azure Functions managed MCP triggers."""

import copy

from shared.data import KNOWLEDGE, get_business_records
from shared.validation import optional_positive_int, required_text

TOOLS = [
    {"name": "search_hwc_knowledge", "description": "Search synthetic governed policy, architecture, and operations documents.", "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}, "category": {"type": "string"}, "maximum_results": {"type": "integer", "minimum": 1}}, "required": ["query"]}},
    {"name": "get_business_summary", "description": "Return a grounded summary for a fictional client or process.", "inputSchema": {"type": "object", "properties": {"entity_id": {"type": "string"}}, "required": ["entity_id"]}},
    {"name": "prepare_follow_up_action", "description": "Prepare a fictional action; never executes without explicit human approval.", "inputSchema": {"type": "object", "properties": {"entity_id": {"type": "string"}, "action_type": {"type": "string"}, "instructions": {"type": "string"}}, "required": ["entity_id", "action_type", "instructions"]}},
]
STATE = {}


def _ensure_state():
    if not STATE:
        STATE.update(get_business_records())


def reset_state():
    STATE.clear()
    _ensure_state()


def call_tool(name, arguments):
    arguments = arguments or {}
    if name == "search_hwc_knowledge":
        query = required_text(arguments.get("query"), "query").lower()
        category = arguments.get("category")
        if category is not None:
            category = required_text(category, "category").lower()
        limit = optional_positive_int(arguments.get("maximum_results"), "maximum_results", 5)
        return [item for item in KNOWLEDGE if (not category or item["category"] == category) and query in (item["title"] + " " + item["summary"]).lower()][:limit]
    if name == "get_business_summary":
        _ensure_state()
        entity_id = required_text(arguments.get("entity_id"), "entity_id").upper()
        if entity_id not in STATE:
            raise KeyError(f"No entity found for {entity_id}")
        return copy.deepcopy(STATE[entity_id])
    if name == "prepare_follow_up_action":
        _ensure_state()
        entity_id = required_text(arguments.get("entity_id"), "entity_id").upper()
        action_type = required_text(arguments.get("action_type"), "action_type")
        instructions = required_text(arguments.get("instructions"), "instructions")
        if entity_id not in STATE:
            raise KeyError(f"No entity found for {entity_id}")
        return {"proposed_action": f"{action_type}: {instructions}", "affected_system": "HWC governed exception tracker", "risk_level": "medium", "approval_requirement": "Explicit human approval required", "execution_status": "PENDING_APPROVAL", "entity_id": entity_id}
    raise KeyError(f"Unknown tool: {name}")


__all__ = ["TOOLS", "call_tool", "reset_state"]








