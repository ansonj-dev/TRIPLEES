from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .db import get_db
from .models import (AgentAuditEvent, AgentExecution, AgentFinding, EvidenceFile, FindingReview,
                     Investigation, InvestigationReport, InvestigationReportAnchor, Profile, Project, SourceReference, utcnow)
from .schemas import FindingReviewRequest, InvestigationCreate, InvestigationRetry
from .security import current_user
from .services.investigation_reports import _citations, create_report_snapshot, finding_dict
from .services.report_anchoring import CANONICALIZATION, report_sha256

router = APIRouter()
TERMINAL = {"cancelled", "completed", "completed_with_limitations", "partial", "failed"}


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12].upper()}"


def _project(db: Session, project_id: str, user: Profile) -> Project:
    row = db.get(Project, project_id)
    if row is None or (row.created_by != user.id and user.role not in {"reviewer", "admin"}):
        raise HTTPException(404, detail={"code": "project_not_found", "message": "Project was not found."})
    return row


def _get(db: Session, investigation_id: str, user: Profile) -> Investigation:
    row = db.get(Investigation, investigation_id)
    if row is None:
        raise HTTPException(404, detail={"code": "investigation_not_found", "message": "Investigation was not found."})
    _project(db, row.project_id, user)
    return row


def _event(db: Session, inv: Investigation, event_type: str, details: dict | None = None, execution_id: str | None = None) -> None:
    db.add(AgentAuditEvent(id=_id("AUD"), investigation_id=inv.id, execution_id=execution_id,
                           event_type=event_type, details_json=json.dumps(details or {}, separators=(",", ":"))))


def _view(row: Investigation, executions: list[AgentExecution] | None = None) -> dict:
    return {
        "id": row.id, "project_id": row.project_id, "created_by": row.created_by,
        "title": row.title, "scope": row.scope, "evidence_ids": json.loads(row.evidence_ids_json),
        "status": row.status, "external_ai_authorized": row.external_ai_authorized,
        "public_research_authorized": row.public_research_authorized,
        "ai_token_budget": row.ai_token_budget, "ai_tokens_used": row.ai_tokens_used,
        "attempt_count": row.attempt_count, "cancel_requested": row.cancel_requested,
        "failure_summary": row.failure_summary,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "started_at": row.started_at.isoformat() if row.started_at else None,
        "completed_at": row.completed_at.isoformat() if row.completed_at else None,
        "executions": [{"id": x.id, "agent_key": x.agent_key, "attempt_number": x.attempt_number,
                        "status": x.status, "task_summary": x.task_summary, "output": json.loads(x.output_json) if x.output_json else None,
                        "error_code": x.error_code, "started_at": x.started_at.isoformat() if x.started_at else None,
                        "completed_at": x.completed_at.isoformat() if x.completed_at else None} for x in (executions or [])],
    }


@router.post("/api/investigations", status_code=201)
def create_investigation(body: InvestigationCreate, response: Response, idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
                         db: Session = Depends(get_db), user: Profile = Depends(current_user)):
    project = _project(db, body.project_id, user)
    key = (idempotency_key or "").strip() or None
    if key and len(key) > 100:
        raise HTTPException(422, detail={"code": "idempotency_key_too_long", "message": "Idempotency-Key must be at most 100 characters."})
    evidence_ids = list(dict.fromkeys(body.evidence_ids))
    if evidence_ids:
        evidence = list(db.scalars(select(EvidenceFile).where(EvidenceFile.id.in_(evidence_ids), EvidenceFile.project_id == project.id)))
        if {x.id for x in evidence} != set(evidence_ids):
            raise HTTPException(422, detail={"code": "evidence_project_mismatch", "message": "Every selected evidence file must belong to the selected project."})
    if key:
        existing = db.scalar(select(Investigation).where(Investigation.created_by == user.id, Investigation.request_key == key))
        if existing:
            expected = (project.id, body.title, body.scope, evidence_ids, body.external_ai_authorized, body.public_research_authorized, body.ai_token_budget)
            actual = (existing.project_id, existing.title, existing.scope, json.loads(existing.evidence_ids_json), existing.external_ai_authorized, existing.public_research_authorized, existing.ai_token_budget)
            if actual != expected:
                raise HTTPException(409, detail={"code": "idempotency_key_conflict", "message": "This Idempotency-Key was already used with a different request."})
            response.status_code = 200
            return _view(existing)
    row = Investigation(id=_id("INV"), project_id=project.id, created_by=user.id, request_key=key,
                        title=body.title, scope=body.scope, evidence_ids_json=json.dumps(evidence_ids),
                        external_ai_authorized=body.external_ai_authorized,
                        public_research_authorized=body.public_research_authorized,
                        ai_token_budget=body.ai_token_budget, status="draft")
    db.add(row)
    db.flush()
    _event(db, row, "investigation_created", {"evidence_count": len(evidence_ids), "external_ai_authorized": body.external_ai_authorized,
                                               "public_research_authorized": body.public_research_authorized})
    db.commit()
    return _view(row)


