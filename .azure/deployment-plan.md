# Azure Deployment Plan

## Status

Corrected hosted acceptance passed on 2026-10-29 at 22:34-22:40 UTC after the
approved PR-fix deployment: orchestrator v9, Contract v6, RFP v6. Original
HWC v6 is unchanged. MCP publishing succeeded and both retrieval tools executed.
All three acceptance turns have actual receipts, including exact artifact
read/annotation lineage and stable reused RFP context; reset and new contexts
also passed. A fresh browser run repeated all five actions. Existing Application
Insights contains 330 metadata spans and ten linked successful business trees
across both completed runs. See the [hosted deployment record](../deployment/contract-assurance/README.md)
for versions, approvals, and trace IDs.

## Request-Context And Scoped Permission Investigation

### PR #5 Follow-Up: Corrected Hosted Deployment And Verification Complete

All five review findings are fixed, with 49 passing focused tests and compile/
whitespace validation. A real-model local browser run against the corrected
agents and synthetic MCP passed comparison/citations, exact document handoff,
follow-up reuse, acknowledged reset, and new contexts afterward. Local metadata
verifies all five business trace trees. Live negative checks verified Host
rejection and reset recovery after a rejected stale transport continuation.

After the initial local-only verification, the user requested hosted testing.
Deployed the same corrected source package to existing orchestrator v9 and both
specialists v6. All three are active with matching package hash
`fb0570aafbb2884e18e3a5057b8ff7db98bc45c3e829571dbaec5fa660c4f3b0`.
No provisioning, permission, identity, model, or MCP allowlist changes occurred.
Hosted acceptance and a fresh browser run passed all three turns, acknowledged
reset, and new contexts. Existing Insights verifies ten fully linked successful
business trees, 24 successful specialist sends/authorizations, and 20 retrievals.
The earlier browser network-suspension attempt is retained separately, not
silently treated as success. Hosted v8/v5/v5 remains historical baseline evidence.

### Approved Responses Migration; Hosted Verification Complete

- User selected supported Responses communication between the three existing
  hosted agents. Preserve model, identities, MCP callers, evidence/document
  validation, caller checks, and metadata-only telemetry.
- Local code now uses the installed Responses host SDK around the unchanged
  specialist executor. All three service definitions use Responses 2.0;
  specialist endpoint gates expose only Responses. The local A2A adapter remains
  for existing tests, not as a hosted fallback.
- Specialist clients send structured application messages as Responses input,
  require one completed structured output with the same context ID, and keep
  server-owned previous-response continuations. Stored Responses content is
  distinct from telemetry: prompts/files are never exported to Insights.
- The verifier now requires three observed Responses endpoints/definitions.
  User explicitly approved three existing agent redeployments, URL updates,
  hosted acceptance, and existing Insights querying. Initial v7/v4/v4 reached
  specialist containers but returned HTTP 401 before JWT verification.
- Corrective v8/v5/v5 uses the documented `x-client-` pass-through prefix for
  the same signed bearer consumed at Foundry ingress. Existing JWT/caller checks
  remain intact. Both credential headers are removed before the Responses host
  sees them, preventing host metadata persistence. No credentials enter stored
  input or telemetry. Hosted authorization and downstream retrieval now succeed.
- Validation: 39 regression/transport/privacy tests pass, including the actual
  Responses SDK roundtrip with offline analysts, complete document bytes and
  lineage, reuse, isolation, failed-call retry, unresolved-call reset, ingress
  authentication rejection, gateway header consumption/credential removal,
  and content-free failure tracing. Compile and whitespace checks pass.
- The unchanged hosted verifier exited 0 after all three turns. Insights verifies
  eight successful sends, authorizations, and MCP retrievals, plus linked document
  handoff and annotation. No new infrastructure, permission grants, models,
  MCP callers, features, or evaluation suite were introduced by this migration.
- In-memory continuation/history remains nondurable across restarts/replicas;
  multi-user frontend and private Copilot Studio integration remain outside this
  verified run.

### Historical Discovery and A2A Diagnosis

