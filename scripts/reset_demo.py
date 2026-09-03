"""Document the reset operation; each server restart resets in-memory state."""
import importlib.util
from pathlib import Path
spec = importlib.util.spec_from_file_location("mcp_server", Path(__file__).resolve().parents[1] / "mcp-server/server.py")
server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)
server.STATE.clear()
server.STATE.update(server.copy.deepcopy(server.BUSINESS))
print("Synthetic demo state reset.")
