"""Azure Functions HTTP entry point for the synthetic MCP endpoint."""
import json
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
    try:
        body = req.get_json()
        if body.get("method") == "tools/list":
            result = {"tools": TOOLS}
        elif body.get("method") == "tools/call":
            params = body.get("params", {})
            result = {"content": [{"type": "text", "text": json.dumps(call_tool(params.get("name"), params.get("arguments")))}]}
        else:
            raise ValueError("Unsupported MCP method")
        return func.HttpResponse(json.dumps({"jsonrpc": "2.0", "id": body.get("id"), "result": result}), mimetype="application/json")
    except (ValueError, KeyError) as exc:
        return func.HttpResponse(json.dumps({"error": str(exc)}), status_code=400, mimetype="application/json")
