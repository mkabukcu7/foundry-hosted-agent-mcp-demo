"""Start MCP and agent services together for a local demo."""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
env = {
    **os.environ,
    "PYTHONPATH": str(ROOT),
    "languageWorkers__python__defaultExecutablePath": sys.executable,
}
processes = [
    subprocess.Popen(
        ["func", "start", "--port", "8001"],
        cwd=ROOT / "mcp-server",
        env=env,
    ),
    subprocess.Popen([sys.executable, "-m", "agent.server"], env=env),
]
try:
    for process in processes:
        process.wait()
finally:
    for process in processes:
        process.terminate()
