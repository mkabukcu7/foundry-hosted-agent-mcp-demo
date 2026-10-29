"""Serve the HWC demo UI and proxy requests to the MCP-backed demo agent."""

import json
from http.cookies import SimpleCookie
import secrets
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock
from urllib.parse import parse_qs, urlsplit

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
FRONTEND = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")
sys.path.insert(0, str(ROOT))

from agent.agent import HostedAgent  # noqa: E402
from frontend.fabric_approvals import submit_approval  # noqa: E402

ASSURANCE = None
ASSURANCE_LOCK = Lock()


def assurance_gateway():
    global ASSURANCE
    with ASSURANCE_LOCK:
        if ASSURANCE is None:
            from frontend.assurance_client import AssuranceGateway
            ASSURANCE = AssuranceGateway()
    return ASSURANCE


class DemoHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(FRONTEND), **kwargs)

    def do_GET(self):
        request = urlsplit(self.path)
        if request.path == "/api/health":
            try:
                HostedAgent().discover_tools()
                self._json_response(200, {"status": "ready", "mcp": "connected"})
            except Exception as error:
                self._json_response(503, {"status": "unavailable", "mcp": "disconnected", "error": str(error)})
            return
        if request.path == "/api/entities":
            try:
                refresh = parse_qs(request.query).get("refresh") == ["1"]
                self._json_response(
                    200,
                    {"entities": HostedAgent().call("list_business_summaries", {"refresh": refresh})},
                )
            except Exception as error:
                self._json_response(502, {"error": f"Unable to load entities: {error}"})
            return
        super().do_GET()

    def do_POST(self):
        if self.path in {"/api/assurance/session", "/api/assurance/respond"}:
            self._assurance_request()
            return
        if self.path not in {"/api/respond", "/api/approvals"}:
            self.send_error(404)
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length) or b"{}")
            if self.path == "/api/approvals":
                result = submit_approval(
                    payload.get("entity_id", ""),
                    payload.get("decision", ""),
                    payload.get("approver", ""),
                )
                self._json_response(200, result)
                return
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

    def _assurance_request(self):
        try:
            host = self.headers.get("Host", "")
            authority = urlsplit("//" + host)
            if (authority.hostname not in {"localhost", "127.0.0.1", "::1"}
                    or authority.username is not None or authority.password is not None
                    or authority.path or authority.query or authority.fragment
                    or authority.port != self.server.server_port):
                self._json_response(403, {"error": "Loopback Host required."})
                return
            origin = self.headers.get("Origin")
            if origin and (urlsplit(origin).scheme != "http" or urlsplit(origin).netloc != host):
                self._json_response(403, {"error": "Same-origin requests only."})
                return
            length = int(self.headers.get("Content-Length", "0"))
            if length < 0 or length > 16384:
                raise ValueError("Request is too large.")
            payload = json.loads(self.rfile.read(length) or b"{}")
            if not isinstance(payload, dict):
                raise ValueError("Expected a JSON object.")
            cookies = SimpleCookie(self.headers.get("Cookie", ""))
            owner = cookies["assurance_owner"].value if "assurance_owner" in cookies else None
            if self.path == "/api/assurance/session":
                owner = owner or secrets.token_urlsafe(32)
                session_id = assurance_gateway().create_session(owner)
                self._json_response(200, {"session_id": session_id, "mode": "live"},
                                    cookie=f"assurance_owner={owner}; HttpOnly; SameSite=Strict; Path=/")
            elif not owner:
                self._json_response(403, {"error": "Start an assurance session first."})
            else:
                result = assurance_gateway().respond(owner, payload.get("session_id", ""),
                                                     payload.get("prompt", ""), payload.get("reset") is True)
                self._json_response(200, result)
        except PermissionError as error:
            self._json_response(403, {"error": str(error)})
        except ValueError as error:
            self._json_response(400, {"error": str(error)})
        except Exception:
            self._json_response(502, {"error": "Live orchestrator unavailable or incomplete. No mock fallback. Check service configuration and metadata traces."})

    def _json_response(self, status, payload, cookie=None):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        if cookie:
            self.send_header("Set-Cookie", cookie)
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        print(f"[frontend] {self.address_string()} {format % args}")


def run(host="127.0.0.1", port=5173):
    print(f"HWC demo UI running at http://{host}:{port}")
    ThreadingHTTPServer((host, port), DemoHandler).serve_forever()


if __name__ == "__main__":
    run()