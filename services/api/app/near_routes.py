from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import config
from .db import get_db
from .investigation_routes import _event, _get
from .models import Investigation, InvestigationReport, NearCommitment, Profile, utcnow
from .security import current_user
from .services.near_chain import (
    NearChainClient, NearChainError, NearConfigurationError, NearNetworkError,
    NearRpcError, NearTransactionMismatch, valid_account_id, valid_transaction_hash,
)
from .services.report_anchoring import CANONICALIZATION, report_sha256, report_sha256_from_document

router = APIRouter()


class PrepareCommitmentRequest(BaseModel):
    report_id: str = Field(min_length=1, max_length=80)
    near_account_id: str = Field(min_length=2, max_length=64)
    reason: str = Field(min_length=5, max_length=2000)

    @field_validator("near_account_id")
    @classmethod
    def validate_near_account_id(cls, value: str) -> str:
        if not valid_account_id(value):
            raise ValueError("Invalid NEAR account ID.")
        return value


class ConfirmCommitmentRequest(BaseModel):
    transaction_hash: str = Field(min_length=43, max_length=44)

    @field_validator("transaction_hash")
    @classmethod
    def validate_transaction_hash(cls, value: str) -> str:
        if not valid_transaction_hash(value):
            raise ValueError("Invalid NEAR transaction hash.")
        return value


class PublicReportVerificationRequest(BaseModel):
    report: dict[str, Any]

    @field_validator("report")
    @classmethod
    def bound_report_size(cls, value: dict[str, Any]) -> dict[str, Any]:
        try:
            serialized = json.dumps(value, ensure_ascii=False, allow_nan=False).encode("utf-8")
        except (TypeError, ValueError) as exc:
            raise ValueError("Report must be valid JSON.") from exc
        if len(serialized) > 2_000_000:
            raise ValueError("Report exceeds the 2 MB verification limit.")
        return value


def _require_reviewer(user: Profile) -> None:
    if user.role not in {"reviewer", "admin"}:
        raise HTTPException(403, detail={"code": "reviewer_role_required", "message": "Only an authorized reviewer can prepare or confirm a NEAR report commitment."})


def _contract_id() -> str:
    contract_id = config.NEAR_REPORT_REGISTRY_CONTRACT_ID
    if not valid_account_id(contract_id):
        raise HTTPException(503, detail={"code": "near_contract_not_configured", "message": "Configure the deployed NEAR testnet report registry before preparing commitments."})
    return contract_id


def _require_commitments_enabled() -> str:
    if not config.NEAR_ENABLED or config.NEAR_NETWORK != "testnet":
        raise HTTPException(503, detail={"code": "near_testnet_disabled", "message": "NEAR report commitments are disabled or not configured for testnet."})
    if not config.NEAR_REPORT_COMMITMENTS_ENABLED:
        raise HTTPException(503, detail={"code": "near_commitments_disabled", "message": "NEAR report commitments are disabled by configuration."})
    return _contract_id()


def _commitment_view(row: NearCommitment) -> dict:
    return {
        "id": row.id, "investigation_id": row.investigation_id, "report_id": row.report_id,
        "report_version": row.report_version, "sha256": row.report_digest,
        "canonicalization": CANONICALIZATION, "near_account_id": row.near_account_id,
        "contract_id": row.contract_id, "transaction_hash": row.transaction_hash,
        "network": row.network, "status": row.status,
        "created_at": row.created_at.isoformat(),
        "confirmed_at": row.confirmed_at.isoformat() if row.confirmed_at else None,
        "failure_summary": row.failure_summary,
        "explorer_url": config.NEAR_EXPLORER_URL,
    }


def _expected(row: NearCommitment) -> dict:
    return {
        "investigation_id": row.investigation_id,
        "report_version": row.report_version,
        "report_digest": row.report_digest,
    }


@router.get("/api/near/config")
def near_config():
    enabled = config.NEAR_ENABLED and config.NEAR_NETWORK == "testnet"
    contract_ready = valid_account_id(config.NEAR_REPORT_REGISTRY_CONTRACT_ID)
    return {
        "enabled": enabled,
        "network": config.NEAR_NETWORK,
        "rpc_url": config.NEAR_RPC_URL,
        "wallet_url": config.NEAR_WALLET_URL,
        "explorer_url": config.NEAR_EXPLORER_URL,
        "contract_id": config.NEAR_REPORT_REGISTRY_CONTRACT_ID or None,
        "report_commitments_enabled": enabled and config.NEAR_REPORT_COMMITMENTS_ENABLED and contract_ready,
        "contract_ready": contract_ready,
    }


