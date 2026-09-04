import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("mcp_server", ROOT / "mcp-server/server.py")
mcp = importlib.util.module_from_spec(spec); spec.loader.exec_module(mcp)
previous_server_module = sys.modules.get("server")
try:
    sys.modules["server"] = mcp
    function_spec = importlib.util.spec_from_file_location("function_app", ROOT / "mcp-server/function_app.py")
    function_app = importlib.util.module_from_spec(function_spec); function_spec.loader.exec_module(function_app)
finally:
    if previous_server_module is None:
        sys.modules.pop("server", None)
    else:
        sys.modules["server"] = previous_server_module
from agent.agent import HostedAgent

class ToolTests(unittest.TestCase):
    def test_functions_register_managed_mcp_triggers(self):
        functions = function_app.app.get_functions()
        self.assertEqual(
            {item.get_function_name() for item in functions},
            {tool["name"] for tool in mcp.TOOLS},
        )
        self.assertTrue(
            all(
                any(binding.type == "mcpToolTrigger" for binding in item.get_bindings())
                for item in functions
            )
        )

    def test_discovery_has_all_tools(self):
        self.assertEqual({tool["name"] for tool in mcp.TOOLS}, {"search_hwc_knowledge", "get_business_summary", "prepare_follow_up_action"})

    def test_search_and_empty_results(self):
        self.assertEqual(len(mcp.call_tool("search_hwc_knowledge", {"query": "exception"})), 2)
        self.assertEqual(mcp.call_tool("search_hwc_knowledge", {"query": "nothing fictional"}), [])

    def test_validation_and_missing_entity(self):
        with self.assertRaises(ValueError): mcp.call_tool("search_hwc_knowledge", {"query": ""})
        with self.assertRaises(KeyError): mcp.call_tool("get_business_summary", {"entity_id": "missing"})

    def test_action_requires_approval(self):
        action = mcp.call_tool("prepare_follow_up_action", {"entity_id": "HWC-1001", "action_type": "Review", "instructions": "Contact owner"})
        self.assertEqual(action["execution_status"], "PENDING_APPROVAL")
        self.assertIn("approval", action["approval_requirement"].lower())

    def test_fabric_data_source_records_can_be_loaded(self):
        with patch.dict(
            "os.environ",
            {
                "HWC_DATA_SOURCE": "fabric",
                "FABRIC_WORKSPACE_ID": "workspace-123",
                "FABRIC_LAKEHOUSE_ID": "lakehouse-123",
            },
            clear=False,
        ):
            import importlib
            import shared.data as data
            importlib.reload(data)

            with patch.object(data, "_query_fabric", return_value=[{ "entity_id": "HWC-1001", "name": "Contoso", "current_status": "Needs attention", "important_metrics": {"open_exceptions": 1, "days_since_review": 12, "service_health": "Green"}, "risks": ["Reconciliation exception is overdue"], "recent_activity": ["Reviewed on 2026-09-02"], "supporting_sources": ["SYN-OPS-001"]}]):
                records = data.get_business_records()

            self.assertIn("HWC-1001", records)
            self.assertEqual(records["HWC-1001"]["current_status"], "Needs attention")

    def test_fabric_row_is_normalized_to_agent_contract(self):
        import shared.data as data
        with patch.object(data, "_query_fabric", return_value=[{
            "entity_id": "HWC-1002",
            "status": "In Review",
            "owner": "Michael Torres",
            "primary_risk": "Workflow Exception",
        }]):
            mcp.STATE.clear()
            mcp.STATE.update(data.get_business_records())

        summary = mcp.call_tool("get_business_summary", {"entity_id": "HWC-1002"})
        self.assertEqual(summary["current_status"], "In Review")
        self.assertEqual(summary["risks"], ["Workflow Exception"])
        self.assertEqual(summary["supporting_sources"], ["OneLake:dbo.vw_exception_summary"])
        mcp.reset_state()

    def test_agent_responses_shape(self):
        agent = HostedAgent("http://unused")
        agent.call = lambda name, args: mcp.call_tool(name, args)
        result = agent.respond("Summarize the current position")
        self.assertEqual(result["object"], "response")
        self.assertFalse(result["approval_required"])

if __name__ == "__main__":
    unittest.main()
