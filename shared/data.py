"""Business state for the demo.

The repo defaults to synthetic data, but it also supports a live Lakehouse-backed
source via environment configuration. The application reads the view
``vw_exception_summary`` when the project is configured for Fabric, and falls
back to the in-memory demo set otherwise.
"""

import copy
import os
import re
import struct
from datetime import date, datetime

from azure.identity import DefaultAzureCredential


_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _validate_sql_identifier(value, name):
    value = str(value).strip() if value is not None else ""
    if not value or not _NAME_RE.fullmatch(value):
        raise ValueError(f"{name} must be an unqualified SQL identifier.")
    return value


def _normalise_record(record):
    """Normalise the source record into the existing in-memory shape."""
    entity_id = str(record.get("entity_id") or record.get("id") or "").upper()
    if not entity_id:
        raise ValueError("Each business record must include an entity_id.")

    record = dict(record)
    record["entity_id"] = entity_id

    record.setdefault("name", entity_id)
    record.setdefault("current_status", record.get("status", "Unknown"))
    record.setdefault("risks", [record["primary_risk"]] if record.get("primary_risk") else [])
    record.setdefault("recent_activity", [])
    if "important_metrics" not in record and "metrics" in record:
        record["important_metrics"] = record["metrics"]
    record.setdefault("important_metrics", {})

    if "supporting_sources" not in record and "source_ids" in record:
        record["supporting_sources"] = record["source_ids"]
    record.setdefault("supporting_sources", ["OneLake:dbo.vw_exception_summary"])

    return record


def _json_value(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _json_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    return value

def _query_fabric():
    """Read the governed summary view from the Fabric SQL analytics endpoint."""
    if os.getenv("HWC_DATA_SOURCE", "synthetic").lower() != "fabric":
        return []

    server = os.getenv("FABRIC_SQL_ENDPOINT")
    database = os.getenv("FABRIC_SQL_DATABASE", os.getenv("FABRIC_LAKEHOUSE_NAME", ""))
    view = _validate_sql_identifier(os.getenv("FABRIC_SUMMARY_VIEW", "vw_exception_summary"), "FABRIC_SUMMARY_VIEW")
    if not server or not database:
        raise RuntimeError("FABRIC_SQL_ENDPOINT and FABRIC_SQL_DATABASE are required for Fabric data access.")

    credential = DefaultAzureCredential()
    token = credential.get_token("https://database.windows.net/.default").token
    token_bytes = token.encode("utf-16le")
    token_struct = struct.pack("<I", len(token_bytes)) + token_bytes

    import pyodbc

    connection_string = (
        f"DRIVER={{{os.getenv('FABRIC_SQL_DRIVER', 'ODBC Driver 18 for SQL Server')}}};"
        f"SERVER={server},1433;DATABASE={database};"
        "Encrypt=yes;TrustServerCertificate=no;"
    )
    with pyodbc.connect(connection_string, attrs_before={1256: token_struct}, timeout=30) as connection:
        cursor = connection.cursor()
        cursor.execute(
            f"SELECT entity_id, status, owner, due_date, severity, exception_category, "
            f"primary_risk, last_review_date, source_last_updated "
            f"FROM dbo.[{view}] ORDER BY entity_id"
        )
        columns = [column[0] for column in cursor.description]
        return [_json_value(dict(zip(columns, row))) for row in cursor.fetchall()]


def get_business_records():
    """Return the active business record set for tool calls.

    Production runtime: read the current Lakehouse-backed summary rows from the
    configured Fabric source.
    Local/demo runtime: fall back to the in-memory synthetic dataset.
    """
    rows = _query_fabric()

    if rows:
        business = {}
        for entry in rows:
            record = _normalise_record(entry)
            business[record["entity_id"]] = record
        return business

    if os.getenv("HWC_DATA_SOURCE", "synthetic").lower() == "fabric":
        raise RuntimeError("Fabric data source returned no business records.")
    return copy.deepcopy(BUSINESS)

KNOWLEDGE = [
    {"title": "Exception management policy", "summary": "Critical client exceptions require an owner, a due date, and approval before external action.", "category": "policy", "source_id": "SYN-POL-001"},
    {"title": "HWC reference architecture", "summary": "The governed agent uses read-only knowledge and business tools, with human approval for actions.", "category": "architecture", "source_id": "SYN-ARC-001"},
    {"title": "Operations runbook", "summary": "An overdue reconciliation exception should be reviewed with the account owner within two business days.", "category": "operations", "source_id": "SYN-OPS-001"},
]

BUSINESS = {
    "HWC-1001": {
        "entity_id": "HWC-1001", "name": "Fictional HWC Industries", "current_status": "Needs attention",
        "important_metrics": {"open_exceptions": 1, "days_since_review": 12, "service_health": "Green"},
        "risks": ["Reconciliation exception is overdue"],
        "recent_activity": ["Automated reconciliation flagged a variance on 2026-08-22", "Account review scheduled for 2026-09-05"],
        "supporting_sources": ["SYN-OPS-001", "SYN-POL-001"],
    }
}


__all__ = ["BUSINESS", "KNOWLEDGE", "get_business_records"]

def reset_state():
    """Return a fresh, in-memory copy of the synthetic business state."""
    import copy
    return copy.deepcopy(BUSINESS)
