"""Run real assurance services locally; never provisions or deploys resources."""

import argparse
import os
from pathlib import Path
import socket
import subprocess
import sys

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]


def listening(port):
    with socket.socket() as connection:
        connection.settimeout(0.5)
        return connection.connect_ex(("127.0.0.1", port)) == 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--without-orchestrator", action="store_true", help="Start dependencies; debug the orchestrator with F5.")
    args = parser.parse_args()
    load_dotenv(ROOT / ".env")
    environment = {
        **os.environ,
        "PYTHONPATH": str(ROOT),
        "CONTRACT_ASSURANCE_LOCAL": "1",
        "CONTRACT_ANALYST_URL": "http://127.0.0.1:8091/",
        "RFP_ANALYST_URL": "http://127.0.0.1:8092/",
        "CONTRACT_ORCHESTRATOR_BASE_URL": "http://127.0.0.1:8090/",
    }
    required = (8091, 8092) if args.without_orchestrator else (8090, 8091, 8092)
    if any(listening(port) for port in required):
        parser.error("An assurance port is already in use (8090-8092); stop that service first.")
    for name in ("FOUNDRY_PROJECT_ENDPOINT", "AZURE_AI_MODEL_DEPLOYMENT_NAME", "MCP_SERVER_URL"):
        if not environment.get(name):
            parser.error(f"Configure {name} in the root .env first.")
    processes = []
    def start(module, extra=None):
        process = subprocess.Popen([sys.executable, "-m", module], cwd=ROOT, env={**environment, **(extra or {})})
        processes.append(process)
    try:
        if not listening(8001):
            processes.append(subprocess.Popen(
                [sys.executable, "-c", "from agent.assurance_runtime import configure_privacy; configure_privacy(); import runpy; runpy.run_path('local_mcp.py', run_name='__main__')"],
                cwd=ROOT / "mcp-server", env=environment))
        for role, port in (("contract", 8091), ("rfp", 8092)):
            start("agent.contract_specialist", {"CONTRACT_ASSURANCE_ROLE": role, "PORT": str(port)})
        if not args.without_orchestrator:
            start("agent.contract_assurance", {"PORT": "8090"})
        if not listening(5173):
            start("frontend.server")
        else:
            print("Existing frontend retained. Restart it with CONTRACT_ASSURANCE_LOCAL=1 and CONTRACT_ORCHESTRATOR_BASE_URL=http://127.0.0.1:8090/ if needed.", flush=True)
        print("Assurance services started: http://127.0.0.1:5173/contract-assurance.html", flush=True)
        if args.without_orchestrator:
            print("Press F5: Debug Vendor Contract Assurance.", flush=True)
        for process in processes:
            process.wait()
    except KeyboardInterrupt:
        pass
    finally:
        for process in processes:
            if process.poll() is None:
                process.terminate()
        for process in processes:
            process.wait()


if __name__ == "__main__":
    main()