# TRIPLEES Phase 0 — Repository Audit and Implementation Roadmap

Date: 2026-10-30 (UTC)

## Purpose

This document records the initial audit of the attached VERICARB codebase, which is the starting point for TRIPLEES. The architecture follows the referenced hackathon conversation: extend the existing application with an evidence-grounded, multi-agent carbon integrity investigation workflow while preserving the current product, database history, X1 EcoChain integration, and Solidity registry.

The implementation is intentionally gated on review of this audit, as requested in the referenced conversation. No AI feature implementation, database migration, contract change, chain transaction, deployment, Git commit, or GitHub push has been performed in Phase 0.

## Repository inventory

- Static browser application: `frontend/index.html`, `auth.html`, `app.html`, `verify.html`, vanilla JavaScript, CSS, and local SVG assets.
- FastAPI API: `services/api/app/` with route handlers in `main.py`, SQLAlchemy models, Pydantic schemas, authentication, SQLite database setup, integrity scoring, and X1 chain services.
- Database history: Alembic configuration and three existing migration revisions, including the initial schema and X1 chain references.
- Blockchain: `services/contracts/contracts/VericarbRegistry.sol`, Hardhat scripts, contract tests, and testnet operations.
- Supporting material: `docs/`, synthetic data under `sample-data/`, and API/contract dependencies.
- No `.git` directory is present in the attached folder. The target `https://github.com/ansonj-dev/TRIPLEES.git` returned no branch refs from a read-only `git ls-remote` check. The folder is therefore not currently connected to a local Git history or a confirmed remote branch.

## Existing system and boundaries

### Application and data

- The API uses FastAPI, SQLAlchemy, Pydantic, Alembic, and SQLite by default. SQLAlchemy is already the persistence boundary; the application does not use MongoDB today.
- Existing models cover profiles, projects, evidence files, credit batches/events, imported registry records, monitoring observations, alerts, deterministic assessments, reviews, claims, and integrity scores.
- Evidence bytes are stored off-chain and SHA-256 hashed. Current extraction does not read document contents for AI analysis.
- The application already supports project/evidence/batch workflows, imported-record conflict checks, synthetic monitoring examples, human review, public batch verification, and testnet-aware X1 registration/anchoring/issuance.
- Authentication is a custom HMAC-signed bearer token and local password hashing. Demo access is intentionally available for the prototype and is not production identity management.

### AI and investigation capability

- There is no Nebius Token Factory client, Nemotron configuration, provider abstraction, investigation orchestrator, specialized agent, research adapter, document extraction pipeline, investigation persistence, report API, or AI usage accounting.
- `.env.example` contains generic `AI_PROVIDER_API_KEY` and `AI_PROVIDER_BASE_URL` placeholders, but the current application does not use them.
- Current assessments and integrity scores are deterministic heuristic/demo logic. They are explicitly described as advisory and are not evidence of fraud, environmental damage, or credit validity.

### X1 and contract boundary

- The current X1 service supports read-only network/status checks and authorized project registration, evidence anchoring, and batch issuance when configured.
- Transfer, retirement, risk, and review actions in the main app remain local database workflows. The separate contract harness can exercise contract lifecycle methods.
- Existing code and documentation state that report anchoring is not implemented. A report commitment would need a deliberate contract/API design, tests, and explicit human authorization; the AI must never control signing keys or submit transactions independently.
- No chain transaction or deployment operation was run during this audit.

### Database choice to preserve or resolve

The referenced architecture specifies PostgreSQL with Alembic and suggests PostgreSQL full-text search plus pgvector before adding another vector database. The current project defaults to SQLite. MongoDB Atlas was tagged in the request, but the existing application and the referenced architecture do not define a MongoDB data model or migration plan. Phase 0 therefore leaves the persistence choice unchanged; implementation should follow the reviewed architecture decision and must not silently replace existing persistence or migration history.

## Baseline verification

Checks run against the attached folder on 2026-10-30 UTC:

| Check | Result |
| --- | --- |
| `python -m pytest services/api/tests -q` | Passed: 4 tests. One third-party deprecation warning. |
| `node --check` for `app.js`, `auth.js`, `public-verify.js`, and `script.js` | Passed. |
| `python -m compileall -q services/api/app` | Passed. |
| `npm test` from `services/contracts` | Could not run: `hardhat` is not installed in the current checkout (`node_modules` is absent/ignored). No dependency installation was attempted. |
| Git worktree and remote refs | No local Git metadata; the read-only remote query returned no refs. |

