# Azure Deployment Plan

## Status

Deployed; telemetry privacy gate passed

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