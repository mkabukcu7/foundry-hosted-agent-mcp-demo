"""Reset the state of the running synthetic MCP server."""
import os
import urllib.request

url = os.getenv("MCP_SERVER_URL", "http://127.0.0.1:8001").rstrip("/") + "/reset"
headers = {}
token = os.getenv("MCP_AUTH_TOKEN")
if token:
    headers["Authorization"] = "Bearer " + token
request = urllib.request.Request(url, method="POST", headers=headers)
with urllib.request.urlopen(request, timeout=5):
    pass
print("Synthetic demo state reset.")
