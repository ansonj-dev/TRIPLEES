from __future__ import annotations

import csv
import hashlib
import io
import json
import logging
import time
import re
import secrets
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from alembic import command
from alembic.config import Config
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from web3 import Web3

from .config import ALLOWED_ORIGINS, APP_ENV, AUTO_MIGRATE, LOG_LEVEL, MAX_UPLOAD_BYTES, OBJECT_STORAGE_BUCKET, PRODUCTION_AUTH_SUPPORTED, ROOT_DIR, SEED_DEMO_DATA, TOKEN_TTL_SECONDS
from .db import SessionLocal, get_db
from .models import (
    Alert, Assessment, Claim, CreditBatch, CreditEvent, EvidenceFile, IntegrityScore,
    MonitoringObservation, Profile, Project, RegistryRecord, Review, utcnow,
)
from .schemas import (
    AlertReviewRequest, BatchCreate, BatchReviewRequest, ClaimCreate, DemoAuthResponse, EvidenceAssessmentRequest,
    LoginRequest, ObservationCreate, ProjectCreate, ProfileUpdate, ReasonRequest,
    RetireRequest, SignupRequest, TransferRequest,
)
from .security import current_user, issue_token, require_role
from .ai_routes import router as ai_router
from .document_routes import router as document_router
from .investigation_routes import router as investigation_router
from .report_anchor_routes import router as report_anchor_router
from .services.integrity import WEIGHTS, update_score
from .services.x1_chain import X1ChainClient, X1ConfigurationError, X1NetworkError
from .storage import EvidenceStorageError, check_storage, delete_all_local_evidence_except, get_evidence, put_evidence

if APP_ENV == "production" and not PRODUCTION_AUTH_SUPPORTED:
    raise RuntimeError("Production API startup is blocked: prototype authentication has no integrated production identity provider or session controls.")

logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.INFO), format="%(message)s")
logger = logging.getLogger("triplees.api")
@asynccontextmanager
async def lifespan(_app: FastAPI):
    if AUTO_MIGRATE:
        alembic_config = Config(str(ROOT_DIR / "alembic.ini"))
        command.upgrade(alembic_config, "head")
    else:
        with SessionLocal() as db:
            db.execute(select(1))
    if SEED_DEMO_DATA:
        seed_database()
    yield


app = FastAPI(
    title="TRIPLEES API",
    description="Local prototype API for traceable climate project records, evidence review, registry imports, and credit lifecycle history. Demo data is not certified.",
    version="0.1.0",
    lifespan=lifespan,
    openapi_url=None if APP_ENV == "production" else "/api/openapi.json",
    docs_url=None if APP_ENV == "production" else "/api/docs",
    redoc_url=None if APP_ENV == "production" else "/api/redoc",
)


@app.middleware("http")
async def request_observability(request: Request, call_next):
    started = time.perf_counter()
    request_id = request.headers.get("x-request-id", "")
    if not re.fullmatch(r"[A-Za-z0-9._-]{1,80}", request_id):
        request_id = uuid.uuid4().hex
    try:
        response = await call_next(request)
    except Exception:
        logger.exception(json.dumps({"event": "http_request_failed", "request_id": request_id, "method": request.method, "path": request.url.path}))
        raise
    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    logger.info(json.dumps({"event": "http_request", "request_id": request_id, "method": request.method,
                            "path": request.url.path, "status_code": response.status_code, "duration_ms": elapsed_ms}, separators=(",", ":")))
    return response
app.include_router(ai_router)
app.include_router(document_router)
app.include_router(investigation_router)
app.include_router(report_anchor_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    expose_headers=["X-Request-ID"],
)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_request: Request, exc: RequestValidationError):
    issues = [{"field": ".".join(map(str, item["loc"])), "message": item["msg"]} for item in exc.errors()]
    return JSONResponse(status_code=422, content={"error": {"code": "validation_error", "message": "Request fields are invalid.", "issues": issues}})


@app.exception_handler(IntegrityError)
async def integrity_error_handler(_request: Request, _exc: IntegrityError):
    return JSONResponse(status_code=409, content={"error": {"code": "record_conflict", "message": "A unique identifier or related record conflicts with an existing record."}})


def identifier(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12].upper()}"


def iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def json_value(value: str | None, fallback: Any):
    try:
        return json.loads(value) if value else fallback
    except (TypeError, json.JSONDecodeError):
        return fallback


def owned_project(db: Session, project_id: str, user: Profile) -> Project:
    project = db.get(Project, project_id)
    if project is None or (project.created_by != user.id and user.role not in {"reviewer", "admin"}):
        raise HTTPException(404, detail={"code": "project_not_found", "message": "Project was not found."})
    return project


def owned_batch(db: Session, batch_id: str, user: Profile) -> CreditBatch:
    batch = db.get(CreditBatch, batch_id)
    if batch is None:
        raise HTTPException(404, detail={"code": "batch_not_found", "message": "Credit batch was not found."})
    owned_project(db, batch.project_id, user)
    return batch


def append_event(
    db: Session,
    user: Profile,
    project_id: str,
    event_type: str,
    reason: str,
    *,
    batch_id: str | None = None,
    from_state: str | None = None,
    to_state: str | None = None,
    quantity: int | None = None,
    evidence_hash: str | None = None,
    is_demo: bool = True,
) -> CreditEvent:
    row = CreditEvent(
        id=identifier("EVT"), project_id=project_id, credit_batch_id=batch_id,
        event_type=event_type, from_state=from_state, to_state=to_state,
        actor_id=user.id, quantity_kg_co2e=quantity, evidence_hash=evidence_hash,
        reason=reason, is_demo=is_demo,
    )
    db.add(row)
    return row


def project_dict(project: Project) -> dict:
    return {
        "id": project.id, "project_code": project.id, "name": project.name,
        "project_type": project.project_type, "country": project.country, "region": project.region,
        "methodology_id": project.methodology_id, "vintage_start": project.vintage_start,
        "vintage_end": project.vintage_end, "registry_name": project.registry_name,
        "registry_project_ref": project.registry_project_ref, "baseline_summary": project.baseline_summary,
        "status": project.status, "is_demo": project.is_demo,
        "chain_project_id": project.chain_project_id, "chain_id": project.chain_id,
        "contract_address": project.contract_address, "tx_hash": project.tx_hash,
        "created_by": project.created_by, "created_at": iso(project.created_at), "updated_at": iso(project.updated_at),
    }


def evidence_dict(row: EvidenceFile) -> dict:
    return {
        "id": row.id, "project_id": row.project_id, "credit_batch_id": row.credit_batch_id,
        "filename": row.filename, "content_type": row.content_type, "size_bytes": row.size_bytes,
        "sha256": row.sha256, "evidence_type": row.evidence_type, "source_name": row.source_name,
        "observed_at": row.observed_at, "uploaded_by": row.uploaded_by,
        "review_state": row.review_state, "is_demo": row.is_demo, "created_at": iso(row.created_at),
        "anchor_chain_id": row.anchor_chain_id, "anchor_contract_address": row.anchor_contract_address,
        "anchor_tx_hash": row.anchor_tx_hash, "anchor_block_number": row.anchor_block_number,
    }


def batch_dict(row: CreditBatch) -> dict:
    return {
        "id": row.id, "batch_code": row.batch_code, "project_id": row.project_id,
        "registry_name": row.registry_name, "registry_batch_ref": row.registry_batch_ref,
        "serial_start": row.serial_start, "serial_end": row.serial_end,
        "quantity_kg_co2e": row.quantity_kg_co2e, "available_balance_kg": row.available_balance_kg,
        "retired_balance_kg": row.retired_balance_kg,
        "transferred_balance_kg": max(0, row.quantity_kg_co2e - row.available_balance_kg - row.retired_balance_kg),
        "vintage_start": row.vintage_start, "vintage_end": row.vintage_end,
        "methodology_id": row.methodology_id, "evidence_hash": row.evidence_hash,
        "state": row.state, "score": row.score, "score_components": json_value(row.score_components, {}),
        "score_missing_flags": json_value(row.score_missing_flags, []), "score_calculated_at": iso(row.score_calculated_at),
        "is_demo": row.is_demo, "chain_id": row.chain_id, "contract_address": row.contract_address,
        "tx_hash": row.tx_hash, "created_at": iso(row.created_at), "updated_at": iso(row.updated_at),
    }


def event_dict(row: CreditEvent) -> dict:
    return {
        "id": row.id, "project_id": row.project_id, "credit_batch_id": row.credit_batch_id,
        "event_type": row.event_type, "from_state": row.from_state, "to_state": row.to_state,
        "actor_id": row.actor_id, "quantity_kg_co2e": row.quantity_kg_co2e,
        "evidence_hash": row.evidence_hash, "reason": row.reason,
        "chain_id": row.chain_id, "tx_hash": row.tx_hash, "block_number": row.block_number,
        "is_demo": row.is_demo, "created_at": iso(row.created_at),
    }


def create_seed_file() -> tuple[str, int, str]:
    filename = "demo-baseline-evidence.txt"
    content = ("TRIPLEES DEMO DATA — NOT A REAL PROJECT EVIDENCE FILE.\n"
               "Synthetic fixture for local prototype behavior only.\n").encode("utf-8")
    try:
        data = get_evidence(filename)
    except EvidenceStorageError:
        put_evidence(filename, content, "text/plain")
        data = content
    return filename, len(data), hashlib.sha256(data).hexdigest()