The tracked `docs/TEST_REPORT.md` describes older results (2 API tests and a passing Hardhat suite). It does not match this fresh baseline and should be refreshed after dependencies are installed and the contract suite is rerun.

## Documentation inconsistencies found

- `docs/CONTRACTS.md` says the contract is not deployed, while `docs/DEPLOYMENT_AND_VERIFICATION.md` records a confirmed Maculatus testnet deployment and QA flow.
- The README says the deployment and verification are recorded, while its description of new checkouts can be read as if no deployment exists; deployment state is local configuration and must remain explicit.
- The recorded test report predates the current four API tests and the current missing local Hardhat install.
- Existing docs and user-facing copy still brand the product as VERICARB. The requested product name is TRIPLEES; VERICARB should be identified as the former product/codebase name where that context is useful.

These documents should be reconciled as part of the documentation/branding work without claiming a fresh live-chain verification.

## Architecture requirements carried forward from the conversation

1. Keep the existing HTML/CSS/JavaScript frontend and FastAPI application; do not replace the product or framework.
2. Preserve existing API compatibility, data, Alembic migration history, X1 configuration and contract/deployment references.
3. Add a configurable Nebius OpenAI-compatible provider for an NVIDIA Nemotron model. Validate structured output, add timeouts/retries, usage capture, redacted logs, health reporting, and never hardcode model identifiers throughout the application.
4. Build document extraction and evidence-linked claims. Keep original files, extracted content, prompts, and reports off-chain. Treat uploaded files and web pages as untrusted input; never allow their instructions to expand agent permissions.
5. Implement a controlled orchestrator and five specialized roles: Evidence Analyst, Research Agent, Integrity Agent, Monitoring Agent, and adversarial Independent Review Agent. The workflow should be resumable, cancellable, retryable, auditable, and explicit about partial failures.
6. Keep every finding structured with category, severity, evidence IDs, source references, uncertainty/confidence, review status, and recommended next steps. Preserve source URLs and retrieval times; do not fabricate citations or present model suspicions as verified facts.
7. Add durable investigation, execution, findings, sources, extracted claims/evidence links, report versions, usage, and append-only audit records using Alembic migrations.
8. Add `/api/investigations`, run/cancel/status, findings/report, human review, AI health, and usage routes under `/api/`. Long-running runs must not occupy an HTTP request; use a worker/job approach.
9. Add the Intelligence Dashboard, Investigation Center, Agent Activity, Risk Intelligence, Investigation Report, and Human Review Queue while retaining existing projects, evidence, credits, registry, settings, and blockchain activity.
10. Keep humans responsible for material decisions. Any future report anchoring must hash a canonical report, require reviewer approval, use a separately authorized signer, and be verified from a confirmed receipt/state read-back.
11. Do not add separate microservices, a new vector database, token economics, satellite feeds, or unrequested contract scope without evidence that the MVP requires them.
12. Keep synthetic data labeled as synthetic. Never describe AI risk analysis or an on-chain hash as certification or proof of environmental impact.

## Recommended implementation sequence

### Phase 0 — Audit and baseline (current)

Inventory existing routes/models/UI/contracts and trust boundaries; capture baseline checks; reconcile the repo starting state and remote setup; present this audit for review.

### Phase 1 — Nebius/Nemotron foundation

Add a small provider abstraction, environment-based model settings, structured response validation, bounded retry/timeout behavior, redaction, usage records, and an AI health endpoint. Keep a deterministic/offline path for tests and local demo use.

### Phase 2 — Evidence intelligence

Extract text and metadata from supported uploads, preserve source-file hashes, capture claims and source spans, link claims to supporting/conflicting evidence, and add searchable chunks. Reject unsupported file types and enforce size limits. Do not send original sensitive files to public research providers.

### Phase 3 — Specialized analysis agents

Build the five scoped agent services, with structured outputs, source/citation checks, explicit per-run AI and public-research consent, and no arbitrary tools.

### Phase 4 — Persistent investigation lifecycle

Add persisted investigation and agent-execution state, run/cancel/retry/resume behavior, partial failure reporting, append-only audit events, and a database-backed worker.

### Phase 5 — Risk findings and reports

Connect project evidence, imported registry records, and available monitoring observations to structured findings. Add report versioning, limitations, and human review actions.

