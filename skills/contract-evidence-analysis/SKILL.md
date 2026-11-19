---
name: contract-evidence-analysis
description: Analyze a fictional vendor contract request, retrieve only contract evidence, and return cited findings for a parent assurance agent. Use when a request concerns contract terms, obligations, remedies, or differences from promised commitments.
---

# Contract evidence analysis

Treat the corpus as fictional demo data. Never use prior knowledge about a real vendor.

1. Reduce the user request to the contract topics that need evidence.
2. Use the allowed contract-retrieval MCP capability for those topics.
3. Return only claims supported by retrieved evidence.
4. Include every `source_id` used.
5. If evidence is absent or a call fails, report `insufficient_evidence`; do not infer a clause.
6. Do not retrieve or compare RFP evidence. Leave cross-document comparison to the parent agent.
7. Keep the workflow read-only and never approve, execute, or modify a contract action.
