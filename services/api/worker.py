from __future__ import annotations

import argparse
from dataclasses import replace
import json
import logging
import signal
import socket
import time
import uuid
from datetime import timedelta

from sqlalchemy import func, select, update

from .app import config
from .app.db import SessionLocal
from .app.models import (
    AgentAuditEvent, AgentExecution, AgentFinding, DocumentExtraction, EvidenceFile, ExtractedClaim,
    Investigation, ModelUsage, MonitoringObservation, Project, RegistryRecord, SourceReference, utcnow,
)
from .app.services.agents import (
    AgentContext, EvidenceAnalyst, IndependentReviewAgent, IntegrityAnalyst,
    MonitoringAnalyst, ResearchInvestigator,
)
from .app.services.ai.structured_output import FindingOutput
from .app.services.ai.usage_tracker import usage_cost
from .app.services.investigation_reports import create_report_snapshot, persist_agent_output

logger = logging.getLogger("triplees.worker")
MAX_JOB_ATTEMPTS = 5
AGENT_ATTEMPTS = 2
LEASE_SECONDS = 180
AGENT_SUITE = (EvidenceAnalyst, IntegrityAnalyst, ResearchInvestigator, MonitoringAnalyst, IndependentReviewAgent)


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12].upper()}"


def _audit(db, investigation_id: str, event_type: str, details: dict | None = None, execution_id: str | None = None) -> None:
    db.add(AgentAuditEvent(id=_id("AUD"), investigation_id=investigation_id, execution_id=execution_id,
                           event_type=event_type, details_json=json.dumps(details or {}, separators=(",", ":"))))


def recover_expired_leases(db) -> int:
    now = utcnow()
    stale = list(db.scalars(select(Investigation).where(Investigation.status == "running", Investigation.lease_expires_at < now)))
    for row in stale:
        executions = list(db.scalars(select(AgentExecution).where(AgentExecution.investigation_id == row.id, AgentExecution.status == "running")))
        for execution in executions:
            execution.status = "failed"
            execution.error_code = "worker_lease_expired"
            execution.completed_at = now
            _audit(db, row.id, "agent_execution_interrupted", {"error_code": "worker_lease_expired"}, execution.id)
        row.worker_id = None
        row.lease_expires_at = None
        if row.cancel_requested:
            row.status = "cancelled"
            row.completed_at = now
        elif row.attempt_count >= MAX_JOB_ATTEMPTS:
            row.status = "failed"
            row.failure_summary = "Worker lease expired too many times."
            row.completed_at = now
        else:
            row.status = "retry_wait"
            row.next_attempt_at = now + timedelta(seconds=min(60, 2 ** row.attempt_count))
        _audit(db, row.id, "worker_lease_expired", {"attempt_count": row.attempt_count, "next_status": row.status})
    if stale:
        db.commit()
    return len(stale)


def claim_next_job(worker_id: str) -> str | None:
    with SessionLocal() as db:
        recover_expired_leases(db)
        now = utcnow()
        candidate = db.scalar(select(Investigation.id).where(
            Investigation.status.in_(["queued", "retry_wait"]),
            (Investigation.next_attempt_at.is_(None) | (Investigation.next_attempt_at <= now)),
        ).order_by(Investigation.created_at).limit(1))
        if candidate is None:
            return None
        result = db.execute(update(Investigation).where(
            Investigation.id == candidate,
            Investigation.status.in_(["queued", "retry_wait"]),
        ).values(status="running", attempt_count=Investigation.attempt_count + 1,
                 worker_id=worker_id, lease_expires_at=now + timedelta(seconds=LEASE_SECONDS),
                 started_at=func.coalesce(Investigation.started_at, now),
                 updated_at=now))
        if result.rowcount != 1:
            db.rollback()
            return None
        _audit(db, candidate, "worker_job_claimed", {"worker_id": worker_id})
        db.commit()
        return candidate


