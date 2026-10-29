# Contract Assurance Requirements Audit

**Updated after hosted acceptance, 2026-10-29:** the complete three-turn workflow
passed at 14:55-14:58 UTC against orchestrator v8 and Contract/RFP v5. Original
HWC v6 is unchanged. MCP publishing succeeded; authenticated specialist retrieval,
exact generated-document read/annotation lineage, and stable reused RFP context
are verified by actual execution receipts. Existing Application Insights contains
94 allowlisted metadata spans, including four linked successful business trace
trees. All 39 focused regression/transport/privacy tests pass.

The [hosted deployment record](../deployment/contract-assurance/README.md)
records explicit deployment/network/permission approvals, earlier publishing and
discovery failures, confirmed hosted A2A rejection, and the approved Responses
migration. No new resources, permissions, identities, models, MCP callers, or
features were added by that migration. The HWC manifest, Fabric data path, both
MCP transports, and approval controls remain preserved.

## Coverage

PR #5 follow-up: all five review findings are fixed and 49 focused tests pass.
A real-model local browser demo of the corrected code verified all three turns,
exact document lineage, reset, fresh contexts, and linked metadata traces.
Actual local Host rebinding rejection and expired Responses continuation recovery
were also verified. Corrected Azure redeployment awaits explicit approval;
the earlier hosted results below remain evidence for v8/v5/v5, not these fixes.

| Requirement | Status | Supporting implementation and evidence |
| --- | --- | --- |
| Separately hosted Foundry agents communicate | **HOSTED VERIFIED** | Three distinct `kind: hosted` services in [deployment manifest](../deployment/contract-assurance/azure.yaml); v8/v5/v5 completed real Responses calls with signed caller validation and MCP retrieval. |
| Preserve specialist context per parent/user | **HOSTED REUSE VERIFIED; OFFLINE ISOLATION TESTED** | [Session registry](../agent/assurance_runtime.py) scopes by trusted caller, parent, specialist. [Specialist server](../agent/contract_specialist.py) retains its AgentSession. Both hosted specialist tags stayed stable; follow-ups reported actual reuse. Restart/replica durability and authenticated multi-user frontend remain outside this run. |
| Pass generated documents between agents | **HOSTED VERIFIED** | [Artifact boundary](../agent/assurance_artifacts.py) sends complete inline file bytes in structured Responses input. The RFP read receipt matches the findings ID/version/hash; annotation version 2 references those exact version-1 bytes. |
| Complete real-client scenario and safe traces | **HOSTED VERIFIED** | [Real client](../frontend/assurance_client.py) and [verifier](../scripts/verify_contract_assurance.py) passed all three turns using execution receipts, all eight citations, lineage, and stable RFP reuse. Existing Insights verifies linked comparison/handoff, specialist, and retrieval spans without content export. |
| Explain private Copilot Studio access | **DOCUMENTED; TENANT UNVERIFIED** | [Private connectivity note](copilot-studio-private-connectivity.md) distinguishes Activity-native connector, A2A, and private Responses/custom-connector paths, with official prerequisites and limitations. No networking solution was deployed. |

## Real Call Path and Protocol

Browser -> cookie-owned gateway -> OpenAI-compatible Responses HTTP endpoint ->
real Agent Framework orchestrator -> `consult_specialists` or
`generate_and_validate_findings` -> `ResponsesRemote` -> authenticated specialist
Responses endpoint -> existing specialist executor in a separate hosted service ->
allowlisted Streamable HTTP MCP retrieval -> synthetic document corpus.

The orchestrator tools are local *delegation adapters*, not substitute analyst
functions: specialist reasoning and history live in separate services. Standardized
**Responses** is now the explicitly approved hosted transport, replacing the
unsupported hosted A2A route. This is not a claim of A2A interoperability.
MCP remains retrieval rather than agent delegation. Inline file bytes use the
standard FilePart/FileWithBytes models; document scope, hash, version, reset,
resume, replay, and read receipts are **application conventions**, not claims of
standardized A2A document authorization or lifecycle semantics.

