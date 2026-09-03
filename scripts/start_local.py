"""Start MCP and agent services together for a local demo."""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
env = {**os.environ, "PYTHONPATH": str(ROOT)}
processes = [
    subprocess.Popen([sys.executable, str(ROOT / "mcp-server/server.py")], env=env),
    subprocess.Popen([sys.executable, "-m", "agent.server"], env=env),
]
try:
    for process in processes:
        process.wait()
finally:
    for process in processes:
        process.terminate()
