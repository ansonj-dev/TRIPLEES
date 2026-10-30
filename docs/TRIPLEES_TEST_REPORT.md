# TRIPLEES local test report

**Run date:** 2026-10-30  
**Scope:** local-only checks in `C:\Users\Administrator\Desktop\TRIPLEES`. No GitHub access, push, deployment, external infrastructure, live provider call, or X1 transaction was performed.

## Results

| Area | Command or check | Result |
| --- | --- | --- |
| Backend | `python -m pytest services/api/tests -q` | **PASS** — final run: 27 passed in 17.67s; one third-party Starlette/AnyIO deprecation warning. Pytest also printed its `pytest-asyncio` loop-scope configuration warning at startup. |
| Python syntax/import compilation | `python -m compileall -q services/api/app services/api/worker.py services/api/migrations` | **PASS** — exit 0. |
| Frontend JavaScript | `node --check frontend/assets/js/app.js`; same for `auth.js`, `public-verify.js`, `report-verify.js`, `script.js` | **PASS** — all five syntax checks exited 0. |
| Alembic | `python -m alembic -c alembic.ini heads` | **PASS** — one head: `20261103_report_anchors`. No local user database was reset. |
| Solidity tests | `npm test` (from `services/contracts`) | **PASS** — 7 Hardhat tests passed, covering report anchor permissions/hash metadata and existing registry access/lifecycle rules. |
| Solidity compile | `npm run compile` (from `services/contracts`) | **PASS** — “Nothing to compile”; current local artifacts were already up to date. |
| Branding search | Case-insensitive `rg -oi --hidden` excluding `node_modules`, artifacts/cache, `data`, Python/pytest caches and minified files | **PASS with intentional legacy matches** — 54 post-change tokens after adding these audit docs; five frontend source lines are legacy localStorage keys only. Exact pre-change count is unavailable because this folder has no Git metadata and earlier branding edits predate this audit. |
| AI | Environment variable presence only; no values printed | **BLOCKED for live test** — no `NEBIUS_API_KEY`/`NEBIUS_TOKEN` in process environment. Mocked client/schema/retry/redaction/usage tests passed in the API suite. No inference call was made. |
| PostgreSQL | Configuration/environment check | **BLOCKED** — no `DATABASE_URL` or PostgreSQL service configured. PostgreSQL runtime/migration not tested. |
| X1 | Local tests/compile only | **PASS locally** — no RPC query, deployment, or transaction performed during this audit. Chain ID/address on a live network therefore remain unverified here. |
| Local browser smoke | Open landing/auth, use demo access, render Projects, Evidence, Intelligence, Investigation Center, Agent Activity, Risk Intelligence, Investigation Reports, Review Queue, Settings and Marketplace; inspect errors and title | **PASS** — all pages rendered with `TRIPLEES` title, no visible error state and no console errors. |
| Local app startup | `python -m uvicorn services.api.app.main:app --host 127.0.0.1 --port 8000`; `python -m services.api.worker` | **PASS / RUNNING** — API and worker are still running on localhost, both pointed at disposable `%TEMP%\TRIPLEES_Audit_Run_20261030\triplees.sqlite3`, with evidence under the same temp directory. Existing `data\vericarb.sqlite3` was not used. `/`, `/auth.html`, `/app.html`, `/verify.html`, `/api/health`, `/readyz` and `/api/docs` returned HTTP 200. |
| Synthetic browser workflow | Upload synthetic PDF and CSV, verify SHA-256 rows, extract locally, select both in an investigation, queue worker, review five agent execution records, inspect report, request more evidence, generate report v2, approve digest for test only | **PASS with limits** — run completed with limitations, no public web research or Nebius inference; approval reason explicitly states no X1 submission is authorized. All data is in the disposable SQLite database under `%TEMP%`, not the existing workspace database. |
| Public report verification page | Follow generated public verification link for the approved but unsubmitted anchor | **BLOCKED** — browser safety policy rejected navigation to the generated local verification URL. The action was stopped. The report itself displayed `NOT ANCHORED TO X1`; the API suite covers public verification response fields and data minimization. |
| X1 submit control | No signer/contract is configured; no submission performed | Report UI displayed the unavailable signer/contract state. No transaction was submitted. API/Hardhat tests validate confirmation and role gates. |
| Responsive/console | Browser viewport and browser-console inspection | **PARTIAL** — no errors in desktop smoke and synthetic workflow. At the in-app browser's 685px viewport, the report digest layout was corrected and its code element measured 569px wide; mobile viewport validation was not run. |
| Production/security deployment | External identity, CORS, durable object store, production database, deployed rate limits | **BLOCKED/NOT RUN** — production config intentionally fails closed pending identity integration. |
| GitHub | Git metadata and remote operation | **NOT RUN** — this local folder has no `.git` directory; no GitHub tool or network request was used. |

## Backend coverage represented by the passing suite

The suite includes API authentication/role boundaries, project/evidence ownership, demo token access without a static password, upload and static-file boundaries, extraction/hash reuse and PDF/CSV/JSON locations, AI health/usage redaction and provider retry/schema behavior, daily AI limits, agent citation and untrusted-input behavior, deterministic registry conflict checks, synthetic monitoring labels, unsafe research URL handling, independent review flags, investigation lifecycle/worker recovery, report/reviewer behavior, production auth guard, and storage path/S3 adapter checks. See test names in `services/api/tests/` for exact cases.

Passing backend unit/integration tests are not equivalent to the full browser acceptance scenario. Real Nebius inference, external research, production PostgreSQL, live monitoring feeds, deployed identity, browser responsive behavior, and X1 writes remain unverified or intentionally untouched.

## Data and safety notes

- No repository data or database was deleted/reset.
- Tests use isolated temporary databases/fixtures per the test setup.
- The local data directory was not inspected for record contents.
- No `.env` was overwritten or created; variable presence checks did not print secret values.
- No X1 write, GitHub operation, or deployment command was run.

See [requirements traceability](TRIPLEES_REQUIREMENTS_TRACEABILITY.md) for requirement-level statuses.
