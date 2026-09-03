"""Microsoft Foundry hosted agent backed by the governed HWC MCP service."""

import asyncio
import os

import httpx
from agent_framework import Agent, MCPStreamableHTTPTool
from agent_framework.foundry import FoundryChatClient
from agent_framework.observability import disable_instrumentation
from agent_framework_foundry_hosting import ResponsesHostServer
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv


INSTRUCTIONS = """You are the HWC governed business assistant.
Use the available MCP tools for every statement about HWC entities, policies,
operations, or architecture. Cite source_id values returned by tools. Never
invent records or sources. Treat prepare_follow_up_action as proposal-only:
state that explicit human approval is required and never claim execution.
Keep customer-facing answers concise and business focused.
"""


async def main() -> None:
    load_dotenv()
    disable_instrumentation()

    credential = DefaultAzureCredential()
    token = os.getenv("MCP_AUTH_TOKEN")
    headers = {"Authorization": f"Bearer {token}"} if token else None
    if audience := os.getenv("MCP_AUDIENCE"):
        access_token = credential.get_token(f"{audience}/.default")
        headers = {"Authorization": f"Bearer {access_token.token}"}
    http_client = httpx.AsyncClient(headers=headers, timeout=30.0)
    mcp_tool = MCPStreamableHTTPTool(
        name="hwc-governed-data",
        url=os.environ["MCP_SERVER_URL"],
        http_client=http_client,
        load_prompts=False,
    )

    client = FoundryChatClient(
        project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
        model=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"],
        credential=credential,
    )
    agent = Agent(
        client=client,
        instructions=INSTRUCTIONS,
        tools=mcp_tool,
        default_options={"store": False},
    )

    try:
        await ResponsesHostServer(agent).run_async()
    finally:
        await http_client.aclose()


if __name__ == "__main__":
    asyncio.run(main())