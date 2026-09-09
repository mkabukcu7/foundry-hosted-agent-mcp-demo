import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from frontend.fabric_approvals import submit_approval


class Response:
    def __init__(self, body, headers=None):
        self.body = json.dumps(body).encode("utf-8")
        self.headers = headers or {}

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.body


class ApprovalTests(unittest.TestCase):
    def test_rejects_invalid_decision_before_calling_fabric(self):
        with self.assertRaisesRegex(ValueError, "APPROVED or REJECTED"):
            submit_approval("HWC-1001", "pending", "reviewer@example.com")

    @patch("frontend.fabric_approvals.time.sleep")
    @patch("frontend.fabric_approvals.urlopen")
    @patch("azure.identity.DefaultAzureCredential")
    def test_submits_and_returns_notebook_exit_value(self, credential, urlopen, sleep):
        credential.return_value.get_token.return_value = SimpleNamespace(token="token")
        result = {
            "approval_id": "approval-123",
            "entity_id": "HWC-1001",
            "decision": "APPROVED",
            "approver": "reviewer@example.com",
        }
        urlopen.side_effect = [
            Response({}, {"Location": "https://fabric/jobs/job-1", "Retry-After": "1"}),
            Response({"status": "Completed", "executionData": {"exitValue": json.dumps(result)}}),
        ]
        with patch.dict(
            "os.environ",
            {"FABRIC_WORKSPACE_ID": "workspace", "FABRIC_APPROVAL_NOTEBOOK_ID": "notebook"},
        ):
            self.assertEqual(
                submit_approval("hwc-1001", "approved", "reviewer@example.com"),
                result,
            )

        request = urlopen.call_args_list[0].args[0]
        payload = json.loads(request.data)
        self.assertEqual(payload["executionData"]["parameters"][1]["value"], "APPROVED")


if __name__ == "__main__":
    unittest.main()