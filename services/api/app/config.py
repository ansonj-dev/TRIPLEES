from __future__ import annotations

import os
import secrets
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[3]
load_dotenv(ROOT_DIR / ".env")
DATA_DIR = Path(os.getenv("VERICARB_DATA_DIR", ROOT_DIR / "data")).resolve()
UPLOAD_DIR = DATA_DIR / "evidence"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{(DATA_DIR / 'vericarb.sqlite3').as_posix()}")
SQLALCHEMY_DATABASE_URL = DATABASE_URL
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = "postgresql+psycopg://" + SQLALCHEMY_DATABASE_URL.removeprefix("postgres://")
elif SQLALCHEMY_DATABASE_URL.startswith("postgresql://"):
    SQLALCHEMY_DATABASE_URL = "postgresql+psycopg://" + SQLALCHEMY_DATABASE_URL.removeprefix("postgresql://")
APP_ENV = os.getenv("APP_ENV", "development").lower()
PRODUCTION_AUTH_SUPPORTED = False
_configured_token_secret = os.getenv("VERICARB_TOKEN_SECRET", "").strip()
if APP_ENV == "production" and len(_configured_token_secret) < 32:
    raise RuntimeError("Production requires VERICARB_TOKEN_SECRET with at least 32 characters.")
TOKEN_SECRET = _configured_token_secret or secrets.token_urlsafe(48)
TOKEN_TTL_SECONDS = int(os.getenv("TOKEN_TTL_SECONDS", "28800"))
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(10 * 1024 * 1024)))
MAX_EXTRACTED_CHARS = max(10_000, min(int(os.getenv("MAX_EXTRACTED_CHARS", "500000")), 2_000_000))
ALLOWED_ORIGINS = [x.strip() for x in os.getenv("CORS_ORIGINS", "" if APP_ENV == "production" else "http://localhost:8000,http://127.0.0.1:8000").split(",") if x.strip()]
AUTO_MIGRATE = os.getenv("AUTO_MIGRATE", "false" if APP_ENV == "production" else "true").lower() in {"1", "true", "yes"}
SEED_DEMO_DATA = os.getenv("SEED_DEMO_DATA", "false" if APP_ENV == "production" else "true").lower() in {"1", "true", "yes"}
DB_POOL_SIZE = max(1, int(os.getenv("DB_POOL_SIZE", "5")))
DB_MAX_OVERFLOW = max(0, int(os.getenv("DB_MAX_OVERFLOW", "10")))
DB_POOL_RECYCLE_SECONDS = max(60, int(os.getenv("DB_POOL_RECYCLE_SECONDS", "1800")))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
OBJECT_STORAGE_BUCKET = os.getenv("OBJECT_STORAGE_BUCKET", "").strip()
OBJECT_STORAGE_REGION = os.getenv("OBJECT_STORAGE_REGION", "").strip() or None
OBJECT_STORAGE_ENDPOINT_URL = os.getenv("OBJECT_STORAGE_ENDPOINT_URL", "").strip() or None
OBJECT_STORAGE_PREFIX = os.getenv("OBJECT_STORAGE_PREFIX", "evidence").strip("/")
if APP_ENV == "production":
    if not (DATABASE_URL.startswith("postgresql://") or DATABASE_URL.startswith("postgresql+psycopg://") or DATABASE_URL.startswith("postgres://")):
        raise RuntimeError("Production requires DATABASE_URL to point to PostgreSQL.")
    if not OBJECT_STORAGE_BUCKET:
        raise RuntimeError("Production requires OBJECT_STORAGE_BUCKET for durable evidence storage.")
    if not ALLOWED_ORIGINS:
        raise RuntimeError("Production requires explicit CORS_ORIGINS.")
    if AUTO_MIGRATE:
        raise RuntimeError("Production requires AUTO_MIGRATE=false; run Alembic as a controlled release step.")
    if SEED_DEMO_DATA:
        raise RuntimeError("Production requires SEED_DEMO_DATA=false.")
AI_PROVIDER = os.getenv("AI_PROVIDER", "nebius_token_factory").strip().lower()
NEBIUS_API_KEY = os.getenv("NEBIUS_API_KEY", "").strip()
NEBIUS_BASE_URL = os.getenv("NEBIUS_BASE_URL", "https://api.tokenfactory.nebius.com/v1").rstrip("/")
NEBIUS_MODEL = os.getenv("NEBIUS_MODEL", "nvidia/nemotron-3-super-120b-a12b").strip()
NEBIUS_CONNECT_TIMEOUT_SECONDS = float(os.getenv("NEBIUS_CONNECT_TIMEOUT_SECONDS", "5"))
NEBIUS_READ_TIMEOUT_SECONDS = float(os.getenv("NEBIUS_READ_TIMEOUT_SECONDS", "60"))
NEBIUS_MAX_RETRIES = max(0, min(int(os.getenv("NEBIUS_MAX_RETRIES", "2")), 4))
AI_MAX_COMPLETION_TOKENS = max(64, min(int(os.getenv("AI_MAX_COMPLETION_TOKENS", "1800")), 8192))
AI_DAILY_TOKEN_LIMIT = max(0, int(os.getenv("AI_DAILY_TOKEN_LIMIT", "100000")))
AI_INPUT_COST_PER_MILLION_USD = os.getenv("AI_INPUT_COST_PER_MILLION_USD", "").strip()
AI_OUTPUT_COST_PER_MILLION_USD = os.getenv("AI_OUTPUT_COST_PER_MILLION_USD", "").strip()

if not OBJECT_STORAGE_BUCKET:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

