from __future__ import annotations

import json
import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import (
    AgentExecution, AgentFinding, EvidenceFile, FindingReview, Investigation, InvestigationReport,
    MonitoringObservation, Project, RegistryRecord, SourceReference, utcnow,
)
from ..services.agents.common import AgentContext, safe_public_https_url
from ..services.ai.structured_output import AgentOutput, FindingOutput


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12].upper()}"


def _dump(value) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def persist_agent_output(db: Session, investigation: Investigation, execution: AgentExecution,
                         output: AgentOutput, context: AgentContext) -> tuple[AgentOutput, int, int]:
    """Persist typed output after enforcing project context and citation rules."""
    source_rows: list[SourceReference] = []
    source_id_map: dict[str, str] = {}
    output_sources = []
    rejected_source_count = 0
    for source in output.sources:
        if not safe_public_https_url(source.url):
            rejected_source_count += 1
            continue
        existing = db.scalar(select(SourceReference).where(
            SourceReference.investigation_id == investigation.id, SourceReference.url == source.url,
        ))
        if existing is None:
            existing = SourceReference(
                id=_id("SRC"), investigation_id=investigation.id, execution_id=execution.id,
                title=source.title, url=source.url, publisher=source.publisher, domain=source.domain,
                retrieved_at=source.retrieved_at, published_at=source.published_at, excerpt=source.excerpt,
                created_at=utcnow(),
            )
            db.add(existing)
            db.flush()
            source_rows.append(existing)
        if source.id:
            source_id_map[source.id] = existing.id
        output_sources.append(source.model_copy(update={"id": existing.id}))

    valid_sources = context.source_ids | {item.id for item in source_rows}
    valid_sources.update(row.id for row in db.scalars(select(SourceReference).where(SourceReference.investigation_id == investigation.id)))
    findings: list[FindingOutput] = []
    limitations = list(output.limitations)
    if rejected_source_count:
        limitations.append(f"{rejected_source_count} public source reference(s) were excluded because the URL was not safe to retain.")
    for index, finding in enumerate(output.findings):
        evidence_ids = list(dict.fromkeys(value for value in finding.evidence_ids if value in context.evidence_ids))
        mapped_sources = [source_id_map.get(value, value) for value in finding.source_ids]
        invalid_refs = any(value not in context.evidence_ids for value in finding.evidence_ids) or any(value not in valid_sources for value in mapped_sources)
        source_ids = list(dict.fromkeys(value for value in mapped_sources if value in valid_sources))
        status, basis = finding.status, finding.basis
        if invalid_refs:
            limitations.append(f"Finding {finding.title!r} referenced an unavailable evidence/source ID; unsupported references were removed.")
            status, basis = "unresolved", "unresolved"
        if not evidence_ids and not source_ids and status == "requires_human_review":
            limitations.append(f"Finding {finding.title!r} has no linked evidence or source and was marked unresolved.")
            status, basis = "unresolved", "unresolved"
        cleaned = finding.model_copy(update={
            "evidence_ids": evidence_ids, "source_ids": source_ids,
            "status": status, "basis": basis,
        })
        findings.append(cleaned)
        db.add(AgentFinding(
            id=_id("FND"), investigation_id=investigation.id, execution_id=execution.id,
            finding_index=index, category=cleaned.category, severity=cleaned.severity,
            title=cleaned.title, description=cleaned.description, claim=cleaned.claim,
            observed_value=cleaned.observed_value, evidence_ids_json=_dump(evidence_ids),
            source_ids_json=_dump(source_ids), confidence=cleaned.confidence,
            status=cleaned.status, basis=cleaned.basis, recommendation=cleaned.recommendation,
            created_at=utcnow(),
        ))
    updated = output.model_copy(update={
        "findings": findings,
        "sources": output_sources,
        "limitations": list(dict.fromkeys(limitations)),
    })
    execution.output_json = _dump(updated.model_dump(mode="json"))
    return updated, len(findings), len(source_rows)


def finding_dict(row: AgentFinding, *, reviews: list[dict] | None = None,
                 evidence: list[dict] | None = None, sources: list[dict] | None = None) -> dict:
    return {
        "id": row.id, "investigation_id": row.investigation_id, "execution_id": row.execution_id,
        "category": row.category, "severity": row.severity, "title": row.title,
        "description": row.description, "claim": row.claim, "observed_value": row.observed_value,
        "evidence_ids": json.loads(row.evidence_ids_json), "source_ids": json.loads(row.source_ids_json),
        "evidence": evidence or [], "sources": sources or [], "confidence": row.confidence,
        "confidence_note": "Confidence is an agent estimate, not a calibrated probability.",
        "status": row.status, "basis": row.basis, "recommendation": row.recommendation,
        "review_decision": row.review_decision, "review_reason": row.review_reason,
        "reviewer_id": row.reviewer_id, "reviewed_at": row.reviewed_at.isoformat() if row.reviewed_at else None,
        "reviews": reviews or [], "created_at": row.created_at.isoformat(),
    }