- On 2026-10-29, user explicitly approved an orchestrator-only diagnostic
  deployment comparing card GETs with/without forwarded call context using
  the same token. Both variants initially returned 404 for both specialists.
- User separately approved `Foundry Agent Consumer` for orchestrator principal
  `55719306-f61e-486e-891b-d94c0216ad50`, scoped only to the existing
  `admin-2684` Foundry project. The persisted role grants only
  `Microsoft.CognitiveServices/accounts/AIServices/endpoints/interact/action`.
- After ten minutes of propagation, both variants returned 200. Keep the
  SDK-required forwarded call-ID header; it was not the discovery blocker.
- The next stage fails with `A2AClientError` and HTTP 200; no specialist session
  or execution span was observed. A native-wire CLI probe returned RPC
  `-32099`; a separate compatibility probe returned `HostedAgentNotSupported`.
  The native-wire invocation root cause remains unresolved.
- User explicitly approved probe removal and one orchestrator-only cleanup
  redeployment. V6 has no probe setting and retains manual Insights export.
  No new features, model changes, network weakening, protocol downgrade,
  specialist/MCP allowlist changes, or additional grants were made.
- All 34 retained regression/privacy tests pass. Final unchanged acceptance
  rerun at 14:17 UTC fails turn 1 with no receipts. Insights trace
  `b15cf4b08062436c87f66a5c9f5a6f18` confirms discovery 200/send failure.
  See the hosted deployment record for correlation IDs and next diagnostic gate.

Deployed and verified: approved existing Application Insights attachment only.
Recipe: Azure CLI / scoped Bicep project-connection update. No application deployment.

MCP deployed successfully; post-publish hosted acceptance blocked at delegation.

The user-approved controlled MCP publish retry succeeded at 13:04 UTC on
2026-10-29. No further source, network, identity, or permission changes were made.
The user-approved hosted rerun at 13:10 UTC checked orchestrator v3 and both
specialist v2 definitions, but turn 1 failed with no execution receipts.
Both specialist delegations have correlated failure metadata in hosted logs.
The scoped Application Insights API query returned zero rows. The verifier
stopped before the document-handoff and reuse turns. No cloud changes were
made during this rerun.

## Approved Metadata-Only Diagnostic Redeployment

- On 2026-10-29, user explicitly approved manual diagnostic instrumentation,
  redeployment of the three assurance agents, and the failing-conversation rerun.
- Reuse the attached `appi-nowhyh5puoj7q` resource and existing project/model.
  No new infrastructure, identities, or caller allowlist changes.
- Keep Agent Framework and global OTel instrumentation disabled. Export only
  explicitly constructed metadata spans through a dedicated batch exporter.
  Never collect prompts, documents, tokens, URLs, exception messages/stacks,
  tool payloads, or automatic HTTP/model instrumentation.
- Capture stage, exception class/causal class chain, HTTP status, timing,
  hashed session tags and trace/span IDs. Preserve actual business behavior.
- Probe verified key-only ingestion returns 401: Insights has
  `DisableLocalAuth=true`. Entra-authenticated ingestion accepted 1/1 probe item.
- User separately approved `Monitoring Metrics Publisher` grants for the three
  existing assurance-agent identities, scoped only to this Insights resource.
  Retain disabled local auth; do not broaden roles or MCP access.
- Deployment passes the existing connection string only through process
  environment into hosted settings; never persist its value in source or logs.
- Validation: assurance regression/privacy tests, Bicep-free code packaging,
  verify exact identity grants and target settings, deploy only the three roles,
  rerun existing live verifier, then query correlated Application Insights.
- Tests before Entra credential wiring: 34 passed, including content exclusion,
  trace-parent linkage, global-SDK-disabled export and card HTTP failure stages.
- Final tests after Entra wiring: 34 passed. Approved resource-scoped grants
  succeeded for the three existing agent identities; no other roles changed.
- Deployed and verified active: orchestrator v4, Contract v3, RFP v3. Existing
  identities are unchanged; trace flag and Insights destination are configured.
- Rerun at 13:36 UTC failed turn 1 without receipts. Application Insights now
  contains linked manual spans for trace `a67c216af4ea48be933d7182f9c32312`.
  Both token acquisitions succeeded; both card discoveries returned HTTP 404.
  No A2A execution or MCP retrieval was reached.