### Phase 6 — Intelligence workspace

Add the investigation screens and navigation. Keep existing screens available and show evidence, sources, agent status, unresolved items, and human decisions clearly.

### Phase 7 — X1 integration

Only after the prior phases and human approval flow are stable, design report-hash anchoring and connect currently local lifecycle actions where justified. Add contract/API tests and an explicit testnet verification plan before any live transaction.

### Phase 8 — Production hardening

Address tenant isolation, document upload defenses, prompt injection, signer isolation, durable jobs, idempotency, rate and cost limits, observability, production database/object storage, security testing, backup/retention, and deployment documentation.

## Phase 1 — AI foundation (approved and implemented)

The user selected the PostgreSQL direction and approved proceeding. Phase 1 adds the provider foundation while leaving local SQLite development functional:

- Added configurable Nebius Token Factory endpoint, NVIDIA Nemotron model, timeouts, bounded retries, output-token limit, and optional per-million-token rates.
- Added an OpenAI-compatible HTTP client, strict Pydantic structured-output validation, and model identity checks that reject non-Nemotron identifiers.
- Added the `model_usage` Alembic migration, token/latency/cost tracker, authenticated `/api/ai/health` and `/api/ai/usage` routes, and user-scoped usage visibility (workspace-wide for admins).
- Documented setup and limits in `docs/AI_FOUNDATION.md` and the README.
- Added mocked provider, retry, redaction, structured-output, cost, and API authorization tests.

Verification after Phase 1:

| Check | Result |
| --- | --- |
| `python -m pytest services/api/tests -q` | Passed: 11 tests. One existing third-party deprecation warning. |
| `python -m compileall -q services/api/app` | Passed. |
| `node --check` for the four existing frontend JavaScript files | Passed. |
| `python -m alembic -c alembic.ini heads` | Passed; `20261030_model_usage` is the single head. |
| Live Nebius inference | Not run: no API key is configured and no billable inference request was authorized. |
| Contract suite | Not rerun in this phase; Hardhat remains unavailable in the local checkout. |

The AI health endpoint reports configuration only and does not test network reachability. Costs remain unknown until both rate values are configured. GitHub push remains a separate approval gate; no commit or push is included.

## Phase 2 — Evidence/document intelligence (approved and implemented)

The user approved Phase 2. This phase adds local, authenticated evidence extraction and retrieval while keeping SQLite usable:

- Added bounded PDF embedded-text, CSV row, JSON scalar, and UTF-8 text extraction with page/row/JSON-path/line locations.
- Added MIME/extension and basic binary signature checks, JSON validation, stored-file SHA-256 re-verification, extraction status/limitations, bounded chunks, deterministic candidate-claim extraction, and SHA-linked claim/evidence records.
- Added hash-based reuse scoped to the same project, authenticated extraction/chunk APIs, project-scoped lexical search, and pagination.
- Added Alembic migration `20261031_document_intelligence` and the `PyMuPDF` dependency. No OCR, external research, embeddings, or AI claim extraction was added in this phase.
- Documented format limits and candidate-claim semantics in `docs/EVIDENCE_INTELLIGENCE.md` and the README.
- Added tests for PDF, CSV, JSON and TXT source locations, hashing, reuse, upload validation, search, and ownership boundaries.

Verification after Phase 2:

| Check | Result |
| --- | --- |
| `python -m pytest services/api/tests -q` | Passed: 13 tests. One existing third-party deprecation warning. |
| `python -m compileall -q services/api/app` | Passed. |
| `node --check` for the four existing frontend JavaScript files | Passed. |
| `python -m alembic -c alembic.ini heads` | Passed; `20261031_document_intelligence` is the single head. |
| Real Nebius inference | Not run; no credential is configured and no billable request was authorized. |
| Hardhat contract tests | Not rerun; this phase does not change the contract, and Hardhat was unavailable in the local checkout. |

## Phase 3 — Specialized agents (approved and implemented)

The user approved Phase 3. The five agent modules now accept an explicit `AgentContext` and return structured execution results:

