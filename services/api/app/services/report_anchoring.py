from __future__ import annotations

import hashlib
import json
import secrets
from datetime import datetime, timezone

from ..models import InvestigationReport

CANONICALIZATION = "triplees-canonical-json-v1"


def _utc_iso(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if not isinstance(value, datetime):
        raise ValueError("Report creation time must be an ISO 8601 timestamp.")
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _canonical_payload(fields: dict) -> dict:
    return {"schema": CANONICALIZATION, "report": fields}


def canonical_report_payload(report: InvestigationReport) -> dict:
    """Stable snapshot fields; excludes mutable anchor metadata and available-version lists."""
    return _canonical_payload({
        "id": report.id,
        "version": report.version,
        "status": report.status,
        "summary": report.summary,
        "limitations": json.loads(report.limitations_json),
        "content": json.loads(report.content_json),
        "created_at": _utc_iso(report.created_at),
    })


def canonical_report_bytes(report: InvestigationReport) -> bytes:
    return json.dumps(
        canonical_report_payload(report), ensure_ascii=False, sort_keys=True,
        separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")


def report_sha256(report: InvestigationReport) -> str:
    return hashlib.sha256(canonical_report_bytes(report)).hexdigest()


def report_sha256_from_document(document: dict) -> str:
    """Hash a downloaded report using the exact same canonical fields as a stored snapshot."""
    if "report" in document and isinstance(document["report"], dict):
        document = document["report"]
    version = document.get("version")
    if isinstance(version, bool) or not isinstance(version, int) or version < 1:
        raise ValueError("Report version must be a positive integer.")
    if not isinstance(document.get("limitations"), list) or not isinstance(document.get("content"), dict):
        raise ValueError("Report limitations and content must be supplied in their original JSON shapes.")
    fields = {
        "id": document.get("id"),
        "version": version,
        "status": document.get("status"),
        "summary": document.get("summary"),
        "limitations": document["limitations"],
        "content": document["content"],
        "created_at": _utc_iso(document.get("created_at")),
    }
    if not all(isinstance(fields[key], str) and fields[key] for key in ("id", "status", "summary", "created_at")):
        raise ValueError("Report ID, status, summary, and creation time are required.")
    return hashlib.sha256(json.dumps(
        _canonical_payload(fields), ensure_ascii=False, sort_keys=True,
        separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")).hexdigest()


def new_anchor_reference() -> tuple[str, str]:
    """Return an unguessable public reference and an independent bytes32 chain key."""
    return f"RAN-{secrets.token_urlsafe(32)}", "0x" + secrets.token_hex(32)
