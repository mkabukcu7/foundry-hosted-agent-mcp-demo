"""Start MCP and agent services together for a local demo."""
import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
env = {
    **os.environ,
    "PYTHONPATH": str(ROOT),
    "languageWorkers__python__defaultExecutablePath": sys.executable,
}
mcp_command = (
    [sys.executable, "local_mcp.py"]
    if os.getenv("USE_LOCAL_MCP") == "1"
    else ["func", "start", "--port", "8001"]
)
processes = [
    subprocess.Popen(
        mcp_command,
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