def _citations(db: Session, ids: set[str]) -> tuple[list[dict], list[dict]]:
    evidence = list(db.scalars(select(EvidenceFile).where(EvidenceFile.id.in_(ids)))) if ids else []
    registry = list(db.scalars(select(RegistryRecord).where(RegistryRecord.id.in_(ids)))) if ids else []
    observations = list(db.scalars(select(MonitoringObservation).where(MonitoringObservation.id.in_(ids)))) if ids else []
    refs = list(db.scalars(select(SourceReference).where(SourceReference.id.in_(ids)))) if ids else []
    evidence_rows = [{"id": x.id, "kind": "evidence", "title": x.filename, "sha256": x.sha256,
                      "project_id": x.project_id} for x in evidence]
    source_rows = [{"id": x.id, "kind": "registry_record", "title": x.external_project_name,
                    "publisher": x.source_name, "external_project_id": x.external_project_id,
                    "serial": x.external_serial, "status": x.status} for x in registry]
    source_rows.extend({"id": x.id, "kind": "monitoring_observation", "title": f"{x.signal_type} observation",
                        "publisher": x.source_name, "observed_at": x.observed_at,
                        "severity": x.severity, "is_synthetic": x.is_synthetic} for x in observations)
    source_rows.extend({"id": x.id, "kind": "public_source", "title": x.title, "url": x.url,
                        "publisher": x.publisher, "domain": x.domain, "retrieved_at": x.retrieved_at,
                        "published_at": x.published_at} for x in refs)
    return evidence_rows, source_rows


def create_report_snapshot(db: Session, investigation: Investigation, *, created_by: str | None = None) -> InvestigationReport:
    findings = list(db.scalars(select(AgentFinding).where(AgentFinding.investigation_id == investigation.id).order_by(AgentFinding.created_at, AgentFinding.id)))
    executions = list(db.scalars(select(AgentExecution).where(AgentExecution.investigation_id == investigation.id).order_by(AgentExecution.created_at, AgentExecution.id)))
    source_refs = list(db.scalars(select(SourceReference).where(SourceReference.investigation_id == investigation.id).order_by(SourceReference.created_at, SourceReference.id)))
    output_limitations = []
    for execution in executions:
        if execution.output_json:
            try:
                output_limitations.extend(json.loads(execution.output_json).get("limitations", []))
            except (json.JSONDecodeError, TypeError):
                output_limitations.append("An agent output could not be parsed while generating the report.")
        if execution.status == "failed":
            output_limitations.append(f"{execution.agent_key} did not complete successfully ({execution.error_code or 'unknown_error'}).")
    if investigation.failure_summary:
        output_limitations.append(investigation.failure_summary)
    if not findings:
        output_limitations.append("No structured findings were available when this report version was generated.")
    limitations = list(dict.fromkeys(str(item)[:1000] for item in output_limitations if item))

    finding_rows = []
    for row in findings:
        ids = set(json.loads(row.evidence_ids_json)) | set(json.loads(row.source_ids_json))
        evidence, sources = _citations(db, ids)
        reviews = list(db.scalars(select(FindingReview).where(FindingReview.finding_id == row.id).order_by(FindingReview.created_at, FindingReview.id)))
        finding_rows.append(finding_dict(row, evidence=evidence, sources=sources, reviews=[{
            "id": review.id, "decision": review.decision, "reason": review.reason,
            "reviewer_id": review.reviewer_id, "created_at": review.created_at.isoformat(),
        } for review in reviews]))
    project = db.get(Project, investigation.project_id)
    content = {
        "investigation": {"id": investigation.id, "title": investigation.title, "scope": investigation.scope,
                          "status": investigation.status, "project_id": investigation.project_id,
                          "project_name": project.name if project else None},
        "findings": finding_rows,
        "sources": [{"id": x.id, "execution_id": x.execution_id, "title": x.title, "url": x.url,
                     "publisher": x.publisher, "domain": x.domain, "retrieved_at": x.retrieved_at,
                     "published_at": x.published_at, "excerpt": x.excerpt} for x in source_refs],
        "agents": [{"execution_id": x.id, "agent_key": x.agent_key, "attempt_number": x.attempt_number,
                    "status": x.status, "error_code": x.error_code, "started_at": x.started_at.isoformat() if x.started_at else None,
                    "completed_at": x.completed_at.isoformat() if x.completed_at else None} for x in executions],
        "limitations": limitations,
        "confidence_note": "Confidence values are agent estimates, not calibrated probabilities.",
        "human_review_note": "Reviewer decisions are recorded separately and do not establish environmental or legal facts.",
    }
    previous = db.scalar(select(func.max(InvestigationReport.version)).where(InvestigationReport.investigation_id == investigation.id)) or 0
    report = InvestigationReport(
        id=_id("RPT"), investigation_id=investigation.id, version=previous + 1,
        status=investigation.status, summary=f"{len(findings)} finding(s) from {len(executions)} agent execution record(s).",
        content_json=_dump(content), limitations_json=_dump(limitations), created_by=created_by,
        created_at=utcnow(),
    )
    db.add(report)
    db.flush()
    return report
