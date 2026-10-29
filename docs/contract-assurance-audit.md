# Contract Assurance Requirements Audit

**Historical predeployment audit:** the later user-approved deployments and
current live verification result are in the
[hosted deployment record](../deployment/contract-assurance/README.md), which
supersedes the deployment/version status below. Four agents are now active;
the complete deployed workflow remains unverified due to the documented MCP
publishing blocker.

Current branch: `feature/contract-assurance`. Changes extend the existing feature;
the HWC deployment manifest, Fabric data path, both MCP transports, and approval
controls are preserved. No production data, deployments, new Azure resources,
permission changes, or new approval workflow were used.

## Coverage

| Requirement | Status | Supporting implementation and evidence |
| --- | --- | --- |
| Separately hosted Foundry agents communicate | **BLOCKED / UNVERIFIED live** | Three distinct `kind: hosted` service definitions in [deployment manifest](../deployment/contract-assurance/azure.yaml), role-isolated [entrypoint](../agent/assurance_host.py), and source-allowlisted container. Definition schema and source paths validated; image build, platform ingress, and deployed calls NOT RUN. |
| Preserve specialist context per parent/user | **IMPLEMENTED; OFFLINE TESTED** | [Session registry](../agent/assurance_runtime.py) scopes by trusted caller, parent, specialist. [Specialist server](../agent/contract_specialist.py) retains its own AgentSession. Expiry/restart fails closed, request replay is idempotent, model failure rolls back history, reset requires acknowledgements and is owner-scoped. Hosted sandbox continuity remains UNVERIFIED. |
| Pass generated documents between agents | **IMPLEMENTED; MOCK-ONLY integration evidence** | [Artifact boundary](../agent/assurance_artifacts.py) and A2A FilePart transport send complete bytes from Contract Analyst via orchestrator to RFP Analyst, which receives the full JSON in its model input, annotates against MCP evidence, and acknowledges the exact ID/version/hash. The SDK round-trip uses explicitly fake analysts. No deployed/model-backed handoff has been demonstrated in this audit. |
| Complete real-client scenario and safe traces | **IMPLEMENTED verifier; LIVE NOT RUN** | [Real client](../frontend/assurance_client.py) reads actual Responses function-call outputs, not model assertions. [Verifier](../scripts/verify_contract_assurance.py) checks actual hosted definitions, three distinct observed endpoints, gap/residency receipts, document lineage/read receipt, and stable reused RFP context. [UI](../frontend/contract-assurance.html) renders execution receipts. |
| Explain private Copilot Studio access | **DOCUMENTED; TENANT UNVERIFIED** | [Private connectivity note](copilot-studio-private-connectivity.md) distinguishes Activity-native connector, A2A, and private Responses/custom-connector paths, with official prerequisites and limitations. No networking solution was deployed. |

## Real Call Path and Protocol

Browser -> cookie-owned gateway -> OpenAI-compatible Responses HTTP endpoint ->
real Agent Framework orchestrator -> `consult_specialists` or
`generate_and_validate_findings` -> `A2ARemote` -> discovered specialist card ->
official SDK JSON-RPC `message/send` -> separate specialist service ->
allowlisted Streamable HTTP MCP retrieval -> synthetic document corpus.

The orchestrator tools are local *delegation adapters*, not substitute analyst
functions: specialist reasoning and history live in separate services. Standardized
**A2A 0.3 JSON-RPC** is used between agents. The browser's Responses calls are not
A2A, and MCP is retrieval rather than agent delegation. A2A file bytes use the
standard FilePart/FileWithBytes models; document scope, hash, version, reset,
resume, replay, and read receipts are **application conventions**, not claims of
standardized A2A document authorization or lifecycle semantics.

No alternate protocol is silently substituted when A2A is unsupported. The pinned
client rejects incompatible cards, mismatched advertised URLs, missing structured
results, expired context, or missing/unauthorized document bytes.

## Authentication and Hosting Boundaries

Local mode is explicit loopback-only anonymous development and is **not** Foundry
hosting. Nonlocal calls use HTTPS and DefaultAzureCredential bearer tokens, with
the Foundry scope `https://ai.azure.com/.default` unless explicitly configured.
The installed request-context API forwards the opaque Foundry call-ID header only
on first-party Foundry calls; it does not forward a caller-provided user ID.
Specialist ingress validates JWT signature, issuer, tenant, audience and expiry.
It also requires `CONTRACT_ASSURANCE_ALLOWED_CALLER_IDS` containing only existing
authorized caller object IDs; a valid tenant token alone is insufficient. Auth
mode is fixed at startup. No role assignments are created or broadened.
MCP retains its existing token/audience configuration; tokens refresh on connection.

