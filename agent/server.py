"""Minimal local Responses endpoint for the hosted-agent demo."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from agent.agent import HostedAgent

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/healthz":
            body = {"status": "ok", "agent": "hwc-hosted-agent", "synthetic_data": True}
            data = json.dumps(body).encode(); self.send_response(200); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data)
            return
        self.send_response(404); self.end_headers()
    def do_POST(self):
        if self.path != "/v1/responses":
            self.send_response(404); self.end_headers(); return
        try:
            request = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))))
            prompt = request.get("input", "")
            if isinstance(prompt, list):
                prompt = " ".join(str(item.get("text", item)) if isinstance(item, dict) else str(item) for item in prompt)
            result = HostedAgent().respond(prompt)
            data = json.dumps(result).encode(); self.send_response(200); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data)
        except Exception:
            data = json.dumps({"error": {"type": "upstream_error", "message": "Unable to complete the response request."}}).encode()
            self.send_response(502); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data)
    def log_message(self, fmt, *args): return

def run(host="127.0.0.1", port=8000):
    ThreadingHTTPServer((host, port), Handler).serve_forever()

if __name__ == "__main__":
    import os
    run(os.getenv("AGENT_HOST", "127.0.0.1"), int(os.getenv("AGENT_PORT", "8000")))
