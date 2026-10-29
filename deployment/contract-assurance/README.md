# Hosted Deployment Record

## Current State

Verified in the existing `admin-2684` Foundry project on 2026-10-28:

| Agent | Hosted version | Status | Protocol |
| --- | --- | --- | --- |
| `hwc-governed-agent` | 6 | Active, unchanged | Responses 2.0 |
| `assurance-orchestrator` | 3 | Active | Responses 2.0 |
| `contract-analyst` | 2 | Active | A2A 1.0 |
| `rfp-analyst` | 2 | Active | A2A 1.0 |

The three new agents were deployed with explicit approval. They are separate
Foundry hosted agents, not local processes or prompt-agent substitutes. Code
deployment uses the existing project; no customer container registry, project,
networking resource, or evaluation suite was created. Hosted execution/model
usage is billable. The user deferred evaluation-suite creation.

Observed endpoints (the clients preserve `api-version=v1` separately):

- Orchestrator: `https://admin-2684-resource.services.ai.azure.com/api/projects/admin-2684/agents/assurance-orchestrator/endpoint/protocols/openai/responses?api-version=v1`
- Contract: `https://admin-2684-resource.services.ai.azure.com/api/projects/admin-2684/agents/contract-analyst/endpoint/protocols/a2a?api-version=v1`
- RFP: `https://admin-2684-resource.services.ai.azure.com/api/projects/admin-2684/agents/rfp-analyst/endpoint/protocols/a2a?api-version=v1`

The ignored root `.env` contains the real normalized client endpoints, deployed
names/versions, and `CONTRACT_ASSURANCE_LOCAL=0`. The separate azd environment is
`contract-assurance-hosted`; original HWC environment/version are preserved.

## Protocol and Packaging

The live service rejected A2A 0.3 registration and explicitly required 1.0. The
implementation now uses official `a2a-sdk==1.2.3` native 1.0 JSON-RPC routes and
client transport, including the `A2A-Version: 1.0` header. The SDK's supported
conversion helpers retain internal DTOs without sending legacy 0.3 wire traffic.
File bytes, identity/hash/version lineage, isolation, replay, and reset tests pass
through the new wire adapter. Agent Framework core remains pinned at 1.15.0.

Run `scripts/package_assurance.py` to stage the allowlisted code and dependencies
inside `.build/agent-code`. Foundry requires service paths to remain inside this
deployment project. Generated files and local azd environment files are ignored.
The manifest uses Python 3.13 code deployment, not the optional Dockerfile.

Reference: [official A2A migration guide](https://github.com/a2aproject/a2a-python/blob/v1.2.3/docs/migrations/v1_0/README.md).

## Verification and Blocker

Hosted-definition checks passed for orchestrator v3 and both specialist v2
versions. The live checker returned a response but **did not pass execution
verification**, with no execution receipts. Comparison, document handoff, and
specialist session reuse therefore remain **unverified**. Deployment status
alone is not proof of working A2A or MCP integration.

Read-only troubleshooting found two A2A discovery issues and both have since been
corrected with explicit approval. Foundry requires both `a2a` and `responses` on
the specialist endpoint and a published agent card. Endpoint-only updates enabled
both protocols and published each specialist's `agentCard` metadata, preserving
Entra authorization, version selection, and hosted versions. Foundry also rejects
unversioned well-known card discovery and advertises `agentCard/v1.0`; orchestrator
v3 contains the adapter for that path. Both actual cards returned HTTP 200 and
the adapter verified native A2A 1.0 JSON-RPC with matching trusted RPC URLs.
Despite those corrections, the hosted acceptance run still returned no receipts.

The required MCP source update is not deployed. The specialists require
`retrieve_contract_clauses` and `retrieve_rfp_commitments`, but the Function App
still has its earlier published tool set. Existing Function App
`func-api-nowhyh5puoj7q` rejected code publishing with
`BlobUploadFailedException` / deployment-storage HTTP 403. Read-only inspection
found storage `stnowhyh5puoj7q` has public network access disabled, no private
endpoint, and the Function App has no VNet integration. No network controls were
weakened and no storage permission was granted. A deployment path with authorized
private storage connectivity, or an organization-approved exception, is required
before publishing the retrieval-tool update.

The separately approved MCP identity allowlist change succeeded: it retains HWC's
identity and adds only the Contract/RFP specialist identities (three total), with
authentication still required. The failed publish did not deploy the two new
retrieval tools. Fabric and approval workflow configuration were not changed.

After the MCP publishing path is resolved, publish the existing MCP source and
rerun `scripts/verify_contract_assurance.py --live`; retain actual execution
receipts for comparison, exact document-version handoff, and specialist reuse.
Do not treat the current blocked state or passing offline tests as a live pass.