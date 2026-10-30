from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, CheckConstraint, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Profile(Base):
    __tablename__ = "profiles"
    __table_args__ = (UniqueConstraint("email", name="uq_profiles_email"),)
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(160), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False, default="developer")
    email: Mapped[str | None] = mapped_column(String(320))
    location: Mapped[str | None] = mapped_column(String(160))
    organization: Mapped[str | None] = mapped_column(String(200))
    password_salt: Mapped[str | None] = mapped_column(String(64))
    password_hash: Mapped[str | None] = mapped_column(String(128))
    is_demo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class Project(Base):
    __tablename__ = "projects"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    project_type: Mapped[str] = mapped_column(String(80), nullable=False)
    country: Mapped[str] = mapped_column(String(120), nullable=False)
    region: Mapped[str] = mapped_column(String(160), nullable=False, default="Not specified")
    boundary_geojson: Mapped[str | None] = mapped_column(Text)
    methodology_id: Mapped[str | None] = mapped_column(String(160))
    vintage_start: Mapped[str | None] = mapped_column(String(10))
    vintage_end: Mapped[str | None] = mapped_column(String(10))
    registry_name: Mapped[str | None] = mapped_column(String(160))
    registry_project_ref: Mapped[str | None] = mapped_column(String(160))
    baseline_summary: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="Draft")
    chain_project_id: Mapped[str | None] = mapped_column(String(80))
    chain_id: Mapped[int | None] = mapped_column(Integer)
    contract_address: Mapped[str | None] = mapped_column(String(80))
    tx_hash: Mapped[str | None] = mapped_column(String(80))
    is_demo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_by: Mapped[str] = mapped_column(ForeignKey("profiles.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class EvidenceFile(Base):
    __tablename__ = "evidence_files"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    credit_batch_id: Mapped[str | None] = mapped_column(ForeignKey("credit_batches.id"))
    filename: Mapped[str] = mapped_column(String(240), nullable=False)
    content_type: Mapped[str] = mapped_column(String(120), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_key: Mapped[str] = mapped_column(String(240), nullable=False, unique=True)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    evidence_type: Mapped[str] = mapped_column(String(40), nullable=False)
    source_name: Mapped[str | None] = mapped_column(String(160))
    observed_at: Mapped[str | None] = mapped_column(String(40))
    uploaded_by: Mapped[str] = mapped_column(ForeignKey("profiles.id"), nullable=False)
    review_state: Mapped[str] = mapped_column(String(40), nullable=False, default="Not reviewed")
    anchor_chain_id: Mapped[int | None] = mapped_column(Integer)
    anchor_contract_address: Mapped[str | None] = mapped_column(String(80))
    anchor_tx_hash: Mapped[str | None] = mapped_column(String(80))
    anchor_block_number: Mapped[int | None] = mapped_column(Integer)
    is_demo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class CreditBatch(Base):
    __tablename__ = "credit_batches"
    __table_args__ = (
        UniqueConstraint("serial_start", name="uq_credit_serial_start"),
        CheckConstraint("quantity_kg_co2e > 0", name="ck_batch_quantity_positive"),
        CheckConstraint("available_balance_kg >= 0", name="ck_batch_balance_nonnegative"),
        CheckConstraint("retired_balance_kg >= 0", name="ck_batch_retired_nonnegative"),
    )
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    batch_code: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    registry_name: Mapped[str | None] = mapped_column(String(160))
    registry_batch_ref: Mapped[str | None] = mapped_column(String(160))
    serial_start: Mapped[str] = mapped_column(String(160), nullable=False)
    serial_end: Mapped[str | None] = mapped_column(String(160))
    quantity_kg_co2e: Mapped[int] = mapped_column(Integer, nullable=False)
    available_balance_kg: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    retired_balance_kg: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    vintage_start: Mapped[str | None] = mapped_column(String(10))
    vintage_end: Mapped[str | None] = mapped_column(String(10))
    methodology_id: Mapped[str | None] = mapped_column(String(160))
    evidence_hash: Mapped[str | None] = mapped_column(String(64))
    state: Mapped[str] = mapped_column(String(40), nullable=False, default="Draft")
    score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    score_components: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    score_missing_flags: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    score_calculated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_demo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    chain_id: Mapped[int | None] = mapped_column(Integer)
    contract_address: Mapped[str | None] = mapped_column(String(80))
    tx_hash: Mapped[str | None] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class CreditEvent(Base):
    __tablename__ = "credit_events"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    credit_batch_id: Mapped[str | None] = mapped_column(ForeignKey("credit_batches.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    from_state: Mapped[str | None] = mapped_column(String(40))
    to_state: Mapped[str | None] = mapped_column(String(40))
    actor_id: Mapped[str] = mapped_column(ForeignKey("profiles.id"), nullable=False)
    quantity_kg_co2e: Mapped[int | None] = mapped_column(Integer)
    evidence_hash: Mapped[str | None] = mapped_column(String(64))
    reason: Mapped[str | None] = mapped_column(Text)
    chain_id: Mapped[int | None] = mapped_column(Integer)
    tx_hash: Mapped[str | None] = mapped_column(String(80))
    block_number: Mapped[int | None] = mapped_column(Integer)
    is_demo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class RegistryRecord(Base):
    __tablename__ = "registry_records"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    source_name: Mapped[str] = mapped_column(String(160), nullable=False)
    external_project_id: Mapped[str] = mapped_column(String(160), nullable=False)
    external_project_name: Mapped[str] = mapped_column(String(200), nullable=False)
    external_serial: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    vintage_start: Mapped[str | None] = mapped_column(String(10))
    vintage_end: Mapped[str | None] = mapped_column(String(10))
    methodology_id: Mapped[str | None] = mapped_column(String(160))
    country: Mapped[str | None] = mapped_column(String(120))
    region: Mapped[str | None] = mapped_column(String(160))
    quantity_kg_co2e: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="unknown")
    source_timestamp: Mapped[str | None] = mapped_column(String(40))
    raw_record_hash: Mapped[str | None] = mapped_column(String(64))
    is_demo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    imported_by: Mapped[str] = mapped_column(ForeignKey("profiles.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class MonitoringObservation(Base):
    __tablename__ = "monitoring_observations"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    source_name: Mapped[str] = mapped_column(String(160), nullable=False)
    signal_type: Mapped[str] = mapped_column(String(80), nullable=False)
    severity: Mapped[str] = mapped_column(String(24), nullable=False)
    affected_area_percent: Mapped[int | None] = mapped_column(Integer)
    observed_at: Mapped[str] = mapped_column(String(40), nullable=False)
    evidence_file_id: Mapped[str | None] = mapped_column(ForeignKey("evidence_files.id"))
    evidence_hash: Mapped[str | None] = mapped_column(String(64))
    is_synthetic: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    raw_payload_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    review_state: Mapped[str] = mapped_column(String(40), nullable=False, default="Needs human review")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class Alert(Base):
    __tablename__ = "alerts"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    observation_id: Mapped[str | None] = mapped_column(ForeignKey("monitoring_observations.id"))
    alert_type: Mapped[str] = mapped_column(String(80), nullable=False)
    severity: Mapped[str] = mapped_column(String(24), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    state: Mapped[str] = mapped_column(String(40), nullable=False, default="Open")
    assigned_reviewer: Mapped[str | None] = mapped_column(ForeignKey("profiles.id"))
    decision: Mapped[str | None] = mapped_column(String(80))
    decision_reason: Mapped[str | None] = mapped_column(Text)
    is_demo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Assessment(Base):
    __tablename__ = "assessments"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    credit_batch_id: Mapped[str | None] = mapped_column(ForeignKey("credit_batches.id"))
    evidence_file_id: Mapped[str | None] = mapped_column(ForeignKey("evidence_files.id"))
    assessment_type: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    result_json: Mapped[str] = mapped_column(Text, nullable=False)
    model_name: Mapped[str | None] = mapped_column(String(120))
    is_demo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class Review(Base):
    __tablename__ = "reviews"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    assessment_id: Mapped[str | None] = mapped_column(ForeignKey("assessments.id"))
    alert_id: Mapped[str | None] = mapped_column(ForeignKey("alerts.id"))
    credit_batch_id: Mapped[str | None] = mapped_column(ForeignKey("credit_batches.id"))
    finding: Mapped[str | None] = mapped_column(Text)
    reviewer_id: Mapped[str] = mapped_column(ForeignKey("profiles.id"), nullable=False)
    decision: Mapped[str] = mapped_column(String(40), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Claim(Base):
    __tablename__ = "claims"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    credit_batch_id: Mapped[str] = mapped_column(ForeignKey("credit_batches.id"), nullable=False, index=True)
    claimant_entity: Mapped[str] = mapped_column(String(200), nullable=False)
    claim_purpose: Mapped[str] = mapped_column(String(240), nullable=False)
    target_framework: Mapped[str | None] = mapped_column(String(120))
    claim_status: Mapped[str] = mapped_column(String(40), nullable=False, default="draft")
    external_claim_ref: Mapped[str | None] = mapped_column(String(160))
    authorization_status: Mapped[str] = mapped_column(String(40), nullable=False, default="unknown")
    corresponding_adjustment_status: Mapped[str] = mapped_column(String(40), nullable=False, default="unknown")
    evidence_hash: Mapped[str | None] = mapped_column(String(64))
    is_demo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_by: Mapped[str] = mapped_column(ForeignKey("profiles.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class IntegrityScore(Base):
    __tablename__ = "integrity_scores"
    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    credit_batch_id: Mapped[str] = mapped_column(ForeignKey("credit_batches.id"), nullable=False, index=True)
    score_total: Mapped[int] = mapped_column(Integer, nullable=False)
    evidence_quality_score: Mapped[int] = mapped_column(Integer, nullable=False)
    verification_score: Mapped[int] = mapped_column(Integer, nullable=False)
    registry_consistency_score: Mapped[int] = mapped_column(Integer, nullable=False)
    reversal_resilience_score: Mapped[int] = mapped_column(Integer, nullable=False)
    authorization_score: Mapped[int] = mapped_column(Integer, nullable=False)
    missing_data_flags: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    explanation_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class ModelUsage(Base):
    __tablename__ = "model_usage"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    requested_by: Mapped[str | None] = mapped_column(ForeignKey("profiles.id"), index=True)
    investigation_id: Mapped[str | None] = mapped_column(ForeignKey("investigations.id", ondelete="SET NULL"), index=True)
    execution_id: Mapped[str | None] = mapped_column(ForeignKey("agent_executions.id", ondelete="SET NULL"), index=True)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    model_name: Mapped[str] = mapped_column(String(160), nullable=False)
    input_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cost_usd: Mapped[float | None] = mapped_column(Float)
    succeeded: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    error_code: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class DocumentExtraction(Base):
    __tablename__ = "document_extractions"
    __table_args__ = (UniqueConstraint("evidence_file_id", name="uq_extraction_evidence_file"),)
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    evidence_file_id: Mapped[str] = mapped_column(ForeignKey("evidence_files.id", ondelete="CASCADE"), nullable=False, index=True)
    content_sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="processing", index=True)
    extracted_text: Mapped[str | None] = mapped_column(Text)
    character_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    page_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    warning: Mapped[str | None] = mapped_column(Text)
    reused_from_id: Mapped[str | None] = mapped_column(ForeignKey("document_extractions.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    __table_args__ = (UniqueConstraint("extraction_id", "chunk_index", name="uq_extraction_chunk_index"),)
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    extraction_id: Mapped[str] = mapped_column(ForeignKey("document_extractions.id", ondelete="CASCADE"), nullable=False, index=True)
    evidence_file_id: Mapped[str] = mapped_column(ForeignKey("evidence_files.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    source_location: Mapped[str] = mapped_column(String(160), nullable=False)
    start_offset: Mapped[int] = mapped_column(Integer, nullable=False)
    end_offset: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class ExtractedClaim(Base):
    __tablename__ = "extracted_claims"
    __table_args__ = (UniqueConstraint("extraction_id", "claim_sha256", name="uq_extraction_claim_hash"),)
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    extraction_id: Mapped[str] = mapped_column(ForeignKey("document_extractions.id", ondelete="CASCADE"), nullable=False, index=True)
    evidence_file_id: Mapped[str] = mapped_column(ForeignKey("evidence_files.id", ondelete="CASCADE"), nullable=False, index=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    source_location: Mapped[str] = mapped_column(String(160), nullable=False)
    claim_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    extraction_method: Mapped[str] = mapped_column(String(48), nullable=False, default="heuristic_candidate")
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.25)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="candidate")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class ClaimEvidenceLink(Base):
    __tablename__ = "claim_evidence_links"
    __table_args__ = (UniqueConstraint("claim_id", "evidence_file_id", name="uq_claim_evidence_link"),)
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    claim_id: Mapped[str] = mapped_column(ForeignKey("extracted_claims.id", ondelete="CASCADE"), nullable=False, index=True)
    evidence_file_id: Mapped[str] = mapped_column(ForeignKey("evidence_files.id", ondelete="CASCADE"), nullable=False, index=True)
    relationship: Mapped[str] = mapped_column(String(24), nullable=False, default="extracted_from")
    source_location: Mapped[str] = mapped_column(String(160), nullable=False)
    evidence_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class Investigation(Base):
    __tablename__ = "investigations"
    __table_args__ = (UniqueConstraint("created_by", "request_key", name="uq_investigation_idempotency_key"),)
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by: Mapped[str] = mapped_column(ForeignKey("profiles.id"), nullable=False, index=True)
    request_key: Mapped[str | None] = mapped_column(String(100))
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    scope: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_ids_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft", index=True)
    external_ai_authorized: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    public_research_authorized: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    ai_token_budget: Mapped[int] = mapped_column(Integer, nullable=False, default=6000)
    ai_tokens_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cancel_requested: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    failure_summary: Mapped[str | None] = mapped_column(Text)
    next_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    worker_id: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class AgentExecution(Base):
    __tablename__ = "agent_executions"
    __table_args__ = (
        UniqueConstraint("investigation_id", "agent_key", "attempt_number", name="uq_investigation_agent_attempt"),
    )
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    investigation_id: Mapped[str] = mapped_column(ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_key: Mapped[str] = mapped_column(String(64), nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued", index=True)
    task_summary: Mapped[str] = mapped_column(Text, nullable=False)
    output_json: Mapped[str | None] = mapped_column(Text)
    error_code: Mapped[str | None] = mapped_column(String(64))
    worker_id: Mapped[str | None] = mapped_column(String(100))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class AgentAuditEvent(Base):
    __tablename__ = "agent_audit_events"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    investigation_id: Mapped[str] = mapped_column(ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False, index=True)
    execution_id: Mapped[str | None] = mapped_column(ForeignKey("agent_executions.id", ondelete="SET NULL"), index=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    details_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class AgentFinding(Base):
    __tablename__ = "agent_findings"
    __table_args__ = (UniqueConstraint("execution_id", "finding_index", name="uq_execution_finding_index"),)
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    investigation_id: Mapped[str] = mapped_column(ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False, index=True)
    execution_id: Mapped[str] = mapped_column(ForeignKey("agent_executions.id", ondelete="CASCADE"), nullable=False, index=True)
    finding_index: Mapped[int] = mapped_column(Integer, nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    claim: Mapped[str | None] = mapped_column(Text)
    observed_value: Mapped[str | None] = mapped_column(Text)
    evidence_ids_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    source_ids_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    basis: Mapped[str] = mapped_column(String(24), nullable=False)
    recommendation: Mapped[str | None] = mapped_column(Text)
    review_decision: Mapped[str | None] = mapped_column(String(32), index=True)
    review_reason: Mapped[str | None] = mapped_column(Text)
    reviewer_id: Mapped[str | None] = mapped_column(ForeignKey("profiles.id"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class SourceReference(Base):
    __tablename__ = "source_references"
    __table_args__ = (UniqueConstraint("investigation_id", "url", name="uq_investigation_source_url"),)
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    investigation_id: Mapped[str] = mapped_column(ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False, index=True)
    execution_id: Mapped[str | None] = mapped_column(ForeignKey("agent_executions.id", ondelete="SET NULL"), index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    url: Mapped[str] = mapped_column(String(2000), nullable=False)
    publisher: Mapped[str | None] = mapped_column(String(200))
    domain: Mapped[str | None] = mapped_column(String(255))
    retrieved_at: Mapped[str | None] = mapped_column(String(40))
    published_at: Mapped[str | None] = mapped_column(String(40))
    excerpt: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class FindingReview(Base):
    __tablename__ = "finding_reviews"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    finding_id: Mapped[str] = mapped_column(ForeignKey("agent_findings.id", ondelete="CASCADE"), nullable=False, index=True)
    reviewer_id: Mapped[str] = mapped_column(ForeignKey("profiles.id"), nullable=False, index=True)
    decision: Mapped[str] = mapped_column(String(32), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class InvestigationReport(Base):
    __tablename__ = "investigation_reports"
    __table_args__ = (UniqueConstraint("investigation_id", "version", name="uq_investigation_report_version"),)
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    investigation_id: Mapped[str] = mapped_column(ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    content_json: Mapped[str] = mapped_column(Text, nullable=False)
    limitations_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    created_by: Mapped[str | None] = mapped_column(ForeignKey("profiles.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)


class InvestigationReportAnchor(Base):
    __tablename__ = "investigation_report_anchors"
    __table_args__ = (
        UniqueConstraint("report_id", name="uq_report_anchor_report_id"),
        UniqueConstraint("anchor_key", name="uq_report_anchor_anchor_key"),
    )
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    report_id: Mapped[str] = mapped_column(ForeignKey("investigation_reports.id", ondelete="CASCADE"), nullable=False, index=True)
    anchor_key: Mapped[str] = mapped_column(String(66), nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    canonicalization: Mapped[str] = mapped_column(String(48), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="approved")
    approval_reason: Mapped[str] = mapped_column(Text, nullable=False)
    approved_by: Mapped[str] = mapped_column(ForeignKey("profiles.id"), nullable=False)
    approved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    chain_id: Mapped[int | None] = mapped_column(Integer)
    contract_address: Mapped[str | None] = mapped_column(String(80))
    tx_hash: Mapped[str | None] = mapped_column(String(80))
    block_number: Mapped[int | None] = mapped_column(Integer)
    anchored_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failure_summary: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
