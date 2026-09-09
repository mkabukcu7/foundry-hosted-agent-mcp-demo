"""Native local MCP transport for hosts that cannot run Azure Functions."""

from mcp.server.fastmcp import FastMCP

from server import call_tool


mcp = FastMCP(
    "hwc-governed-mcp-local",
    instructions="Expose governed HWC knowledge and proposal-only actions.",
    host="127.0.0.1",
    port=8001,
    streamable_http_path="/runtime/webhooks/mcp",
    stateless_http=True,
)


@mcp.tool()
def search_hwc_knowledge(
    query: str,
    category: str | None = None,
    maximum_results: int | None = None,
) -> list[dict]:
    return call_tool(
        "search_hwc_knowledge",
        {
            "query": query,
            "category": category,
            "maximum_results": maximum_results,
        },
    )


@mcp.tool()
def list_business_summaries(refresh: bool = False) -> list[dict]:
    return call_tool("list_business_summaries", {"refresh": refresh})


@mcp.tool()
def get_business_summary(entity_id: str) -> dict:
    return call_tool("get_business_summary", {"entity_id": entity_id})


@mcp.tool()
def prepare_follow_up_action(
    entity_id: str,
    action_type: str,
    instructions: str,
) -> dict:
    return call_tool(
        "prepare_follow_up_action",
        {
            "entity_id": entity_id,
            "action_type": action_type,
            "instructions": instructions,
        },
    )


if __name__ == "__main__":
    mcp.run(transport="streamable-http")