@router.get("/api/investigations")
def list_investigations(offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db), user: Profile = Depends(current_user)):
    query = select(Investigation).join(Project, Project.id == Investigation.project_id)
    if user.role not in {"reviewer", "admin"}:
        query = query.where(Investigation.created_by == user.id)
    rows = list(db.scalars(query.order_by(Investigation.created_at.desc()).offset(offset).limit(limit)))
    return {"items": [_view(x) for x in rows], "offset": offset, "limit": limit}


@router.get("/api/investigations/{investigation_id}")
def get_investigation(investigation_id: str, db: Session = Depends(get_db), user: Profile = Depends(current_user)):
    row = _get(db, investigation_id, user)
    executions = list(db.scalars(select(AgentExecution).where(AgentExecution.investigation_id == row.id).order_by(AgentExecution.created_at)))
    return _view(row, executions)


@router.post("/api/investigations/{investigation_id}/run", status_code=202)
def run_investigation(investigation_id: str, response: Response, db: Session = Depends(get_db), user: Profile = Depends(current_user)):
    row = _get(db, investigation_id, user)
    if row.status in {"queued", "running", "retry_wait", "cancel_requested"}:
        response.status_code = 202
        return _view(row)
    if row.status not in {"draft", "partial", "failed", "completed_with_limitations"}:
        raise HTTPException(409, detail={"code": "investigation_not_runnable", "message": "Investigation cannot be queued in its current state."})
    row.status = "queued"
    row.cancel_requested = False
    row.failure_summary = None
    row.completed_at = None
    row.next_attempt_at = utcnow()
    row.updated_at = utcnow()
    _event(db, row, "investigation_queued")
    db.commit()
    return _view(row)


@router.post("/api/investigations/{investigation_id}/cancel")
def cancel_investigation(investigation_id: str, db: Session = Depends(get_db), user: Profile = Depends(current_user)):
    row = _get(db, investigation_id, user)
    if row.status in TERMINAL:
        return _view(row)
    if row.status in {"queued", "retry_wait", "draft"}:
        row.status = "cancelled"
        row.cancel_requested = True
        row.completed_at = utcnow()
    else:
        row.status = "cancel_requested"
        row.cancel_requested = True
    row.updated_at = utcnow()
    _event(db, row, "cancellation_requested")
    db.commit()
    return _view(row)


@router.post("/api/investigations/{investigation_id}/retry", status_code=202)
def retry_investigation(investigation_id: str, body: InvestigationRetry, db: Session = Depends(get_db), user: Profile = Depends(current_user)):
    row = _get(db, investigation_id, user)
    if row.status not in {"failed", "partial"}:
        raise HTTPException(409, detail={"code": "investigation_not_retryable", "message": "Only failed or partial investigations can be retried."})
    row.status = "queued"
    row.cancel_requested = False
    row.failure_summary = None
    row.completed_at = None
    row.next_attempt_at = utcnow()
    row.updated_at = utcnow()
    _event(db, row, "investigation_retry_queued", {"reason": body.reason} if body.reason else {})
    db.commit()
    return _view(row)


@router.get("/api/investigations/{investigation_id}/audit")
def investigation_audit(investigation_id: str, db: Session = Depends(get_db), user: Profile = Depends(current_user)):
    row = _get(db, investigation_id, user)
    events = list(db.scalars(select(AgentAuditEvent).where(AgentAuditEvent.investigation_id == row.id).order_by(AgentAuditEvent.created_at, AgentAuditEvent.id)))
    return {"items": [{"id": x.id, "execution_id": x.execution_id, "event_type": x.event_type, "details": json.loads(x.details_json), "created_at": x.created_at.isoformat()} for x in events]}


@router.get("/api/investigations/{investigation_id}/agents")
def investigation_agents(investigation_id: str, db: Session = Depends(get_db), user: Profile = Depends(current_user)):
    row = _get(db, investigation_id, user)
    executions = list(db.scalars(select(AgentExecution).where(AgentExecution.investigation_id == row.id).order_by(AgentExecution.created_at, AgentExecution.id)))
    latest: dict[str, AgentExecution] = {}
    for execution in executions:
        if execution.agent_key not in latest or execution.attempt_number > latest[execution.agent_key].attempt_number:
            latest[execution.agent_key] = execution
    return {"investigation_id": row.id, "status": row.status, "items": [{
        "agent_key": key, "execution_id": item.id, "attempt_number": item.attempt_number,
        "status": item.status, "task_summary": item.task_summary, "error_code": item.error_code,
        "started_at": item.started_at.isoformat() if item.started_at else None,
        "completed_at": item.completed_at.isoformat() if item.completed_at else None,
    } for key, item in latest.items()]}


