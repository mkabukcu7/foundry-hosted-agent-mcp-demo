"""Small dependency-free MCP-over-HTTP server for local demos and Azure Functions."""
import copy
import json
import os
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from shared.data import BUSINESS, KNOWLEDGE
from shared.validation import optional_positive_int, required_text

TOOLS = [
    {"name": "search_hwc_knowledge", "description": "Search synthetic governed policy, architecture, and operations documents.", "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}, "category": {"type": "string"}, "maximum_results": {"type": "integer", "minimum": 1}}, "required": ["query"]}},
    {"name": "get_business_summary", "description": "Return a grounded summary for a fictional client or process.", "inputSchema": {"type": "object", "properties": {"entity_id": {"type": "string"}}, "required": ["entity_id"]}},
    {"name": "prepare_follow_up_action", "description": "Prepare a fictional action; never executes without explicit human approval.", "inputSchema": {"type": "object", "properties": {"entity_id": {"type": "string"}, "action_type": {"type": "string"}, "instructions": {"type": "string"}}, "required": ["entity_id", "action_type", "instructions"]}},
]
STATE = copy.deepcopy(BUSINESS)

def call_tool(name, arguments):
    arguments = arguments or {}
    if name == "search_hwc_knowledge":
        query = required_text(arguments.get("query"), "query").lower()
        category = arguments.get("category")
        if category is not None:
            category = required_text(category, "category").lower()
        limit = optional_positive_int(arguments.get("maximum_results"), "maximum_results", 5)
        return [item for item in KNOWLEDGE if (not category or item["category"] == category) and query in (item["title"] + " " + item["summary"]).lower()][:limit]
    if name == "get_business_summary":
        entity_id = required_text(arguments.get("entity_id"), "entity_id").upper()
        if entity_id not in STATE:
            raise KeyError(f"No synthetic entity found for {entity_id}")
        return copy.deepcopy(STATE[entity_id])
    if name == "prepare_follow_up_action":
        entity_id = required_text(arguments.get("entity_id"), "entity_id").upper()
        action_type = required_text(arguments.get("action_type"), "action_type")
        instructions = required_text(arguments.get("instructions"), "instructions")
        if entity_id not in STATE:
            raise KeyError(f"No synthetic entity found for {entity_id}")
        return {"proposed_action": f"{action_type}: {instructions}", "affected_system": "Synthetic HWC case tracker", "risk_level": "medium", "approval_requirement": "Explicit human approval required", "execution_status": "PENDING_APPROVAL", "entity_id": entity_id}
    raise KeyError(f"Unknown tool: {name}")

class MCPHandler(BaseHTTPRequestHandler):
    server_version = "HWC-MCP/1.0"
    def _send(self, status, body):
        payload = json.dumps(body).encode()
        self.send_response(status); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(payload))); self.end_headers(); self.wfile.write(payload)
    def do_GET(self):
        if self.path == "/healthz":
            return self._send(200, {"status": "ok", "synthetic_data": True})
        if self.path in ("/mcp", "/mcp/"):
            return self._send(200, {"jsonrpc": "2.0", "result": {"protocolVersion": "2025-03-26", "capabilities": {"tools": {}}, "serverInfo": {"name": "hwc-synthetic-mcp", "version": "1.0.0"}}})
        self._send(404, {"error": "not found"})
    def do_POST(self):
        correlation_id = self.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        expected = os.getenv("MCP_AUTH_TOKEN")
        if expected and self.headers.get("Authorization") != "Bearer " + expected:
            return self._send(401, {"error": "unauthorized", "correlation_id": correlation_id})
        try:
            request = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))))
            method = request.get("method")
            if method == "tools/list":
                result = {"tools": TOOLS}
            elif method == "tools/call":
                result = {"content": [{"type": "text", "text": json.dumps(call_tool(request.get("params", {}).get("name"), request.get("params", {}).get("arguments")))}]}
            else:
                raise ValueError("Unsupported MCP method")
            self._send(200, {"jsonrpc": "2.0", "id": request.get("id"), "result": result, "correlation_id": correlation_id})
        except (ValueError, KeyError, json.JSONDecodeError) as exc:
            self._send(400, {"jsonrpc": "2.0", "id": request.get("id") if "request" in locals() else None, "error": {"code": -32602, "message": str(exc)}, "correlation_id": correlation_id})
    def log_message(self, fmt, *args):
        return

def run(host="127.0.0.1", port=8001):
    ThreadingHTTPServer((host, port), MCPHandler).serve_forever()

if __name__ == "__main__":
    run(os.getenv("MCP_HOST", "127.0.0.1"), int(os.getenv("MCP_PORT", "8001")))
