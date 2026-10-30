from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models import CreditBatch, IntegrityScore, RegistryRecord


WEIGHTS = {"M": 0.25, "V": 0.20, "C": 0.20, "R": 0.25, "A": 0.10}


def calculate_score(components: dict[str, int]) -> int:
    return round(sum(WEIGHTS[key] * components[key] for key in WEIGHTS))


def update_score(db: Session, batch: CreditBatch, reason: str) -> IntegrityScore:
    component = json.loads(batch.score_components or "{}")
    components = {key: max(0, min(100, int(component.get(key, 50)))) for key in WEIGHTS}
    serial_matches = db.query(RegistryRecord).filter(func.lower(RegistryRecord.external_serial) == batch.serial_start.casefold()).count()
    if serial_matches > 1:
        components["C"] = min(components["C"], 25)
    score = calculate_score(components)
    flags = []
    if not batch.evidence_hash:
        flags.append("batch_evidence_hash_missing")
    if not batch.methodology_id:
        flags.append("methodology_not_provided")
    if not batch.registry_name:
        flags.append("registry_source_not_provided")
    if serial_matches == 0:
        flags.append("registry_coverage_not_checked")
    elif serial_matches > 1:
        flags.append("serial_conflict_in_available_records")
    if batch.state in {"At Risk", "Under Review"}:
        flags.append("open_risk_or_review_signal")
    flags.append("prototype_heuristic_not_independently_validated")
    calculated = datetime.now(timezone.utc)
    batch.score = score
    batch.score_components = json.dumps(components)
    batch.score_missing_flags = json.dumps(flags)
    batch.score_calculated_at = calculated
    record = IntegrityScore(
        id=f"SCORE-{batch.id}-{int(calculated.timestamp() * 1000)}",
        credit_batch_id=batch.id,
        score_total=score,
        evidence_quality_score=components["M"],
        verification_score=components["V"],
        registry_consistency_score=components["C"],
        reversal_resilience_score=components["R"],
        authorization_score=components["A"],
        missing_data_flags=json.dumps(flags),
        explanation_json=json.dumps({"reason": reason, "weights": WEIGHTS, "score_is_provisional": True}),
        calculated_at=calculated,
        is_demo=batch.is_demo,
    )
    db.add(record)
    return record

