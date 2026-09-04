"""Responses-protocol demo agent using the remote MCP server."""
import json
import os
import urllib.request

class HostedAgent:
    def __init__(self, mcp_url=None):
        self.mcp_url = mcp_url or os.getenv(
            "MCP_SERVER_URL",
            "http://127.0.0.1:8001/runtime/webhooks/mcp",
        )

    def _rpc(self, method, params=None):
        headers = {"Content-Type": "application/json"}
        token = os.getenv("MCP_AUTH_TOKEN")
        if token:
            headers["Authorization"] = "Bearer " + token
        request = urllib.request.Request(self.mcp_url, data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}}).encode(), headers=headers)
        with urllib.request.urlopen(request, timeout=5) as response:
            payload = json.loads(response.read())
        if "error" in payload:
            raise RuntimeError(payload["error"].get("message", "MCP request failed"))
        return payload["result"]

    def discover_tools(self):
        return self._rpc("tools/list")["tools"]

    def call(self, name, arguments):
        result = self._rpc("tools/call", {"name": name, "arguments": arguments})
        return json.loads(result["content"][0]["text"])

    def respond(self, prompt):
        """Return a Responses-style JSON object for either scripted demo prompt."""
        if "follow-up" in prompt.lower() or "follow up" in prompt.lower():
            summary = self.call("get_business_summary", {"entity_id": "HWC-1001"})
            action = self.call("prepare_follow_up_action", {"entity_id": "HWC-1001", "action_type": "Review exception", "instructions": "Coordinate an account-owner review of the overdue reconciliation exception."})
            text = f"Prepared (not executed) action for HWC-1001. Primary risk: {summary['risks'][0]}. Status: {action['execution_status']}. {action['approval_requirement']}."
            return {"object": "response", "output_text": text, "tools_used": ["get_business_summary", "prepare_follow_up_action"], "approval_required": True, "source_ids": summary["supporting_sources"]}
        summary = self.call("get_business_summary", {"entity_id": "HWC-1001"})
        sources = self.call("search_hwc_knowledge", {"query": "exception", "maximum_results": 3})
        text = f"{summary['name']} is {summary['current_status']}. Primary exception: {summary['risks'][0]}. Sources: {', '.join(summary['supporting_sources'])}."
        return {"object": "response", "output_text": text, "tools_used": ["get_business_summary", "search_hwc_knowledge"], "approval_required": False, "source_ids": [item["source_id"] for item in sources]}

if __name__ == "__main__":
    import sys
    print(json.dumps(HostedAgent().respond(" ".join(sys.argv[1:]) or "Summarize HWC-1001"), indent=2))
