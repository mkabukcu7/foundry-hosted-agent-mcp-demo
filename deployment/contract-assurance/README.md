# Hosted Deployment Record

## Current State

Rechecked in the existing `admin-2684` Foundry project on 2026-10-29.
**MCP publishing and the complete three-turn hosted conversation passed.**
The successful run at 14:55-14:58 UTC uses the explicitly approved Responses
migration; earlier A2A failures below are historical.
After initially stopping cloud changes and declining a temporary private runner,
the user approved read-only diagnosis and one controlled MCP publish retry.
That retry succeeded without further network, identity, or permission changes.

### PR #5 Fixes: Corrected Hosted And Browser Verification (22:34-22:45 UTC)

- After the initial local-only demo below, the user requested hosted testing.
  Corrected source commit `6de79f7` was deployed to the three existing assurance
  agents only: orchestrator v9, Contract v6, RFP v6. All are active with unchanged
  principals and matching source package hash
  `fb0570aafbb2884e18e3a5057b8ff7db98bc45c3e829571dbaec5fa660c4f3b0`.
  No provisioning, permission, identity, model, or MCP caller changes occurred.
  The deferred evaluation-suite decision is unchanged.
- The hosted verifier checked all three hosted definitions and passed the three
  existing turns at 22:34:58-22:40:10 UTC: three discrepancies/EU match and all
  eight citations; exact version-1 findings read and version-2 annotation lineage;
  and the 10% service-credit follow-up with the same reused RFP context.
  Additional calls verified the actual `contexts_reset` receipt and fresh
  Contract/RFP contexts with new tags afterward.
- The verifier's artifact `690e7b586d9c42eb838dee7f19ab794e` version 1 had SHA-256
  `7d7b671c67b47666bc23242478cadc836252dab9eaa4e5ab83fc95c1d3942c83`;
  both the read receipt and annotation parent matched that exact reference.
  Version 2 had SHA-256
  `550d643ad2d1f82ac551a7eb5a54d8644c30fd838a871d6956fa9f14b3119631`.
- A fresh real-browser run then repeated all five actions through the loopback
  gateway to Azure v9/v6/v6 and the deployed authenticated MCP service.
  Every response was HTTP 200/live; no rendered errors remained. RFP tag
  `a5633378fb26b7d6` was reused for handoff/follow-up, then changed to
  `ab898ebcd3785b39` with reuse false after acknowledged reset. Contract tags
  similarly changed from `02c62649c014c4ee` to `a74c8b73258e942b`.
  Browser artifact `c80bdc83d0a848549f5f7ad546a6775b` version-1 read/parent
  SHA-256 was `907e1483721119e5321ea4bd27347fe70e58df74055f7babc75ceda223ad055f`;
  version 2 was `a1dbdc718cdf323ce83b25bf1fe2b3866303c75958c963b733a9cc57b7b1389f`.
- Existing `appi-nowhyh5puoj7q` contains 330 metadata spans for those two runs:
  ten fully linked successful business trees (134 business spans), 24 successful
  specialist sends, 24 successful authorizations, and 20 successful retrievals.
  Authorization and MCP HTTP diagnostics are separate from the business trees.
  All 24 unsuccessful diagnostic spans were MCP HTTP 405; no failed retrieval
  or business descendant occurred in the completed runs.

  | Operation | Acceptance trace ID | Browser trace ID |
  | --- | --- | --- |
  | Initial comparison | `a0e897c9d10c4b0bb6d9847b8bf05c94` | `8adb67c9ec6c44048da27ea5894667a1` |
  | Document handoff | `1cda151ed4ed4930b6fda4277f18d2fd` | `bf37c51b79de45afacc5f89a59cb0454` |
  | Document-turn comparison | `fe07cf997ce5458ca91f3e78819fd650` | `1dfcd5af75b149a2860148865bf4850a` |
  | Service-credit follow-up | `3d0c295e438c491d991a9e609d6c74ec` | `4524eb460a3f4b079f45892cf599b299` |
  | Fresh comparison after reset | `4dfc88782bbf473085d317a5ff98b59d` | `947061c2c48347b3aa58c09c2c85d1f5` |

- An earlier browser attempt completed comparison but reported
  `ERR_NETWORK_IO_SUSPENDED` during handoff; associated cancellation spans are
  retained separately. It was not counted as a passing browser run. The fresh
  browser run above completed without suspension or business failures.
