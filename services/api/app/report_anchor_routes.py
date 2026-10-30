from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from web3 import Web3

from .db import get_db
from .investigation_routes import _event, _get
from .models import Investigation, InvestigationReport, InvestigationReportAnchor, Profile, utcnow
from .security import current_user
from .services.report_anchoring import CANONICALIZATION, new_anchor_reference, report_sha256
from .services.x1_chain import EXPECTED_X1_CHAIN_ID, X1ChainClient, X1ConfigurationError, X1NetworkError, X1Settings

router = APIRouter()


class AnchorApprovalRequest(BaseModel):
    reason: str = Field(min_length=5, max_length=2000)


class AnchorSubmissionRequest(BaseModel):
    confirm_submission: bool


def _require_reviewer(user: Profile) -> None:
    if user.role not in {"reviewer", "admin"}:
        raise HTTPException(403, detail={"code": "reviewer_role_required", "message": "Only an authorized reviewer can approve or submit a report anchor."})


def _anchor_dict(row: InvestigationReportAnchor) -> dict:
    return {
        "id": row.id, "status": row.status, "sha256": row.sha256_hash,
        "canonicalization": row.canonicalization, "approval_reason": row.approval_reason,
        "approved_by": row.approved_by, "approved_at": row.approved_at.isoformat(),
        "chain_id": row.chain_id, "contract_address": row.contract_address,
        "transaction_hash": row.tx_hash, "block_number": row.block_number,
        "anchored_at": row.anchored_at.isoformat() if row.anchored_at else None,
        "failure_summary": row.failure_summary,
    }


@router.post("/api/investigations/{investigation_id}/reports/{report_id}/anchor/approve")
def approve_report_anchor(investigation_id: str, report_id: str, body: AnchorApprovalRequest,
                          db: Session = Depends(get_db), user: Profile = Depends(current_user)):
    _require_reviewer(user)
    investigation = _get(db, investigation_id, user)
    report = db.scalar(select(InvestigationReport).where(
        InvestigationReport.id == report_id, InvestigationReport.investigation_id == investigation.id,
    ))
    if report is None:
        raise HTTPException(404, detail={"code": "report_not_found", "message": "Report version was not found."})
    existing = db.scalar(select(InvestigationReportAnchor).where(InvestigationReportAnchor.report_id == report.id))
    digest = report_sha256(report)
    if existing:
        if existing.sha256_hash == digest and existing.approved_by == user.id:
            return _anchor_dict(existing)
        raise HTTPException(409, detail={"code": "report_anchor_already_approved", "message": "This immutable report version already has an anchor approval."})
    public_id, anchor_key = new_anchor_reference()
    anchor = InvestigationReportAnchor(
        id=public_id, report_id=report.id, anchor_key=anchor_key, sha256_hash=digest,
        canonicalization=CANONICALIZATION, status="approved", approval_reason=body.reason.strip(),
        approved_by=user.id, approved_at=utcnow(), created_at=utcnow(),
    )
    db.add(anchor)
    db.flush()
    _event(db, investigation, "report_anchor_approved", {
        "report_id": report.id, "version": report.version, "anchor_id": anchor.id,
        "sha256": digest, "canonicalization": CANONICALIZATION,
    })
    db.commit()
    return _anchor_dict(anchor)


