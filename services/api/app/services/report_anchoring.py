from __future__ import annotations

import hashlib
import json
import secrets
from datetime import timezone

from ..models import InvestigationReport

CANONICALIZATION = "triplees-canonical-json-v1"


def _utc_iso(value) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def canonical_report_payload(report: InvestigationReport) -> dict:
    """Stable snapshot fields; excludes mutable anchor metadata and available-version lists."""
    return {
        "schema": CANONICALIZATION,
        "report": {
            "id": report.id,
            "version": report.version,
            "status": report.status,
            "summary": report.summary,
            "limitations": json.loads(report.limitations_json),
            "content": json.loads(report.content_json),
            "created_at": _utc_iso(report.created_at),
        },
    }


def canonical_report_bytes(report: InvestigationReport) -> bytes:
    return json.dumps(
        canonical_report_payload(report), ensure_ascii=False, sort_keys=True,
        separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")


def report_sha256(report: InvestigationReport) -> str:
    return hashlib.sha256(canonical_report_bytes(report)).hexdigest()


def new_anchor_reference() -> tuple[str, str]:
    """Return an unguessable public reference and an independent bytes32 chain key."""
    return f"RAN-{secrets.token_urlsafe(32)}", "0x" + secrets.token_hex(32)