@router.get("/api/investigations/{investigation_id}/findings")
def investigation_findings(
    investigation_id: str,
    offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200),
    severity: str | None = Query(default=None, pattern="^(info|low|medium|high|critical)$"),
    status: str | None = Query(default=None, pattern="^(requires_human_review|hypothesis|unresolved)$"),
    review_decision: str | None = Query(default=None, pattern="^(confirmed|rejected|needs_more_evidence)$"),
    db: Session = Depends(get_db), user: Profile = Depends(current_user),
):
    row = _get(db, investigation_id, user)
    query = select(AgentFinding).where(AgentFinding.investigation_id == row.id)
    if severity:
        query = query.where(AgentFinding.severity == severity)
    if status:
        query = query.where(AgentFinding.status == status)
    if review_decision:
        query = query.where(AgentFinding.review_decision == review_decision)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    findings = list(db.scalars(query.order_by(AgentFinding.created_at, AgentFinding.id).offset(offset).limit(limit)))
    items = []
    for finding in findings:
        evidence, sources = _citations(db, set(json.loads(finding.evidence_ids_json)) | set(json.loads(finding.source_ids_json)))
        reviews = list(db.scalars(select(FindingReview).where(FindingReview.finding_id == finding.id).order_by(FindingReview.created_at, FindingReview.id)))
        items.append(finding_dict(finding, evidence=evidence, sources=sources, reviews=[{
            "id": review.id, "decision": review.decision, "reason": review.reason,
            "reviewer_id": review.reviewer_id, "created_at": review.created_at.isoformat(),
        } for review in reviews]))
    return {"items": items, "total": total, "offset": offset, "limit": limit}


@router.get("/api/findings/review-queue")
def finding_review_queue(offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200),
                         db: Session = Depends(get_db), user: Profile = Depends(current_user)):
    if user.role not in {"reviewer", "admin"}:
        raise HTTPException(403, detail={"code": "reviewer_role_required", "message": "Only an authorized reviewer can access the finding review queue."})
    query = select(AgentFinding).join(Investigation, Investigation.id == AgentFinding.investigation_id).where(
        AgentFinding.review_decision.is_(None),
        Investigation.status.in_(["completed", "completed_with_limitations", "partial", "failed"]),
    )
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = list(db.scalars(query.order_by(AgentFinding.created_at, AgentFinding.id).offset(offset).limit(limit)))
    items = []
    for finding in rows:
        investigation = db.get(Investigation, finding.investigation_id)
        evidence, sources = _citations(db, set(json.loads(finding.evidence_ids_json)) | set(json.loads(finding.source_ids_json)))
        items.append({**finding_dict(finding, evidence=evidence, sources=sources),
                      "investigation_title": investigation.title, "project_id": investigation.project_id})
    return {"items": items, "total": total, "offset": offset, "limit": limit}


@router.get("/api/findings")
def list_findings(offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200),
                  severity: str | None = Query(default=None, pattern="^(info|low|medium|high|critical)$"),
                  status: str | None = Query(default=None, pattern="^(requires_human_review|hypothesis|unresolved)$"),
                  review_decision: str | None = Query(default=None, pattern="^(confirmed|rejected|needs_more_evidence)$"),
                  db: Session = Depends(get_db), user: Profile = Depends(current_user)):
    query = select(AgentFinding).join(Investigation, Investigation.id == AgentFinding.investigation_id).join(Project, Project.id == Investigation.project_id)
    if user.role not in {"reviewer", "admin"}:
        query = query.where(Investigation.created_by == user.id)
    if severity:
        query = query.where(AgentFinding.severity == severity)
    if status:
        query = query.where(AgentFinding.status == status)
    if review_decision:
        query = query.where(AgentFinding.review_decision == review_decision)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = list(db.scalars(query.order_by(AgentFinding.created_at.desc(), AgentFinding.id).offset(offset).limit(limit)))
    items = []
    for finding in rows:
        investigation = db.get(Investigation, finding.investigation_id)
        evidence, sources = _citations(db, set(json.loads(finding.evidence_ids_json)) | set(json.loads(finding.source_ids_json)))
        items.append({**finding_dict(finding, evidence=evidence, sources=sources),
                      "investigation_title": investigation.title, "project_id": investigation.project_id,
                      "investigation_status": investigation.status})
    return {"items": items, "total": total, "offset": offset, "limit": limit}