The independently authenticated Foundry identity, RBAC, A2A protocol registration,
well-known card path, advertised endpoint rewriting, ingress header preservation,
and routing to the same specialist sandbox **must be verified**. A2A contextId is
not treated as proof of platform session retention. If state is missing, the
application now reports `context_expired` and requires explicit reset rather than
recreating memory and claiming reuse. The in-memory stores are not durable or
cross-replica storage. An authenticated multi-user frontend/OBO flow is not supplied
by the local browser gateway.

## Documents and Retry Semantics

The Contract Analyst creates a synthetic JSON findings document from returned MCP
clauses plus its generated narrative. It is an inline file, not just a summary.
The orchestrator retains those exact bytes and passes them in an authenticated
A2A message to the RFP Analyst. The receiver verifies scope, hash, size, version,
and latest-known version before passing the complete decoded document to its model.
Its annotation preserves artifact ID, increments version, records the parent
ID/version/hash, retains the original findings, and adds cited RFP comparisons.
The orchestrator validates the read receipt and parent reference. No file URLs,
public links, embedded credentials, shared storage service, or new permissions
are needed. Hashes provide integrity; authenticated transport and server-owned
conversation mappings supply the authorization boundary.

Same logical call retries reuse one message ID. Successful replies are replayed
without advancing model history; failed calls restore the prior session. An
ambiguous outcome blocks a different request until the same operation is retried
or explicitly reset. Concurrent parent operations serialize with reset; partial
reset failure leaves both specialists blocked rather than claiming success.
Caches and history are process-local and expire; restart/expiry requires reset.

## Verification Performed

- Installed APIs inspected: Agent Framework core **1.15.0**, Foundry **1.11.0**,
  hosting **1.0.0b260821**, agentserver-core **2.1.0**, Responses **2.2.0b1**,
  official a2a-sdk **0.3.22**, OpenAI **2.54.0**. Public AgentSession snapshot APIs,
  file models, agent version lookup, request-context headers, and hosting tool
  output serialization were checked. The SDK's deprecated A2AClient warning is
  retained as a version constraint, not hidden by upgrading the original runtime.
- [Prior assurance tests](../tests/test_contract_assurance.py) and
  [new audit/handoff tests](../tests/test_assurance_handoff.py) cover three seeded
  gaps, matching EU residency, citations, transport parity, ownership, concurrent
  contexts, expired/lost contexts, failed/retried calls, replay, partial reset,
  document bytes/lineage, missing/stale/unauthorized artifacts, and receipt gating.
- New hosted service definitions passed the current official agent JSON schema
  and source-path validation. This is not a container build or hosted deployment.
- Live preflight was run without `--live`; it returned **NOT RUN**. Only a loopback
  orchestrator was configured; observed hosted specialist endpoints, distinct
  names, versions, and authorization were absent. No live model invocation or
  document handoff was attempted during this audit.
- Earlier local-only live results recorded in the README predate this audit's
  artifact/lifecycle changes. They are **not** proof of the complete revised demo
  or separately hosted Foundry communication.

## Remaining Prerequisites

1. Supply three already-deployed, authorized Foundry hosted agent names/versions
   and their observed protocol endpoints. Do not infer URLs from a flag.
2. Verify A2A 0.3 is enabled on specialist versions and that the card, ingress
   authentication, platform headers and sandbox routing match the adapter.
3. Verify existing invocation/MCP permissions, private DNS/routing, and an
   authenticated end-user frontend/session boundary. No permission grants occur here.
4. In that authorized environment run the documented verifier with `--live` and
   retain linked metadata-only spans plus execution receipts. Model text or
   passing mock tests cannot satisfy these gates.

## Official References

- [Hosted protocols, identities, dedicated endpoints and sessions](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/concepts/hosted-agents)
- [A2A 0.3 message and file specification](https://a2a-protocol.org/v0.3.0/specification/)
- [Agent Framework session isolation and service IDs](https://learn.microsoft.com/en-us/agent-framework/agents/conversations/session)
- [Current azd hosted-agent schema](https://raw.githubusercontent.com/Azure/azure-dev/main/cli/azd/extensions/azure.ai.agents/schemas/azure.ai.agent.json)
- [Private Copilot Studio references and limitations](copilot-studio-private-connectivity.md#official-references)