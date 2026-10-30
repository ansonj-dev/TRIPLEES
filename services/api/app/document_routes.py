from __future__ import annotations

import hashlib
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import get_db
from .models import ClaimEvidenceLink, DocumentChunk, DocumentExtraction, EvidenceFile, ExtractedClaim, Profile, Project, utcnow
from .security import current_user
from .services.documents import DocumentProcessingError, ExtractionResult, extract_document
from .storage import EvidenceStorageError, get_evidence

router = APIRouter()
SUPPORTED_EXTRACTION_SUFFIXES = {".pdf", ".csv", ".json", ".txt"}
COMPLETE_STATES = {"complete", "complete_with_limitations"}


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12].upper()}"


def _get_evidence(db: Session, evidence_id: str, user: Profile) -> EvidenceFile:
    record = db.get(EvidenceFile, evidence_id)
    if record is None:
        raise HTTPException(404, detail={"code": "evidence_not_found", "message": "Evidence record was not found."})
    _owned_project(db, record.project_id, user)
    return record


def _owned_project(db: Session, project_id: str, user: Profile) -> Project:
    project = db.get(Project, project_id)
    if project is None or (project.created_by != user.id and user.role not in {"reviewer", "admin"}):
        raise HTTPException(404, detail={"code": "project_not_found", "message": "Project was not found."})
    return project


def _summary(record: EvidenceFile, extraction: DocumentExtraction, db: Session, *, reused: bool = False) -> dict:
    return {
        "id": extraction.id,
        "evidence_file_id": record.id,
        "filename": record.filename,
        "evidence_sha256": record.sha256,
        "content_sha256": extraction.content_sha256,
        "status": extraction.status,
        "character_count": extraction.character_count,
        "page_count": extraction.page_count,
        "chunk_count": db.query(DocumentChunk).filter(DocumentChunk.extraction_id == extraction.id).count(),
        "candidate_claim_count": db.query(ExtractedClaim).filter(ExtractedClaim.extraction_id == extraction.id).count(),
        "warning": extraction.warning,
        "reused_from_id": extraction.reused_from_id,
        "reused": reused or bool(extraction.reused_from_id),
        "created_at": extraction.created_at.isoformat(),
        "completed_at": extraction.completed_at.isoformat() if extraction.completed_at else None,
    }


def _copy_cached_result(db: Session, source: DocumentExtraction, target: DocumentExtraction, evidence: EvidenceFile) -> None:
    target.status = source.status
    target.extracted_text = source.extracted_text
    target.character_count = source.character_count
    target.page_count = source.page_count
    target.warning = source.warning
    target.reused_from_id = source.id
    target.completed_at = utcnow()
    db.flush()
    for row in db.scalars(select(DocumentChunk).where(DocumentChunk.extraction_id == source.id).order_by(DocumentChunk.chunk_index)):
        db.add(DocumentChunk(
            id=_id("CHK"), extraction_id=target.id, evidence_file_id=evidence.id,
            chunk_index=row.chunk_index, source_location=row.source_location,
            start_offset=row.start_offset, end_offset=row.end_offset,
            content=row.content, content_sha256=row.content_sha256,
        ))
    for claim in db.scalars(select(ExtractedClaim).where(ExtractedClaim.extraction_id == source.id).order_by(ExtractedClaim.created_at)):
        copied = ExtractedClaim(
            id=_id("CLM"), extraction_id=target.id, evidence_file_id=evidence.id,
            text=claim.text, source_location=claim.source_location,
            claim_sha256=claim.claim_sha256, extraction_method=claim.extraction_method,
            confidence=claim.confidence, status=claim.status,
        )
        db.add(copied)
        db.flush()
        db.add(ClaimEvidenceLink(
            id=_id("LNK"), claim_id=copied.id, evidence_file_id=evidence.id,
            relationship="extracted_from", source_location=claim.source_location,
            evidence_sha256=evidence.sha256,
        ))


