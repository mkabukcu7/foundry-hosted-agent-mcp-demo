# Evaluation

## Local Baseline

The pre-deployment baseline is deterministic and uses only synthetic data. It
checks the business contract without model tokens or an LLM judge:

- the HWC-1001 status and primary exception are grounded in tool output;
- both expected source identifiers are cited;
- the expected MCP tools are selected;
- follow-up actions remain pending and require explicit approval.

Run the baseline from VS Code Test Explorer or from PowerShell:

```powershell
agent\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Update cases in `evaluations/hwc_cases.jsonl`. Keep customer or production data
out of this dataset.

## Managed Evaluation

Foundry-managed evaluation requires a deployed, running agent and is therefore
outside the current local-only scope. Before enabling it:

1. Choose a judge model that supports structured evaluation output. The
   current `gpt-5-mini` agent model is not suitable as the judge.
2. Install `pytest-agent-evals` as a development dependency.
3. Add relevance, task-adherence, intent-resolution, and tool-call-accuracy
   evaluators, then persist results under `agent/.foundry/results/`.
4. Run a smoke case before the full suite and compare later agent versions
   against the same dataset.