- Exact card routes return 200 under the active CLI identity. Hosted
  caller-specific discovery/routing/access remains unresolved; do not infer
  missing roles or broaden permissions from HTTP 404 alone.

## MCP Publishing Remediation

### Existing Application Insights Attachment

- User approved attaching existing `appi-nowhyh5puoj7q` on 2026-10-29.
- Scope: inspect the existing Foundry project monitoring connection and attach
  that existing resource if missing. Do not create monitoring resources, change
  networking or identities, or redeploy agents as part of attachment.
- Preserve metadata-only telemetry. Project attachment alone may not export
  application spans because agent instrumentation is currently disabled.
- Verify the persisted connection and report any separate runtime instrumentation
  or deployment needed before claiming trace ingestion.
- Result: deployment `foundry-existing-insights-20261029` succeeded at
  `2026-10-29T13:21:16Z`. ARM GET confirms the project `AppInsights` connection;
  the Foundry SDK resolves a connection string exactly matching the approved
  existing resource. No credentials were displayed.
- Attachment does not override `configure_privacy()` or enable agent exporters.
  Successful telemetry ingestion and hosted acceptance remain separate gates.

#### Attachment Validation: All validation checks pass

- [x] Core validation: active authentication, existing target resource, correct
  project, no conflicting App Insights connection, supported connection schema.
- [x] Template build, resource-group provider validation, and what-if using only
  the session-scoped attachment template, never the root application template.
- [x] Azure Policy validation through provider validation for the scoped update.
- [x] Configuration validation: only one project connection is added; connection
  string stays in memory and managed connection credentials, never source/logs.
- [x] Build verification: Bicep compiled; application code and packages unchanged.
- [x] Static role verification: no RBAC assignments or identities changed.
- [x] Validation proof recorded before the scoped connection update.

#### Section 7: Attachment Validation Proof

- Validation completed on 2026-10-29 before the 13:21 UTC scoped deployment.
- ARM GETs of account and project connections returned no App Insights connection.
- Existing `appi-nowhyh5puoj7q`: `Succeeded`, East US 2, existing
  `log-nowhyh5puoj7q` workspace.
- The standard `validate-deployment.ps1` helper passed CLI, authentication, Bicep
  compilation, group provider validation, and what-if for the session-scoped
  `attach-existing-insights.bicep`; no root provisioning template was used.
- Exact JSON what-if resource results: one `Create`, the project connection
  `admin-2684-resource/admin-2684/appi-nowhyh5puoj7q`; zero modifications and zero
  deletions. The helper's text-line create count was 2, not a resource count.
- Static review: all other resources are `existing`; no RBAC, identity, network,
  application-code, package, or agent-version changes.
- Connection schema matches the installed Foundry SDK: category `AppInsights`,
  `ApiKey` credential containing the connection string. ARM resolves the existing
  Insights connection string; its value is not copied into files or logs.

- Approval: private networking explicitly approved on 2026-10-29.
- Confirmed context: subscription `064bf515-5976-4108-a5fb-2f23b3135756`,
  resource group `rg-admin-2684`, location `eastus2`.
- Existing Function `func-api-nowhyh5puoj7q` and storage `stnowhyh5puoj7q`
  are retained. Public storage access stays disabled, shared keys stay disabled,
  and Easy Auth plus the three-agent identity allowlist remain unchanged.
- Register Microsoft.Network, deploy `infra/mcp-network.bicep` in incremental
  mode, then attach the Function to its dedicated Flex Consumption subnet.
- Reuse existing network/private endpoint modules. Flex Consumption requires
  `Microsoft.App/environments` subnet delegation.
- Create only a VNet, Blob/Queue private endpoints, private DNS zones/links,
  and associated endpoint NICs. No new Foundry, identity, or monitoring resource.
- Private endpoints and private DNS incur Azure charges; user approved that
  path. Do not deploy the full root template or replace existing app settings.
- Validate the template and preview changes before provisioning, then publish
  only `mcp-server`. Run all three hosted acceptance turns with real receipts.
