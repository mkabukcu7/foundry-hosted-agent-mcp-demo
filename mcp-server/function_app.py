"""Azure Functions managed MCP tool triggers for the HWC demo."""

import azure.functions as func

from server import call_tool


app = func.FunctionApp()


@app.mcp_tool()
@app.mcp_tool_property(
    arg_name="query",
    description="Terms to find in governed HWC knowledge.",
    is_required=True,
)
@app.mcp_tool_property(
    arg_name="category",
    description="Optional policy, architecture, or operations category.",
    is_required=False,
)
@app.mcp_tool_property(
    arg_name="maximum_results",
    description="Optional positive maximum number of results.",
    is_required=False,
)
def search_hwc_knowledge(
    query: str,
    category: str | None = None,
    maximum_results: int | None = None,
) -> list[dict]:
    """Search synthetic governed HWC knowledge and return source identifiers."""
    return call_tool(
        "search_hwc_knowledge",
        {
            "query": query,
            "category": category,
            "maximum_results": maximum_results,
        },
    )


@app.mcp_tool()
@app.mcp_tool_property(
    arg_name="entity_id",
    description="The fictional HWC client or process identifier.",
    is_required=True,
)
def get_business_summary(entity_id: str) -> dict:
    """Return a governed summary for a fictional HWC client or process."""
    return call_tool("get_business_summary", {"entity_id": entity_id})


@app.mcp_tool()
@app.mcp_tool_property(
    arg_name="entity_id",
    description="The fictional HWC client or process identifier.",
    is_required=True,
)
@app.mcp_tool_property(
    arg_name="action_type",
    description="The type of follow-up to propose.",
    is_required=True,
)
@app.mcp_tool_property(
    arg_name="instructions",
    description="The proposed follow-up instructions.",
    is_required=True,
)
def prepare_follow_up_action(
    entity_id: str,
    action_type: str,
    instructions: str,
) -> dict:
    """Prepare a fictional action that always requires explicit approval."""
    return call_tool(
        "prepare_follow_up_action",
        {
            "entity_id": entity_id,
            "action_type": action_type,
            "instructions": instructions,
        },
    )