- The Azure MCP log-query identity returned insufficient access; the existing
  authenticated Azure CLI identity successfully queried the same Insights app
  without permission changes. A KQL reserved-word alias was corrected during
  query setup. Telemetry assertions account for the exporter's root parent-ID
  representation while requiring every business descendant's real parent.
- TTL/capacity, lost-first-response refusal, and stale-continuation injection
  remain focused regression/local-live checks, not claimed injected into Azure.
  In-memory restart/replica durability and production multi-user authentication
  remain outside this acceptance run.

### Historical Predeployment Local Review-Fix Verification

- All five review findings are fixed: loopback Host validation before assurance
  session creation/forwarding, reset without stale specialist Responses
  continuation, bounded specialist cleanup, fail-closed unresolved browser calls,
  and clean source-only restaging.
- The focused suite now passes 49 tests, including 10 new review regressions.
  Compile and whitespace checks pass. Cleanup tests cover expired document/history
  eviction, old replay rejection, active/queued-call protection, explicit capacity
  limits, and idle periodic maintenance. Retries keep timestamped operation IDs;
  after expiry they fail closed instead of re-running an evicted request.
- A corrected-code browser demo used separate local agents with the existing real
  Foundry model and the local synthetic MCP service. No Azure resource or
  permission changes, provisioning, or deployment occurred. Hosted redeployment
  approval was unavailable at that point; Azure still used v8/v5/v5.
  This local run was not hosted verification; the later approved run is above.
- All three browser turns passed: three discrepancies/matching EU residency with
  eight citations; exact generated-document read and version-2 annotation lineage;
  and service-credit follow-up with the same reused RFP context. Reset received
  the actual `contexts_reset` receipt; the next comparison had new specialist
  tags and `session_reused=false`. No browser error messages appeared.
- Synthetic artifact `da132edc9be3493ba0f21ad95d2943c9` version 1 read/parent
  SHA-256 was `e0cf2fad4d4a5af259ed8d804ce52b708ec41d3b11ca232eb3f0cecf0e966f50`.
  The version-2 annotation retained that exact parent reference.
- Manual local metadata confirmed 12 successful specialist sends, 10 successful
  retrievals, and five fully linked successful business trees:

  | Operation | Trace ID |
  | --- | --- |
  | Initial comparison | `34a9c906bc3b458891a7d48179625c3d` |
  | Document handoff | `74224f9ae8204e1cabcaa3d3176f7e9e` |
  | Document-turn comparison | `8ba2883680324babaa413cd4995ce258` |
  | Service-credit follow-up | `8ee9509b1c934a6f885821a548fdb6ba` |
  | Fresh comparison after reset | `10afb1ab808943e7ae4316f582d74eb7` |

- An actual request with matching attacker Host/Origin returned 403 before
  session creation. A separate live specialist test intentionally supplied a lost
  continuation: the real Responses host rejected it with HTTP 400, then the
  corrected reset succeeded without that continuation and the next model call
  confirmed fresh history. Other failure paths are covered by deterministic
  regression tests, not claimed injected into Azure.

### MCP Publish Result (13:04 UTC)

- Deployment `06b89ba7-8192-46fa-8dc8-bee34a403d57`, `LegionOneDeploy`,
  remote build: status `4` (success), complete and active.
- Started `2026-10-29T13:04:17Z`; completed `2026-10-29T13:04:35Z`.
- Azure indexed six enabled `mcpToolTrigger` functions:
  `get_business_summary`, `list_business_summaries`,
  `prepare_follow_up_action`, `retrieve_contract_clauses`,
  `retrieve_rfp_commitments`, and `search_hwc_knowledge`.
- Storage still has `publicNetworkAccess=Disabled` and
  `allowSharedKeyAccess=false`. Anonymous access to the MCP endpoint returns 401.
- No temporary runner, new role assignment, or public-storage exception was
  needed. Subsequent hosted acceptance also verified authenticated tool execution
  through both specialists.

| Agent | Hosted version | Status | Protocol |
| --- | --- | --- | --- |
| `hwc-governed-agent` | 6 | Active, unchanged | Responses 2.0 |
| `assurance-orchestrator` | 9 | Active, corrected acceptance/reset passed | Responses 2.0 |
| `contract-analyst` | 6 | Active, authenticated retrieval verified | Responses 2.0 |
| `rfp-analyst` | 6 | Active, handoff and reuse verified | Responses 2.0 |

