"""Read-only fictional terms for the Vendor Contract Assurance demo."""

from copy import deepcopy

VENDOR_ID = "northstar-demo"
VENDOR_NAME = "Northstar Cloud Services (fictional)"
TERMS = (
    ("uptime", "Uptime", "99.95%", "99.5%"),
    ("service_credit", "Service credit", "10%", "5%"),
    ("breach_notification", "Breach notification", "24 hours", "72 hours"),
    ("data_residency", "Data residency", "EU", "EU"),
)
DOCUMENTS = {
    document_set: [
        {
            "source_id": f"DEMO-NS-{prefix}-{index:03d}",
            "vendor_id": VENDOR_ID,
            "vendor_name": VENDOR_NAME,
            "document_set": document_set,
            "clause": f"{prefix} section {index}",
            "topic": topic,
            "value": rfp_value if document_set == "rfp" else contract_value,
            "text": f"{label}: {rfp_value if document_set == 'rfp' else contract_value}.",
            "fictional": True,
        }
        for index, (topic, label, rfp_value, contract_value) in enumerate(TERMS, 1)
    ]
    for document_set, prefix in (("contract", "CON"), ("rfp", "RFP"))
}


def retrieve_terms(document_set, vendor_id=VENDOR_ID, topic=None):
    if document_set not in DOCUMENTS:
        raise ValueError("Unknown document set.")
    if vendor_id != VENDOR_ID:
        return []
    return deepcopy([
        clause for clause in DOCUMENTS[document_set]
        if topic is None or clause["topic"] == topic
    ])


def compare_evidence(contract, rfp):
    """Compare only returned evidence; absent clauses are not inferred."""
    contract_by_topic = {item["topic"]: item for item in contract}
    rfp_by_topic = {item["topic"]: item for item in rfp}
    comparisons = []
    for topic, label, _, _ in TERMS:
        contract_item = contract_by_topic.get(topic)
        rfp_item = rfp_by_topic.get(topic)
        if not contract_item or not rfp_item:
            comparisons.append({"topic": topic, "status": "insufficient_evidence", "source_ids": []})
            continue
        comparisons.append({
            "topic": topic,
            "label": label,
            "status": "match" if contract_item["value"] == rfp_item["value"] else "discrepancy",
            "contract": contract_item["value"],
            "rfp": rfp_item["value"],
            "source_ids": [contract_item["source_id"], rfp_item["source_id"]],
        })
    return comparisons