- Evidence Analyst inventories extraction results and candidate claims; Nebius analysis requires per-run external-AI authorization.
- Research Investigator has an injected provider interface, reports clearly when research is unavailable, and filters source URLs. No research provider or live search request is configured in this phase.
- Integrity Analyst performs deterministic exact normalized serial and quantity comparisons on supplied records.
- Monitoring Analyst preserves synthetic/real labels and observation sources; it does not claim live satellite or sensor feeds.
- Independent Review Agent checks unsupported sources, missing traceability, and overclaim language, and can make a separate adversarial model call only with explicit per-run authorization.

All AI outputs use strict typed claims/sources/findings. Unknown evidence and source identifiers are removed; affected findings are downgraded to unresolved. Agent code exposes no arbitrary shell, SQL, URL-fetch, or signing tools. The agents are connected to persistent investigations and the worker in Phase 4; investigation screens and report review remain later phases.

Verification after Phase 3:

| Check | Result |
| --- | --- |
| `python -m pytest services/api/tests -q` | Passed: 21 tests, including the new agent tests. One existing third-party deprecation warning. |
| `python -m compileall -q services/api/app` | Passed. |
| `node --check` for the four existing frontend JavaScript files | Passed; no frontend files changed in this phase. |
| `python -m alembic -c alembic.ini heads` | Passed; `20261031_document_intelligence` remains the single head. |
| Live Nebius or public research calls | Not run; no credential/provider is configured and no external request was authorized. |

## Phase 4 — Persistent investigation lifecycle (approved and implemented)

The user approved a PostgreSQL-backed lifecycle while preserving local SQLite development. This phase adds:

- `investigations`, `agent_executions`, and append-only application audit-event records, plus per-run AI usage links. Alembic revision: `20261101_investigation_lifecycle`.
- Authenticated create/list/detail/run/cancel/retry/audit APIs with project ownership checks, evidence-to-project validation, and request idempotency using `Idempotency-Key`.
- A database worker that atomically claims queued work, persists agent checkpoints, retries an agent once, resumes completed agents, checks cancellation between agents, recovers expired worker leases, and records sanitized errors and token usage.
- Per-run consent remains explicit. AI token budgets conservatively estimate whether a model call fits before sending it. Public research remains unavailable unless a provider is configured and explicitly authorized.
- A CLI worker runbook in `docs/INVESTIGATION_WORKER.md`. Findings/report versioning and investigation UI are later phases.

Verification after Phase 4:

| Check | Result |
| --- | --- |
| `python -m pytest services/api/tests -q` | Passed: 23 tests. One existing third-party deprecation warning. |
| Python compile | Passed. |
| Frontend JavaScript syntax | Passed; no frontend files changed. |
| Alembic upgrade and head check | Passed on local SQLite; `20261101_investigation_lifecycle` is the single head. |
| Live Nebius/public research calls | Not made. No credentials/provider or external request authorization was used. |
| GitHub | No commit or push. User approval is still required before any push. |

## Phase 5 — Findings, review, and reports (approved and implemented)

The user approved Phase 5. This phase adds:

- Persistent `agent_findings`, `source_references`, `finding_reviews`, and versioned `investigation_reports`, using Alembic revision `20261102_findings_reports`.
- Project-context citation validation, source metadata persistence, and downgrade to `unresolved` for unsupported citations or unsupported material findings.
- Paginated finding/source/agent APIs, reviewer-only queue and decision APIs, review audit events, and a new immutable report version after each decision.
- Reports capture agent outcomes, findings, citations, source references, confidence caveats, review state, and limitations for successful, limited, partial, and failed investigations.
- Documentation in `docs/FINDINGS_AND_REPORTS.md`; Phase 6 remains the frontend intelligence workspace.

Verification after Phase 5:

| Check | Result |
| --- | --- |
| `python -m pytest services/api/tests -q` | Passed: 23 tests. One existing third-party deprecation warning. |
| `python -m compileall -q services/api/app services/api/worker.py` | Passed. |
| Alembic migration and head check | Passed on local SQLite; `20261102_findings_reports` is the single head. |
| Frontend JavaScript syntax | Passed for the four existing JavaScript files; Phase 5 adds no UI. |
| Live Nebius/public research calls | Not made. Tests use local fixture outputs. |
| GitHub or X1 | No push, deployment, or blockchain transaction. |

## Phase 6 — Intelligence workspace (approved and implemented)

The user approved Phase 6. The existing vanilla frontend now includes:

