"""Run the acceptance prompts against a real orchestrator, with no mock fallback."""

import json
import argparse
import os
from pathlib import Path
import sys
from urllib.parse import urlsplit

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from frontend.assurance_client import AssuranceGateway


def configured_hosted_agents(environment):
    roles = (("orchestrator", "CONTRACT_ORCHESTRATOR_BASE_URL", "CONTRACT_ORCHESTRATOR_AGENT_NAME", "responses"),
             ("contract", "CONTRACT_ANALYST_URL", "CONTRACT_ANALYST_AGENT_NAME", "responses"),
             ("rfp", "RFP_ANALYST_URL", "RFP_ANALYST_AGENT_NAME", "responses"))
    project = environment.get("FOUNDRY_PROJECT_ENDPOINT", "").rstrip("/")
    configured = []
    if not project.startswith("https://"):
        return [], ["Existing Foundry project endpoint is not configured."]
    for role, url_name, name_key, protocol in roles:
        name = environment.get(name_key, "")
        version = environment.get(name_key + "_VERSION", "")
        url = environment.get(url_name, "").rstrip("/")
        parsed = urlsplit(url)
        base = f"{project}/agents/{name}/endpoint/protocols/"
        suffix = "openai"
        if not name or not version or url != base + suffix or parsed.scheme != "https" or parsed.query or parsed.fragment:
            return [], [f"{role}: provide the observed Foundry endpoint, distinct agent name, and version; loopback is not hosted proof."]
        configured.append((role, name, version, protocol))
    if len({item[1] for item in configured}) != 3:
        return [], ["Three distinct hosted agent names are required."]
    return configured, []


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Invoke already-authorized deployed Foundry agents only.")
    args = parser.parse_args(argv)
    load_dotenv(ROOT / ".env")
    configured, blockers = configured_hosted_agents(os.environ)
    if not args.live:
        blockers.insert(0, "Live execution was not explicitly authorized with --live.")
    if os.getenv("CONTRACT_ASSURANCE_LOCAL") == "1":
        blockers.append("Disable local mode for hosted verification.")
    if blockers:
        print(json.dumps({"status": "NOT RUN", "blockers": blockers}))
        return 2
    from azure.ai.projects import AIProjectClient
    from azure.identity import DefaultAzureCredential
    from agent.assurance_runtime import configure_privacy
    configure_privacy()
    try:
        with DefaultAzureCredential() as credential, AIProjectClient(
            endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"], credential=credential
        ) as project:
            for role, name, version, protocol in configured:
                actual = project.agents.get_version(name, version)
                definition = actual.definition
                if definition.kind != "hosted" or protocol not in {record.protocol for record in definition.protocol_versions or []}:
                    raise ValueError("Agent definition is not hosted or does not declare the required protocol.")
                print(json.dumps({"role": role, "status": "hosted_definition_verified", "version": version}))
    except Exception as error:
        print(json.dumps({"status": "NOT RUN", "stage": "hosted_definition_check", "blocker_type": type(error).__name__}))
        return 2
    gateway = AssuranceGateway()
    session = gateway.create_session("live-verification")
    checks = (
        ("Compare this vendor's contract with its RFP commitments.",
         ["99.95%", "99.5%", "10%", "5%", "24", "72", "EU"]
         + [f"DEMO-NS-{kind}-{index:03d}" for kind in ("CON", "RFP") for index in range(1, 5)]),
        ("Generate synthetic findings, then have the RFP Analyst read and validate the document.", []),
        ("What did they promise instead for service credits?", ["10%", "DEMO-NS-RFP-002"]),
    )
    original_rfp_tag = None
    for index, (prompt, expected) in enumerate(checks, 1):
        try:
            result = gateway.respond("live-verification", session, prompt)
        except Exception as error:
            print(json.dumps({"turn": index, "live_verified": False, "blocker_type": type(error).__name__}))
            return 1
        receipts = result.get("execution_receipts", [])
        passed = all(term in result["output_text"] for term in expected)
        if index in {1, 3}:
            comparison = next((receipt for receipt in receipts if receipt["status"] == "comparison_completed"), None)
            passed = passed and comparison is not None
            if index == 1 and comparison:
                original_rfp_tag = comparison["sessions"]["rfp"]["session_tag"]
                passed = passed and set(comparison["discrepancy_topics"]) == {"uptime", "service_credit", "breach_notification"}
                passed = passed and comparison["matching_topics"] == ["data_residency"] and comparison["insufficient_evidence"] == 0
            if index == 3 and comparison:
                passed = passed and comparison["sessions"]["rfp"]["session_reused"] is True
                passed = passed and comparison["sessions"]["rfp"]["session_tag"] == original_rfp_tag
        else:
            document = next((receipt for receipt in receipts if receipt["status"] == "document_validated"), None)
            passed = passed and document is not None
            if document:
                passed = passed and document["read_artifact"] == document["findings"]
                passed = passed and document["annotation_parent"] == document["findings"] and document["operation_replayed"] is False
                passed = passed and document["annotated"]["version"] == document["findings"]["version"] + 1
                passed = passed and document["annotated"]["artifact_id"] == document["findings"]["artifact_id"]
                passed = passed and document["rfp_reused"] is True and document["rfp_session_tag"] == original_rfp_tag
        print(json.dumps({"turn": index, "live_response": True, "execution_verified": bool(passed), "receipts": receipts}))
        if not passed:
            return 1
    print("Execution receipts passed. Also retain linked metadata-only delegation and handoff spans; flags alone are not integration proof.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())