- Trace verification: user confirmed existing `appi-nowhyh5puoj7q` and safe
  hosted session logs. Preserve metadata-only instrumentation and content privacy.
- Historical sections below describe the earlier HWC deployment, not current
  remediation approval or verification.

### Remediation Outcome

- Successful retry: deployment `06b89ba7-8192-46fa-8dc8-bee34a403d57`,
  remote build, complete/active/status 4. All six MCP triggers indexed and enabled,
  including both retrieval tools. Anonymous MCP access returns 401. Storage public
  access and shared keys remain disabled.
- Diagnosis located MSI storage failures in Kudu before build. Existing Kudu
  specialization preceded the private integration; later network association and
  OAuth Blob reads succeeded. Network convergence/stale deployment context is the
  strongest explanation, not a conclusively isolated platform mechanism.
- No private runner or additional permission was needed. Earlier publishing
  failures below are historical. The post-publish conversation rerun still failed
  at delegation; its underlying exception and successful trace ingestion remain
  unresolved. Detailed correlation evidence is in the hosted deployment record.
- Read-only follow-up: Flex deployment diagnostics show Kudu specialized at
  12:29 UTC, before VNet integration; it subsequently failed MSI Blob uploads.
  Earlier logs show 30-minute deployment-container recycling. Current subnet
  service association is Succeeded. Fresh SCM deployment-state reads returned
  200 and storage metrics show OAuth GetBlob success at 13:00 UTC. Stale
  deployment-container context/network convergence is a hypothesis, not yet
  proven root cause. One publish retry explicitly approved; no private runner.

- Network deployment `mcp-private-network-20261029`: Succeeded. Function attached
  to the Flex subnet; Blob/Queue private connections Approved; DNS records present.
- Storage public access and shared keys remain disabled. No authentication,
  caller allowlist, identity, or RBAC changes were applied.
- MCP package publishing still returned `BlobUploadFailedException` / HTTP 403
  through azd and CLI, including after a Function restart.
- The live verifier failed at turn 1 without receipts. Explicit v3 invocation
  returned failed tool outputs. Document handoff/context reuse remain untested.
- Correlated failure metadata exists in hosted logs. Application Insights query
  via CLI returned zero requests/dependencies in the preceding hour; MCP query
  identity was denied access. Successful trace ingestion remains unverified.
- User declined a temporary private deployment runner and stopped further cloud
  changes. Private networking remains provisioned and billable.
- Detailed evidence and remaining gates: `deployment/contract-assurance/README.md`.

## Objective

Deploy a cost-optimized, single-region HWC proof-of-concept that demonstrates
a Microsoft Foundry hosted agent calling three proposal-only Azure Functions
managed MCP tools. Continue using synthetic data only.

## Azure Context

- **Environment:** `<azd-environment-name>`
- **Subscription:** `<subscription-name>` (`<subscription-id>`)
- **Tenant:** `<tenant-id>`
- **Location:** `eastus2`
- **Resource group:** reuse `<resource-group>`
- **Foundry project:** reuse `<foundry-project>`
- **Model deployment:** reuse `gpt-5-mini`

## Requirements

- **Classification:** cost-optimized proof of concept
- **Scale:** small, single-region demonstration workload
- **Data:** synthetic only; no SharePoint, Fabric, OneLake, or HWC API access
- **Security:** Microsoft Entra authentication for the deployed MCP endpoint,
  managed identities, least-privilege RBAC, no automatic actions
- **Network:** public HTTPS Function endpoint protected by Easy Auth; no APIM,
  VNet, private endpoint, or Key Vault for the synthetic-data PoC
- **Observability:** Application Insights and Log Analytics; telemetry contains
  operational metadata only, with sensitive prompt and completion capture off

## Resources To Provision

1. Azure Functions Flex Consumption Function App hosting the managed MCP
   extension and Python tool triggers.
2. General-purpose v2 Storage Account required by the Functions runtime and
   MCP extension.
3. User-assigned managed identity for the Function App and storage deployment
   access, with only required Storage Blob and Queue data roles.
