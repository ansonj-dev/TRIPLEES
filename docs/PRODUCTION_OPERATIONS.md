# Production operations and deployment readiness

This document records the Phase 8 operating configuration. No service was deployed. The application is not yet approved for production traffic because authentication is still the local prototype system; production startup intentionally fails closed until an external identity provider and session controls are integrated.

## PostgreSQL and object storage

`DATABASE_URL` accepts PostgreSQL URLs (`postgresql://`, `postgres://`, or `postgresql+psycopg://`). The API uses psycopg 3, SQLAlchemy connection pre-ping, and configurable pool settings. SQLite remains the default for local development.

Evidence storage uses local `data/evidence/` when `OBJECT_STORAGE_BUCKET` is empty. Set a bucket to use S3-compatible storage. `OBJECT_STORAGE_ENDPOINT_URL` supports providers such as MinIO; leave it empty for AWS. The worker and API must use the same bucket, region, endpoint, prefix, and platform identity. Grant only the required bucket object read/write/delete permissions and bucket health-check permission. The API hashes evidence before storage and verifies SHA-256 again on extraction and download. Evidence contents remain off-chain.

## Application and worker processes

Run the API and worker as separate services against the same PostgreSQL database and object store:

```powershell
uvicorn services.api.app.main:app --host 0.0.0.0 --port 8000
python -m services.api.worker --poll-seconds 2
```

The worker handles SIGTERM/SIGINT, checks queued investigations, and recovers expired leases. Run one worker process per deployment initially; increase concurrency only after measuring database locks, provider quotas, and lease behavior. Set the same `NEBIUS_*`, database, and storage variables on both services. Configure platform health checks to use `/readyz`; `/health` is a process liveness check and does not test dependencies. Readiness checks PostgreSQL and evidence storage without contacting X1.

Controlled release sequence:

1. Build and review the exact application artifact.
2. Run `python -m alembic -c alembic.ini upgrade head` as a one-off release step.
3. Start the API with `AUTO_MIGRATE=false` and `SEED_DEMO_DATA=false`.
4. Start the worker with the same database and storage settings.
5. Confirm `/readyz`, worker logs, and a staging end-to-end evidence/investigation flow.

Production settings require PostgreSQL, a durable object bucket, an explicit `CORS_ORIGINS` allowlist, a 32-character minimum `VERICARB_TOKEN_SECRET`, migrations disabled at API startup, and demo seeding disabled. The current production startup guard still refuses to run because prototype sign-in, account creation, and token/session handling are not a production identity system. Do not remove that guard by setting an environment variable; integrate and review the identity provider first.

## Security and limits

- `/api/auth/demo` and `/api/demo/reset` are unavailable in production; sign-up is rejected there.
- API docs and OpenAPI are disabled in production mode.
- Request logs are JSON and include request ID, method, path, status, and duration. They omit headers, query strings, bodies, tokens, and uploaded content. Send logs to the platform log sink and alert on 5xx rates, worker crash/lease events, database readiness failures, and object storage failures.
- AI calls require per-investigation consent and budget. `AI_DAILY_TOKEN_LIMIT` sets an additional per-user rolling 24-hour token ceiling; `0` disables the daily ceiling. Upload size is bounded by `MAX_UPLOAD_BYTES`; extraction is bounded by `MAX_EXTRACTED_CHARS`.
- The daily AI limit checks persisted usage before each provider call. Keep one worker process until token reservations are added; multiple workers could check the same remaining allowance concurrently.
- Keep wallet private keys and provider credentials in the platform secret manager. The API worker does not sign X1 transactions for investigations. Do not set X1 transaction keys on the worker unless a separately reviewed human-operated blockchain workflow requires them.

## Backup and restore

Keep PostgreSQL backups and object-store backups/versioning under the same retention policy. Record a backup timestamp and PostgreSQL point-in-time or snapshot identifier alongside the object-store versioning/snapshot state. Restoring only the database can leave evidence references without bytes; restoring only the bucket can leave unreferenced objects. Restore both to a consistent point, then verify representative evidence SHA-256 values.

Example PostgreSQL logical backup and restore (replace placeholders in a secure shell; never put credentials in command history):

```powershell
pg_dump --format=custom --no-owner --file=triplees.dump "$env:DATABASE_URL"
pg_restore --clean --if-exists --no-owner --dbname="$env:RESTORE_DATABASE_URL" triplees.dump
```

For AWS S3, enable bucket versioning and lifecycle retention. For S3-compatible providers, use their equivalent versioning or scheduled immutable backup process. Test a restore in an isolated environment at least once before production approval. After restore, run Alembic head checks, `/readyz`, integrity checks, and the staging smoke workflow before routing traffic.

## Deployment gate

Phase 8 produced deployment instructions and configuration safeguards only. It did not deploy an API, worker, database, or bucket; publish the application; run migrations against a remote database; or submit an X1 transaction. Deployment remains blocked until production authentication is integrated and the production end-to-end review is approved.