No alternate protocol is silently substituted. The Responses client rejects
hosted A2A URLs, incomplete envelopes, missing structured results, changed
context IDs, expired context, and missing/unauthorized document bytes. The local
A2A adapter remains covered by its existing tests, not used as a fallback.

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
For Foundry ingress, the same signed bearer is forwarded using
`x-client-assurance-authorization`. The boundary validates it with the existing
verifier and removes both credential headers before the Responses host processes
the request; tokens are never stored in Responses content or handler metadata.

The independently authenticated Foundry identity, RBAC, Responses registration,
ingress header preservation,
and specialist continuity were verified in the hosted acceptance run. Application contextId is
not treated as proof of platform session retention. If state is missing, the
application now reports `context_expired` and requires explicit reset rather than
recreating memory and claiming reuse. The in-memory stores are not durable or
cross-replica storage. An authenticated multi-user frontend/OBO flow is not supplied
by the local browser gateway.

## Documents and Retry Semantics

The Contract Analyst creates a synthetic JSON findings document from returned MCP
clauses plus its generated narrative. It is an inline file, not just a summary.
The orchestrator retains those exact bytes and passes them in an authenticated
Responses payload to the RFP Analyst. The receiver verifies scope, hash, size, version,
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
Specialist maintenance now deletes expired history and replay payloads, skips
in-flight/queued work, and caps each registry at 1,024 entries with explicit
capacity errors. Timestamped operation IDs reject stale replay after eviction.
The Responses reset transport omits the prior response ID, retaining explicit
application-context/reset acknowledgement semantics. The browser gateway rejects
non-loopback Host values before creating sessions and fails closed after an
unresolved first or subsequent call, including reset requests.

## Verification Performed

- Installed APIs inspected: Agent Framework core **1.15.0**, Foundry **1.11.0**,
  hosting **1.0.0b260821**, agentserver-core **2.1.0**, Responses **2.2.0b1**,
  official a2a-sdk **1.2.3**, OpenAI **2.54.0**. Public AgentSession snapshot APIs,
  file models, agent version lookup, request-context headers, and hosting tool
  output serialization were checked. The SDK's deprecated A2AClient warning is
  retained as a version constraint, not hidden by upgrading the original runtime.
- [Prior assurance tests](../tests/test_contract_assurance.py) and
  [new audit/handoff tests](../tests/test_assurance_handoff.py) cover three seeded
  gaps, matching EU residency, citations, transport parity, ownership, concurrent
  contexts, expired/lost contexts, failed/retried calls, replay, partial reset,
  document bytes/lineage, missing/stale/unauthorized artifacts, and receipt gating.
- The initial predeployment audit below predates the successful v8/v5/v5 run.
  Current [Responses transport tests](../tests/test_assurance_responses.py),
  handoff, regression and telemetry tests total 39 passing cases. Hosted
  acceptance separately verifies live execution; the offline tests are not its proof.
- New hosted service definitions passed the current official agent JSON schema
  and source-path validation. This is not a container build or hosted deployment.
- Live preflight was run without `--live`; it returned **NOT RUN**. Only a loopback
  orchestrator was configured; observed hosted specialist endpoints, distinct
  names, versions, and authorization were absent. No live model invocation or
  document handoff was attempted during this audit.
- Earlier local-only live results recorded in the README predate this audit's
  artifact/lifecycle changes. They are **not** proof of the complete revised demo
  or separately hosted Foundry communication.

## Remaining Boundaries

1. Session/history stores are in-memory and single-process, not durable or shared
   across replicas. Lost state fails closed and requires explicit reset.
2. The loopback frontend is not an authenticated multi-user/OBO gateway.
3. Private Copilot Studio tenant connectivity remains documented, not deployed
   or verified. The hosted Responses run does not establish that integration.
4. No new feature or evaluation suite was requested or added.

## Official References

- [Hosted protocols, identities, dedicated endpoints and sessions](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/concepts/hosted-agents)
- [A2A 0.3 message and file specification](https://a2a-protocol.org/v0.3.0/specification/)
- [Agent Framework session isolation and service IDs](https://learn.microsoft.com/en-us/agent-framework/agents/conversations/session)
- [Current azd hosted-agent schema](https://raw.githubusercontent.com/Azure/azure-dev/main/cli/azd/extensions/azure.ai.agents/schemas/azure.ai.agent.json)
- [Private Copilot Studio references and limitations](copilot-studio-private-connectivity.md#official-references)