@router.post("/api/near/commitments/prepare", status_code=201)
def prepare_near_commitment(body: PrepareCommitmentRequest, db: Session = Depends(get_db), user: Profile = Depends(current_user)):
    _require_reviewer(user)
    contract_id = _require_commitments_enabled()
    report = db.get(InvestigationReport, body.report_id)
    if report is None:
        raise HTTPException(404, detail={"code": "report_not_found", "message": "Report version was not found."})
    investigation = _get(db, report.investigation_id, user)
    digest = report_sha256(report)
    existing = db.scalar(select(NearCommitment).where(
        NearCommitment.investigation_id == investigation.id,
        NearCommitment.report_version == report.version,
    ))
    if existing and existing.status == "confirmed":
        raise HTTPException(409, detail={"code": "near_commitment_already_confirmed", "message": "This report version already has a confirmed NEAR commitment."})
    if existing and existing.status == "pending" and existing.transaction_hash:
        raise HTTPException(409, detail={"code": "near_commitment_reconciliation_required", "message": "A transaction is already recorded for this report version; confirm or reconcile it before preparing another."})
    if existing and existing.status == "pending" and existing.near_account_id != body.near_account_id:
        raise HTTPException(409, detail={"code": "near_commitment_account_conflict", "message": "This report version already has a pending wallet authorization for a different account."})

    now = utcnow()
    if existing:
        row = existing
        row.report_digest = digest
        row.near_account_id = body.near_account_id
        row.contract_id = contract_id
        row.approved_by = user.id
        row.approval_reason = body.reason.strip()
        row.approved_at = now
        row.transaction_hash = None
        row.status = "pending"
        row.failure_summary = None
    else:
        row = NearCommitment(
            id=f"NRC-{uuid.uuid4().hex[:16].upper()}", investigation_id=investigation.id,
            report_id=report.id, report_version=report.version, report_digest=digest,
            near_account_id=body.near_account_id, contract_id=contract_id,
            approved_by=user.id, approval_reason=body.reason.strip(), approved_at=now,
            network="testnet", status="pending", created_at=now,
        )
        db.add(row)
    db.flush()
    _event(db, investigation, "near_report_commitment_prepared", {
        "commitment_id": row.id, "report_id": report.id, "report_version": report.version,
        "sha256": digest, "near_account_id": body.near_account_id, "network": "testnet",
    })
    db.commit()
    result = _commitment_view(row)
    result["transaction"] = {
        "receiver_id": contract_id,
        "method_name": "commit_report",
        "args": {"investigation_id": investigation.id, "report_version": report.version,
                 "report_digest": digest, "metadata_digest": None},
        "gas": "100000000000000",
        "deposit": "0",
    }
    return result


@router.post("/api/near/commitments/{commitment_id}/confirm")
def confirm_near_commitment(commitment_id: str, body: ConfirmCommitmentRequest, response: Response,
                            db: Session = Depends(get_db), user: Profile = Depends(current_user)):
    _require_reviewer(user)
    _require_commitments_enabled()
    row = db.get(NearCommitment, commitment_id)
    if row is None:
        raise HTTPException(404, detail={"code": "near_commitment_not_found", "message": "NEAR commitment was not found."})
    investigation = _get(db, row.investigation_id, user)
    if row.status == "confirmed":
        return _commitment_view(row)
    if row.transaction_hash and row.transaction_hash != body.transaction_hash:
        raise HTTPException(409, detail={"code": "near_transaction_conflict", "message": "A different transaction hash is already associated with this commitment."})
    report = db.get(InvestigationReport, row.report_id)
    if report is None or report_sha256(report) != row.report_digest:
        raise HTTPException(409, detail={"code": "near_report_digest_changed", "message": "The stored report no longer matches the approved commitment digest."})
    row.transaction_hash = body.transaction_hash
    db.commit()
    try:
        state = NearChainClient().verify_report_transaction(
            body.transaction_hash, row.near_account_id, row.contract_id, _expected(row),
        )
    except NearTransactionMismatch as exc:
        # A conclusively mismatched transaction must not permanently lock the
        # pending commitment to the wrong hash. Keep an audit trail and permit
        # the reviewer to submit the correct transaction hash.
        rejected_hash = row.transaction_hash
        row.transaction_hash = None
        row.failure_summary = "A submitted transaction did not match the approved report commitment."
        _event(db, investigation, "near_report_commitment_transaction_rejected", {
            "commitment_id": row.id, "rejected_transaction_hash": rejected_hash,
            "reason": str(exc), "near_account_id": row.near_account_id,
        })
        db.commit()
        raise HTTPException(422, detail={"code": "near_transaction_mismatch", "message": str(exc)}) from exc
    except NearNetworkError as exc:
        raise HTTPException(503, detail={"code": "near_wrong_network", "message": str(exc)}) from exc
    except (NearConfigurationError, NearRpcError) as exc:
        raise HTTPException(503, detail={"code": "near_rpc_unavailable", "message": "NEAR testnet transaction status could not be verified; commitment remains pending."}) from exc
    except NearChainError as exc:
        raise HTTPException(503, detail={"code": "near_confirmation_unavailable", "message": "NEAR confirmation could not be verified; commitment remains pending."}) from exc

    if state == "failed":
        row.status = "failed"
        row.failure_summary = "The NEAR testnet transaction execution failed."
        row.confirmed_at = utcnow()
        _event(db, investigation, "near_report_commitment_failed", {"commitment_id": row.id, "transaction_hash": row.transaction_hash})
    elif state == "confirmed":
        row.status = "confirmed"
        row.failure_summary = None
        row.confirmed_at = utcnow()
        _event(db, investigation, "near_report_commitment_confirmed", {
            "commitment_id": row.id, "report_version": row.report_version,
            "sha256": row.report_digest, "transaction_hash": row.transaction_hash,
            "contract_id": row.contract_id, "network": "testnet",
        })
    else:
        response.status_code = 202
    db.commit()
    return _commitment_view(row)


