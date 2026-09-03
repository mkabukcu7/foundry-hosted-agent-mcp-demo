import importlib.util
import json
from pathlib import Path
import unittest

from agent.agent import HostedAgent


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("mcp_server", ROOT / "mcp-server/server.py")
mcp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mcp)


class EvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        dataset = ROOT / "evaluations/hwc_cases.jsonl"
        cls.cases = [json.loads(line) for line in dataset.read_text(encoding="utf-8").splitlines()]

    def test_demo_response_contracts(self):
        agent = HostedAgent("http://unused")
        agent.call = lambda name, arguments: mcp.call_tool(name, arguments)

        for case in self.cases:
            with self.subTest(case=case["id"]):
                response = agent.respond(case["query"])
                self.assertTrue(all(term in response["output_text"] for term in case["expected_terms"]))
                self.assertEqual(set(response["source_ids"]), set(case["expected_sources"]))
                self.assertEqual(response["tools_used"], case["expected_tools"])
                self.assertEqual(response["approval_required"], case["approval_required"])


if __name__ == "__main__":
    unittest.main()