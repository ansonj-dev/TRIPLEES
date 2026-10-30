from __future__ import annotations

from pathlib import Path

from .config import (
    OBJECT_STORAGE_BUCKET,
    OBJECT_STORAGE_ENDPOINT_URL,
    OBJECT_STORAGE_PREFIX,
    OBJECT_STORAGE_REGION,
    UPLOAD_DIR,
)


class EvidenceStorageError(RuntimeError):
    """Raised when evidence bytes cannot be persisted or retrieved."""


def _safe_key(storage_key: str) -> str:
    path = Path(storage_key)
    if path.is_absolute() or len(path.parts) != 1 or storage_key in {"", ".", ".."}:
        raise EvidenceStorageError("Evidence storage key is invalid.")
    return path.name


def _s3_key(storage_key: str) -> str:
    name = _safe_key(storage_key)
    return f"{OBJECT_STORAGE_PREFIX}/{name}" if OBJECT_STORAGE_PREFIX else name


def _s3_client():
    try:
        import boto3
    except ImportError as exc:
        raise EvidenceStorageError("S3 storage is configured but boto3 is not installed.") from exc
    return boto3.client("s3", endpoint_url=OBJECT_STORAGE_ENDPOINT_URL, region_name=OBJECT_STORAGE_REGION)


def put_evidence(storage_key: str, data: bytes, content_type: str) -> None:
    name = _safe_key(storage_key)
    try:
        if OBJECT_STORAGE_BUCKET:
            _s3_client().put_object(Bucket=OBJECT_STORAGE_BUCKET, Key=_s3_key(name), Body=data, ContentType=content_type)
        else:
            (UPLOAD_DIR / name).write_bytes(data)
    except Exception as exc:
        raise EvidenceStorageError("Evidence storage write failed.") from exc


def get_evidence(storage_key: str) -> bytes:
    name = _safe_key(storage_key)
    try:
        if OBJECT_STORAGE_BUCKET:
            response = _s3_client().get_object(Bucket=OBJECT_STORAGE_BUCKET, Key=_s3_key(name))
            return response["Body"].read()
        path = (UPLOAD_DIR / name).resolve()
        root = UPLOAD_DIR.resolve()
        if root not in path.parents or not path.is_file():
            raise FileNotFoundError(name)
        return path.read_bytes()
    except Exception as exc:
        raise EvidenceStorageError("Evidence object is unavailable.") from exc


def delete_evidence(storage_key: str) -> None:
    name = _safe_key(storage_key)
    try:
        if OBJECT_STORAGE_BUCKET:
            _s3_client().delete_object(Bucket=OBJECT_STORAGE_BUCKET, Key=_s3_key(name))
        else:
            (UPLOAD_DIR / name).unlink(missing_ok=True)
    except Exception as exc:
        raise EvidenceStorageError("Evidence storage delete failed.") from exc


def delete_all_local_evidence_except(keep: set[str]) -> None:
    """Demo-only cleanup; never lists or deletes objects from a shared bucket."""
    if OBJECT_STORAGE_BUCKET:
        return
    for path in UPLOAD_DIR.iterdir():
        if path.is_file() and path.name not in keep:
            path.unlink(missing_ok=True)


def check_storage() -> bool:
    if OBJECT_STORAGE_BUCKET:
        # A low-cost permission check; no object is written or altered.
        _s3_client().head_bucket(Bucket=OBJECT_STORAGE_BUCKET)
        return True
    return UPLOAD_DIR.is_dir() and UPLOAD_DIR.exists()