The three new agents were deployed with explicit approval. They are separate
Foundry hosted agents, not local processes or prompt-agent substitutes. Original code
deployment uses the existing project; no customer container registry, project,
networking resource, or evaluation suite was created in that original deployment.
The separately approved private networking added on 2026-10-29 is recorded below.
Hosted execution/model
usage is billable. The user deferred evaluation-suite creation.

### Browser End-to-End Recheck (15:05-15:11 UTC)

- A fresh real-browser conversation used the loopback frontend HTTP gateway
  against the existing hosted v8/v5/v5 agents, with local/mock mode disabled.
  No deployment or Azure configuration changes were needed.
- All three UI actions passed execution-receipt assertions: comparison with
  all eight citations, generated findings read/annotated with exact ID/version/
  SHA-256 lineage, and the 10% service-credit follow-up with the same reused RFP
  context. The browser displayed live receipts and no error messages.
- Findings artifact `f2f9b05196414601b56f45f0308e7cd5` version 1 had SHA-256
  `4fa320b5c98c4a80d58574257350914ab793229cb90330e1c00e5a15004a9fa0`.
  The RFP read receipt and version-2 annotation parent matched that exact
  reference; the annotation digest was
  `881be1d65ca9bb7bf664e7af36929fb82118546c9ea0932e9d2bbbc50840d376`.
- Browser reset returned the actual `contexts_reset` receipt and cleared the
  displayed conversation. A subsequent comparison returned new Contract/RFP
  session tags with `session_reused=false`, distinct from the original tags.
- The bounded Insights query returned 141 metadata-only spans and 12 successful
  specialist Responses sends (including both reset calls). All five business
  trace trees passed success and delegate/specialist/retrieval parent-link checks:

  | Browser operation | Trace ID |
  | --- | --- |
  | Initial comparison | `ded4d8af3235412e9aae731dd788a4fc` |
  | Document handoff | `a37ba96d8b09479c8417d403fe75e6e2` |
  | Document-turn comparison | `c8093154fb49492489b924c94978a8ad` |
  | Service-credit follow-up | `9556aeab5c7f47b3927f531d21ab739c` |
  | Fresh comparison after reset | `7c7b0c5274cb4b3ba10fa0aa5b9cdebb` |

- This verifies browser -> gateway -> hosted orchestrator -> hosted specialists
  -> authenticated MCP -> returned evidence/document -> rendered UI, plus reset.
  It does not expand the production/multi-user/durability boundaries below.

### Responses Migration and Successful Hosted Acceptance (14:58 UTC)

- User selected Responses communication between the existing agents and explicitly
  approved all three redeployments, specialist URL changes, full acceptance, and
  querying existing `appi-nowhyh5puoj7q`. No new resources, identities, models,
  permissions, MCP callers, features, or evaluation suite were added in this migration.
- Initial Responses versions v7/v4/v4 reached the specialist containers but returned
  HTTP 401 before `specialist.authorize`. Foundry consumes normal Authorization
  at ingress. The installed SDK documents `x-client-` pass-through headers.
- Corrective versions v8/v5/v5 send the same signed bearer in
  `x-client-assurance-authorization`. The existing specialist boundary validates
  signature, issuer, tenant, audience, expiry and allowed caller, then removes
  both credential headers before handing the request to the Responses host.
  Credentials are never put in stored input, metadata, or trace content.
  Actual hosted execution confirms this path works; no JWT bypass was introduced.
- Fresh hosted acceptance ran from `2026-10-29T14:55:22Z` through
  `2026-10-29T14:58:46Z`, exited 0, and completed all three turns:
  1. Three discrepancies (uptime, service credit, breach notification), matching
     EU residency, all eight source citations, and no missing evidence.
  2. Complete generated findings read by RFP with identical artifact ID, version 1,
     and SHA-256; annotation version 2 points back to those exact parent bytes.
  3. Service-credit follow-up resolves to the 10% RFP promise and reuses the same
     RFP session as turn 1. Contract and RFP tags stay stable across all calls.
- Existing Insights returned 94 allowlisted metadata spans for the bounded run:
  eight `responses.send` HTTP 200, eight successful `specialist.authorize`,
  eight successful `mcp.retrieve`, and successful artifact handoff/annotation.
  Four MCP HTTP 405 spans occurred outside the successful business trace trees;
  they do not represent failed retrieval in this run.