def _load_context(db, row: Investigation) -> AgentContext:
    project = db.get(Project, row.project_id)
    selected = json.loads(row.evidence_ids_json or "[]")
    evidence_query = select(EvidenceFile).where(EvidenceFile.project_id == row.project_id)
    if selected:
        evidence_query = evidence_query.where(EvidenceFile.id.in_(selected))
    files = list(db.scalars(evidence_query.order_by(EvidenceFile.created_at)))
    context_evidence = []
    for item in files[:40]:
        extraction = db.scalar(select(DocumentExtraction).where(DocumentExtraction.evidence_file_id == item.id))
        claims = list(db.scalars(select(ExtractedClaim).where(ExtractedClaim.evidence_file_id == item.id).order_by(ExtractedClaim.created_at).limit(80)))
        context_evidence.append({
            "id": item.id, "filename": item.filename, "sha256": item.sha256,
            "extraction_status": extraction.status if extraction else "not_extracted",
            "extraction_warning": extraction.warning if extraction else "Text extraction has not been run.",
            "text_excerpt": (extraction.extracted_text or "")[:800] if extraction else "",
            "claims": [{"text": claim.text, "source_location": claim.source_location, "method": claim.extraction_method} for claim in claims],
        })
    project_refs = {str(value).strip().casefold() for value in (project.id, project.name, project.registry_project_ref) if value}
    imported_records = list(db.scalars(select(RegistryRecord).where(RegistryRecord.imported_by == row.created_by).order_by(RegistryRecord.created_at.desc()).limit(5_000)))
    records = [item for item in imported_records if any(
        str(value).strip().casefold() in project_refs
        for value in (item.external_project_id, item.external_project_name)
        if value
    )][:30]
    observations = list(db.scalars(select(MonitoringObservation).where(MonitoringObservation.project_id == row.project_id).order_by(MonitoringObservation.created_at.desc()).limit(30)))
    prior_sources = list(db.scalars(select(SourceReference).where(SourceReference.investigation_id == row.id).order_by(SourceReference.created_at, SourceReference.id)))
    return AgentContext(
        project={"id": project.id, "name": project.name, "project_type": project.project_type, "country": project.country,
                 "region": project.region, "methodology_id": project.methodology_id, "registry_project_ref": project.registry_project_ref,
                 "scope": row.scope},
        evidence=context_evidence,
        registry_records=[{"id": x.id, "source_name": x.source_name, "external_project_id": x.external_project_id,
                           "external_serial": x.external_serial, "quantity_kg_co2e": x.quantity_kg_co2e,
                           "vintage_start": x.vintage_start, "vintage_end": x.vintage_end, "status": x.status, "is_demo": x.is_demo} for x in records],
        observations=[{"id": x.id, "signal_type": x.signal_type, "severity": x.severity, "observed_at": x.observed_at,
                       "affected_area_percent": x.affected_area_percent, "evidence_file_id": x.evidence_file_id,
                       "is_synthetic": x.is_synthetic, "review_state": x.review_state} for x in observations],
        source_references=[{"id": source.id, "title": source.title, "url": source.url, "publisher": source.publisher,
                            "domain": source.domain, "retrieved_at": source.retrieved_at, "published_at": source.published_at}
                           for source in prior_sources],
        external_ai_authorized=row.external_ai_authorized,
        public_research_authorized=row.public_research_authorized,
    )


def _record_usage(db, result, investigation_id: str, execution_id: str, user_id: str) -> None:
    usage = result.usage
    if usage is None:
        return
    db.add(ModelUsage(
        id=_id("USG"), requested_by=user_id, investigation_id=investigation_id, execution_id=execution_id,
        provider=usage.provider, model_name=usage.model,
        input_tokens=usage.input_tokens, output_tokens=usage.output_tokens, latency_ms=usage.latency_ms,
        cost_usd=usage_cost(usage.input_tokens, usage.output_tokens), succeeded=result.status == "completed",
        error_code=result.error_code,
    ))
    investigation = db.get(Investigation, investigation_id)
    if investigation:
        investigation.ai_tokens_used += usage.input_tokens + usage.output_tokens


def daily_ai_token_limit_reached(db, user_id: str, estimated_tokens: int) -> tuple[bool, int]:
    if config.AI_DAILY_TOKEN_LIMIT <= 0:
        return False, 0
    used = db.scalar(select(func.coalesce(func.sum(ModelUsage.input_tokens + ModelUsage.output_tokens), 0)).where(
        ModelUsage.requested_by == user_id,
        ModelUsage.created_at >= utcnow() - timedelta(days=1),
    )) or 0
    return used + estimated_tokens > config.AI_DAILY_TOKEN_LIMIT, int(used)


def _review_drafts(db, investigation_id: str) -> list[FindingOutput]:
    drafts: list[FindingOutput] = []
    outputs = db.scalars(select(AgentExecution.output_json).where(
        AgentExecution.investigation_id == investigation_id,
        AgentExecution.status.in_(["completed", "completed_with_limitations"]),
        AgentExecution.output_json.is_not(None),
        AgentExecution.agent_key != "independent_review_agent",
    ))
    for encoded in outputs:
        try:
            data = json.loads(encoded)
            drafts.extend(FindingOutput.model_validate(item) for item in data.get("findings", []))
        except Exception:
            continue
    return drafts[:200]


