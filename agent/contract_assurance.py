"""Responses-hosted orchestrator and separately hosted specialist calls."""

import asyncio
from contextlib import suppress
import os
from pathlib import Path

from agent_framework import Agent, FunctionInvocationContext, tool
from agent_framework.foundry import FoundryChatClient
from agent_framework_foundry_hosting import ResponsesHostServer
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

from agent.assurance_runtime import ResponsesRemote, SpecialistSessions, configure_privacy, metadata_span, trusted_parent
from shared.contract_assurance import compare_evidence


INSTRUCTIONS = """You are the Vendor Contract Assurance orchestrator.
Northstar Cloud Services (northstar-demo) is fictional. These are demo terms,
not customer facts. This workflow is read-only and cannot approve or modify contracts.
"This vendor" always refers to northstar-demo. This demo has no upload capability;
never request documents, invent upload/checklist steps, or offer unimplemented actions.
For EVERY substantive question, including follow-ups, call consult_specialists with
the user's question and enough topical context from this conversation to resolve
references. Always consult BOTH remote specialists. Never use your own knowledge of
terms. Compare only their returned evidence and cite BOTH source IDs for every
comparison. State discrepancies and matching clauses separately. If evidence is
missing or a specialist fails, abstain; do not infer missing terms or claim success.
Explain business implications briefly, without presenting legal advice.
Keep the comparison under 180 words and follow-up answers under 100 words.
For a broad comparison include all four topics, both values and both source IDs
for each row. Specialists intentionally cannot see each other's document set;
this scope restriction is not an evidence inconsistency. Compare their structured
evidence rather than asking either specialist to perform the comparison.
On reset requests call reset_assurance_context and confirm context was cleared.
For requests to generate or validate a findings document call generate_and_validate_findings.
Only report document handoff as successful when the tool returns document_validated;
cite its actual artifact ID, version, lineage and returned evidence. If a context
expires or a call is unresolved, say an explicit reset or same-request retry is required.
"""


def build_orchestrator(client, sessions):
    @tool
    async def generate_and_validate_findings(ctx: FunctionInvocationContext) -> dict:
        """Have Contract Analyst generate a real file and RFP Analyst read and annotate the same version."""
        principal, parent = trusted_parent(ctx)
        with metadata_span("orchestrator.document_handoff", f"{principal}|{parent}"):
            return await sessions.handoff(principal, parent)

    @tool
    async def consult_specialists(question: str, ctx: FunctionInvocationContext) -> dict:
        """Ask both remote analysts, reuse their own context, and compare their cited evidence."""
        principal, parent = trusted_parent(ctx)
        async with sessions.parent_lock(principal, parent):
            return await compare(question, principal, parent)

    async def compare(question, principal, parent):
        with metadata_span("orchestrator.compare", f"{principal}|{parent}"):
            contract, rfp = await asyncio.gather(
                sessions.ask(principal, parent, "contract",
                             f"Retrieve and explain only the contract evidence relevant to this request. Do not compare the RFP yourself. Request: {question}"),
                sessions.ask(principal, parent, "rfp",
                             f"Retrieve and explain only the RFP commitments relevant to this request. Do not compare the contract yourself. Request: {question}"),
            )
            return {
                "fictional_demo": True,
                "comparisons": compare_evidence(contract.get("evidence", []), rfp.get("evidence", [])),
                "contract_analyst": contract,
                "rfp_analyst": rfp,
                "status": "comparison_completed",
            }

    @tool
    async def reset_assurance_context(ctx: FunctionInvocationContext) -> dict:
        """Clear both remote specialist contexts for this caller and parent conversation only."""
        principal, parent = trusted_parent(ctx)
        await sessions.reset(principal, parent)
        return {"specialist_contexts_reset": True}

    return Agent(client=client, name="Vendor Contract Assurance", instructions=INSTRUCTIONS,
                 tools=[consult_specialists, generate_and_validate_findings, reset_assurance_context],
                 default_options={"store": False, "tool_choice": "required"})


async def main():
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    configure_privacy()
    sessions = SpecialistSessions({
        "contract": ResponsesRemote(os.environ["CONTRACT_ANALYST_URL"]),
        "rfp": ResponsesRemote(os.environ["RFP_ANALYST_URL"]),
    })
    with DefaultAzureCredential() as credential:
        client = FoundryChatClient(project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
                                   model=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"], credential=credential)
        from agent.assurance_runtime import local_mode
        maintenance = asyncio.create_task(sessions.maintain())
        try:
            await ResponsesHostServer(build_orchestrator(client, sessions), configure_observability=None).run_async(
                host="127.0.0.1" if local_mode() else "0.0.0.0", port=int(os.getenv("PORT", "8090")))
        finally:
            maintenance.cancel()
            with suppress(asyncio.CancelledError):
                await maintenance


if __name__ == "__main__":
    asyncio.run(main())