- Each business tree has linked delegate, specialist, and retrieval parents:

  | Operation | Trace ID |
  | --- | --- |
  | Turn 1 comparison | `1eafe6f7b94c449582138817eadb680f` |
  | Turn 2 comparison | `45494c3cdebb46f79ceee88ba917cae4` |
  | Turn 2 document handoff | `bc7a75eaddb640198c1ec320b2503885` |
  | Turn 3 service-credit comparison | `019fd4a70411442482b51373fbead708` |

- Manual telemetry contains only stage, success/status, timing, hashed session
  tags/reuse, and trace linkage; no prompts, documents, bearer tokens, or model
  completions. All 39 focused regression/transport/privacy tests, compile checks,
  and whitespace validation pass.
- Continuation and history remain in-memory/single-process. This successful run
  does not certify durability across restart/replica changes, browser multi-user
  authentication, or private Copilot Studio integration.

### Same-Token Discovery Comparison (13:49 UTC)

- User explicitly approved an orchestrator-only diagnostic redeployment and
  unchanged acceptance rerun. Specialists remain v3; no model, MCP allowlist,
  or network changes were made. All 35 regression/privacy tests pass.
- Both published specialist endpoints advertise A2A and Responses with Entra
  authorization, Entra isolation, and `@latest` receiving 100% of traffic.
- Opt-in `CONTRACT_ASSURANCE_DISCOVERY_PROBE=1` sends one additional card GET
  without `x-agent-foundry-call-id`, using the same client, token, URL, and
  API version as normal discovery. Its response is never used for execution.
  Normal discovery retains the SDK-required forwarded call context.
- Trace `20a8c1f9a7d0492bb0af78fc6e26e181` in the existing Application Insights
  resource records HTTP 404 for both variants on both specialists. Removing
  the call-ID header alone does not resolve discovery. No A2A message or MCP
  execution was reached; turn 1 had no receipts and the verifier exited 1.
- Session `dbf4f929b1d230d4e5b9ddbc84db560c3c84bfc29040590ab01d805a74916b1`;
  request `83975d30-be8e-4755-ac01-7d8323732dbb`.
- Read-only ARM inspection found only the Insights publisher assignment for the
  orchestrator identity. The user separately approved the next permission test:
  `Foundry Agent Consumer` (`eed3b665-ab3a-47b6-8f48-c9382fb1dad6`) for existing
  orchestrator principal `55719306-f61e-486e-891b-d94c0216ad50`, scoped only to
  the existing `admin-2684` project. Assignment succeeded; this role grants only
  `Microsoft.CognitiveServices/accounts/AIServices/endpoints/interact/action`.
  This is a controlled hypothesis test, not yet proof that RBAC caused the 404.

### Discovery Resolved; Invocation Blocker Remains (14:18 UTC)

- The first rerun, less than one minute after the scoped grant, still returned
  404. After allowing ten minutes for propagation, trace
  `88b1029c41774dd6ba2387da4943c50f` records **200 for both specialists, with
  and without forwarded call context**. The project-scoped consumer grant
  resolved the observed discovery blocker; preserve the required context header.
- Execution then failed at both `a2a.send` stages: HTTP 200 with
  `A2AClientError`. Neither specialist had a hosted session or execution spans
  in the checked time window. MCP retrieval was not reached.
- A read-only native-wire CLI probe also returned JSON-RPC `-32099`.
  Changing the native header from `1.0` to `1.0.0` did not resolve it.
  A separate legacy-wire/header compatibility probe returned structured
  `HostedAgentNotSupported`, also with `-32099`; this identifies that probe's
  failure, not the exact cause of the native-wire error.
  Compatibility request `2fa3a37e-9a9c-4e92-aa5a-18511eae27bf`.
- No protocol downgrade, authentication bypass, broader role, specialist
  redeployment, new feature, or evaluation suite was introduced.
- User explicitly approved removing the finished comparison probe and one
  orchestrator-only cleanup deployment. Orchestrator v6 is active; SDK
  configuration inspection confirms the probe setting is absent and manual
  Insights export remains enabled. Specialists remain v3.
- All 34 retained regression/privacy tests pass. The unchanged acceptance
  verifier checked v6/v3/v3, but turn 1 again had no receipts and exited 1.
  Turns 2/3, document handoff, and context reuse remain unverified.
- Final trace `b15cf4b08062436c87f66a5c9f5a6f18` verifies both card GETs
  return 200 and both sends fail with `A2AClientError`; no comparison probe
  spans remain. Session
  `4b2afcb5b6bdafaf4f762a28e96a4bffd15e64ba289d2442825657e11542049`;
  request `50c877ac-f0de-49f9-969b-c9391df2cfcd`.