def process_job(investigation_id: str, worker_id: str, agent_suite=AGENT_SUITE) -> None:
    with SessionLocal() as db:
        row = db.get(Investigation, investigation_id)
        if row is None or row.status != "running" or row.worker_id != worker_id:
            return
        context = _load_context(db, row)
        completed_keys = set(db.scalars(select(AgentExecution.agent_key).where(
            AgentExecution.investigation_id == row.id,
            AgentExecution.status.in_(["completed", "completed_with_limitations"]),
        )))
        _audit(db, row.id, "investigation_started", {"attempt_count": row.attempt_count, "evidence_count": len(context.evidence)})
        db.commit()

    failed_any = False
    limited_any = False
    for agent_cls in agent_suite:
        with SessionLocal() as db:
            row = db.get(Investigation, investigation_id)
            if row is None:
                return
            if row.cancel_requested or row.status == "cancel_requested":
                row.status = "cancelled"
                row.completed_at = utcnow()
                row.lease_expires_at = None
                row.worker_id = None
                _audit(db, row.id, "investigation_cancelled")
                db.commit()
                return
            if agent_cls.agent_key in completed_keys:
                continue
            existing_attempts = db.scalar(select(AgentExecution).where(AgentExecution.investigation_id == row.id, AgentExecution.agent_key == agent_cls.agent_key).order_by(AgentExecution.attempt_number.desc()).limit(1))
            next_attempt = existing_attempts.attempt_number + 1 if existing_attempts else 1
            agent = agent_cls()
            execution = AgentExecution(id=_id("EXE"), investigation_id=row.id, agent_key=agent.agent_key,
                                       attempt_number=next_attempt, status="running", task_summary=agent.task_summary,
                                       worker_id=worker_id, started_at=utcnow())
            db.add(execution)
            db.flush()
            _audit(db, row.id, "agent_execution_started", {"agent_key": agent.agent_key, "attempt_number": next_attempt}, execution.id)
            db.commit()
            current_context = context
            first_execution_id = execution.id
        attempt = 0
        while attempt < AGENT_ATTEMPTS:
            attempt += 1
            if attempt > 1:
                with SessionLocal() as db:
                    row = db.get(Investigation, investigation_id)
                    execution = AgentExecution(id=_id("EXE"), investigation_id=row.id, agent_key=agent.agent_key,
                                               attempt_number=next_attempt + attempt - 1, status="running", task_summary=agent.task_summary,
                                               worker_id=worker_id, started_at=utcnow())
                    db.add(execution)
                    db.flush()
                    _audit(db, row.id, "agent_execution_retry_started", {"agent_key": agent.agent_key, "attempt_number": execution.attempt_number}, execution.id)
                    db.commit()
                    execution_id = execution.id
            else:
                execution_id = first_execution_id
            try:
                with SessionLocal() as budget_db:
                    current_investigation = budget_db.get(Investigation, investigation_id)
                    remaining = max(0, current_investigation.ai_token_budget - current_investigation.ai_tokens_used)
                    estimated_request = len(current_context.model_payload()) // 2 + 512 + config.AI_MAX_COMPLETION_TOKENS
                    daily_limit_hit, daily_usage = daily_ai_token_limit_reached(
                        budget_db, current_investigation.created_by, estimated_request,
                    )
                    if current_context.external_ai_authorized and (estimated_request > remaining or daily_limit_hit):
                        current_context = replace(current_context, external_ai_authorized=False, ai_budget_exhausted=True)
                        if daily_limit_hit:
                            logger.info(json.dumps({"event": "ai_daily_token_limit_reached", "investigation_id": investigation_id,
                                                    "requested_by": current_investigation.created_by, "used_tokens": int(daily_usage),
                                                    "limit_tokens": config.AI_DAILY_TOKEN_LIMIT}, separators=(",", ":")))
                    review_drafts = _review_drafts(budget_db, investigation_id) if agent.agent_key == "independent_review_agent" else []
                if agent.agent_key == "independent_review_agent":
                    result = agent.run(current_context, review_drafts)
                else:
                    result = agent.run(current_context)
            except Exception:
                result = None
            with SessionLocal() as db:
                row = db.get(Investigation, investigation_id)
                execution = db.get(AgentExecution, execution_id)
                if result is None:
                    status, error_code, output = "failed", "agent_execution_error", None
                else:
                    status, error_code = result.status, result.error_code
                    output = result.output.model_dump(mode="json") if result.output else None
                    if result.output is not None:
                        result_output, finding_count, source_count = persist_agent_output(db, row, execution, result.output, current_context)
                        output = result_output.model_dump(mode="json")
                        _audit(db, row.id, "agent_output_persisted", {"finding_count": finding_count, "source_count": source_count}, execution.id)
                    _record_usage(db, result, row.id, execution.id, row.created_by)
                execution.status = status
                execution.error_code = error_code
                execution.output_json = json.dumps(output, ensure_ascii=False, separators=(",", ":")) if output is not None else None
                execution.completed_at = utcnow()
                row.lease_expires_at = utcnow() + timedelta(seconds=LEASE_SECONDS)
                row.updated_at = utcnow()
                _audit(db, row.id, "agent_execution_completed" if status != "failed" else "agent_execution_failed",
                       {"agent_key": agent.agent_key, "status": status, "error_code": error_code}, execution.id)
                db.commit()
            if result is not None and result.output is not None and result.output.sources:
                with SessionLocal() as source_db:
                    source_rows = list(source_db.scalars(select(SourceReference).where(
                        SourceReference.investigation_id == investigation_id,
                    ).order_by(SourceReference.created_at, SourceReference.id)))
                    context = replace(context, source_references=[{
                        "id": source.id, "title": source.title, "url": source.url, "publisher": source.publisher,
                        "domain": source.domain, "retrieved_at": source.retrieved_at,
                    } for source in source_rows])
            if status != "failed":
                limited_any |= status == "completed_with_limitations"
                break
            if attempt >= AGENT_ATTEMPTS:
                failed_any = True

    with SessionLocal() as db:
        row = db.get(Investigation, investigation_id)
        if row is None:
            return
        if row.cancel_requested or row.status == "cancel_requested":
            row.status = "cancelled"
            _audit(db, row.id, "investigation_cancelled")
        elif failed_any:
            row.status = "partial"
            row.failure_summary = "One or more agents failed after retry; completed agent records were retained."
        elif limited_any:
            row.status = "completed_with_limitations"
        else:
            row.status = "completed"
        row.completed_at = utcnow()
        row.lease_expires_at = None
        row.worker_id = None
        row.updated_at = utcnow()
        report = create_report_snapshot(db, row)
        _audit(db, row.id, "investigation_report_generated", {"report_id": report.id, "version": report.version, "finding_count": db.query(AgentFinding).filter_by(investigation_id=row.id).count()})
        _audit(db, row.id, "investigation_finished", {"status": row.status})
        db.commit()


