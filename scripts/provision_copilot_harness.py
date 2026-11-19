"""Create versioned Foundry skills and the Copilot Harness RSG demo agent."""

import argparse
import json
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SKILL_PATHS = (
    ROOT / "skills" / "contract-evidence-analysis" / "SKILL.md",
    ROOT / "skills" / "rfp-evidence-analysis" / "SKILL.md",
)


def required_environment(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Set {name} before provisioning the Copilot Harness demo.")
    return value


def read_skill(path: Path) -> tuple[str, str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"{path.relative_to(ROOT)} must start with YAML front matter.")
    front_matter, instructions = text[4:].split("\n---\n", 1)
    fields = {}
    for line in front_matter.splitlines():
        key, separator, value = line.partition(":")
        if separator:
            fields[key.strip()] = value.strip()
    name = fields.get("name")
    description = fields.get("description")
    if not name or not description or not instructions.strip():
        raise ValueError(f"{path.relative_to(ROOT)} is missing name, description, or instructions.")
    return name, description, instructions.strip()


def provision() -> dict:
    try:
        from azure.ai.projects import AIProjectClient
        from azure.ai.projects.models import (
            MCPTool,
            MicrosoftCopilotHarness,
            MicrosoftCopilotToolsetConfig,
            MicrosoftCopilotToolsetDefaultConfig,
            MicrosoftCopilotToolsetPreview,
            PromptAgentDefinition,
            SkillInlineContent,
            SkillReference,
        )
        from azure.identity import DefaultAzureCredential
    except ImportError as error:
        raise RuntimeError(
            "Install agent/requirements-copilot-harness.txt; Copilot Harness support "
            "requires azure-ai-projects 2.7 or later."
        ) from error

    endpoint = required_environment("FOUNDRY_PROJECT_ENDPOINT")
    model = required_environment("AZURE_AI_MODEL_DEPLOYMENT_NAME")
    mcp_url = required_environment("MCP_SERVER_URL")
    connection_id = required_environment("HARNESS_MCP_PROJECT_CONNECTION_ID")
    agent_name = os.getenv("HARNESS_AGENT_NAME", "rsg-contract-assurance-harness").strip()

    skill_versions = []
    with DefaultAzureCredential() as credential, AIProjectClient(
        endpoint=endpoint, credential=credential, allow_preview=True
    ) as project:
        for path in SKILL_PATHS:
            name, description, instructions = read_skill(path)
            created = project.beta.skills.create(
                name=name,
                inline_content=SkillInlineContent(
                    description=description,
                    instructions=instructions,
                ),
                default=True,
            )
            skill_versions.append(SkillReference(name=created.name, version=created.version))

        mcp_tool = MCPTool(
            server_label="rsg-governed-evidence",
            server_url=mcp_url,
            project_connection_id=connection_id,
            allowed_tools=["retrieve_contract_clauses", "retrieve_rfp_commitments"],
            require_approval="never",
        )
        harness_tools = MicrosoftCopilotToolsetPreview(
            default_config=MicrosoftCopilotToolsetDefaultConfig(enabled=False),
            configs=[MicrosoftCopilotToolsetConfig(name="subagents", enabled=True)],
        )
        instructions = (ROOT / "agent" / "harness-instructions.md").read_text(encoding="utf-8")
        definition = PromptAgentDefinition(
            model=model,
            instructions=instructions,
            harness=MicrosoftCopilotHarness(),
            tools=[mcp_tool, harness_tools],
            skills=skill_versions,
        )
        created_agent = project.agents.create_version(
            agent_name=agent_name,
            definition=definition,
            foundry_features="MicrosoftCopilot=V1Preview",
        )

    return {
        "agent_name": created_agent.name,
        "agent_version": created_agent.version,
        "harness": "microsoft_copilot_preview",
        "skills": [{"name": ref.name, "version": ref.version} for ref in skill_versions],
        "mcp_tools": ["retrieve_contract_clauses", "retrieve_rfp_commitments"],
        "harness_tools": ["subagents"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate local skill files and required environment without contacting Foundry.",
    )
    args = parser.parse_args()
    for path in SKILL_PATHS:
        read_skill(path)
    if args.validate_only:
        for name in (
            "FOUNDRY_PROJECT_ENDPOINT",
            "AZURE_AI_MODEL_DEPLOYMENT_NAME",
            "MCP_SERVER_URL",
            "HARNESS_MCP_PROJECT_CONNECTION_ID",
        ):
            required_environment(name)
        print("Copilot Harness configuration is locally valid.")
        return 0
    print(json.dumps(provision(), indent=2))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, RuntimeError, ValueError) as error:
        print(f"Configuration error: {error}", file=sys.stderr)
        sys.exit(2)