def seed_database() -> None:
    with SessionLocal() as db:
        existing_demo = db.get(Profile, "demo-reviewer")
        if existing_demo:
            if not existing_demo.password_hash or not existing_demo.password_salt:
                existing_demo.password_salt, existing_demo.password_hash = hash_password(secrets.token_urlsafe(48))
                db.commit()
            return
        salt, password_hash = hash_password(secrets.token_urlsafe(48))
        user = Profile(id="demo-reviewer", display_name="Jordan Demo", role="admin", email="demo@example.invalid", password_salt=salt, password_hash=password_hash)
        db.add(user)
        db.flush()
        forest = Project(
            id="DEMO-FOREST-001", name="Demo Forest Project ES-001", project_type="forest",
            country="Spain", region="Demo Region", methodology_id="DEMO-FOREST-METHODOLOGY",
            vintage_start="2024-01-01", vintage_end="2024-12-31", registry_name="DEMO-Registry-A",
            registry_project_ref="DEMO-FOREST-001", baseline_summary="Synthetic baseline for product demonstration only.",
            status="At Risk", is_demo=True, created_by=user.id,
        )
        soil = Project(
            id="DEMO-SOIL-002", name="Demo Soil Project ES-002", project_type="soil",
            country="Spain", region="Demo Region", methodology_id="DEMO-SOIL-METHODOLOGY",
            vintage_start="2024-01-01", vintage_end="2024-12-31", registry_name="DEMO-Registry-A",
            registry_project_ref="DEMO-SOIL-002", baseline_summary="Fictional soil project fixture.",
            status="Under Review", is_demo=True, created_by=user.id,
        )
        wind = Project(
            id="DEMO-WIND-003", name="Demo Wind Project ES-003", project_type="renewable",
            country="Spain", region="Demo Region", methodology_id="DEMO-WIND-METHODOLOGY",
            vintage_start="2023-01-01", vintage_end="2023-12-31", baseline_summary="Synthetic project fixture.",
            status="Active", is_demo=True, created_by=user.id,
        )
        db.add_all([forest, soil, wind])
        db.flush()
        batches = [
            CreditBatch(id="DEMO-BATCH-001", batch_code="DEMO-BATCH-001", project_id=forest.id, registry_name="DEMO-Registry-A", registry_batch_ref="DEMO-FOREST-001", serial_start="DEMO-SERIAL-0001", quantity_kg_co2e=1_000_000, available_balance_kg=1_000_000, retired_balance_kg=0, vintage_start="2024-01-01", vintage_end="2024-12-31", methodology_id=forest.methodology_id, state="At Risk", score=58, score_components=json.dumps({"M":58,"V":64,"C":35,"R":66,"A":72}), score_missing_flags="[]", is_demo=True),
            CreditBatch(id="DEMO-BATCH-002", batch_code="DEMO-BATCH-002", project_id=soil.id, registry_name="DEMO-Registry-A", registry_batch_ref="DEMO-SOIL-002", serial_start="DEMO-SERIAL-0002", quantity_kg_co2e=250_000, available_balance_kg=0, retired_balance_kg=250_000, vintage_start="2024-01-01", vintage_end="2024-12-31", methodology_id=soil.methodology_id, state="Retired", score=71, score_components=json.dumps({"M":78,"V":74,"C":70,"R":62,"A":70}), score_missing_flags="[]", is_demo=True),
            CreditBatch(id="DEMO-BATCH-003", batch_code="DEMO-BATCH-003", project_id=wind.id, serial_start="DEMO-SERIAL-0003", quantity_kg_co2e=350_000, available_balance_kg=350_000, retired_balance_kg=0, vintage_start="2023-01-01", vintage_end="2023-12-31", methodology_id=wind.methodology_id, state="Active", score=76, score_components=json.dumps({"M":82,"V":78,"C":75,"R":72,"A":72}), score_missing_flags="[]", is_demo=True),
        ]
        db.add_all(batches)
        filename, size, digest = create_seed_file()
        evidence = EvidenceFile(
            id="EVD-DEMO-001", project_id=forest.id, filename=filename,
            content_type="text/plain", size_bytes=size, storage_key=filename, sha256=digest,
            evidence_type="document", source_name="Synthetic sample fixture", uploaded_by=user.id,
            review_state="Sample only", is_demo=True,
        )
        records = [
            RegistryRecord(id="REG-DEMO-001", source_name="DEMO-Registry-A", external_project_id="DEMO-FOREST-001", external_project_name=forest.name, external_serial="DEMO-SERIAL-0001", vintage_start="2024-01-01", vintage_end="2024-12-31", methodology_id=forest.methodology_id, country="Spain", region="Demo Region", quantity_kg_co2e=1_000_000, status="active", source_timestamp="2026-01-15T12:00:00Z", is_demo=True, imported_by=user.id),
            RegistryRecord(id="REG-DEMO-002", source_name="DEMO-Registry-B", external_project_id="DEMO-FOREST-ALT-001", external_project_name=forest.name, external_serial="DEMO-SERIAL-0001", vintage_start="2024-01-01", vintage_end="2024-12-31", methodology_id=forest.methodology_id, country="Spain", region="Demo Region", quantity_kg_co2e=1_000_000, status="active", source_timestamp="2026-01-16T12:00:00Z", is_demo=True, imported_by=user.id),
            RegistryRecord(id="REG-DEMO-003", source_name="DEMO-Registry-A", external_project_id="DEMO-SOIL-002", external_project_name=soil.name, external_serial="DEMO-SERIAL-0002", vintage_start="2024-01-01", vintage_end="2024-12-31", methodology_id=soil.methodology_id, country="Spain", region="Demo Region", quantity_kg_co2e=250_000, status="retired", source_timestamp="2026-01-18T12:00:00Z", is_demo=True, imported_by=user.id),
        ]
        observation = MonitoringObservation(id="OBS-DEMO-001", project_id=forest.id, source_name="TRIPLEES synthetic monitoring fixture", signal_type="forest_loss", severity="high", affected_area_percent=18, observed_at="2026-01-20T10:00:00Z", is_synthetic=True, raw_payload_json=json.dumps({"description":"Synthetic demonstration event only; not a real satellite observation."}), review_state="Needs human review")
        db.add_all([evidence, *records, observation])
        db.flush()
        alert = Alert(id="ALT-DEMO-001", project_id=forest.id, observation_id=observation.id, alert_type="Potential disturbance", severity="high", explanation="Synthetic forest-loss signal added for demonstration. Not a confirmed environmental reversal.", state="Open", is_demo=True)
        db.add(alert)
        db.add_all([
            Review(id="REV-DEMO-001", alert_id=alert.id, finding="Synthetic monitoring signal needs human review.", reviewer_id=user.id, decision="pending", reason="Available imported sample records include a duplicate serial; coverage is limited to these rows.", is_demo=True),
            Review(id="REV-DEMO-002", credit_batch_id=batches[0].id, finding="Duplicate serial appears in the available imported sample records.", reviewer_id=user.id, decision="pending", reason="Potential duplicate detected in imported sample rows only.", is_demo=True),
        ])
        seed_events = [
            CreditEvent(id="EVT-DEMO-001", project_id=forest.id, event_type="PROJECT_CREATED", to_state="At Risk", actor_id=user.id, reason="Synthetic project fixture initialized.", is_demo=True),
            CreditEvent(id="EVT-DEMO-002", project_id=forest.id, credit_batch_id=batches[0].id, event_type="CONFLICT_DETECTED", from_state="Active", to_state="At Risk", actor_id=user.id, reason="Duplicate serial in imported sample data. Imported-source coverage only.", is_demo=True),
            CreditEvent(id="EVT-DEMO-003", project_id=soil.id, credit_batch_id=batches[1].id, event_type="CREDIT_RETIRED", from_state="Active", to_state="Retired", actor_id=user.id, quantity_kg_co2e=250_000, reason="Synthetic retirement fixture; no external registry retirement occurred.", is_demo=True),
            CreditEvent(id="EVT-DEMO-004", project_id=forest.id, event_type="MONITORING_OBSERVATION_ADDED", actor_id=user.id, reason="Synthetic monitoring observation, not a live feed.", is_demo=True),
        ]
        db.add_all(seed_events)
        for batch in batches:
            update_score(db, batch, "Initial synthetic demo seed")
        db.commit()


@app.get("/health")
@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/readyz")
@app.get("/api/ready")
def readiness(db: Session = Depends(get_db)):
    try:
        db.execute(select(1))
        storage_ready = check_storage()
    except Exception as exc:
        logger.error("readiness check failed: %s", type(exc).__name__)
        raise HTTPException(503, detail={"code": "service_not_ready", "message": "Database or evidence storage is unavailable."}) from exc
    return {"status": "ready", "database": "connected", "evidence_storage": "connected" if storage_ready else "unavailable"}


@app.get("/api/blockchain/status")
def blockchain_status(db: Session = Depends(get_db), user: Profile = Depends(current_user)):
    """Read-only network check; never exposes configured private keys."""
    client = X1ChainClient()
    network = client.check_network()
    wallets = []
    if network["rpc_connected"] and network["actual_chain_id"] == 10778:
        try:
            wallets = client.wallet_status()
        except Exception:
            wallets = [{"role": role, "configured": configured, "address": None, "balance": None, "currency": network["native_currency"]}
                       for role, configured in client.wallet_presence().items()]
    else:
        wallets = [{"role": role, "configured": configured, "address": None, "balance": None, "currency": network["native_currency"]}
                   for role, configured in client.wallet_presence().items()]
    recent = db.query(CreditEvent).filter(CreditEvent.tx_hash.is_not(None)).order_by(CreditEvent.created_at.desc()).limit(8).all()
    transactions = [{"action": event.event_type, "entity_id": event.credit_batch_id or event.project_id, "transaction_hash": event.tx_hash, "block_number": event.block_number, "status": "confirmed", "explorer_url": f"{network['explorer_url']}/tx/{event.tx_hash}", "created_at": iso(event.created_at)} for event in recent]
    return {"network": network, "wallets": wallets, "transactions": transactions}


@app.get("/api/blockchain/network")
def blockchain_network():
    """Public, read-only X1 status safe for health indicators."""
    return X1ChainClient().check_network()


@app.get("/api/blockchain/wallets/{address}/balance")
def blockchain_wallet_balance(address: str, user: Profile = Depends(current_user)):
    if not Web3.is_address(address):
        raise HTTPException(422, detail={"code": "wallet_address_invalid", "message": "Provide a valid EVM public address."})
    client = X1ChainClient()
    try:
        w3 = client.require_network()
        balance = w3.eth.get_balance(Web3.to_checksum_address(address))
    except Exception as exc:
        raise HTTPException(503, detail={"code": "x1_unavailable", "message": "X1 Maculatus RPC is unavailable or does not match the configured network."}) from exc
    from decimal import Decimal
    return {"address": Web3.to_checksum_address(address), "chain_id": 10778, "balance_wei": str(balance), "balance": str(Decimal(balance) / Decimal(10**18)), "currency": client.settings.native_currency}


@app.get("/api/blockchain/contracts")
def blockchain_contracts(user: Profile = Depends(current_user)):
    client = X1ChainClient()
    status = client.check_network()
    contracts = []
    if status["contract_address"]:
        contracts.append({"name": "VericarbRegistry", "address": status["contract_address"], "deployed": status["contract_deployed"], "explorer_url": f"{status['explorer_url']}/address/{status['contract_address']}"})
    if status["report_anchor_contract_address"]:
        contracts.append({"name": "InvestigationReportAnchorRegistry", "address": status["report_anchor_contract_address"], "deployed": status["report_anchor_contract_deployed"], "explorer_url": f"{status['explorer_url']}/address/{status['report_anchor_contract_address']}"})
    return {"network": status["network_name"], "chain_id": status["actual_chain_id"], "contracts": contracts, "state": status["state"]}


