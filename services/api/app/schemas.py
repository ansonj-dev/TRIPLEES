from __future__ import annotations

from datetime import date
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class APIModel(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")


class DemoAuthResponse(APIModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict
    demo: bool = True


class SignupRequest(APIModel):
    display_name: str = Field(min_length=2, max_length=160)
    email: str = Field(min_length=5, max_length=320)
    password: str = Field(min_length=10, max_length=200)
    organization: str | None = Field(default=None, max_length=200)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        value = value.strip().lower()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
            raise ValueError("Enter a valid email address")
        return value


class LoginRequest(APIModel):
    email: str = Field(min_length=5, max_length=320)
    password: str = Field(min_length=1, max_length=200)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class ProjectCreate(APIModel):
    name: str = Field(min_length=2, max_length=200)
    project_type: str = Field(min_length=2, max_length=80)
    country: str = Field(min_length=2, max_length=120)
    region: str = Field(default="Not specified", max_length=160)
    methodology_id: str | None = Field(default=None, max_length=160)
    vintage_start: date | None = None
    vintage_end: date | None = None
    registry_name: str | None = Field(default=None, max_length=160)
    registry_project_ref: str | None = Field(default=None, max_length=160)
    baseline_summary: str | None = Field(default=None, max_length=10000)
    boundary_geojson: dict | None = None

    @model_validator(mode="after")
    def dates_in_order(self):
        if self.vintage_start and self.vintage_end and self.vintage_end < self.vintage_start:
            raise ValueError("vintage_end must be on or after vintage_start")
        return self


class BatchCreate(APIModel):
    batch_code: str | None = Field(default=None, min_length=3, max_length=100)
    registry_name: str | None = Field(default=None, max_length=160)
    registry_batch_ref: str | None = Field(default=None, max_length=160)
    serial_start: str = Field(min_length=2, max_length=160)
    serial_end: str | None = Field(default=None, max_length=160)
    quantity_kg_co2e: int = Field(gt=0, le=2_000_000_000)
    vintage_start: date | None = None
    vintage_end: date | None = None
    methodology_id: str | None = Field(default=None, max_length=160)

    @model_validator(mode="after")
    def dates_in_order(self):
        if self.vintage_start and self.vintage_end and self.vintage_end < self.vintage_start:
            raise ValueError("vintage_end must be on or after vintage_start")
        return self


class ReasonRequest(APIModel):
    reason: str = Field(min_length=5, max_length=2000)


class BatchReviewRequest(ReasonRequest):
    decision: Literal["approved", "rejected", "needs_more_evidence"]


class TransferRequest(ReasonRequest):
    quantity_kg_co2e: int = Field(gt=0, le=2_000_000_000)
    recipient_ref: str = Field(min_length=2, max_length=200)


class RetireRequest(ReasonRequest):
    quantity_kg_co2e: int = Field(gt=0, le=2_000_000_000)
    beneficiary: str = Field(min_length=2, max_length=200)
    purpose: str = Field(min_length=3, max_length=500)


class ObservationCreate(APIModel):
    source_name: str = Field(min_length=2, max_length=160)
    signal_type: Literal["forest_loss", "fire", "land_use_change", "sensor_anomaly", "data_gap", "other"]
    severity: Literal["low", "medium", "high", "critical"]
    affected_area_percent: int | None = Field(default=None, ge=0, le=100)
    observed_at: str = Field(min_length=10, max_length=40)
    evidence_file_id: str | None = None
    evidence_hash: str | None = Field(default=None, pattern=r"^[a-fA-F0-9]{64}$")
    description: str = Field(min_length=5, max_length=4000)
    is_synthetic: bool = True


class AlertReviewRequest(ReasonRequest):
    decision: Literal["alert_confirmed", "alert_rejected", "needs_more_evidence"]


class ClaimCreate(APIModel):
    credit_batch_id: str
    claimant_entity: str = Field(min_length=2, max_length=200)
    claim_purpose: str = Field(min_length=3, max_length=240)
    target_framework: str | None = Field(default=None, max_length=120)
    external_claim_ref: str | None = Field(default=None, max_length=160)
    authorization_status: Literal["unknown", "authorized", "not_required", "pending", "rejected"] = "unknown"
    corresponding_adjustment_status: Literal["unknown", "yes", "no", "pending", "not_applicable"] = "unknown"
    evidence_hash: str | None = Field(default=None, pattern=r"^[a-fA-F0-9]{64}$")


class ProfileUpdate(APIModel):
    display_name: str = Field(min_length=2, max_length=160)
    email: str | None = Field(default=None, max_length=320)
    location: str | None = Field(default=None, max_length=160)
    organization: str | None = Field(default=None, max_length=200)


class EvidenceAssessmentRequest(APIModel):
    evidence_id: str = Field(min_length=2, max_length=80)


class InvestigationCreate(APIModel):
    project_id: str = Field(min_length=2, max_length=80)
    title: str = Field(min_length=2, max_length=240)
    scope: str = Field(min_length=5, max_length=8000)
    evidence_ids: list[str] = Field(default_factory=list, max_length=100)
    external_ai_authorized: bool = False
    public_research_authorized: bool = False
    ai_token_budget: int = Field(default=6000, ge=0, le=100000)


class InvestigationRetry(APIModel):
    reason: str | None = Field(default=None, max_length=1000)


class FindingReviewRequest(APIModel):
    decision: Literal["confirmed", "rejected", "needs_more_evidence"]
    reason: str = Field(min_length=5, max_length=2000)

