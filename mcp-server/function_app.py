"""Azure Functions HTTP entry point for the synthetic MCP endpoint."""
import json
import os
import uuid
try:
    import azure.functions as func
except ImportError:  # local-only environments do not need the Azure SDK
    func = None
from server import TOOLS, call_tool

def main(req):
    if func is None:
        raise RuntimeError("Install Azure Functions dependencies to use this entry point")
    if req.method == "GET":
        return func.HttpResponse(json.dumps({"status": "ok", "synthetic_data": True}), mimetype="application/json")
    correlation_id = req.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    expected = os.getenv("MCP_AUTH_TOKEN")
    if expected and req.headers.get("Authorization") != "Bearer " + expected:
        return func.HttpResponse(json.dumps({"jsonrpc": "2.0", "id": None, "error": {"code": -32001, "message": "Unauthorized"}, "correlation_id": correlation_id}), status_code=401, mimetype="application/json")
    try:
        body = req.get_json()
        if body.get("method") == "tools/list":
            result = {"tools": TOOLS}
        elif body.get("method") == "tools/call":
            params = body.get("params", {})
            result = {"content": [{"type": "text", "text": json.dumps(call_tool(params.get("name"), params.get("arguments")))}]}
        else:
            raise ValueError("Unsupported MCP method")
        return func.HttpResponse(json.dumps({"jsonrpc": "2.0", "id": body.get("id"), "result": result, "correlation_id": correlation_id}), mimetype="application/json")
    except (ValueError, KeyError) as exc:
        message = exc.args[0] if exc.args else str(exc)
        return func.HttpResponse(json.dumps({"jsonrpc": "2.0", "id": body.get("id") if "body" in locals() else None, "error": {"code": -32602, "message": message}, "correlation_id": correlation_id}), status_code=400, mimetype="application/json")