@app.post("/api/auth/demo", response_model=DemoAuthResponse)
def demo_sign_in(db: Session = Depends(get_db)):
    if APP_ENV == "production":
        raise HTTPException(404, detail={"code": "not_found", "message": "Endpoint was not found."})
    user = db.get(Profile, "demo-reviewer")
    if user is None:
        raise HTTPException(503, detail={"code": "demo_seed_unavailable", "message": "Demo profile is unavailable."})
    return DemoAuthResponse(
        access_token=issue_token(user.id), expires_in=TOKEN_TTL_SECONDS,
        user={"id": user.id, "display_name": user.display_name, "role": user.role, "email": user.email, "is_demo": True},
    )


def hash_password(password: str, salt: bytes | None = None) -> tuple[str, str]:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1, dklen=64)
    return salt.hex(), digest.hex()


@app.post("/api/auth/signup", status_code=201)
def signup(body: SignupRequest, db: Session = Depends(get_db)):
    if APP_ENV == "production":
        raise HTTPException(503, detail={"code": "identity_provider_required", "message": "Account creation is unavailable until production identity is configured."})
    if db.query(Profile).filter(func.lower(Profile.email) == body.email).first():
        raise HTTPException(409, detail={"code": "email_in_use", "message": "An account already exists for this email."})
    salt, password_hash = hash_password(body.password)
    user = Profile(id=identifier("USR"), display_name=body.display_name, role="developer", email=body.email, organization=body.organization, password_salt=salt, password_hash=password_hash, is_demo=True)
    db.add(user)
    db.commit()
    return {"access_token": issue_token(user.id), "token_type": "bearer", "expires_in": TOKEN_TTL_SECONDS, "user": {"id": user.id, "display_name": user.display_name, "role": user.role, "email": user.email, "is_demo": True}, "notice": "Local prototype account. Email verification and production authentication are not configured."}


@app.post("/api/auth/login")
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(Profile).filter(func.lower(Profile.email) == body.email).first()
    if user and user.id == "demo-reviewer":
        raise HTTPException(401, detail={"code": "invalid_credentials", "message": "Use the local demo access button for synthetic records."})
    if not user or not user.password_hash or not user.password_salt:
        raise HTTPException(401, detail={"code": "invalid_credentials", "message": "Email or password is incorrect."})
    _, candidate = hash_password(body.password, bytes.fromhex(user.password_salt))
    if not secrets.compare_digest(candidate, user.password_hash):
        raise HTTPException(401, detail={"code": "invalid_credentials", "message": "Email or password is incorrect."})
    return {"access_token": issue_token(user.id), "token_type": "bearer", "expires_in": TOKEN_TTL_SECONDS, "user": {"id": user.id, "display_name": user.display_name, "role": user.role, "email": user.email, "is_demo": True}, "notice": "Local prototype authentication; configure production identity and session controls before deployment."}


@app.get("/api/me")
def get_me(user: Profile = Depends(current_user)):
    return {"id": user.id, "display_name": user.display_name, "role": user.role, "email": user.email, "location": user.location, "organization": user.organization, "is_demo": True}


@app.put("/api/me")
def update_me(body: ProfileUpdate, db: Session = Depends(get_db), user: Profile = Depends(current_user)):
    user.display_name = body.display_name
    user.email = body.email
    user.location = body.location
    user.organization = body.organization
    db.commit()
    return get_me(user)


@app.get("/api/dashboard")
def dashboard(db: Session = Depends(get_db), user: Profile = Depends(current_user)):
    projects = db.query(Project).filter(Project.created_by == user.id).all()
    batches = db.query(CreditBatch).join(Project).filter(Project.created_by == user.id).all()
    open_alerts = db.query(Alert).join(Project).filter(Project.created_by == user.id, Alert.state == "Open").count()
    pending_reviews = db.query(Review).filter(Review.decision == "pending", Review.reviewer_id == user.id).count()
    conflicts = db.query(RegistryRecord.external_serial, func.count(RegistryRecord.id)).group_by(RegistryRecord.external_serial).having(func.count(RegistryRecord.id) > 1).all()
    return {
        "is_demo": True, "project_count": len(projects), "batch_count": len(batches),
        "available_units_kg": sum(x.available_balance_kg for x in batches),
        "retired_units_kg": sum(x.retired_balance_kg for x in batches),
        "batches_at_risk": sum(x.state == "At Risk" for x in batches),
        "open_alerts": open_alerts, "pending_reviews": pending_reviews,
        "potential_duplicate_serials": len(conflicts),
        "average_provisional_integrity_score": round(sum(x.score for x in batches) / len(batches)) if batches else None,
        "source_coverage": "Imported records only; external sources are not connected.",
    }


@app.get("/api/demo/bootstrap")
def demo_bootstrap(db: Session = Depends(get_db), user: Profile = Depends(current_user)):
    projects_query = db.query(Project)
    if user.role not in {"reviewer", "admin"}:
        projects_query = projects_query.filter(Project.created_by == user.id)
    projects = projects_query.order_by(Project.created_at.desc()).all()
    project_ids = [p.id for p in projects]
    batches = db.query(CreditBatch).filter(CreditBatch.project_id.in_(project_ids)).order_by(CreditBatch.created_at.desc()).all() if project_ids else []
    evidence = db.query(EvidenceFile).filter(EvidenceFile.project_id.in_(project_ids)).order_by(EvidenceFile.created_at.desc()).all() if project_ids else []
    observations = db.query(MonitoringObservation).filter(MonitoringObservation.project_id.in_(project_ids)).order_by(MonitoringObservation.observed_at.desc()).all() if project_ids else []
    alerts = db.query(Alert).filter(Alert.project_id.in_(project_ids)).order_by(Alert.created_at.desc()).all() if project_ids else []
    registry_query = db.query(RegistryRecord)
    review_query = db.query(Review)
    if user.role not in {"reviewer", "admin"}:
        registry_query = registry_query.filter(RegistryRecord.imported_by == user.id)
        review_query = review_query.filter(Review.reviewer_id == user.id)
    registry = registry_query.order_by(RegistryRecord.created_at.asc()).all()
    reviews = review_query.order_by(Review.created_at.desc()).all()
    events = db.query(CreditEvent).filter(CreditEvent.project_id.in_(project_ids)).order_by(CreditEvent.created_at.desc()).all() if project_ids else []
    assessments = db.query(Assessment).filter(Assessment.project_id.in_(project_ids)).order_by(Assessment.created_at.desc()).all() if project_ids else []
    profile = {"id": user.id, "display_name": user.display_name, "role": user.role, "email": user.email, "location": user.location, "organization": user.organization, "is_demo": True}
    return {
        "user": profile,
        "projects": [project_dict(x) for x in projects],
        "batches": [batch_dict(x) for x in batches],
        "evidence": [evidence_dict(x) for x in evidence],
        "observations": [observation_dict(x) for x in observations],
        "alerts": [{"id": x.id, "project_id": x.project_id, "observation_id": x.observation_id, "type": x.alert_type, "severity": x.severity.title(), "explanation": x.explanation, "state": x.state, "decision": x.decision, "reviewer": x.assigned_reviewer, "created_at": iso(x.created_at), "reviewed_at": iso(x.reviewed_at), "demo": x.is_demo} for x in alerts],
        "reviews": [{"id": x.id, "target_id": x.credit_batch_id or x.alert_id or x.assessment_id, "target_type": ("Registry conflict" if x.credit_batch_id and "duplicate" in (x.finding or "").lower() else "Credit batch review") if x.credit_batch_id else "Monitoring alert" if x.alert_id else "Evidence assessment", "finding": x.finding or "Review item", "state": "Pending" if x.decision == "pending" else x.decision.replace("_", " ").title(), "reason": x.reason, "actor": x.reviewer_id, "created_at": iso(x.created_at), "decided_at": iso(x.reviewed_at) if x.reviewed_at else None, "demo": x.is_demo} for x in reviews],
        "imported_records": [{"source": x.source_name, "projectRef": x.external_project_id, "project": x.external_project_name, "serial": x.external_serial, "vintage": (x.vintage_start or "")[:4], "methodology": x.methodology_id, "country": x.country, "quantityKg": x.quantity_kg_co2e, "status": x.status, "demo": x.is_demo} for x in registry],
        "events": [{"id": x.id, "targetId": x.credit_batch_id or x.project_id, "project_id": x.project_id, "credit_batch_id": x.credit_batch_id, "type": x.event_type.replace("_", " ").title(), "actor": x.actor_id, "reason": x.reason or "", "at": iso(x.created_at), "demo": x.is_demo} for x in events],
        "assessments": [{"id": x.id, "project_id": x.project_id, "evidence_file_id": x.evidence_file_id, "status": x.status, "result": json_value(x.result_json, {}), "created_at": iso(x.created_at)} for x in assessments],
        "settings": {"displayName": user.display_name, "email": user.email or "", "organization": user.organization or "TRIPLEES Demo Workspace", "location": user.location or "", "role": user.role},
        "noticesDismissed": False,
        "integrations": {"mode": "local-api", "chain": False, "ai": False, "registry": False, "monitoring": False},
    }


@app.get("/api/reviews")
def list_reviews(db: Session = Depends(get_db), user: Profile = Depends(current_user)):
    query = db.query(Review)
    if user.role not in {"reviewer", "admin"}:
        query = query.filter(Review.reviewer_id == user.id)
    rows = query.order_by(Review.created_at.desc()).all()
    return {"items": [{"id": x.id, "assessment_id": x.assessment_id, "alert_id": x.alert_id, "credit_batch_id": x.credit_batch_id, "finding": x.finding, "decision": x.decision, "reason": x.reason, "reviewer_id": x.reviewer_id, "created_at": iso(x.created_at), "is_demo": x.is_demo} for x in rows]}


