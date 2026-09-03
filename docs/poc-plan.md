# Recommended HWC Proof Of Concept

## Candidate

Build a read-first **client exception briefing** for one governed dataset and
one knowledge source. An authorized user asks for a current client summary; the
agent retrieves the record, finds the applicable policy, identifies the primary
exception, cites both sources, and prepares a follow-up proposal that cannot be
executed without human approval.

This candidate demonstrates managed MCP hosting, grounding, identity,
observability, and approval boundaries without beginning with a high-risk
autonomous workflow.

## Four-Week Scope

- One user group and one non-production Foundry environment
- One curated business-data adapter and one knowledge adapter
- Three tools: knowledge search, business summary, and proposal preparation
- Microsoft Entra authentication and managed identity end to end
- Trace, latency, error, and tool-usage telemetry with sensitive content off
- A 20-30 case evaluation set based on representative, de-identified questions
- No production write endpoint and no automatic action execution

## Success Criteria

- At least 90% of agreed questions return the correct primary exception
- 100% of factual business answers include valid source identifiers
- 100% of follow-up requests remain proposal-only and state approval status
- Zero answers invent a record when the entity or evidence is absent
- P95 response time and availability targets are agreed before the pilot starts
- Security review confirms least privilege, auditability, and data boundaries
- Business owners judge the briefing useful in at least 80% of acceptance cases

## Customer Prerequisites

- Named business owner, security owner, data owner, and pilot user group
- Approved non-production records, knowledge corpus, and expected-answer set
- Entra groups, identity/RBAC approval, and networking constraints
- Data classification, retention, regional, and logging requirements
- Fabric/OneLake or API owners available to define supported access patterns
- Acceptance process, risk register, and decision date for the next phase

## Microsoft Prerequisites

- Confirm Foundry region, hosted-agent capability, model quota, and SDK support
- Validate the chosen MCP network path and managed-identity token flow
- Provide architecture and threat-model review for Foundry, Functions, and APIM
- Help establish baseline evaluations, trace interpretation, and service limits
- Produce a deployment and cost estimate for HWC approval before provisioning

## Exit Decision

Proceed only if quality, security, latency, and operating ownership meet the
agreed thresholds. Otherwise retain the evaluation evidence, address the failed
criterion, and rerun the pilot rather than widening scope.