4. Log Analytics workspace and Application Insights component for Function
   runtime logs, failures, latency, and dependency telemetry.
5. Microsoft Entra application registration and Functions Easy Auth
   configuration to protect `/runtime/webhooks/mcp` with audience and issuer
   validation.
6. Hosted-agent configuration update setting `MCP_SERVER_URL` to the deployed
   Function path `https://<function-app>/runtime/webhooks/mcp`.

The existing Foundry project and `gpt-5-mini` deployment are reused. This plan
does not provision API Management, private networking, Key Vault, Azure AI
Search, Fabric/OneLake resources, or a production action service.

## Implementation Approach

- Use the official Azure Functions remote-MCP Python template as the Bicep
  base and retain its managed identity and Flex Consumption security patterns.
- Preserve the existing HWC `mcpToolTrigger` functions and synthetic data.
- Configure the Function MCP extension endpoint as anonymous at the Functions
  layer only because Easy Auth is the external authentication boundary.
- Add app settings only through generated infrastructure; no credentials are
  written to source control.
- Generate infrastructure and configuration first, then run Azure validation.
  Deployment occurs only after validation and a second explicit approval.

## Policy And Capacity Checks

- Subscription policy assignments were reviewed. The visible assignments are
  Defender recommendations for relational databases and do not directly block
  the selected Functions, Storage, identity, or monitoring resources.
- `Microsoft.Quota` is registered. The `Microsoft.Web` quota API returns
  incomplete limit-only data, so the successful azd provisioning preview is
  the capacity check for this small Flex Consumption PoC.

## Validation

### All Validation Checks Pass

Current remediation recipe: standalone resource-group Bicep, followed by
targeted existing azd Function publishing.

- [x] Core validation: CLI, authentication, Bicep build, ARM validation, what-if
- [x] Azure Policy validation for the private network resources
- [x] Static role review: no new identities or RBAC; retain existing Blob/Queue roles

### Remediation Validation Proof (2026-10-29)

- `validate-deployment.ps1 -Scope group -ResourceGroup rg-admin-2684`
  with `infra/mcp-network.bicep` and the session-scoped parameter file: PASS
  for CLI/auth/build/provider validation/what-if. No modifications or deletions
  of existing resources; only the planned private-network resources are created.
- Effective ARM provider validation passed without policy denial. Azure MCP
  policy discovery returned an authorization failure with its separate identity;
  active CLI scoped assignment enumeration returned no assignments. Existing
  storage policy findings are not claimed fixed by this preflight.
- Static role review: remediation introduces no identities or role assignments.
  Existing `infra/app/rbac.bicep` supplies storage Blob/Queue roles.
- Assurance regression suite: 31 tests and 5 subtests passed.
- Pre-existing BCP318 warnings in conditional private DNS module outputs remain;
  both enabled Blob/Queue paths passed provider validation.

- [x] Azure Developer CLI installation and authentication
- [x] `azure.yaml` schema and azd environment configuration
- [x] Subscription, location, policy, and Functions capacity review
- [x] Bicep build, validate, and subscription-scope what-if preview
- [x] Function and hosted-agent package validation
- [x] Static managed-identity and RBAC verification
- [x] Hosted-agent demo prompts and deterministic evaluation suite

- Validate Bicep and `azure.yaml` configuration.
- Confirm resource names, endpoint wiring, and `mcpToolTrigger` discovery.
- Confirm Function App identity, Storage data roles, and Easy Auth settings.
- Confirm App Insights/Log Analytics connection and sensitive telemetry policy.
- Run the managed MCP initialization, discovery, and tool-call smoke test.
- Run the two hosted-agent demo prompts and deterministic evaluation suite.

## Role Assignment Verification

- **Status:** verified in generated Bicep
- **Function identity:** user-assigned managed identity scoped to the generated
  Storage Account and Application Insights component
- **Storage roles:** Storage Blob Data Owner for the Function package container
  and Storage Queue Data Contributor for the MCP extension's host storage
- **Monitoring role:** Monitoring Metrics Publisher scoped to Application
  Insights
- **Local user role:** the deployer receives matching storage data-plane roles
  for package upload and local validation