@app.post("/api/demo/reset")
def reset_demo(db: Session = Depends(get_db), _user: Profile = Depends(require_role("admin"))):
    if APP_ENV == "production":
        raise HTTPException(404, detail={"code": "not_found", "message": "Endpoint was not found."})
    if OBJECT_STORAGE_BUCKET:
        raise HTTPException(409, detail={"code": "remote_demo_reset_unsupported", "message": "Demo reset is disabled while shared object storage is configured."})
    for model in [Claim, Review, Alert, MonitoringObservation, Assessment, CreditEvent, IntegrityScore, EvidenceFile, CreditBatch, RegistryRecord, Project, Profile]:
        db.query(model).delete(synchronize_session=False)
    db.commit()
    delete_all_local_evidence_except({"demo-baseline-evidence.txt"})
    seed_database()
    return {"status": "reset", "message": "Synthetic local demo data was restored."}


@app.get("/api/projects")
def list_projects(db: Session = Depends(get_db), user: Profile = Depends(current_user)):
    rows = db.query(Project).filter(Project.created_by == user.id).order_by(Project.updated_at.desc()).all()
    return {"items": [project_dict(x) for x in rows], "is_demo": True}


@app.post("/api/projects", status_code=201)
def create_project(body: ProjectCreate, db: Session = Depends(get_db), user: Profile = Depends(current_user)):
    project = Project(
        id=identifier("PRJ-DEMO"), name=body.name, project_type=body.project_type,
        country=body.country, region=body.region, methodology_id=body.methodology_id,
        vintage_start=body.vintage_start.isoformat() if body.vintage_start else None,
        vintage_end=body.vintage_end.isoformat() if body.vintage_end else None,
        registry_name=body.registry_name, registry_project_ref=body.registry_project_ref,
        baseline_summary=body.baseline_summary,
        boundary_geojson=json.dumps(body.boundary_geojson) if body.boundary_geojson is not None else None,
        status="Draft", is_demo=True, created_by=user.id,
    )
    db.add(project)
    db.flush()
    append_event(db, user, project.id, "PROJECT_CREATED", "Local project draft created. No external verification performed.")
    db.commit()
    return project_dict(project)


@app.get("/api/projects/{project_id}")
def get_project(project_id: str, db: Session = Depends(get_db), user: Profile = Depends(current_user)):
    project = owned_project(db, project_id, user)
    batches = db.query(CreditBatch).filter(CreditBatch.project_id == project.id).all()
    evidence = db.query(EvidenceFile).filter(EvidenceFile.project_id == project.id).order_by(EvidenceFile.created_at.desc()).all()
    observations = db.query(MonitoringObservation).filter(MonitoringObservation.project_id == project.id).order_by(MonitoringObservation.created_at.desc()).all()
    events = db.query(CreditEvent).filter(CreditEvent.project_id == project.id).order_by(CreditEvent.created_at.desc()).all()
    return {
        **project_dict(project), "boundary_geojson": json_value(project.boundary_geojson, None),
        "batches": [batch_dict(x) for x in batches], "evidence": [evidence_dict(x) for x in evidence],
        "observations": [observation_dict(x) for x in observations], "events": [event_dict(x) for x in events],
    }


@app.post("/api/projects/{project_id}/register-chain")
def register_project_on_chain(project_id: str, db: Session = Depends(get_db), user: Profile = Depends(require_role("issuer", "admin"))):
    project = owned_project(db, project_id, user)
    client = X1ChainClient()
    try:
        contract = client.contract()
        project_key = Web3.keccak(text=project.id)
        try:
            contract.functions.getProject(project_key).call()
            raise HTTPException(409, detail={"code": "project_already_registered", "message": "This project identifier already exists on the configured X1 contract."})
        except HTTPException:
            raise
        except Exception:
            pass
        start_year = int(project.vintage_start[:4]) if project.vintage_start else 0
        end_year = int(project.vintage_end[:4]) if project.vintage_end else 0
        function = contract.functions.registerProject(
            project_key,
            Web3.keccak(text=project.registry_project_ref or project.id),
            Web3.keccak(text=project.methodology_id or "unspecified"),
            start_year,
            end_year,
        )
        receipt = client.send_contract_transaction("registrar", function)
        onchain = contract.functions.getProject(project_key).call()
        if not onchain[0]:
            raise X1NetworkError("The confirmed transaction did not produce the expected project state.")
    except HTTPException:
        raise
    except X1ConfigurationError as exc:
        raise HTTPException(409, detail={"code": "x1_not_ready", "message": str(exc)}) from exc
    except Exception as exc:
        raise HTTPException(502, detail={"code": "x1_transaction_failed", "message": f"Project registration was not confirmed: {type(exc).__name__}."}) from exc
    event = append_event(db, user, project.id, "PROJECT_REGISTERED_ON_CHAIN", "Project references registered on X1; this confirms a submitted record, not environmental claims.", is_demo=False)
    event.chain_id, event.tx_hash, event.block_number = 10778, receipt["transaction_hash"], receipt["block_number"]
    project.chain_project_id = project_key.hex()
    project.chain_id = 10778
    project.contract_address = receipt["contract_address"]
    project.tx_hash = receipt["transaction_hash"]
    db.commit()
    return {"status": "confirmed", "project_id": project.id, "onchain_project_id": project_key.hex(), "chain_id": 10778, "contract_address": receipt["contract_address"], "transaction_hash": receipt["transaction_hash"], "block_number": receipt["block_number"]}


def observation_dict(row: MonitoringObservation) -> dict:
    return {"id": row.id, "project_id": row.project_id, "source_name": row.source_name,
            "signal_type": row.signal_type, "severity": row.severity,
            "affected_area_percent": row.affected_area_percent, "observed_at": row.observed_at,
            "evidence_file_id": row.evidence_file_id, "evidence_hash": row.evidence_hash,
            "is_synthetic": row.is_synthetic, "review_state": row.review_state,
            "payload": json_value(row.raw_payload_json, {}), "created_at": iso(row.created_at)}


@app.post("/api/projects/{project_id}/evidence", status_code=201)
async def upload_evidence(
    project_id: str,
    file: UploadFile = File(...),
    evidence_type: str = Form(default="document"),
    source_name: str | None = Form(default=None),
    db: Session = Depends(get_db),
    user: Profile = Depends(current_user),
):
    project = owned_project(db, project_id, user)
    if evidence_type not in {"document", "image", "data", "link"}:
        raise HTTPException(422, detail={"code": "evidence_type_invalid", "message": "Evidence type must be document, image, data, or link."})
    if source_name is not None and len(source_name) > 160:
        raise HTTPException(422, detail={"code": "source_name_too_long", "message": "Evidence source name must be 160 characters or fewer."})
    allowed = {".pdf", ".csv", ".json", ".png", ".jpg", ".jpeg", ".webp", ".txt"}
    original = Path(file.filename or "evidence").name
    suffix = Path(original).suffix.lower()
    if suffix not in allowed:
        raise HTTPException(415, detail={"code": "file_type_not_allowed", "message": "Allowed files: PDF, CSV, JSON, PNG, JPG, WEBP, and TXT."})
    allowed_mimes = {
        ".pdf": {"application/pdf"},
        ".csv": {"text/csv", "application/csv", "application/vnd.ms-excel"},
        ".json": {"application/json", "text/json"},
        ".txt": {"text/plain"},
        ".png": {"image/png"},
        ".jpg": {"image/jpeg"},
        ".jpeg": {"image/jpeg"},
        ".webp": {"image/webp"},
    }
    declared_mime = (file.content_type or "application/octet-stream").split(";", 1)[0].strip().lower()
    if declared_mime != "application/octet-stream" and declared_mime not in allowed_mimes[suffix]:
        raise HTTPException(415, detail={"code": "content_type_mismatch", "message": "The uploaded file extension and content type do not match."})
    chunks = bytearray()
    while True:
        chunk = await file.read(1024 * 256)
        if not chunk:
            break
        chunks.extend(chunk)
        if len(chunks) > MAX_UPLOAD_BYTES:
            raise HTTPException(413, detail={"code": "upload_too_large", "message": f"Evidence files must be at most {MAX_UPLOAD_BYTES // (1024 * 1024)} MB."})
    if not chunks:
        raise HTTPException(422, detail={"code": "empty_file", "message": "The selected evidence file is empty."})
    file_bytes = bytes(chunks)
    if suffix == ".pdf" and not file_bytes.startswith(b"%PDF-"):
        raise HTTPException(422, detail={"code": "file_content_mismatch", "message": "The selected PDF file does not have a valid PDF header."})
    if suffix == ".png" and not file_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        raise HTTPException(422, detail={"code": "file_content_mismatch", "message": "The selected PNG file does not have a valid image header."})
    if suffix in {".jpg", ".jpeg"} and not file_bytes.startswith(b"\xff\xd8\xff"):
        raise HTTPException(422, detail={"code": "file_content_mismatch", "message": "The selected JPEG file does not have a valid image header."})
    if suffix == ".webp" and not (file_bytes.startswith(b"RIFF") and file_bytes[8:12] == b"WEBP"):
        raise HTTPException(422, detail={"code": "file_content_mismatch", "message": "The selected WEBP file does not have a valid image header."})
    if suffix in {".txt", ".csv", ".json"}:
        try:
            decoded = file_bytes.decode("utf-8-sig")
            if suffix == ".json":
                json.loads(decoded)
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise HTTPException(422, detail={"code": "invalid_document_content", "message": "The selected text file is not valid UTF-8 or JSON content."})
    digest = hashlib.sha256(file_bytes).hexdigest()
    storage_key = f"{uuid.uuid4().hex}{suffix}"
    try:
        put_evidence(storage_key, file_bytes, file.content_type or "application/octet-stream")
    except EvidenceStorageError as exc:
        raise HTTPException(503, detail={"code": "evidence_storage_unavailable", "message": "Evidence could not be stored. Please retry."}) from exc
    record = EvidenceFile(
        id=identifier("EVD"), project_id=project.id, filename=original,
        content_type=(file.content_type or "application/octet-stream")[:120], size_bytes=len(chunks),
        storage_key=storage_key, sha256=digest, evidence_type=evidence_type[:40],
        source_name=(source_name or "User upload")[:160], uploaded_by=user.id,
        review_state="Not reviewed", is_demo=True,
    )
    db.add(record)
    append_event(db, user, project.id, "EVIDENCE_ADDED", "Raw file stored off-chain; SHA-256 computed server-side.", evidence_hash=digest)
    for batch in db.query(CreditBatch).filter(CreditBatch.project_id == project.id).all():
        components = json_value(batch.score_components, {"M":50,"V":50,"C":50,"R":50,"A":50})
        components["M"] = min(int(components.get("M", 50)), 45)
        batch.score_components = json.dumps(components)
        update_score(db, batch, "New evidence metadata awaits human assessment")
    db.commit()
    return evidence_dict(record)


