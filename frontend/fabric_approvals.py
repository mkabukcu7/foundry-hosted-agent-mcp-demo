"""Submit governed approval decisions through a Fabric notebook job."""

import json
import os
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen


FABRIC_SCOPE = "https://api.fabric.microsoft.com/.default"


def submit_approval(entity_id, decision, approver, timeout_seconds=120):
    entity_id = str(entity_id).strip().upper()
    decision = str(decision).strip().upper()
    approver = str(approver).strip()
    if not entity_id.startswith("HWC-") or not entity_id[4:].isdigit():
        raise ValueError("Select a valid HWC exception record.")
    if decision not in {"APPROVED", "REJECTED"}:
        raise ValueError("Decision must be APPROVED or REJECTED.")
    if not approver:
        raise ValueError("Enter the approver identity.")

    workspace_id = os.environ.get("FABRIC_WORKSPACE_ID", "").strip()
    notebook_id = os.environ.get("FABRIC_APPROVAL_NOTEBOOK_ID", "").strip()
    if not workspace_id or not notebook_id:
        raise RuntimeError("Fabric approval notebook is not configured.")

    from azure.identity import DefaultAzureCredential

    token = DefaultAzureCredential().get_token(FABRIC_SCOPE).token
    url = (
        f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}"
        f"/items/{notebook_id}/jobs/instances?jobType=RunNotebook"
    )
    parameters = [
        {"name": "entity_id", "value": entity_id, "type": "Text"},
        {"name": "decision", "value": decision, "type": "Text"},
        {"name": "approver", "value": approver, "type": "Text"},
    ]
    response, body = _request(url, token, method="POST", payload={"executionData": {"parameters": parameters}})
    location = response.headers.get("Location")
    if not location:
        raise RuntimeError("Fabric accepted the approval but returned no job location.")

    deadline = time.monotonic() + timeout_seconds
    retry_after = max(int(response.headers.get("Retry-After", "2")), 1)
    while time.monotonic() < deadline:
        time.sleep(retry_after)
        response, body = _request(location, token)
        status = body.get("status")
        if status == "Completed":
            return _completed_result(body, entity_id, decision, approver)
        if status in {"Failed", "Cancelled", "Deduped"}:
            error = body.get("failureReason") or body.get("error") or status
            raise RuntimeError(f"Fabric approval job {status.lower()}: {error}")
        retry_after = max(int(response.headers.get("Retry-After", "2")), 1)

    raise TimeoutError("Fabric approval job did not finish before the timeout.")


def _request(url, token, method="GET", payload=None):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = Request(
        url,
        data=data,
        method=method,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    try:
        with urlopen(request, timeout=30) as response:
            content = response.read()
            return response, json.loads(content) if content else {}
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Fabric API returned HTTP {error.code}: {detail}") from error


def _completed_result(job, entity_id, decision, approver):
    exit_value = (job.get("executionData") or {}).get("exitValue")
    if exit_value:
        try:
            return json.loads(exit_value)
        except json.JSONDecodeError:
            pass
    return {
        "entity_id": entity_id,
        "decision": decision,
        "approver": approver,
        "job_status": "Completed",
    }