@router.get("/api/investigations/{investigation_id}/sources")
def investigation_sources(investigation_id: str, db: Session = Depends(get_db), user: Profile = Depends(current_user)):
    row = _get(db, investigation_id, user)
    sources = list(db.scalars(select(SourceReference).where(SourceReference.investigation_id == row.id).order_by(SourceReference.created_at, SourceReference.id)))
    return {"items": [{
        "id": source.id, "execution_id": source.execution_id, "title": source.title, "url": source.url,
        "publisher": source.publisher, "domain": source.domain, "retrieved_at": source.retrieved_at,
        "published_at": source.published_at, "excerpt": source.excerpt,
    } for source in sources]}


@router.get("/api/investigations/{investigation_id}/report")
def investigation_report(investigation_id: str, version: int | None = Query(default=None, ge=1),
                         db: Session = Depends(get_db), user: Profile = Depends(current_user)):
    row = _get(db, investigation_id, user)
    query = select(InvestigationReport).where(InvestigationReport.investigation_id == row.id)
    if version is not None:
        query = query.where(InvestigationReport.version == version)
    else:
        query = query.order_by(InvestigationReport.version.desc())
    report = db.scalar(query.limit(1))
    if report is None:
        raise HTTPException(404, detail={"code": "report_not_found", "message": "No report version has been generated for this investigation."})
    versions = list(db.scalars(select(InvestigationReport.version).where(InvestigationReport.investigation_id == row.id).order_by(InvestigationReport.version.desc())))
    anchor = db.scalar(select(InvestigationReportAnchor).where(InvestigationReportAnchor.report_id == report.id))
    return {"id": report.id, "investigation_id": report.investigation_id, "version": report.version,
            "status": report.status, "summary": report.summary, "limitations": json.loads(report.limitations_json),
            "content": json.loads(report.content_json), "created_by": report.created_by,
            "created_at": report.created_at.isoformat(), "available_versions": versions,
            "commitment": {"sha256": report_sha256(report), "canonicalization": CANONICALIZATION},
            "anchor": ({"id": anchor.id, "status": anchor.status, "sha256": anchor.sha256_hash,
                        "canonicalization": anchor.canonicalization, "approved_by": anchor.approved_by,
                        "approved_at": anchor.approved_at.isoformat(), "approval_reason": anchor.approval_reason,
                        "chain_id": anchor.chain_id, "contract_address": anchor.contract_address,
                        "transaction_hash": anchor.tx_hash, "block_number": anchor.block_number,
                        "anchored_at": anchor.anchored_at.isoformat() if anchor.anchored_at else None,
                        "failure_summary": anchor.failure_summary} if anchor else None)}


@router.post("/api/findings/{finding_id}/review")
def review_finding(finding_id: str, body: FindingReviewRequest, db: Session = Depends(get_db), user: Profile = Depends(current_user)):
    if user.role not in {"reviewer", "admin"}:
        raise HTTPException(403, detail={"code": "reviewer_role_required", "message": "Only an authorized reviewer can decide findings."})
    finding = db.get(AgentFinding, finding_id)
    if finding is None:
        raise HTTPException(404, detail={"code": "finding_not_found", "message": "Finding was not found."})
    investigation = _get(db, finding.investigation_id, user)
    if investigation.status not in {"completed", "completed_with_limitations", "partial", "failed"}:
        raise HTTPException(409, detail={"code": "investigation_not_reviewable", "message": "Findings can be reviewed after investigation execution has stopped."})
    review = FindingReview(id=_id("FRV"), finding_id=finding.id, reviewer_id=user.id,
                           decision=body.decision, reason=body.reason, created_at=utcnow())
    db.add(review)
    finding.review_decision = body.decision
    finding.review_reason = body.reason
    finding.reviewer_id = user.id
    finding.reviewed_at = utcnow()
    db.flush()
    _event(db, investigation, "finding_reviewed", {"finding_id": finding.id, "review_id": review.id, "decision": body.decision})
    report = create_report_snapshot(db, investigation, created_by=user.id)
    _event(db, investigation, "investigation_report_generated", {"report_id": report.id, "version": report.version, "reason": "human_review"})
    db.commit()
    return {"finding_id": finding.id, "review_id": review.id, "decision": review.decision,
            "reason": review.reason, "reviewer_id": review.reviewer_id,
            "reviewed_at": review.created_at.isoformat(), "report_version": report.version}