@app.post("/api/evidence/{evidence_id}/anchor")
def anchor_evidence_hash(evidence_id: str, db: Session = Depends(get_db), user: Profile = Depends(require_role("issuer", "admin"))):
    record = db.get(EvidenceFile, evidence_id)
    if not record:
        raise HTTPException(404, detail={"code": "evidence_not_found", "message": "Evidence record was not found."})
    project = owned_project(db, record.project_id, user)
    client = X1ChainClient()
    try:
        contract = client.contract()
        evidence_key = Web3.keccak(text=record.id)
        try:
            contract.functions.getEvidenceAnchor(evidence_key).call()
            raise HTTPException(409, detail={"code": "evidence_already_anchored", "message": "This evidence identifier already has an on-chain anchor."})
        except HTTPException:
            raise
        except Exception:
            pass
        function = contract.functions.anchorEvidence(
            evidence_key, Web3.keccak(text=project.id), bytes(32), bytes.fromhex(record.sha256),
            Web3.keccak(text=record.evidence_type),
        )
        receipt = client.send_contract_transaction("registrar", function)
        anchor = contract.functions.getEvidenceAnchor(evidence_key).call()
        if not anchor[0] or bytes(anchor[3]).hex() != record.sha256.lower():
            raise X1NetworkError("The confirmed transaction did not produce the expected evidence hash.")
    except HTTPException:
        raise
    except X1ConfigurationError as exc:
        raise HTTPException(409, detail={"code": "x1_not_ready", "message": str(exc)}) from exc
    except Exception as exc:
        raise HTTPException(502, detail={"code": "x1_transaction_failed", "message": f"Evidence anchoring was not confirmed: {type(exc).__name__}."}) from exc
    event = append_event(db, user, project.id, "EVIDENCE_HASH_ANCHORED", "Backend-calculated SHA-256 anchored on X1; the file remains off-chain.", evidence_hash=record.sha256, is_demo=False)
    event.chain_id, event.tx_hash, event.block_number = 10778, receipt["transaction_hash"], receipt["block_number"]
    record.anchor_chain_id = 10778
    record.anchor_contract_address = receipt["contract_address"]
    record.anchor_tx_hash = receipt["transaction_hash"]
    record.anchor_block_number = receipt["block_number"]
    db.commit()
    return {"status": "confirmed", "evidence_id": record.id, "sha256": record.sha256, "chain_id": 10778, "contract_address": receipt["contract_address"], "transaction_hash": receipt["transaction_hash"], "block_number": receipt["block_number"]}


@app.get("/api/projects/{project_id}/evidence")
def list_evidence(project_id: str, db: Session = Depends(get_db), user: Profile = Depends(current_user)):
    project = owned_project(db, project_id, user)
    rows = db.query(EvidenceFile).filter(EvidenceFile.project_id == project.id).order_by(EvidenceFile.created_at.desc()).all()
    return {"items": [evidence_dict(x) for x in rows]}