@router.get("/api/near/commitments")
def list_user_near_commitments(offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200),
                               db: Session = Depends(get_db), user: Profile = Depends(current_user)):
    query = select(NearCommitment).join(Investigation, Investigation.id == NearCommitment.investigation_id)
    if user.role not in {"reviewer", "admin"}:
        query = query.where(Investigation.created_by == user.id)
    rows = db.scalars(query.order_by(NearCommitment.created_at.desc()).offset(offset).limit(limit))
    return {"items": [_commitment_view(row) for row in rows], "offset": offset, "limit": limit}


@router.get("/api/near/commitments/{investigation_id}")
def list_near_commitments(investigation_id: str, db: Session = Depends(get_db), user: Profile = Depends(current_user)):
    investigation = _get(db, investigation_id, user)
    rows = db.scalars(select(NearCommitment).where(
        NearCommitment.investigation_id == investigation.id,
    ).order_by(NearCommitment.report_version.desc()))
    return {"items": [_commitment_view(row) for row in rows]}


def _on_chain_matches(row: NearCommitment, record: dict | None) -> bool:
    return bool(record and all((
        record.get("investigationId") == row.investigation_id,
        record.get("reportVersion") == row.report_version,
        record.get("reportDigest", "").lower() == row.report_digest.lower(),
        record.get("submitter") == row.near_account_id,
        record.get("metadataDigest") is None,
    )))


@router.get("/api/public/near/commitments/{commitment_id}")
def public_near_commitment(commitment_id: str, db: Session = Depends(get_db)):
    row = db.get(NearCommitment, commitment_id)
    if row is None:
        raise HTTPException(404, detail={"code": "near_commitment_not_found", "message": "No public NEAR commitment matches this reference."})
    result = _commitment_view(row)
    result["verified_on_chain"] = None
    if config.NEAR_NETWORK == "testnet" and valid_account_id(row.contract_id):
        try:
            record = NearChainClient().get_report_commitment(row.contract_id, row.investigation_id, row.report_version)
            result["verified_on_chain"] = _on_chain_matches(row, record)
        except NearChainError:
            pass
    result.pop("report_id", None)
    result.pop("failure_summary", None)
    return result


@router.post("/api/public/near/commitments/{commitment_id}/verify")
def verify_public_near_report(commitment_id: str, body: PublicReportVerificationRequest, db: Session = Depends(get_db)):
    row = db.get(NearCommitment, commitment_id)
    if row is None:
        raise HTTPException(404, detail={"code": "near_commitment_not_found", "message": "No public NEAR commitment matches this reference."})
    try:
        supplied_digest = report_sha256_from_document(body.report)
    except (TypeError, ValueError) as exc:
        raise HTTPException(422, detail={"code": "invalid_report_document", "message": str(exc)}) from exc
    on_chain = None
    try:
        on_chain = NearChainClient().get_report_commitment(row.contract_id, row.investigation_id, row.report_version)
    except NearChainError:
        pass
    on_chain_matches = _on_chain_matches(row, on_chain)
    verified = row.status == "confirmed" and supplied_digest == row.report_digest and on_chain_matches
    return {
        "result": "VERIFIED" if verified else "MISMATCH" if on_chain is not None else "UNAVAILABLE",
        "report_digest": supplied_digest,
        "committed_digest": row.report_digest,
        "digest_matches": supplied_digest == row.report_digest,
        "verified_on_chain": on_chain_matches if on_chain is not None else None,
        "report_version": row.report_version,
        "near_account_id": row.near_account_id,
        "contract_id": row.contract_id,
        "transaction_hash": row.transaction_hash,
        "network": row.network,
        "explorer_url": config.NEAR_EXPLORER_URL,
        "canonicalization": CANONICALIZATION,
        "integrity_note": "A matching digest shows that the supplied report representation matches the committed bytes; it does not establish the truth of environmental claims.",
    }