- An intelligence dashboard with persisted investigation counts, severity totals, authorized review-queue visibility, model usage, and provider configuration status.
- An investigation center with project evidence selection, explicit external-service consent, idempotent creation, and worker queueing.
- Agent activity with structured summaries, safe error codes, limitations, retry and cancellation controls, and audit events. Hidden reasoning is not rendered.
- Risk intelligence filters, versioned investigation report viewing and JSON/print export, plus a reviewer-only decision queue with required reasons.
- Loading, empty, recoverable error, and permission states, plus responsive and print styling. No X1 action is part of these screens.
- A paginated authenticated `GET /api/findings` endpoint for dashboard and risk views, scoped to the caller's investigations unless the caller is a reviewer or admin.
- Usage guidance in `docs/INTELLIGENCE_WORKSPACE.md`.

Verification after Phase 6:

| Check | Result |
| --- | --- |
| `python -m pytest services/api/tests -q` | Passed: 23 tests. Existing third-party deprecation warnings only. |
| `node --check frontend/assets/js/app.js` | Passed. |
| Local browser smoke test | Passed: authenticated navigation, dashboard, investigation center, severity filter, and empty states for agent activity, reports, and the reviewer queue. No investigation was created during the smoke test. |
| External AI, public research, GitHub push, or X1 actions | Not performed. |

## Phase 7 — X1 report anchoring (approved and implemented locally)

The user approved Phase 7. The existing deployed registry is preserved. A separate append-only `InvestigationReportAnchorRegistry` contract stores only an opaque anchor key, report SHA-256, report version, anchorer address, and block timestamp. The local extension and integration add:

- Deterministic `triplees-canonical-json-v1` report serialization and SHA-256 generation for immutable report snapshots.
- Reviewer/admin approval with a reason and an append-only investigation audit event, separate from X1 submission.
- A separately confirmed submission API using the reviewer signer, transaction metadata persistence, read-back verification, duplicate protection, and a reconciliation endpoint for uncertain transaction status.
- A public verification API and page that return commitment metadata without report contents.
- A Hardhat test suite for contract role restrictions, unique anchors, digest storage, and report version metadata.
- Local setup and separately gated deployment instructions in `docs/REPORT_ANCHORING.md`.

Verification after Phase 7:

| Check | Result |
| --- | --- |
| `python -m pytest services/api/tests -q` | Passed: 23 tests, including mocked approval, submission, reconciliation, authorization, and public data minimization. Existing third-party warnings only. |
| `python -m compileall -q services/api/app services/api/worker.py` | Passed. |
| `node --check` for workspace, public report verification, and deployment script | Passed. |
| `npm --prefix services/contracts run compile` | Passed: both Solidity contracts compiled. |
| `npm --prefix services/contracts test` | Passed: 7 local Hardhat tests. |
| `python -m alembic -c alembic.ini heads` | Passed; `20261103_report_anchors` is the single head. |
| X1 testnet deployment or transaction | Not performed. Deployment requires separate approval and `--confirm-testnet`; no live transaction was sent. |
| GitHub access, commit, or push | Not performed. |

## Phase 8 — Production hardening (approved and implemented locally)

Phase 8 added configurable PostgreSQL connection pooling and psycopg 3 URL normalization, S3-compatible evidence persistence with local-disk fallback, SHA-256 verification on download and extraction, separate liveness/readiness routes, request IDs and structured request logs, a per-user rolling AI token ceiling, migration/seed controls, and worker operation and backup/restore guidance in `docs/PRODUCTION_OPERATIONS.md`.

The security review found that authentication is still the local prototype implementation. Production API and worker startup now fail closed until an external identity provider and session controls are integrated. Production config also requires PostgreSQL, durable object storage, an explicit CORS allowlist, a persistent token secret, migrations managed as a release step, and demo seeding disabled. No service deployment, remote migration, GitHub action, or X1 transaction was performed.

Verification after Phase 8:

| Check | Result |
| --- | --- |
| `python -m pytest services/api/tests -q` | Passed: 27 tests, including evidence upload/extract/download, readiness/request IDs, worker lifecycle, storage adapter, production startup guard, and AI daily usage ceiling. One existing third-party deprecation warning. |
| `python -m compileall -q services/api/app services/api/worker.py services/api/migrations` | Passed. |
| `python -m alembic -c alembic.ini heads` | Passed; `20261103_report_anchors` is the single head. |
| Production deployment or remote migration | Not performed; production auth is not yet implemented and startup is intentionally blocked. |
| GitHub access, commit, or push | Not performed. |