@router.post("/api/report-anchors/{anchor_id}/submit")
def submit_report_anchor(anchor_id: str, body: AnchorSubmissionRequest,
                         db: Session = Depends(get_db), user: Profile = Depends(current_user)):
    _require_reviewer(user)
    if body.confirm_submission is not True:
        raise HTTPException(422, detail={"code": "explicit_confirmation_required", "message": "Confirm the X1 submission after reviewing the digest and destination."})
    anchor = db.get(InvestigationReportAnchor, anchor_id)
    if anchor is None:
        raise HTTPException(404, detail={"code": "report_anchor_not_found", "message": "Report anchor was not found."})
    report = db.get(InvestigationReport, anchor.report_id)
    investigation = db.get(Investigation, report.investigation_id) if report else None
    if report is None or investigation is None:
        raise HTTPException(404, detail={"code": "report_not_found", "message": "Report version was not found."})
    _get(db, investigation.id, user)
    if anchor.status == "confirmed":
        return _anchor_dict(anchor)
    if anchor.status in {"submitting", "submitted", "submission_unknown"}:
        raise HTTPException(409, detail={"code": "anchor_reconciliation_required", "message": "Check the existing transaction status before considering another submission."})

    client = X1ChainClient()
    try:
        contract = client.report_anchor_contract()
        client.role_account("reviewer")
        key_bytes = Web3.to_bytes(hexstr=anchor.anchor_key)
        if contract.functions.isAnchored(key_bytes).call():
            existing = contract.functions.getReportAnchor(key_bytes).call()
            if bytes(existing[1]).hex() != anchor.sha256_hash.lower() or int(existing[2]) != report.version:
                raise HTTPException(409, detail={"code": "on_chain_commitment_conflict", "message": "The anchor key exists on X1 with a different digest or version."})
            anchor.status = "confirmed"
            anchor.chain_id = EXPECTED_X1_CHAIN_ID
            anchor.contract_address = contract.address
            anchor.anchored_at = datetime.fromtimestamp(int(existing[4]), tz=timezone.utc)
            anchor.failure_summary = None
            _event(db, investigation, "report_anchor_reconciled", {"anchor_id": anchor.id, "version": report.version})
            db.commit()
            return _anchor_dict(anchor)
    except X1ConfigurationError as exc:
        raise HTTPException(409, detail={"code": "x1_report_anchor_not_ready", "message": str(exc)}) from exc
    except X1NetworkError as exc:
        raise HTTPException(503, detail={"code": "x1_unavailable", "message": "X1 Maculatus is unavailable or does not match the configured network."}) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(502, detail={"code": "x1_report_anchor_read_failed", "message": f"Could not check report-anchor contract state: {type(exc).__name__}."}) from exc

    anchor.status = "submitting"
    anchor.failure_summary = None
    _event(db, investigation, "report_anchor_submission_authorized", {
        "anchor_id": anchor.id, "version": report.version, "sha256": anchor.sha256_hash,
        "chain_id": EXPECTED_X1_CHAIN_ID, "contract_address": contract.address,
    })
    db.commit()
    try:
        function = contract.functions.anchorReport(key_bytes, bytes.fromhex(anchor.sha256_hash), report.version)
        def record_broadcast(tx_hash: str) -> None:
            anchor.tx_hash = tx_hash
            anchor.status = "submitted"
            db.commit()

        receipt = client.send_contract_transaction("reviewer", function, contract=contract, on_broadcast=record_broadcast)
        if receipt.get("status") != "confirmed":
            anchor.status = "failed"
            anchor.failure_summary = "The transaction receipt was not successful."
            anchor.tx_hash = receipt.get("transaction_hash")
            anchor.block_number = receipt.get("block_number")
            anchor.chain_id = EXPECTED_X1_CHAIN_ID
            anchor.contract_address = receipt.get("contract_address")
            db.commit()
            raise HTTPException(502, detail={"code": "x1_transaction_reverted", "message": "X1 did not confirm the report-anchor transaction."})
        record = contract.functions.getReportAnchor(key_bytes).call()
        if not record[0] or bytes(record[1]).hex() != anchor.sha256_hash.lower() or int(record[2]) != report.version:
            anchor.status = "verification_failed"
            anchor.failure_summary = "The confirmed transaction did not match the approved report commitment."
            anchor.tx_hash = receipt.get("transaction_hash")
            anchor.block_number = receipt.get("block_number")
            anchor.chain_id = EXPECTED_X1_CHAIN_ID
            anchor.contract_address = receipt.get("contract_address")
            db.commit()
            raise HTTPException(502, detail={"code": "x1_commitment_mismatch", "message": "The confirmed on-chain record did not match the approved report digest."})
        block = client.w3.eth.get_block(receipt["block_number"])
        anchor.status = "confirmed"
        anchor.chain_id = EXPECTED_X1_CHAIN_ID
        anchor.contract_address = receipt["contract_address"]
        anchor.tx_hash = receipt["transaction_hash"]
        anchor.block_number = receipt["block_number"]
        anchor.anchored_at = datetime.fromtimestamp(int(block.timestamp), tz=timezone.utc)
        _event(db, investigation, "report_anchor_confirmed", {
            "anchor_id": anchor.id, "version": report.version, "sha256": anchor.sha256_hash,
            "chain_id": anchor.chain_id, "contract_address": anchor.contract_address,
            "transaction_hash": anchor.tx_hash, "block_number": anchor.block_number,
        })
        db.commit()
        return _anchor_dict(anchor)
    except HTTPException:
        raise
    except X1ConfigurationError as exc:
        anchor.status = "approved"
        anchor.failure_summary = None
        db.commit()
        raise HTTPException(409, detail={"code": "x1_report_anchor_not_ready", "message": str(exc)}) from exc
    except X1NetworkError as exc:
        if anchor.tx_hash:
            anchor.status = "submission_unknown"
            anchor.failure_summary = "The transaction was broadcast but its confirmation could not be read. Reconcile before retrying."
            db.commit()
            raise HTTPException(502, detail={"code": "x1_submission_unknown", "message": "The X1 transaction may have been broadcast. Reconcile its status before retrying."}) from exc
        anchor.status = "approved"
        anchor.failure_summary = None
        db.commit()
        raise HTTPException(503, detail={"code": "x1_unavailable", "message": "X1 Maculatus is unavailable or does not match the configured network."}) from exc
    except Exception as exc:
        # The send may have reached the network before a timeout. Keep the random key
        # and block a second submission until the chain can be reconciled.
        anchor.status = "submission_unknown"
        anchor.failure_summary = "Submission status is unknown. Verify the anchor key on X1 before retrying."
        db.commit()
        raise HTTPException(502, detail={"code": "x1_submission_unknown", "message": f"The X1 submission could not be confirmed ({type(exc).__name__}); check public verification before retrying."}) from exc