- Next investigation: Foundry's hosted A2A invocation routing/support for the
  existing native 1.0 definitions, using the request/trace correlations above.
  Do not treat successful discovery as successful hosted execution or weaken
  caller validation to work around an upstream error.

### Hosted A2A Rejection Confirmed (14:23 UTC)

- Read-only probes reproduced the native RPC `-32099` rejection for Contract
  and RFP. On RFP, native 1.0 and compatibility 0.3 requests have identical
  error messages that explicitly mention hosted agents and lack of support.
  The compatibility envelope additionally identifies `HostedAgentNotSupported`.
  This connects the native failure to the hosted-target restriction rather
  than merely inferring it from a separate compatibility error.
- RFP native request `829f38c2-600e-4652-8100-aaec55ccd3af`;
  compatibility request `765abdfe-e19f-423c-ab1f-596f34e7f899`.
  Contract native request `2e1a7fd1-02ca-4b4a-8110-4547c0b05be2`.
  No tokens, raw exception messages, prompts, or payloads were retained.
- [Microsoft's incoming-A2A documentation](https://learn.microsoft.com/azure/foundry/agents/how-to/enable-agent-to-agent-endpoint)
  lists a deployed prompt agent as a prerequisite and describes the
  Responses-backed incoming endpoint. Publishing a card and declaring the
  A2A gate does not establish support for this custom hosted A2A server.
- `azd ai agent doctor` confirms hosted agents are active, authentication and
  project reachability succeed. Its only failed check is the missing local
  `APPLICATIONINSIGHTS_CONNECTION_STRING` variable: deliberately passed only
  during deployment, not persisted locally. Deployed telemetry was already
  verified; this local check does not explain the A2A gateway rejection.
- No cloud configuration, role, or code changes were made for this diagnosis.
  A transport change needs user approval: retain separately hosted specialists
  behind a supported hosted Responses adapter, or retain native A2A by moving
  specialist hosting behind an A2A-capable ingress. The user subsequently selected
  the Responses migration verified above.

Observed endpoints (the clients preserve `api-version=v1` separately):

- Orchestrator: `https://admin-2684-resource.services.ai.azure.com/api/projects/admin-2684/agents/assurance-orchestrator/endpoint/protocols/openai/responses?api-version=v1`
- Contract: `https://admin-2684-resource.services.ai.azure.com/api/projects/admin-2684/agents/contract-analyst/endpoint/protocols/openai/responses?api-version=v1`
- RFP: `https://admin-2684-resource.services.ai.azure.com/api/projects/admin-2684/agents/rfp-analyst/endpoint/protocols/openai/responses?api-version=v1`

The ignored root `.env` contains the real normalized client endpoints and
`CONTRACT_ASSURANCE_LOCAL=0`, with observed versions 8/5/5. All three live
endpoints route 100% to `@latest`; a configured
definition version alone does not pin the gateway's invocation.
The separate azd environment is
`contract-assurance-hosted`; original HWC environment/version are preserved.

## Protocol and Packaging

All three hosted services now use Responses 2.0. Specialists use the installed
`ResponsesAgentServerHost` around the existing executor; `ResponsesRemote`
serializes the existing structured message/file DTOs into Responses input and
keeps server-owned continuations. The official `a2a-sdk==1.2.3` remains for those
internal models and the separately tested local native A2A adapter, not hosted
wire traffic or a fallback. File bytes, lineage, isolation, replay, and reset
tests pass. Agent Framework core remains pinned at 1.15.0.

Run `scripts/package_assurance.py` to stage the allowlisted code and dependencies
inside `.build/agent-code`. Foundry requires service paths to remain inside this
deployment project. Generated files and local azd environment files are ignored.
Restaging replaces only the dedicated `agent-code` directory instead of overlaying
it, so removed modules, binaries, and other stale files cannot enter later packages.
Broad destinations and linked staging directories are rejected.
The manifest uses Python 3.13 code deployment, not the optional Dockerfile.

Reference: [official A2A migration guide](https://github.com/a2aproject/a2a-python/blob/v1.2.3/docs/migrations/v1_0/README.md).

## Historical Verification And Earlier Publishing Blocker

Hosted-definition checks passed for orchestrator v3 and both specialist v2
versions. The live checker returned a response but **did not pass execution
verification**, with no execution receipts. Comparison, document handoff, and
specialist session reuse were therefore **unverified at that stage**. Deployment status
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

Before the successful 13:04 UTC retry, the required MCP update was not deployed.
The specialists require
`retrieve_contract_clauses` and `retrieve_rfp_commitments`, but the Function App
then still had its earlier published tool set. Existing Function App
`func-api-nowhyh5puoj7q` rejected code publishing with
`BlobUploadFailedException` / deployment-storage HTTP 403. Read-only inspection
originally found storage `stnowhyh5puoj7q` had public network access disabled,
no private endpoint, and the Function App had no VNet integration.
The approved remediation below corrects that missing private infrastructure,
but immediate publishing retries still returned the same 403. No public-access exception or extra
storage permission was granted.

The separately approved MCP identity allowlist change succeeded: it retains HWC's
identity and adds only the Contract/RFP specialist identities (three total), with
authentication still required. The failed publish did not deploy the two new
retrieval tools. Fabric and approval workflow configuration were not changed.

The existing `scripts/verify_contract_assurance.py --live` was rerun after MCP
publishing, with correlation capture outside the repository. It still failed
at turn 1; see the post-publish evidence below. Comparison, exact document-version
handoff, and specialist reuse require actual successful execution receipts.
That earlier blocked run and passing offline tests were not a live pass; the
successful Responses acceptance and linked traces are recorded above.

## Private Networking Remediation (2026-10-29)

The user explicitly approved private networking, confirmed the existing
subscription/resource group and East US 2, and confirmed the existing Application
Insights resource plus metadata-only hosted session logs for trace checks.

- Registered `Microsoft.Network`.
- Deployed `mcp-private-network-20261029` successfully in `rg-admin-2684`
  using [the scoped template](../../infra/mcp-network.bicep). This reuses the
  existing VNet and storage-private-endpoint modules without redeploying the full
  root template, identities, app settings, Foundry, or the MCP caller allowlist.
- Created `vnet-nowhyh5puoj7q`, its dedicated `app` integration subnet and
  `private-endpoints-subnet`, Blob/Queue private endpoints and private DNS
  zones/links. The Flex subnet uses `Microsoft.App/environments` delegation.
- Attached `func-api-nowhyh5puoj7q` to the `app` subnet. ARM confirmed its
  integration subnet and `vnetRouteAllEnabled=true`.
- Both storage private endpoint connections are `Approved`; private DNS records
  map Blob and Queue to `10.0.1.4` and `10.0.1.5` respectively.
- Storage retains `publicNetworkAccess=Disabled` and
  `allowSharedKeyAccess=false`. The Function's existing user-assigned identity
  retains storage-scoped Blob Data Owner and Queue Data Contributor roles.
- Provider validation and what-if passed with no existing resource modifications
  or deletions. The existing assurance tests passed: **31 tests, 5 subtests**.

The MCP package contains both retrieval functions and the shared fictional
corpus. Publishing via azd still failed at SCM `/api/publish` with
`BlobUploadFailedException` / storage HTTP 403. After a Function restart,
Azure CLI package deployment with remote build returned the same error.
One intervening azd retry failed at Entra discovery connectivity before publishing.
The Flex SCM command diagnostic endpoint returned 404, so DNS from inside the
deployment process itself was not verified. Private endpoint/DNS configuration
is not proof that the deployment service successfully used that route.

The user initially declined an additional temporary private deployment runner and
requested that cloud changes stop, then approved one controlled publishing retry
after the read-only investigation below. The private-network resources remain provisioned and
billable; no deletion was requested or performed. Do not retry or provision a
runner without renewed approval. Do not run full root provisioning as a shortcut:
its environment/network and app settings must first be reconciled with this
standalone remediation.

## Publishing Diagnosis And Successful Retry

The first-party `FunctionFlexDeployment` detector was accessible using the active
Azure CLI identity even though Azure MCP/AppLens used a different identity and
returned authorization errors. Explicit detector time ranges must end at least
14.5 minutes before the request; this investigation used a 16-minute offset.

Confirmed findings:

- The failing component was Kudu/Legion deployment storage access, before remote
  build or MCP tool indexing. It failed to read `kudu-state.json`, upload
  `DeploymentTemporaryFiles/*_source.zip`, and delete failed temporary packages.
- The deployment service explicitly reported using an MSI token. Its configured
  user-assigned identity already had unconditional, storage-scoped Blob Data Owner
  and Queue Data Contributor roles. This was not a demonstrated missing-role fix.
- Kudu specialized at 12:29 UTC, before the VNet integration. The same detector
  timeline contained failed uploads at 12:42:45 and 12:44:07 UTC, without another
  specialization entry in that observation window.
- Historical Kudu logs show deployment pods being marked for deletion after
  30 minutes. A Function host restart did not establish that the separate
  deployment pod had refreshed its network context.
- Subsequent ARM checks showed the Flex subnet's `legionservicelink` association
  Succeeded, default Azure DNS, a completed Blob DNS link, and no subnet NSG or
  route table. Storage metrics recorded OAuth authorization errors during failed
  publishes, then an OAuth `GetBlob` success at 13:00 UTC.
- Fresh read-only SCM deployment-state requests returned 200. The single approved
  azd retry then published successfully at 13:04 UTC, without another cloud
  configuration change.

**Most consistent explanation:** private-network convergence and/or a stale
pre-integration Kudu deployment-container context. The evidence locates the
failure and verifies recovery, but does not conclusively separate those two
platform mechanisms. Blob resource logging was not enabled, so requester identity,
caller IP, and the precise Storage error code were not available for per-request
correlation. Do not claim a private runner or broader storage permissions were
required, or that those changes fixed the issue.

## Hosted Conversation And Trace Evidence (2026-10-29)

- Existing live verifier: hosted definitions were returned, but turn 1 had
  `execution_verified=false` and `receipts=[]`. It stopped before document
  generation and context-reuse turns.
- Explicit fresh orchestrator v3 Responses invocation: HTTP 200 and
  `response.status=completed`, but three function outputs were
  `Error: Function failed.` The final answer abstained. This is a failed
  acceptance run, not successful orchestration.
- Hosted session: `07f98834f86596c100O2MVbI9eOhBfpXd8vvl4ktiyRGUQBoKv`.
- Response: `caresp_0619b348b55b074c003tLizI9fovQk2PFiZBckoZLDXLfle67F`.
- Metadata-only session logs contain linked `orchestrator.compare`,
  `delegate.contract`, and `delegate.rfp` failure spans with trace ID
  `a0e79e9aadb348759f682a8d7afe1bc4`. Both delegate spans reference parent
  `fbfc182a625148b2`; they report failure, not context reuse. No successful
  document handoff or specialist receipt was observed.
- Querying `appi-nowhyh5puoj7q` through Azure MCP failed with insufficient
  access. The active Azure CLI identity successfully queried `requests` and
  `dependencies` for the preceding hour, but returned zero rows. Application
  Insights ingestion/correlation for this conversation is **not verified**.
  Foundry agent instrumentation remains intentionally disabled for privacy;
  JSON metadata in hosted stderr is not an ingested OpenTelemetry span.

### Post-Publish Rerun (13:10-13:11 UTC)

- User approved rerunning the existing conversation, not another deployment.
  No application source or cloud configuration was changed. Only the ignored
  local verifier configuration was aligned to orchestrator version `3`.
- Hosted-definition checks passed for orchestrator v3 and both specialist v2
  versions. Turn 1 returned HTTP 200 and a completed Responses envelope, but
  `consult_specialists` returned `Error: Function failed.` The final answer
  abstained and the verifier reported `execution_verified=false`, `receipts=[]`,
  and exit code 1. Turns 2 and 3 were not run because the verifier stops on failure.
- Hosted session:
  `ecd59912ba9b51585b9cb83eb549ed888a100376355fc8094177b570e6cab3d`.
- Response: `caresp_0ba5b68f35bc3ea80018dvMNHWLmmnj4TkmQ6coUxMFXrAJTnI`.
- Request correlation: `cd0ccdd4-49de-43bc-95cf-b6158d4221e9`.
- Hosted metadata logs link all three failed spans under trace
  `75d801e6912b4015870b06a2652f78a3`: `orchestrator.compare` span
  `b793211b23124fcc` (398 ms), `delegate.contract` span `20b454b8fe07454c`
  (398 ms), and `delegate.rfp` span `e83a908448d1462f` (861 ms).
  Both delegates reference the comparison parent; neither reports context reuse.
- A metadata-only Application Insights query for 13:09-13:14 UTC, scoped to
  orchestrator request operations or that exact trace ID across `requests`,
  `dependencies`, `exceptions`, `customEvents`, and `traces`, succeeded through
  the direct API and returned zero rows. The initial CLI query returned
  `BadArgumentError`; the successful API retry is the telemetry result.
  Hosted stderr correlation is verified for failure only, not App Insights
  ingestion or a successful end-to-end trace.
- Current logs do not expose the underlying delegation exception. The failure
  persists after publishing, so missing MCP tools were not the sole blocker.
  The evidence does not yet distinguish token acquisition, discovery, transport,
  specialist authorization, or downstream execution failures.

### Existing Application Insights Attached (13:21 UTC)

- With explicit user approval, attached existing `appi-nowhyh5puoj7q` to the
  `admin-2684` Foundry project. Both account and project connection lists
  previously had no App Insights connection.
- Scoped deployment `foundry-existing-insights-20261029` succeeded at
  `2026-10-29T13:21:16Z`, correlation ID
  `2d163ed9-7469-4ad5-8b6c-9d6f9634d388`.
- Bicep compilation, provider validation, and exact JSON what-if passed:
  one new project connection, zero existing resource modifications or deletions.
  No new Application Insights/workspace, identity, network, or agent version.
- Persisted connection: `appi-nowhyh5puoj7q`, category `AppInsights`, using the
  SDK-required `ApiKey` credential containing the existing connection string.
  ARM resolves that value directly from the existing resource; it was not
  copied into source, local environment files, or logs.
- ARM GET verified the target resource ID. The installed Foundry SDK's
  `telemetry.get_application_insights_connection_string()` resolved the
  connection, and an in-memory comparison confirmed it exactly matches the
  approved existing Application Insights resource.
- This establishes the project attachment, not application telemetry ingestion.
  Hosted code still intentionally disables instrumentation and emits only
  metadata JSON to stderr. Enabling safe runtime export requires a separately
  approved narrow runtime change and agent redeployment; attachment does not
  itself resolve the specialist-delegation failure.

### Diagnostic Redeployment And Application Insights Finding (13:36 UTC)

- User approved metadata-only instrumentation, redeploying all three assurance
  agents, and rerunning the failing conversation. Separately approved three
  `Monitoring Metrics Publisher` grants scoped only to `appi-nowhyh5puoj7q`.
  Existing principal IDs and MCP permissions were preserved.
- Insights has `DisableLocalAuth=true`: a key-only probe returned 401, while an
  Entra-authenticated probe was accepted. Local authentication remains disabled.
- Active diagnostic versions are orchestrator v4, Contract v3, and RFP v3.
  Their existing instance identities are unchanged. The ignored verifier config
  was aligned with these versions.
- The dedicated batch exporter sends only manually constructed spans. Framework
  instrumentation, global OTel SDK instrumentation, and content recording remain
  disabled. No prompt, document, token, URL, tool payload, exception message or
  stack is exported. Export failures emit a metadata-only stderr signal.
- All 34 regression and telemetry privacy/correlation tests passed.
- The existing live verifier reproduced turn-1 failure with no receipts.
  Session `07841c9a6d39b958f3a47440d45c93cc3dc2d1ead9fe5df654aecc397425638`,
  response `caresp_030afbd5c2a131a800C2yYefVlFQqEG8mOGWVHcmrjlZza6t9Z`.
- **Application Insights ingestion and correlation are now verified.** Trace
  `a67c216af4ea48be933d7182f9c32312` contains the comparison, both delegations,
  both successful `a2a.token` spans, and both failed `a2a.card` spans.
  Contract card discovery returned HTTP **404** after 306 ms; RFP returned
  **404** after 525 ms. Both raise `AgentCardResolutionError` caused by
  `HTTPStatusError`. No `a2a.send` or MCP stage was reached in this trace.
- Query manual spans from `dependencies`, correlate on `operation_Id`, and read
  `customDimensions["assurance.error_type"]` and
  `customDimensions["assurance.http_status_code"]`. The exporter's generic
  `resultCode` is `0` for these INTERNAL spans; it is not the observed HTTP code.
- An independent read-only card GET using the active CLI identity returned 200
  for both exact versioned card routes. Therefore, the cards are available to
  that identity, but the hosted orchestrator's request path/context receives 404.
  This narrows the blocker to hosted caller-specific discovery/routing/access;
  it does not prove a missing permission or missing published card. No
  authorization weakening or speculative endpoint changes were made.
- A model retry hit the existing unresolved-specialist-request guard
  (`SpecialistCallFailed`); it did not execute either specialist.

Remaining gates: isolate the caller-specific card discovery failure without logging tokens or
document content, verify authenticated retrieval through the now-indexed tools,
then rerun all three acceptance turns and retain successful comparison,
document-lineage, and specialist-reuse receipts with correlated metadata traces.
Any cloud deployment or configuration change requires fresh explicit approval.