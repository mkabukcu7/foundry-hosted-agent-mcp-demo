"""Serve the HWC demo UI and proxy requests to the MCP-backed demo agent."""

import json
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FRONTEND = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from agent.agent import HostedAgent  # noqa: E402


class DemoHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(FRONTEND), **kwargs)

    def do_GET(self):
        if self.path == "/api/health":
            self._json_response(200, {"status": "ready", "mcp": "connected"})
            return
        if self.path == "/api/entities":
            try:
                self._json_response(
                    200,
                    {"entities": HostedAgent().call("list_business_summaries", {})},
                )
            except Exception as error:
                self._json_response(502, {"error": f"Unable to load entities: {error}"})
            return
        super().do_GET()

    def do_POST(self):
        if self.path != "/api/respond":
            self.send_error(404)
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length) or b"{}")
            prompt = str(payload.get("prompt", "")).strip()
            if not prompt:
                raise ValueError("Enter a question for the agent.")
            self._json_response(200, HostedAgent().respond(prompt))
        except ValueError as error:
            self._json_response(400, {"error": str(error)})
        except Exception as error:
            self._json_response(
                502,
                {"error": f"The MCP-backed agent could not complete the request: {error}"},
            )

    def _json_response(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        print(f"[frontend] {self.address_string()} {format % args}")


def run(host="127.0.0.1", port=5173):
    print(f"HWC demo UI running at http://{host}:{port}")
    ThreadingHTTPServer((host, port), DemoHandler).serve_forever()


if __name__ == "__main__":
    run()