- **Result:** roles are data-plane roles scoped to individual resources; no
  broad Contributor or Owner role is assigned by the template

## Validation Proof

- `azd provision --preview --no-prompt` completed successfully. It reuses the
  Foundry account/project, modifies only the `azd-env-name` tag on
  `<resource-group>`, and previews Application Insights, Log Analytics, Storage,
  and the Flex Consumption plan.
- `azd package --no-prompt` completed successfully for `mcp-server` and
  `hwc-governed-agent`.
- Python compilation and the full deterministic suite completed successfully:
  7 tests and 2 evaluation subtests passed.
- The managed MCP smoke test is post-deployment because its remote endpoint
  does not exist yet.

## Post-Deployment Smoke Test

- [x] Call `initialize` on the deployed `/runtime/webhooks/mcp` endpoint.
- [x] Discover all three managed HWC MCP tools.
- [x] Invoke `get_business_summary` for `HWC-1001` using Entra authentication.
- [x] Run both hosted-agent demo prompts and inspect telemetry.

## Deployment Result

- Azure Functions managed MCP service deployed at
  `https://<function-app>.azurewebsites.net/runtime/webhooks/mcp`.
- Foundry hosted agent `<agent-name>` is active.
- Easy Auth is configured with the hosted agent's managed-identity object ID
  under `allowedPrincipals.identities`; the caller obtains a token for the
  Function Entra API audience.
- The HWC summary successfully called `get_business_summary`, returned the
  overdue reconciliation exception, and cited `SYN-OPS-001` and `SYN-POL-001`.
- The follow-up flow successfully called `prepare_follow_up_action` and
  returned `PENDING_APPROVAL` with explicit human approval required.
- Storage has `securitycontrol=ignore`, which permits the approved synthetic
  demo deployment path while shared-key access remains disabled.

## Observability Privacy Gate

- **Status:** passed with hosted agent version 6 on 2026-09-03.
- Agent Framework instrumentation is disabled at startup with
  `disable_instrumentation()`. The Agent365 integration and its content-recording
  settings are also disabled through deployment environment variables.
- A fresh synthetic HWC-1001 request returned successfully and made MCP calls
  with HTTP 200 responses. Its session log contained zero `gen_ai.input.messages`,
  `gen_ai.output.messages`, or `tool_call_response` markers.
- This intentionally removes Agent Framework trace/span detail from session logs.
  Azure Functions platform telemetry and HTTP status logging remain available.
- Real data must still follow HWC classification, retention, and access policy;
  re-enabling detailed agent traces requires a separately approved redacting
  exporter and another synthetic verification.

## Deployment Blocker

- Provisioning initially succeeded for the Flex Consumption plan, Function
  App, Storage Account, Log Analytics workspace, Application Insights, managed
  identity, RBAC assignments, and Functions Easy Auth configuration.
- `azd deploy --no-prompt` cannot upload the Function package because the
  deployment Storage Account has `publicNetworkAccess: Disabled`. Direct Blob
  access from the approved deployer is similarly blocked by the network rule,
  even though the deployer has Storage Blob Data Owner and Storage Queue Data
  Contributor roles.
- The Bicep parameters set `VNET_ENABLED=false` and the Bicep branch requests
  public Storage access, but the deployed Storage Account retains disabled
  public access. This indicates an effective management-group network policy.
- Do not retry deployment until the platform owner provides a policy-compliant
  deployment route: an approved private build agent with Storage private-endpoint
  access, or a policy exemption/approved public deployment-access configuration.

## Policy-Tag Probe

- Hypothesis: MCAPS allows the approved `securitycontrol=ignore` tag to exclude
  this synthetic-demo Storage Account from the public-network enforcement rule.
- Scope: add that tag only to the deployment Storage Account through Bicep.
- Check: preview, provision the tag, verify `publicNetworkAccess`, and attempt
  one Entra-authenticated Blob upload before retrying application deployment.

## Deployment Gate

After the infrastructure preparation and validation succeed, present the
validated plan and cost-estimate output for a second explicit approval before
running any provisioning or deployment command.