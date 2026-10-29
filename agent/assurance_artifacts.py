"""Inline synthetic A2A documents; hashes establish integrity, not authorization."""

import base64
from copy import deepcopy
import hashlib
import json
import re
from uuid import uuid4

from agent.assurance_protocol import Artifact, FilePart, FileWithBytes, Part

from shared.contract_assurance import VENDOR_ID, compare_evidence


MAX_DOCUMENT_BYTES = 65536


class ArtifactRejected(ValueError):
    pass


def reference(artifact):
    metadata = artifact["metadata"]
    return {"artifact_id": artifact["artifactId"], "version": metadata["version"],
            "sha256": metadata["sha256"]}


def make_document(evidence, narrative, scope, *, original=None, original_body=None):
    if not scope or not evidence:
        raise ArtifactRejected("Synthetic cited evidence and conversation scope are required.")
    body = {"fictional": True, "vendor_id": VENDOR_ID, "contract_findings": deepcopy(evidence),
            "contract_narrative": narrative}
    artifact_id, version, parent = uuid4().hex, 1, None
    if original is not None:
        body = deepcopy(original_body)
        body["rfp_annotation"] = {"narrative": narrative, "evidence": deepcopy(evidence),
                                  "comparisons": compare_evidence(body["contract_findings"], evidence)}
        parent = reference(original)
        artifact_id, version = parent["artifact_id"], parent["version"] + 1
    raw = json.dumps(body, sort_keys=True, ensure_ascii=True).encode("utf-8")
    if len(raw) > MAX_DOCUMENT_BYTES:
        raise ArtifactRejected("Generated document exceeds the inline demo size limit.")
    source_ids = sorted({item["source_id"] for item in body["contract_findings"]}
                        | {item["source_id"] for item in body.get("rfp_annotation", {}).get("evidence", [])})
    artifact = Artifact(artifact_id=artifact_id, name="synthetic-contract-findings.json", parts=[Part(root=FilePart(
        file=FileWithBytes(bytes=base64.b64encode(raw).decode("ascii"), mime_type="application/json",
                           name="synthetic-contract-findings.json")))],
        metadata={"version": version, "parent": parent, "sha256": hashlib.sha256(raw).hexdigest(),
                  "scope": scope, "source_ids": source_ids})
    return artifact.model_dump(mode="json", by_alias=True)


def read_document(artifact, scope, expected, versions=None):
    try:
        parsed = Artifact.model_validate(artifact)
        metadata = parsed.metadata or {}
        if not re.fullmatch(r"[0-9a-f]{32}", parsed.artifact_id) or not re.fullmatch(r"[0-9a-f]{64}", metadata.get("sha256", "")):
            raise ArtifactRejected("Artifact identifiers must be opaque IDs and content digests.")
        if metadata.get("scope") != scope:
            raise ArtifactRejected("Artifact is not authorized for this conversation.")
        if reference(artifact) != expected:
            raise ArtifactRejected("Artifact identity or version differs from the intended document.")
        version = metadata.get("version")
        if isinstance(version, float) and version.is_integer():
            version = int(version)
        if type(version) is not int or version < 1:
            raise ArtifactRejected("Invalid document version.")
        parent = metadata.get("parent")
        if version > 1 and (not parent or parent.get("artifact_id") != parsed.artifact_id
                            or parent.get("version") != version - 1):
            raise ArtifactRejected("Document version lineage is invalid.")
        if versions and parsed.artifact_id in versions:
            latest = versions[parsed.artifact_id]
            if version < latest["version"] or (version == latest["version"] and expected != latest):
                raise ArtifactRejected("Stale or conflicting document version.")
        if len(parsed.parts) != 1 or parsed.parts[0].root.kind != "file":
            raise ArtifactRejected("The actual document file is missing.")
        file = parsed.parts[0].root.file
        if not isinstance(file, FileWithBytes) or file.mime_type != "application/json":
            raise ArtifactRejected("Only inline synthetic JSON files are supported; no URLs are fetched.")
        if len(file.bytes) > MAX_DOCUMENT_BYTES * 2:
            raise ArtifactRejected("Document exceeds size limit.")
        raw = base64.b64decode(file.bytes, validate=True)
        if len(raw) > MAX_DOCUMENT_BYTES or hashlib.sha256(raw).hexdigest() != metadata.get("sha256"):
            raise ArtifactRejected("Document integrity verification failed.")
        body = json.loads(raw)
        if body.get("fictional") is not True or body.get("vendor_id") != VENDOR_ID:
            raise ArtifactRejected("Only the fictional Northstar demo document is accepted.")
        findings = body.get("contract_findings")
        if not isinstance(findings, list) or not findings or any(
            item.get("document_set") != "contract" or not item.get("source_id", "").startswith("DEMO-NS-CON-")
            for item in findings
        ):
            raise ArtifactRejected("Document has no cited synthetic contract findings.")
        return body, raw.decode("utf-8")
    except ArtifactRejected:
        raise
    except (KeyError, TypeError, ValueError, AttributeError) as error:
        raise ArtifactRejected("Malformed or missing inline artifact.") from error