def _persist_result(db: Session, evidence: EvidenceFile, extraction: DocumentExtraction, result: ExtractionResult) -> None:
    extraction.status = "complete_with_limitations" if result.warning else "complete"
    extraction.extracted_text = result.text
    extraction.character_count = len(result.text)
    extraction.page_count = result.page_count
    extraction.warning = result.warning
    extraction.completed_at = utcnow()
    db.flush()
    for index, chunk in enumerate(result.chunks):
        db.add(DocumentChunk(
            id=_id("CHK"), extraction_id=extraction.id, evidence_file_id=evidence.id,
            chunk_index=index, source_location=chunk.location,
            start_offset=chunk.start, end_offset=chunk.end, content=chunk.text,
            content_sha256=hashlib.sha256(chunk.text.encode("utf-8")).hexdigest(),
        ))
    for claim in result.claims:
        row = ExtractedClaim(
            id=_id("CLM"), extraction_id=extraction.id, evidence_file_id=evidence.id,
            text=claim.text, source_location=claim.location,
            claim_sha256=claim.sha256, extraction_method="heuristic_candidate",
            confidence=0.25, status="candidate",
        )
        db.add(row)
        db.flush()
        db.add(ClaimEvidenceLink(
            id=_id("LNK"), claim_id=row.id, evidence_file_id=evidence.id,
            relationship="extracted_from", source_location=claim.location,
            evidence_sha256=evidence.sha256,
        ))


@router.post("/api/evidence/{evidence_id}/extract")
def extract_evidence(evidence_id: str, db: Session = Depends(get_db), user: Profile = Depends(current_user)):
    evidence = _get_evidence(db, evidence_id, user)
    suffix = Path(evidence.filename).suffix.lower()
    if suffix not in SUPPORTED_EXTRACTION_SUFFIXES:
        raise HTTPException(415, detail={"code": "extraction_type_unsupported", "message": "Extraction supports PDF, CSV, JSON, and plain text files."})
    try:
        data = get_evidence(evidence.storage_key)
    except EvidenceStorageError as exc:
        raise HTTPException(404, detail={"code": "file_unavailable", "message": "The original evidence file is unavailable."}) from exc
    digest = hashlib.sha256(data).hexdigest()
    if digest != evidence.sha256:
        raise HTTPException(409, detail={"code": "evidence_hash_mismatch", "message": "Stored evidence bytes do not match the recorded SHA-256 digest."})

    extraction = db.scalar(select(DocumentExtraction).where(DocumentExtraction.evidence_file_id == evidence.id))
    if extraction and extraction.content_sha256 == digest and extraction.status in COMPLETE_STATES:
        return _summary(evidence, extraction, db)
    if extraction:
        db.query(DocumentChunk).filter(DocumentChunk.extraction_id == extraction.id).delete(synchronize_session=False)
        db.query(ExtractedClaim).filter(ExtractedClaim.extraction_id == extraction.id).delete(synchronize_session=False)
        extraction.status = "processing"
        extraction.content_sha256 = digest
        extraction.warning = None
        extraction.reused_from_id = None
    else:
        extraction = DocumentExtraction(
            id=_id("EXT"), evidence_file_id=evidence.id, content_sha256=digest,
            status="processing", character_count=0, page_count=0,
        )
        db.add(extraction)
        db.flush()

    cached = db.scalar(select(DocumentExtraction).where(
        DocumentExtraction.content_sha256 == digest,
        DocumentExtraction.evidence_file_id != evidence.id,
        DocumentExtraction.evidence_file_id.in_(select(EvidenceFile.id).where(EvidenceFile.project_id == evidence.project_id)),
        DocumentExtraction.status.in_(COMPLETE_STATES),
    ).order_by(DocumentExtraction.created_at))
    if cached:
        _copy_cached_result(db, cached, extraction, evidence)
        db.commit()
        return _summary(evidence, extraction, db, reused=True)

    try:
        result = extract_document(evidence.filename, data)
    except DocumentProcessingError as exc:
        extraction.status = "failed"
        extraction.warning = str(exc)
        extraction.completed_at = utcnow()
        db.commit()
        status_code = 415 if exc.code == "document_type_unsupported" else (503 if exc.code == "pdf_support_unavailable" else 422)
        raise HTTPException(status_code, detail={"code": exc.code, "message": str(exc)}) from exc
    except Exception as exc:
        extraction.status = "failed"
        extraction.warning = "Document extraction failed. Check that the file is valid and retry."
        extraction.completed_at = utcnow()
        db.commit()
        raise HTTPException(422, detail={"code": "document_extraction_failed", "message": extraction.warning}) from exc
    _persist_result(db, evidence, extraction, result)
    db.commit()
    return _summary(evidence, extraction, db)


