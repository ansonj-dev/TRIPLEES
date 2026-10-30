# TRIPLEES current-state audit

**Audit date:** 2026-10-30  
**Scope:** local folder `C:\Users\Administrator\Desktop\TRIPLEES` only. No GitHub, deployment, external infrastructure, or X1 write was used.

## Executive assessment

TRIPLEES is a substantial local prototype with a FastAPI backend, a vanilla-JavaScript workspace, SQLite/PostgreSQL-compatible persistence, a database-backed investigation worker, five specialized agents plus an orchestrator, evidence extraction, versioned reports and review records, and Solidity integrations. The API and contract test suites pass locally. It is suitable for a synthetic, locally run product demonstration with honest limits.

It is **not production ready**. Authentication is explicitly prototype-only and production startup is guarded. No Nebius credential is configured in this environment, so live Nemotron inference is unavailable and was not attempted. The acceptance workflow has not been driven end-to-end through a browser in this audit. X1 code and local contract tests exist; no transaction was sent. Monitoring and registry comparison use supplied/imported/synthetic data rather than connected live services.

## Architecture and verified components

| Area | Implementation | Current assessment |
| --- | --- | --- |
| Web UI | `frontend/index.html`, `auth.html`, `app.html`, verification pages, CSS and browser JavaScript | Local static UI served by FastAPI; JavaScript syntax passes. Primary labels are TRIPLEES. Some future/education views remain previews. |
| API | `services/api/app/main.py` and service modules | Authenticated project, evidence, registry import, conflict, monitoring, review, public verification, investigation, report and AI routes. API tests pass. |
| Persistence | SQLAlchemy models and Alembic migrations | SQLite local support and PostgreSQL configuration; `20261103_report_anchors` is the single migration head. |
| Worker | `services/api/worker.py` and investigation lifecycle services | Persistent queued execution, retries, cancellation, lease recovery and audit state are implemented; lifecycle covered by tests. |
| Agents | Evidence, research, integrity, monitoring, independent review; orchestrator | Distinct bounded modules, structured outputs, citations/limitations and safe handling; tests use fixture/mocked provider paths. |
| AI | `services/api/app/services/ai/` | Nebius-compatible provider, configured model registry, schema validation, bounded retry and usage tracking. Health is configuration-only. Live inference unavailable here. |
| Evidence | Upload/storage and extraction services | Hashing, safe storage, content/size checks, PDF/CSV/JSON/text extraction, locations and claim candidates are tested locally. Extraction candidates are not reviewed facts. |
| Chain | `services/contracts/`, `services/api/app/services/x1_chain.py`, report-anchor service | Existing registry plus separate report anchor contract; local Hardhat suite passes. Deployed address history is documented, not independently queried in this local-only audit. |
| Operations | README and `docs/PRODUCTION_OPERATIONS.md` | Production startup fails closed until identity/session controls are integrated; durable storage, production database, CORS and release migration requirements are documented. |

## Branding audit

The exact pre-change token count cannot be reconstructed: this folder has no Git metadata, and branding edits predate this final audit. The reproducible post-change source scan reports 54 case-insensitive tokens after adding the audit documents; most are intentional compatibility identifiers or these reports' classification tables. The frontend source has five matching lines, all legacy browser storage keys retained for local-state compatibility; no visible old-name branding remains. Current-facing titles, auth, landing page, workspace, examples and explanatory docs use TRIPLEES. The product tagline is **“Investigate. Verify. Trace.”** Static checks confirm `frontend/app.html` is titled `Workspace — TRIPLEES`; the local application is started and its HTTP pages checked separately in the test report.

The remaining legacy matches are retained intentionally. They fall into these groups:

| File(s) | Occurrence | Classification / reason |
| --- | --- | --- |
| `.env.example`, `services/api/app/config.py`, `README.md`, `docs/PRODUCTION_OPERATIONS.md` | `VERICARB_DATA_DIR`, `VERICARB_TOKEN_SECRET`; legacy database filename | Configuration and on-disk compatibility. Renaming environment variables or the database file can break existing deployments/data. README labels the token variable legacy-compatible. |
| `frontend/assets/js/auth.js`, `frontend/assets/js/app.js` | `vericarb-api-demo-token`, `vericarb-local-demo-v1`, `vericarb-notice-dismissed` | Browser storage keys kept to preserve existing local sessions and demo state. Not displayed in the UI. |
| `services/contracts/contracts/VericarbRegistry.sol`, test/scripts/artifact paths/package metadata; API contract metadata and `docs/CONTRACTS.md`, `docs/BLOCKCHAIN_ARCHITECTURE.md`, `docs/PROJECT_EXPLAINED_A_TO_Z.md`, `docs/REPORT_ANCHORING.md` | `VericarbRegistry` | Deployed/source-level contract identifier. Changing it would break ABI/artifact and historic chain references. |
| `services/api/app/main.py` | `VERICARB-BATCH-REF` | Historical hash domain marker. Changing it would change deterministic fallback hashes. |
| `services/api/tests/test_storage.py`, `services/api/tests/test_api.py` | test secret variable, test DB path, static-file denylist | Compatibility and security test fixtures. |
| `docs/PHASE_0_AUDIT_AND_ROADMAP.md`, `docs/TEST_REPORT.md` | historical product/deployment narrative | Dated records of the original codebase and prior test/deployment claims. Not current UI copy. |

Generated `node_modules`, Hardhat artifacts/cache, pytest cache, `data/`, and bytecode were excluded from the source-text count because they are generated, dependencies, or runtime data. The old contract name is expected in generated artifacts too.

## Branding and UI observations

- Landing, auth, workspace and public verification HTML titles and visible labels use TRIPLEES in source.
- The auth page no longer exposes a static test password; demo access uses the token endpoint.
- Settings now reads the authenticated AI health configuration endpoint and describes that check as non-inference. It no longer claims SQLite specifically or always reports AI as unconfigured.
- The Evidence Library now offers local extraction for uploaded supported files. The investigation form includes project-scoped synthetic evidence instead of silently hiding all demo records.
- Removed the dashboard quick action that routed to the disabled Marketplace preview. The direct optional Marketplace route remains explicitly labeled as unavailable; Community is explicitly an education preview with no posting capability.
- Synthetic records, provisional scores and imported-source limits are labeled in the UI.

## Security and reliability findings

### High

- Local demo signup/token authentication is not production identity. Production API and worker startup are intentionally blocked until an external identity provider and session controls exist. Do not expose this prototype as a production service.
- A live Nebius request can transmit explicitly consented prompt excerpts and incur provider charges. There is no credential in the current process environment; no live request was made.

### Medium

- Marketplace, community and live monitoring integrations are not implemented. Their UI copy identifies these limits; do not present the previews or synthetic monitoring as live capabilities.
- The X1 client depends on local configuration and contract artifacts. No network read was relied on for this report, and no write was attempted. Report anchoring requires explicit reviewer approval and a separately authorized transaction.
- Existing names are embedded in env variables, storage keys, a contract identifier, and deterministic hash compatibility. They should only be migrated with explicit compatibility and data-preservation work.
- The README and historical phase reports include earlier test counts. This audit’s exact run results are in `TRIPLEES_TEST_REPORT.md`; dated earlier counts should not be read as this run.

## Functional coverage

API tests cover authenticated access, role checks, project/evidence boundaries, upload/extraction and hashes, AI configuration/usage redaction and provider behavior, agent outputs, investigation lifecycle, worker behavior, findings/review/report flows, storage safety and production startup guards. Hardhat tests cover role boundaries, unique records, lifecycle transitions and the report-hash contract. These results validate local/test paths; they do not establish live-provider, live-registry, production identity or complete browser acceptance.

See [requirements traceability](TRIPLEES_REQUIREMENTS_TRACEABILITY.md), [test report](TRIPLEES_TEST_REPORT.md), and [implementation roadmap](TRIPLEES_IMPLEMENTATION_ROADMAP.md).
