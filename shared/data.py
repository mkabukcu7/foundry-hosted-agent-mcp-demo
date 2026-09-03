"""Fictional data used by the demo. No customer or production data is included."""

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

def reset_state():
    """Return a fresh, in-memory copy of the synthetic business state."""
    import copy
    return copy.deepcopy(BUSINESS)
