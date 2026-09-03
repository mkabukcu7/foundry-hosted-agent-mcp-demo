"""Stage the Azure Functions MCP deployment artifact for azd."""

from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "mcp-server"
DESTINATION = ROOT / ".azure" / "mcp-server"


def ignore_cache(_directory, names):
    return {
        name
        for name in names
        if name in {"__pycache__", ".venv", "local.settings.json"}
        or name.endswith((".pyc", ".pyo"))
    }


if DESTINATION.exists():
    shutil.rmtree(DESTINATION)
shutil.copytree(SOURCE, DESTINATION, ignore=ignore_cache)
shutil.copytree(ROOT / "shared", DESTINATION / "shared", ignore=ignore_cache)
print(f"Staged MCP Function artifact at {DESTINATION}")