@app.get("/api/evidence/{evidence_id}/download")
def download_evidence(evidence_id: str, db: Session = Depends(get_db), user: Profile = Depends(current_user)):
    record = db.get(EvidenceFile, evidence_id)
    if not record:
        raise HTTPException(404, detail={"code": "evidence_not_found", "message": "Evidence record was not found."})
    owned_project(db, record.project_id, user)
    try:
        data = get_evidence(record.storage_key)
    except EvidenceStorageError as exc:
        raise HTTPException(404, detail={"code": "file_unavailable", "message": "The original evidence file is unavailable."}) from exc
    if hashlib.sha256(data).hexdigest() != record.sha256:
        raise HTTPException(409, detail={"code": "evidence_hash_mismatch", "message": "Stored evidence bytes do not match the recorded SHA-256 digest."})
    filename = quote(record.filename, safe="")
    return Response(data, media_type=record.content_type, headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"})


@app.post("/api/assessments/evidence-review", status_code=201)
def assess_evidence(payload: EvidenceAssessmentRequest, db: Session = Depends(get_db), user: Profile = Depends(current_user)):
    evidence_id = payload.evidence_id
    evidence = db.get(EvidenceFile, evidence_id)
    if not evidence:
        raise HTTPException(404, detail={"code": "evidence_not_found", "message": "Evidence record was not found."})
    owned_project(db, evidence.project_id, user)
    findings = []
    if evidence.size_bytes == 0:
        findings.append({"severity": "high", "category": "file", "explanation": "File has no content.", "next_step": "Upload a non-empty file."})
    if not evidence.sha256:
        findings.append({"severity": "high", "category": "provenance", "explanation": "No file digest is available.", "next_step": "Recompute the evidence hash."})
    findings.append({"severity": "info", "category": "scope", "explanation": "Source authenticity and document contents have not been independently verified.", "next_step": "Have an authorized reviewer inspect the evidence."})
    result = {"mode": "deterministic_demo", "findings": findings, "automatic_approval": False, "scope": "local file metadata and deterministic checks only"}
    assessment = Assessment(id=identifier("ASM"), project_id=evidence.project_id, evidence_file_id=evidence.id, assessment_type="document_review", status="needs_human_review", result_json=json.dumps(result), model_name=None, is_demo=True)
    db.add(assessment)
    evidence.review_state = "Assessment ready"
    for batch in db.query(CreditBatch).filter(CreditBatch.project_id == evidence.project_id).all():
        components = json_value(batch.score_components, {"M":50,"V":50,"C":50,"R":50,"A":50})
        components["M"] = min(int(components.get("M", 50)), 45)
        batch.score_components = json.dumps(components)
        update_score(db, batch, "Deterministic evidence assessment requires human review")
    db.flush()
    db.add(Review(id=identifier("REV"), assessment_id=assessment.id, finding="Evidence assessment needs human review.", reviewer_id=user.id, decision="pending", reason="Deterministic findings are advisory; reviewer decision required.", is_demo=True))
    append_event(db, user, evidence.project_id, "ASSESSMENT_CREATED", "Deterministic demo assessment; no AI provider configured.", evidence_hash=evidence.sha256)
    db.commit()
    return {"id": assessment.id, "project_id": assessment.project_id, "evidence_file_id": evidence.id, **result, "created_at": iso(assessment.created_at)}


@app.get("/api/assessments")
def list_assessments(db: Session = Depends(get_db), user: Profile = Depends(current_user)):
    rows = db.query(Assessment).join(Project).filter(Project.created_by == user.id).order_by(Assessment.created_at.desc()).all()
    return {"items": [{"id": x.id, "project_id": x.project_id, "credit_batch_id": x.credit_batch_id, "evidence_file_id": x.evidence_file_id, "type": x.assessment_type, "status": x.status, "result": json_value(x.result_json, {}), "is_demo": x.is_demo, "created_at": iso(x.created_at)} for x in rows]}


@app.post("/api/assessments/{assessment_id}/review", status_code=201)
def review_assessment(assessment_id: str, body: BatchReviewRequest, db: Session = Depends(get_db), user: Profile = Depends(require_role("reviewer", "admin"))):
    assessment = db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(404, detail={"code": "assessment_not_found", "message": "Assessment was not found."})
    owned_project(db, assessment.project_id, user)
    review = db.query(Review).filter(Review.assessment_id == assessment.id, Review.decision == "pending").order_by(Review.created_at.asc()).first()
    if review:
        review.decision = body.decision
        review.reason = body.reason
        review.reviewed_at = utcnow()
    else:
        review = Review(id=identifier("REV"), assessment_id=assessment.id, finding="Evidence assessment decision", reviewer_id=user.id, decision=body.decision, reason=body.reason, is_demo=True, reviewed_at=utcnow())
        db.add(review)
    if assessment.evidence_file_id:
        evidence = db.get(EvidenceFile, assessment.evidence_file_id)
        if evidence:
            evidence.review_state = {"approved": "Reviewed by Human", "rejected": "Review Rejected", "needs_more_evidence": "Evidence Needed"}[body.decision]
            if body.decision == "approved":
                for batch in db.query(CreditBatch).filter(CreditBatch.project_id == assessment.project_id).all():
                    components = json_value(batch.score_components, {"M":50,"V":50,"C":50,"R":50,"A":50})
                    components["M"] = max(int(components.get("M", 50)), 60)
                    batch.score_components = json.dumps(components)
                    update_score(db, batch, "Evidence review completed by a human reviewer")
    append_event(db, user, assessment.project_id, "REVIEW_DECISION", f"{body.decision}: {body.reason}")
    db.commit()
    return {"id": review.id, "assessment_id": assessment.id, "decision": review.decision, "reason": review.reason, "reviewer_id": review.reviewer_id, "created_at": iso(review.created_at)}


@app.post("/api/registry/import", status_code=201)
async def import_registry(file: UploadFile = File(...), db: Session = Depends(get_db), user: Profile = Depends(current_user)):
    if not (file.filename or "").lower().endswith(".csv"):
        raise HTTPException(415, detail={"code": "csv_required", "message": "Upload a CSV file."})
    content = await file.read(5 * 1024 * 1024 + 1)
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(413, detail={"code": "csv_too_large", "message": "Registry CSV is limited to 5 MB."})
    try:
        reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig")))
        required = {"source_name", "external_project_id", "external_project_name", "external_serial", "quantity_kg_co2e", "status"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise HTTPException(422, detail={"code": "csv_headers_invalid", "message": "CSV is missing required headers.", "fields": sorted(missing)})
        rows = list(reader)
    except UnicodeDecodeError as exc:
        raise HTTPException(422, detail={"code": "csv_encoding_invalid", "message": "Use UTF-8 encoded CSV."}) from exc
    if not rows or len(rows) > 10000:
        raise HTTPException(422, detail={"code": "csv_row_count_invalid", "message": "CSV must contain between 1 and 10,000 data rows."})
    inserted = []
    for row in rows:
        serial = (row.get("external_serial") or "").strip()
        quantity = (row.get("quantity_kg_co2e") or "").strip()
        if not serial or not quantity.isdecimal():
            raise HTTPException(422, detail={"code": "csv_row_invalid", "message": "Each row needs an external serial and a non-negative integer quantity."})
        safe = {k: (v or "").strip() for k, v in row.items() if k}
        inserted.append(RegistryRecord(
            id=identifier("REG"), source_name=safe.get("source_name", "Imported CSV")[:160],
            external_project_id=safe.get("external_project_id", "")[:160], external_project_name=safe.get("external_project_name", "")[:200],
            external_serial=serial[:160], vintage_start=safe.get("vintage_start") or None, vintage_end=safe.get("vintage_end") or None,
            methodology_id=safe.get("methodology_id") or None, country=safe.get("country") or None, region=safe.get("region") or None,
            quantity_kg_co2e=int(quantity), status=(safe.get("status") or "unknown")[:40], source_timestamp=safe.get("source_timestamp") or None,
            raw_record_hash=hashlib.sha256(json.dumps(safe, sort_keys=True).encode()).hexdigest(),
            is_demo=True, imported_by=user.id,
        ))
    first_project = db.query(Project).filter(Project.created_by == user.id).first()
    if first_project is None and user.role not in {"reviewer", "admin"}:
        raise HTTPException(409, detail={"code": "project_required", "message": "Create a project before importing registry rows so the import is associated with a project audit trail."})
    db.add_all(inserted)
    db.flush()
    if first_project is None:
        first_project = db.query(Project).first()
    if first_project:
        append_event(db, user, first_project.id, "REGISTRY_CSV_IMPORTED", f"{len(inserted)} CSV rows imported; comparisons cover these records only.")
    for conflict in find_conflicts(db, user):
        batches = db.query(CreditBatch).join(Project).filter(Project.created_by == user.id, func.lower(CreditBatch.serial_start) == conflict["serial"].casefold()).all()
        for batch in batches:
            if not db.query(Review).filter(Review.credit_batch_id == batch.id, Review.decision == "pending").first():
                db.add(Review(id=identifier("REV"), credit_batch_id=batch.id, finding="Potential duplicate serial found in imported rows.", reviewer_id=user.id, decision="pending", reason="Exact serial collision in imported source records; source coverage is limited.", is_demo=True))
            components = json_value(batch.score_components, {"M":50,"V":50,"C":50,"R":50,"A":50})
            components["C"] = min(int(components.get("C", 50)), 25)
            batch.score_components = json.dumps(components)
            update_score(db, batch, "Potential duplicate in the available imported registry rows")
            append_event(db, user, batch.project_id, "CONFLICT_DETECTED", "Exact serial match in imported rows only; other registries have not been checked.", batch_id=batch.id, from_state=batch.state, to_state="Conflict Detected")
            if batch.state == "Active":
                batch.state = "Conflict Detected"
    db.commit()
    conflicts = find_conflicts(db, user)
    return {"imported_count": len(inserted), "potential_conflicts": conflicts, "source_coverage": "Imported rows only; no live registry was queried.", "is_demo": True}


def find_conflicts(db: Session, user: Profile) -> list[dict]:
    records = db.query(RegistryRecord).filter(RegistryRecord.imported_by == user.id).all()
    groups: dict[str, list[RegistryRecord]] = {}
    for row in records:
        groups.setdefault(row.external_serial.casefold().strip(), []).append(row)
    conflicts = []
    for serial, rows in groups.items():
        if len(rows) > 1:
            conflicts.append({"match_type": "exact_serial", "serial": serial, "record_count": len(rows), "sources": sorted({r.source_name for r in rows}), "record_ids": [r.id for r in rows], "reason": "Exact serial appears in multiple imported records.", "is_demo": all(r.is_demo for r in rows)})
    return conflicts


@app.post("/api/registry/check-conflicts")
def registry_conflicts(db: Session = Depends(get_db), user: Profile = Depends(current_user)):
    return {"items": find_conflicts(db, user), "coverage": "Imported/connected records only; other registries have not been checked.", "is_demo": True}


@app.post("/api/projects/{project_id}/batches", status_code=201)
def create_batch(project_id: str, body: BatchCreate, db: Session = Depends(get_db), user: Profile = Depends(current_user)):
    project = owned_project(db, project_id, user)
    serial = body.serial_start.strip()
    if db.query(CreditBatch).filter(func.lower(CreditBatch.serial_start) == serial.casefold()).first():
        raise HTTPException(409, detail={"code": "duplicate_serial", "message": "This serial already exists in the local workspace."})
    batch_code = body.batch_code or identifier("BATCH-DEMO")
    if db.query(CreditBatch).filter_by(batch_code=batch_code).first():
        raise HTTPException(409, detail={"code": "duplicate_batch_code", "message": "Batch code is already in use."})
    batch = CreditBatch(
        id=batch_code, batch_code=batch_code, project_id=project.id,
        registry_name=body.registry_name or project.registry_name, registry_batch_ref=body.registry_batch_ref,
        serial_start=serial, serial_end=body.serial_end, quantity_kg_co2e=body.quantity_kg_co2e,
        available_balance_kg=0, retired_balance_kg=0,
        vintage_start=body.vintage_start.isoformat() if body.vintage_start else project.vintage_start,
        vintage_end=body.vintage_end.isoformat() if body.vintage_end else project.vintage_end,
        methodology_id=body.methodology_id or project.methodology_id, state="Draft", is_demo=True,
        score_components=json.dumps({"M":50,"V":50,"C":50,"R":50,"A":50}),
    )
    db.add(batch)
    db.flush()
    update_score(db, batch, "Batch draft created with missing issuance and review data")
    append_event(db, user, project.id, "BATCH_CREATED", "Draft batch created; not issued or certified.", batch_id=batch.id, from_state=None, to_state="Draft")
    db.commit()
    return batch_dict(batch)


@app.post("/api/batches/{batch_id}/submit")
def submit_batch(batch_id: str, body: ReasonRequest, db: Session = Depends(get_db), user: Profile = Depends(current_user)):
    batch = owned_batch(db, batch_id, user)
    if batch.state != "Draft":
        raise HTTPException(409, detail={"code": "invalid_transition", "message": "Only Draft batches can be submitted."})
    previous = batch.state
    batch.state = "Submitted"
    db.add(Review(
        id=identifier("REV"), credit_batch_id=batch.id,
        finding="Credit batch submitted for human review.", reviewer_id=user.id,
        decision="pending", reason="Submission awaits an authorized reviewer decision.", is_demo=True,
    ))
    update_score(db, batch, "Batch submitted for human review")
    append_event(db, user, batch.project_id, "BATCH_SUBMITTED", body.reason, batch_id=batch.id, from_state=previous, to_state=batch.state)
    db.commit()
    return batch_dict(batch)


@app.post("/api/batches/{batch_id}/review", status_code=201)
def review_batch(batch_id: str, body: BatchReviewRequest, db: Session = Depends(get_db), user: Profile = Depends(require_role("reviewer", "admin"))):
    batch = owned_batch(db, batch_id, user)
    if batch.state not in {"Draft", "Submitted", "Under Review", "Conflict Detected", "At Risk", "Evidence Needed"}:
        raise HTTPException(409, detail={"code": "invalid_transition", "message": "Batch is not in a reviewable state."})
    conflict_serials = {x["serial"].casefold() for x in find_conflicts(db, user)}
    if body.decision == "approved" and batch.serial_start.casefold() in conflict_serials:
        raise HTTPException(409, detail={"code": "unresolved_conflict", "message": "Resolve or document an authorized conflict decision before approval."})
    previous = batch.state
    batch.state = {"approved":"Verified by Reviewer", "rejected":"Review Rejected", "needs_more_evidence":"Evidence Needed"}[body.decision]
    pending = db.query(Review).filter(Review.credit_batch_id == batch.id, Review.decision == "pending").order_by(Review.created_at.asc()).first()
    if pending:
        pending.decision = body.decision
        pending.reason = body.reason
        pending.reviewed_at = utcnow()
    else:
        db.add(Review(id=identifier("REV"), credit_batch_id=batch.id, finding="Credit batch review decision", reviewer_id=user.id, decision=body.decision, reason=body.reason, is_demo=True, reviewed_at=utcnow()))
    if body.decision == "approved":
        components = json_value(batch.score_components, {"M":50,"V":50,"C":50,"R":50,"A":50})
        components["V"] = max(int(components.get("V", 50)), 65)
        batch.score_components = json.dumps(components)
    update_score(db, batch, f"Human review decision: {body.decision}")
    append_event(db, user, batch.project_id, "REVIEW_DECISION", body.reason, batch_id=batch.id, from_state=previous, to_state=batch.state)
    db.commit()
    return {"batch": batch_dict(batch), "decision": body.decision, "reason": body.reason, "reviewer_id": user.id}


@app.post("/api/batches/{batch_id}/issue")
def issue_batch(batch_id: str, body: ReasonRequest, db: Session = Depends(get_db), user: Profile = Depends(require_role("issuer", "admin"))):
    batch = owned_batch(db, batch_id, user)
    if batch.state != "Verified by Reviewer":
        raise HTTPException(409, detail={"code": "review_required", "message": "Issuance requires an authorized reviewer decision."})
    if any(x["serial"].casefold() == batch.serial_start.casefold() for x in find_conflicts(db, user)):
        raise HTTPException(409, detail={"code": "unresolved_conflict", "message": "Issuance is blocked by a potential duplicate in imported records."})
    client = X1ChainClient()
    receipt = None
    if client.settings.contract_address:
        try:
            contract = client.contract()
            project_key = Web3.keccak(text=batch.project_id)
            try:
                contract.functions.getProject(project_key).call()
            except Exception as exc:
                raise HTTPException(409, detail={"code": "project_not_registered", "message": "Register this project on X1 before issuing its batch."}) from exc
            batch_key = Web3.keccak(text=batch.id)
            try:
                contract.functions.getCreditBatch(batch_key).call()
                raise HTTPException(409, detail={"code": "batch_already_issued", "message": "This batch identifier already exists on the X1 contract."})
            except HTTPException:
                raise
            except Exception:
                pass
            project_evidence = db.query(EvidenceFile).filter(EvidenceFile.project_id == batch.project_id).order_by(EvidenceFile.created_at.desc()).first()
            evidence_ref = bytes.fromhex(project_evidence.sha256) if project_evidence else Web3.keccak(text=f"VERICARB-BATCH-REF:{batch.id}")
            signer = client.role_account("registrar")
            function = contract.functions.registerCreditBatch(batch_key, project_key, Web3.to_checksum_address(signer.address), batch.quantity_kg_co2e, evidence_ref)
            receipt = client.send_contract_transaction("registrar", function)
            chain_batch = contract.functions.getCreditBatch(batch_key).call()
            if int(chain_batch[1]) != batch.quantity_kg_co2e or int(contract.functions.balances(batch_key, signer.address).call()) != batch.quantity_kg_co2e:
                raise X1NetworkError("The confirmed transaction did not produce the expected credit batch state.")
        except HTTPException:
            raise
        except X1ConfigurationError as exc:
            raise HTTPException(409, detail={"code": "x1_not_ready", "message": str(exc)}) from exc
        except Exception as exc:
            raise HTTPException(502, detail={"code": "x1_transaction_failed", "message": f"Credit issuance was not confirmed: {type(exc).__name__}."}) from exc
    previous = batch.state
    batch.available_balance_kg = batch.quantity_kg_co2e
    batch.state = "Active"
    if receipt:
        batch.chain_id = 10778
        batch.contract_address = receipt["contract_address"]
        batch.tx_hash = receipt["transaction_hash"]
    update_score(db, batch, "Confirmed X1 registry issuance" if receipt else "Local demo issuance; no chain transaction is configured")
    event = append_event(db, user, batch.project_id, "BATCH_ISSUED_ON_CHAIN" if receipt else "BATCH_ISSUED_LOCAL_DEMO", body.reason, batch_id=batch.id, from_state=previous, to_state=batch.state, quantity=batch.quantity_kg_co2e, is_demo=not bool(receipt))
    if receipt:
        event.chain_id, event.tx_hash, event.block_number = 10778, receipt["transaction_hash"], receipt["block_number"]
    db.commit()
    return {**batch_dict(batch), "transaction": ({"status": "confirmed", "tx_hash": receipt["transaction_hash"], "chain_id": 10778, "block_number": receipt["block_number"]} if receipt else {"status": "not_configured", "tx_hash": None, "message": "No blockchain transaction was sent."})}


@app.post("/api/batches/{batch_id}/transfer")
def transfer_batch(batch_id: str, body: TransferRequest, db: Session = Depends(get_db), user: Profile = Depends(require_role("issuer", "admin"))):
    batch = owned_batch(db, batch_id, user)
    if batch.state != "Active":
        raise HTTPException(409, detail={"code": "invalid_batch_state", "message": "Only Active, non-risk batches can transfer."})
    if body.quantity_kg_co2e > batch.available_balance_kg:
        raise HTTPException(409, detail={"code": "insufficient_balance", "message": "Transfer exceeds the available balance."})
    previous = batch.state
    batch.available_balance_kg -= body.quantity_kg_co2e
    if batch.available_balance_kg == 0:
        batch.state = "Transferred"
    append_event(db, user, batch.project_id, "CREDIT_TRANSFERRED_LOCAL_DEMO", f"{body.reason} Recipient reference: {body.recipient_ref}. No external transfer occurred.", batch_id=batch.id, from_state=previous, to_state=batch.state, quantity=body.quantity_kg_co2e)
    db.commit()
    return {**batch_dict(batch), "transaction": {"status": "not_configured", "tx_hash": None}}


@app.post("/api/batches/{batch_id}/retire")
def retire_batch(batch_id: str, body: RetireRequest, db: Session = Depends(get_db), user: Profile = Depends(require_role("issuer", "admin"))):
    batch = owned_batch(db, batch_id, user)
    if batch.state != "Active":
        raise HTTPException(409, detail={"code": "invalid_batch_state", "message": "Only Active, non-risk batches can be retired."})
    if body.quantity_kg_co2e > batch.available_balance_kg:
        raise HTTPException(409, detail={"code": "insufficient_balance", "message": "Retirement exceeds the available balance."})
    previous = batch.state
    batch.available_balance_kg -= body.quantity_kg_co2e
    batch.retired_balance_kg += body.quantity_kg_co2e
    if batch.available_balance_kg == 0:
        batch.state = "Retired"
    append_event(db, user, batch.project_id, "CREDIT_RETIRED_LOCAL_DEMO", f"{body.reason} Beneficiary: {body.beneficiary}. Purpose: {body.purpose}. No external registry retirement occurred.", batch_id=batch.id, from_state=previous, to_state=batch.state, quantity=body.quantity_kg_co2e)
    db.commit()
    return {**batch_dict(batch), "transaction": {"status": "not_configured", "tx_hash": None}}


@app.get("/api/batches")
def list_batches(db: Session = Depends(get_db), user: Profile = Depends(current_user)):
    rows = db.query(CreditBatch).join(Project).filter(Project.created_by == user.id).order_by(CreditBatch.updated_at.desc()).all()
    return {"items": [batch_dict(x) for x in rows], "is_demo": True}


@app.get("/api/batches/{batch_id}")
def get_batch(batch_id: str, db: Session = Depends(get_db), user: Profile = Depends(current_user)):
    batch = owned_batch(db, batch_id, user)
    return batch_dict(batch)


@app.get("/api/batches/{batch_id}/events")
def list_batch_events(batch_id: str, db: Session = Depends(get_db), user: Profile = Depends(current_user)):
    owned_batch(db, batch_id, user)
    events = db.query(CreditEvent).filter(CreditEvent.credit_batch_id == batch_id).order_by(CreditEvent.created_at.desc()).all()
    return {"items": [event_dict(x) for x in events]}


@app.get("/api/batches/{batch_id}/integrity")
def get_integrity(batch_id: str, db: Session = Depends(get_db), user: Profile = Depends(current_user)):
    batch = owned_batch(db, batch_id, user)
    history = db.query(IntegrityScore).filter(IntegrityScore.credit_batch_id == batch.id).order_by(IntegrityScore.calculated_at.desc()).all()
    return {"batch_id": batch.id, "score": batch.score, "components": json_value(batch.score_components, {}), "weights": WEIGHTS, "missing_data_flags": json_value(batch.score_missing_flags, []), "calculated_at": iso(batch.score_calculated_at), "is_provisional": True, "history": [{"score": x.score_total, "calculated_at": iso(x.calculated_at), "reason": json_value(x.explanation_json, {}).get("reason")} for x in history]}


@app.post("/api/projects/{project_id}/monitoring-observations", status_code=201)
def add_observation(project_id: str, body: ObservationCreate, db: Session = Depends(get_db), user: Profile = Depends(current_user)):
    project = owned_project(db, project_id, user)
    if body.evidence_file_id:
        evidence = db.get(EvidenceFile, body.evidence_file_id)
        if not evidence or evidence.project_id != project.id:
            raise HTTPException(422, detail={"code": "evidence_project_mismatch", "message": "Evidence must belong to the selected project."})
    observation = MonitoringObservation(
        id=identifier("OBS"), project_id=project.id, source_name=body.source_name,
        signal_type=body.signal_type, severity=body.severity,
        affected_area_percent=body.affected_area_percent, observed_at=body.observed_at,
        evidence_file_id=body.evidence_file_id, evidence_hash=body.evidence_hash,
        is_synthetic=body.is_synthetic, raw_payload_json=json.dumps({"description": body.description}),
        review_state="Needs human review",
    )
    db.add(observation)
    append_event(db, user, project.id, "MONITORING_OBSERVATION_ADDED", body.description, evidence_hash=body.evidence_hash)
    db.flush()
    db.commit()
    return observation_dict(observation)


@app.get("/api/monitoring-observations")
def list_observations(db: Session = Depends(get_db), user: Profile = Depends(current_user)):
    rows = db.query(MonitoringObservation).join(Project).filter(Project.created_by == user.id).order_by(MonitoringObservation.observed_at.desc()).all()
    return {"items": [observation_dict(x) for x in rows]}


@app.post("/api/monitoring-observations/{observation_id}/evaluate")
def evaluate_observation(observation_id: str, body: ReasonRequest, db: Session = Depends(get_db), user: Profile = Depends(current_user)):
    observation = db.get(MonitoringObservation, observation_id)
    if not observation:
        raise HTTPException(404, detail={"code": "observation_not_found", "message": "Monitoring observation was not found."})
    project = owned_project(db, observation.project_id, user)
    if observation.severity not in {"high", "critical"}:
        return {"observation": observation_dict(observation), "alert": None, "evaluation": "No alert threshold met; rule configuration is a prototype assumption."}
    alert = Alert(
        id=identifier("ALT"), project_id=project.id, observation_id=observation.id,
        alert_type="Potential environmental risk", severity="At Risk",
        explanation=f"{observation.severity.title()} {observation.signal_type} signal requires human review. This is not proof of reversal.",
        state="Open", is_demo=True,
    )
    db.add(alert)
    previous = project.status
    project.status = "At Risk"
    observation.review_state = "Alert opened"
    batches = db.query(CreditBatch).filter(CreditBatch.project_id == project.id, CreditBatch.state == "Active").all()
    for batch in batches:
        batch.state = "At Risk"
        components = json_value(batch.score_components, {"M":50,"V":50,"C":50,"R":50,"A":50})
        components["R"] = min(int(components.get("R", 50)), 30)
        batch.score_components = json.dumps(components)
        update_score(db, batch, "Synthetic or configured high-severity signal; reviewer action required")
    append_event(db, user, project.id, "CREDIT_AT_RISK", body.reason, from_state=previous, to_state=project.status)
    db.commit()
    return {"observation": observation_dict(observation), "alert": {"id": alert.id, "state": alert.state, "severity": alert.severity, "is_demo": alert.is_demo}, "evaluation": "Rule-created review alert; no reversal was confirmed."}


@app.get("/api/alerts")
def list_alerts(db: Session = Depends(get_db), user: Profile = Depends(current_user)):
    rows = db.query(Alert).join(Project).filter(Project.created_by == user.id).order_by(Alert.created_at.desc()).all()
    return {"items": [{"id": x.id, "project_id": x.project_id, "observation_id": x.observation_id, "type": x.alert_type, "severity": x.severity, "explanation": x.explanation, "state": x.state, "assigned_reviewer": x.assigned_reviewer, "decision": x.decision, "created_at": iso(x.created_at), "reviewed_at": iso(x.reviewed_at), "is_demo": x.is_demo} for x in rows]}


@app.post("/api/alerts/{alert_id}/review", status_code=201)
def review_alert(alert_id: str, body: AlertReviewRequest, db: Session = Depends(get_db), user: Profile = Depends(require_role("reviewer", "admin"))):
    alert = db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(404, detail={"code": "alert_not_found", "message": "Alert was not found."})
    owned_project(db, alert.project_id, user)
    if alert.state != "Open":
        raise HTTPException(409, detail={"code": "alert_already_reviewed", "message": "This alert already has a reviewer decision."})
    alert.assigned_reviewer = user.id
    alert.decision = body.decision
    alert.decision_reason = body.reason
    alert.reviewed_at = utcnow()
    alert.state = "Reviewed"
    observation = db.get(MonitoringObservation, alert.observation_id) if alert.observation_id else None
    if observation:
        observation.review_state = "Reviewer decision recorded"
    pending = db.query(Review).filter(Review.alert_id == alert.id, Review.decision == "pending").order_by(Review.created_at.asc()).first()
    if pending:
        pending.decision = body.decision
        pending.reason = body.reason
        pending.reviewed_at = utcnow()
    else:
        db.add(Review(id=identifier("REV"), alert_id=alert.id, finding=alert.alert_type, reviewer_id=user.id, decision=body.decision, reason=body.reason, is_demo=True, reviewed_at=utcnow()))
    event_type = "REVERSAL_CONFIRMED" if body.decision == "alert_confirmed" else "REVERSAL_REJECTED" if body.decision == "alert_rejected" else "REVIEW_OPENED"
    append_event(db, user, alert.project_id, event_type, f"{body.decision}: {body.reason}. Original observation and retirement history are preserved.")
    if body.decision in {"alert_confirmed", "alert_rejected"}:
        project_batches = db.query(CreditBatch).filter(CreditBatch.project_id == alert.project_id, CreditBatch.state == "At Risk").all()
        for batch in project_batches:
            previous = batch.state
            batch.state = "Reversed" if body.decision == "alert_confirmed" else ("Retired" if batch.available_balance_kg == 0 else "Active")
            components = json_value(batch.score_components, {"M":50,"V":50,"C":50,"R":50,"A":50})
            if body.decision == "alert_rejected": components["R"] = min(100, int(components.get("R", 50)) + 25)
            batch.score_components = json.dumps(components)
            update_score(db, batch, f"Human reviewer decision: {body.decision}; historical balances retained")
            append_event(db, user, alert.project_id, event_type, body.reason, batch_id=batch.id, from_state=previous, to_state=batch.state)
    db.commit()
    return {"id": alert.id, "state": alert.state, "decision": alert.decision, "decision_reason": alert.decision_reason, "reviewer_id": user.id, "reviewed_at": iso(alert.reviewed_at), "is_demo": alert.is_demo}


@app.get("/api/public/verify/{batch_code}")
def public_verify(batch_code: str, db: Session = Depends(get_db)):
    batch = db.query(CreditBatch).filter(CreditBatch.batch_code == batch_code).first()
    if not batch:
        raise HTTPException(404, detail={"code": "batch_not_found", "message": "No public record matches this batch code."})
    project = db.get(Project, batch.project_id)
    events = db.query(CreditEvent).filter(CreditEvent.credit_batch_id == batch.id).order_by(CreditEvent.created_at.asc()).all()
    alerts = db.query(Alert).filter(Alert.project_id == project.id, Alert.is_demo == batch.is_demo).all()
    public_evidence = db.query(EvidenceFile).filter(EvidenceFile.project_id == project.id, EvidenceFile.is_demo == batch.is_demo).order_by(EvidenceFile.created_at.asc()).all()
    chain_settings = X1ChainClient().settings
    return {
        "is_demo": batch.is_demo, "disclaimer": "This record does not certify credits or guarantee a climate outcome.",
        "project": {"id": project.id, "name": project.name, "project_type": project.project_type, "country": project.country, "region": project.region, "status": project.status, "chain_project_id": project.chain_project_id, "chain_id": project.chain_id, "contract_address": project.contract_address, "tx_hash": project.tx_hash, "is_demo": project.is_demo},
        "batch": {"batch_code": batch.batch_code, "serial_start": batch.serial_start, "vintage_start": batch.vintage_start, "vintage_end": batch.vintage_end, "quantity_kg_co2e": batch.quantity_kg_co2e, "available_balance_kg": batch.available_balance_kg, "retired_balance_kg": batch.retired_balance_kg, "state": batch.state, "registry_name": batch.registry_name, "integrity_score": batch.score, "score_components": json_value(batch.score_components, {}), "score_missing_flags": json_value(batch.score_missing_flags, []), "score_calculated_at": iso(batch.score_calculated_at), "chain_id": batch.chain_id, "contract_address": batch.contract_address, "tx_hash": batch.tx_hash, "is_demo": batch.is_demo},
        "chain": {"network": "X1 EcoChain Testnet (Maculatus)", "chain_id": project.chain_id or batch.chain_id, "explorer_url": chain_settings.explorer_url, "contract_address": project.contract_address or batch.contract_address, "project_tx_hash": project.tx_hash},
        "events": [{"event_type": e.event_type, "from_state": e.from_state, "to_state": e.to_state, "quantity_kg_co2e": e.quantity_kg_co2e, "evidence_hash": e.evidence_hash, "chain_id": e.chain_id, "tx_hash": e.tx_hash, "block_number": e.block_number, "created_at": iso(e.created_at), "is_demo": e.is_demo} for e in events],
        "public_evidence": [{"evidence_type": e.evidence_type, "sha256": e.sha256, "review_state": e.review_state, "anchor_chain_id": e.anchor_chain_id, "anchor_contract_address": e.anchor_contract_address, "anchor_tx_hash": e.anchor_tx_hash, "anchor_block_number": e.anchor_block_number, "created_at": iso(e.created_at), "is_demo": e.is_demo} for e in public_evidence],
        "alerts": [{"type": a.alert_type, "severity": a.severity, "state": a.state, "decision": a.decision, "created_at": iso(a.created_at), "reviewed_at": iso(a.reviewed_at), "is_demo": a.is_demo} for a in alerts],
        "source_coverage": "Imported records only; external registry coverage has not been verified.",
    }


@app.get("/api/claims")
def list_claims(db: Session = Depends(get_db), user: Profile = Depends(current_user)):
    rows = db.query(Claim).filter(Claim.created_by == user.id).order_by(Claim.created_at.desc()).all()
    return {"items": [{"id": x.id, "credit_batch_id": x.credit_batch_id, "claimant_entity": x.claimant_entity, "claim_purpose": x.claim_purpose, "target_framework": x.target_framework, "claim_status": x.claim_status, "authorization_status": x.authorization_status, "corresponding_adjustment_status": x.corresponding_adjustment_status, "evidence_hash": x.evidence_hash, "is_demo": x.is_demo, "created_at": iso(x.created_at)} for x in rows]}


@app.post("/api/claims", status_code=201)
def create_claim(body: ClaimCreate, db: Session = Depends(get_db), user: Profile = Depends(current_user)):
    batch = owned_batch(db, body.credit_batch_id, user)
    row = Claim(id=identifier("CLM"), credit_batch_id=batch.id, claimant_entity=body.claimant_entity, claim_purpose=body.claim_purpose, target_framework=body.target_framework, claim_status="draft", external_claim_ref=body.external_claim_ref, authorization_status=body.authorization_status, corresponding_adjustment_status=body.corresponding_adjustment_status, evidence_hash=body.evidence_hash, is_demo=True, created_by=user.id)
    db.add(row)
    append_event(db, user, batch.project_id, "CLAIM_CREATED", "Draft claim created; no external authorization or compliance determination.", batch_id=batch.id, evidence_hash=body.evidence_hash)
    db.commit()
    return {"id": row.id, "credit_batch_id": row.credit_batch_id, "claim_status": row.claim_status, "is_demo": row.is_demo}


@app.get("/api/admin/data-sources")
def data_sources(_user: Profile = Depends(current_user)):
    return {"items": [
        {"id":"database","name":"Application database","state":"Local SQLite","configured":True,"is_demo":True},
        {"id":"file_storage","name":"Evidence storage","state":"Local disk storage","configured":True,"is_demo":True},
        {"id":"ai","name":"AI provider","state":"Not configured; deterministic fallback only","configured":False,"is_demo":True},
        {"id":"registry","name":"External registry APIs","state":"Not connected; imported CSV only","configured":False,"is_demo":True},
        {"id":"monitoring","name":"Satellite / IoT providers","state":"Not connected; synthetic fixtures only","configured":False,"is_demo":True},
        {"id":"chain","name":"EVM chain","state":"Not configured","configured":False,"is_demo":True},
        {"id":"wallet","name":"Wallet","state":"Not connected","configured":False,"is_demo":True},
    ]}


@app.get("/api/events")
def list_events(project_id: str | None = None, batch_id: str | None = None, limit: int = 100, db: Session = Depends(get_db), user: Profile = Depends(current_user)):
    limit = max(1, min(limit, 500))
    query = db.query(CreditEvent).join(Project).filter(Project.created_by == user.id)
    if project_id:
        owned_project(db, project_id, user)
        query = query.filter(CreditEvent.project_id == project_id)
    if batch_id:
        owned_batch(db, batch_id, user)
        query = query.filter(CreditEvent.credit_batch_id == batch_id)
    rows = query.order_by(CreditEvent.created_at.desc()).limit(limit).all()
    return {"items": [event_dict(x) for x in rows]}


@app.get("/api/projects/{project_id}/monitoring-observations")
def project_observations(project_id: str, db: Session = Depends(get_db), user: Profile = Depends(current_user)):
    project = owned_project(db, project_id, user)
    rows = db.query(MonitoringObservation).filter(MonitoringObservation.project_id == project.id).order_by(MonitoringObservation.observed_at.desc()).all()
    return {"items": [observation_dict(x) for x in rows]}


@app.get("/api/registry/records")
def list_registry_records(db: Session = Depends(get_db), user: Profile = Depends(current_user)):
    rows = db.query(RegistryRecord).filter(RegistryRecord.imported_by == user.id).order_by(RegistryRecord.created_at.desc()).all()
    return {"items": [{"id": x.id, "source_name": x.source_name, "external_project_id": x.external_project_id, "external_project_name": x.external_project_name, "external_serial": x.external_serial, "vintage_start": x.vintage_start, "vintage_end": x.vintage_end, "methodology_id": x.methodology_id, "country": x.country, "region": x.region, "quantity_kg_co2e": x.quantity_kg_co2e, "status": x.status, "source_timestamp": x.source_timestamp, "is_demo": x.is_demo} for x in rows]}


def observation_seed_check() -> None:
    """Keep startup import surface explicit for API discovery and app lifecycle."""


# The API and the plain HTML app share one local origin; API routes are registered before static files.
app.mount("/", StaticFiles(directory=str(ROOT_DIR / "frontend"), html=True), name="workspace")