@router.get("/api/evidence/{evidence_id}/extraction")
def get_evidence_extraction(evidence_id: str, db: Session = Depends(get_db), user: Profile = Depends(current_user)):
    evidence = _get_evidence(db, evidence_id, user)
    extraction = db.scalar(select(DocumentExtraction).where(DocumentExtraction.evidence_file_id == evidence.id))
    if extraction is None:
        raise HTTPException(404, detail={"code": "extraction_not_found", "message": "This evidence file has not been extracted."})
    summary = _summary(evidence, extraction, db)
    summary["text_preview"] = (extraction.extracted_text or "")[:4_000]
    summary["claims"] = [{
        "id": claim.id, "text": claim.text, "source_location": claim.source_location,
        "method": claim.extraction_method, "confidence": claim.confidence,
        "status": claim.status, "evidence_sha256": evidence.sha256,
    } for claim in db.scalars(select(ExtractedClaim).where(ExtractedClaim.extraction_id == extraction.id).order_by(ExtractedClaim.created_at))]
    return summary


@router.get("/api/evidence/{evidence_id}/extraction/chunks")
def list_extraction_chunks(
    evidence_id: str,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    user: Profile = Depends(current_user),
):
    evidence = _get_evidence(db, evidence_id, user)
    extraction = db.scalar(select(DocumentExtraction).where(DocumentExtraction.evidence_file_id == evidence.id))
    if extraction is None:
        raise HTTPException(404, detail={"code": "extraction_not_found", "message": "This evidence file has not been extracted."})
    rows = list(db.scalars(select(DocumentChunk).where(DocumentChunk.extraction_id == extraction.id).order_by(DocumentChunk.chunk_index).offset(offset).limit(limit)))
    return {"items": [{
        "id": row.id, "index": row.chunk_index, "source_location": row.source_location,
        "start_offset": row.start_offset, "end_offset": row.end_offset,
        "content": row.content, "sha256": row.content_sha256,
    } for row in rows], "offset": offset, "limit": limit}


@router.get("/api/evidence/search")
def search_extracted_evidence(
    project_id: str,
    q: str = Query(min_length=2, max_length=200),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: Profile = Depends(current_user),
):
    project = _owned_project(db, project_id, user)
    needle = f"%{q.strip()}%"
    statement = (select(DocumentChunk, EvidenceFile)
        .join(EvidenceFile, EvidenceFile.id == DocumentChunk.evidence_file_id)
        .join(DocumentExtraction, DocumentExtraction.id == DocumentChunk.extraction_id)
        .where(EvidenceFile.project_id == project.id, DocumentExtraction.status.in_(COMPLETE_STATES), DocumentChunk.content.ilike(needle))
        .order_by(DocumentChunk.created_at.desc()).offset(offset).limit(limit))
    rows = db.execute(statement).all()
    return {"query": q.strip(), "offset": offset, "limit": limit, "items": [{
        "evidence_id": evidence.id, "filename": evidence.filename,
        "evidence_sha256": evidence.sha256, "chunk_id": chunk.id,
        "source_location": chunk.source_location, "excerpt": chunk.content,
    } for chunk, evidence in rows]}