@router.post("/api/report-anchors/{anchor_id}/reconcile")
def reconcile_report_anchor(anchor_id: str, db: Session = Depends(get_db), user: Profile = Depends(current_user)):
    _require_reviewer(user)
    anchor = db.get(InvestigationReportAnchor, anchor_id)
    if anchor is None:
        raise HTTPException(404, detail={"code": "report_anchor_not_found", "message": "Report anchor was not found."})
    report = db.get(InvestigationReport, anchor.report_id)
    investigation = db.get(Investigation, report.investigation_id) if report else None
    if report is None or investigation is None:
        raise HTTPException(404, detail={"code": "report_not_found", "message": "Report version was not found."})
    _get(db, investigation.id, user)
    try:
        client = X1ChainClient()
        contract = client.report_anchor_contract()
        key_bytes = Web3.to_bytes(hexstr=anchor.anchor_key)
        if not contract.functions.isAnchored(key_bytes).call():
            if anchor.tx_hash:
                try:
                    receipt = client.w3.eth.get_transaction_receipt(anchor.tx_hash)
                except Exception:
                    receipt = None
                if receipt is not None and int(receipt.status) == 0:
                    anchor.status = "failed"
                    anchor.failure_summary = "The previously broadcast transaction reverted. A new submission requires a fresh confirmation."
                    db.commit()
            return {**_anchor_dict(anchor), "verified_on_chain": False}
        record = contract.functions.getReportAnchor(key_bytes).call()
        matches = bytes(record[1]).hex() == anchor.sha256_hash.lower() and int(record[2]) == report.version
        if not matches:
            anchor.status = "verification_failed"
            anchor.failure_summary = "The on-chain anchor key contains a different report hash or version."
            db.commit()
            raise HTTPException(409, detail={"code": "on_chain_commitment_conflict", "message": "The on-chain anchor does not match the approved report commitment."})
        anchor.status = "confirmed"
        anchor.chain_id = EXPECTED_X1_CHAIN_ID
        anchor.contract_address = contract.address
        if anchor.tx_hash:
            try:
                receipt = client.w3.eth.get_transaction_receipt(anchor.tx_hash)
                anchor.block_number = int(receipt.blockNumber)
            except Exception:
                pass
        anchor.anchored_at = datetime.fromtimestamp(int(record[4]), tz=timezone.utc)
        anchor.failure_summary = None
        _event(db, investigation, "report_anchor_reconciled", {"anchor_id": anchor.id, "version": report.version})
        db.commit()
        return {**_anchor_dict(anchor), "verified_on_chain": True}
    except HTTPException:
        raise
    except X1ConfigurationError as exc:
        raise HTTPException(409, detail={"code": "x1_report_anchor_not_ready", "message": str(exc)}) from exc
    except Exception as exc:
        raise HTTPException(503, detail={"code": "x1_reconciliation_unavailable", "message": f"Could not read the report-anchor state ({type(exc).__name__})."}) from exc


@router.get("/api/public/report-anchors/{anchor_id}")
def verify_public_report_anchor(anchor_id: str, db: Session = Depends(get_db)):
    anchor = db.get(InvestigationReportAnchor, anchor_id)
    if anchor is None:
        raise HTTPException(404, detail={"code": "report_anchor_not_found", "message": "No public report commitment matches this reference."})
    report = db.get(InvestigationReport, anchor.report_id)
    if report is None:
        raise HTTPException(404, detail={"code": "report_not_found", "message": "Report version was not found."})
    result = {
        "status": anchor.status, "sha256": anchor.sha256_hash,
        "canonicalization": anchor.canonicalization, "report_version": report.version,
        "network": "X1 EcoChain Testnet (Maculatus)", "chain_id": anchor.chain_id,
        "explorer_url": X1Settings.from_env().explorer_url,
        "contract_address": anchor.contract_address, "transaction_hash": anchor.tx_hash,
        "block_number": anchor.block_number,
        "anchored_at": anchor.anchored_at.isoformat() if anchor.anchored_at else None,
        "verified_on_chain": None,
    }
    try:
        contract = X1ChainClient().report_anchor_contract()
        key_bytes = Web3.to_bytes(hexstr=anchor.anchor_key)
        exists = contract.functions.isAnchored(key_bytes).call()
        if exists:
            record = contract.functions.getReportAnchor(key_bytes).call()
            result["verified_on_chain"] = bool(
                record[0] and bytes(record[1]).hex() == anchor.sha256_hash.lower()
                and int(record[2]) == report.version
            )
            if result["verified_on_chain"]:
                result["status"] = "confirmed"
                result["chain_id"] = EXPECTED_X1_CHAIN_ID
                result["contract_address"] = contract.address
                result["anchored_at"] = datetime.fromtimestamp(int(record[4]), tz=timezone.utc).isoformat()
        else:
            result["verified_on_chain"] = False
    except Exception:
        result["verified_on_chain"] = None
    return result