def run_worker(*, once: bool = False, poll_seconds: float = 2.0, agent_suite=AGENT_SUITE) -> None:
    if config.APP_ENV == "production" and not config.PRODUCTION_AUTH_SUPPORTED:
        raise RuntimeError("Production worker startup is blocked until production authentication is integrated.")
    worker_id = f"{socket.gethostname()}-{uuid.uuid4().hex[:8]}"
    logger.info(json.dumps({"event": "worker_started", "worker_id": worker_id, "once": once,
                            "poll_seconds": max(0.1, poll_seconds)}, separators=(",", ":")))
    stopping = False

    def stop(_signum, _frame):
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    while not stopping:
        job_id = claim_next_job(worker_id)
        if job_id:
            logger.info(json.dumps({"event": "worker_job_started", "worker_id": worker_id, "investigation_id": job_id}, separators=(",", ":")))
            try:
                process_job(job_id, worker_id, agent_suite)
            except Exception:
                logger.exception(json.dumps({"event": "worker_job_crashed", "worker_id": worker_id, "investigation_id": job_id}))
            logger.info(json.dumps({"event": "worker_job_finished", "worker_id": worker_id, "investigation_id": job_id}, separators=(",", ":")))
        elif once:
            return
        else:
            time.sleep(max(0.1, poll_seconds))
    logger.info(json.dumps({"event": "worker_stopped", "worker_id": worker_id}, separators=(",", ":")))


def main() -> None:
    parser = argparse.ArgumentParser(description="TRIPLEES persistent investigation worker")
    parser.add_argument("--once", action="store_true", help="process at most one job and exit")
    parser.add_argument("--poll-seconds", type=float, default=2.0)
    args = parser.parse_args()
    logging.basicConfig(level=getattr(logging, getattr(config, "LOG_LEVEL", "INFO").upper(), logging.INFO))
    run_worker(once=args.once, poll_seconds=args.poll_seconds)


if __name__ == "__main__":
    main()
