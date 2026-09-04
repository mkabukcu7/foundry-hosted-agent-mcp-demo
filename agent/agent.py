"""Responses-protocol demo agent using the remote MCP server."""
import asyncio
import ast
import json
import os
import re

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

class HostedAgent:
    def __init__(self, mcp_url=None):
        self.mcp_url = mcp_url or os.getenv(
            "MCP_SERVER_URL",
            "http://127.0.0.1:8001/runtime/webhooks/mcp",
        )

    async def _session_request(self, operation, *args):
        headers = {}
        token = os.getenv("MCP_AUTH_TOKEN")
        if token:
            headers["Authorization"] = "Bearer " + token
        async with streamablehttp_client(self.mcp_url, headers=headers) as streams:
            async with ClientSession(streams[0], streams[1]) as session:
                await session.initialize()
                return await operation(session, *args)

    def discover_tools(self):
        async def list_tools(session):
            result = await session.list_tools()
            return [tool.model_dump(by_alias=True) for tool in result.tools]

        return asyncio.run(self._session_request(list_tools))

    def call(self, name, arguments):
        async def call_tool(session, tool_name, tool_arguments):
            result = await session.call_tool(tool_name, tool_arguments)
            if result.isError:
                details = " ".join(
                    item.text for item in result.content if hasattr(item, "text")
                )
                raise RuntimeError(details or "MCP tool call failed")
            text = result.content[0].text
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return ast.literal_eval(text)

        return asyncio.run(self._session_request(call_tool, name, arguments))

    def respond(self, prompt):
        """Return a Responses-style JSON object for either scripted demo prompt."""
        match = re.search(r"\bHWC-\d+\b", prompt, re.IGNORECASE)
        entity_id = match.group(0).upper() if match else "HWC-1001"
        if "follow-up" in prompt.lower() or "follow up" in prompt.lower():
            summary = self.call("get_business_summary", {"entity_id": entity_id})
            action = self.call("prepare_follow_up_action", {"entity_id": entity_id, "action_type": "Review exception", "instructions": "Coordinate an owner review of the primary exception."})
            text = f"Prepared (not executed) action for {entity_id}. Primary risk: {summary['risks'][0]}. Status: {action['execution_status']}. {action['approval_requirement']}."
            return {"object": "response", "output_text": text, "tools_used": ["get_business_summary", "prepare_follow_up_action"], "approval_required": True, "source_ids": summary["supporting_sources"]}
        summary = self.call("get_business_summary", {"entity_id": entity_id})
        sources = self.call("search_hwc_knowledge", {"query": "exception", "maximum_results": 3})
        text = f"{summary['name']} is {summary['current_status']}. Primary exception: {summary['risks'][0]}. Sources: {', '.join(summary['supporting_sources'])}."
        return {"object": "response", "output_text": text, "tools_used": ["get_business_summary", "search_hwc_knowledge"], "approval_required": False, "source_ids": [item["source_id"] for item in sources]}

if __name__ == "__main__":
    import sys
    print(json.dumps(HostedAgent().respond(" ".join(sys.argv[1:]) or "Summarize HWC-1001"), indent=2))
