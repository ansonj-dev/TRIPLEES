# TRIPLEES requirements traceability

Audit baseline: the attached `TRIPLEES_Complete_Audit_Test_and_Build_Prompt.md`, dated 2026-10-30. Status meanings follow its section 16. **PASS** requires a tested workflow, not just a route or document. **MOCK** identifies fixture, deterministic, or mocked provider behavior.

## Product and hackathon goals

| Requirement | Status | Evidence | Remaining work |
| --- | --- | --- | --- |
| Useful evidence-grounded investigation application | **PARTIAL** | FastAPI and workspace pages; `services/api/tests/test_api.py`; docs for investigation/evidence/report workflows | Run the complete acceptance workflow through the browser against an isolated workspace. |
| Distinguish supplied facts, external observations, model inferences, hypotheses and unknowns | **PARTIAL** | Agent schemas and limitation/source fields in `services/api/app/services/agents/`; report and finding models; `test_agents.py` | Complete all evidence types in a user-visible, end-to-end report and reviewer workflow. |
| Real Nebius Token Factory inference with an NVIDIA Nemotron model | **BLOCKED** | `services/api/app/services/ai/`; `docs/AI_FOUNDATION.md`; mocked provider tests | Configure a valid credential/model and authorize a paid request. No live call was made. |
| Honest errors, sources, uncertainty and review status | **MOCK** | Agent schema, source/citation validation and adversarial-review tests in `test_agents.py`; persisted findings/report tests | Demonstrate with a real provider only after credential and external-send approval. |

## Orchestrator and agents

| Requirement | Status | Evidence | Remaining work |
| --- | --- | --- | --- |
| Persistent orchestrator validates scope and queues work | **PASS** | Investigation APIs/services; `test_investigation_lifecycle_and_worker_resume` | Browser acceptance run remains outstanding. |
| Persistent agent execution, status/progress, retry, cancellation and recovery | **PASS** | Worker/service and agent execution records; lifecycle test | Exercise live worker UI flow in isolated demo data. |
| Budget controls and bounded AI token usage | **PASS** | AI usage tracker/config; `test_daily_ai_token_limit_uses_rolling_user_usage` | Operational tuning requires deployment metrics. |
| Partial failures and report generation | **PASS** | Investigation orchestration/report services and lifecycle/report tests | Verify visually in browser with a fixture that forces partial failure. |
| No arbitrary shell/SQL/HTTP/wallet/signing tools for agents | **PASS** | Agent service boundaries and safety tests; X1 submission is a separate reviewer API | Continue permission review before any tool expansion. |
| Evidence Analyst PDF/CSV/JSON/text, source locations, extraction limits | **PASS** | `services/api/app/services/evidence_extraction.py` and evidence routes; `test_document_extraction_preserves_csv_json_and_pdf_locations` | Browser upload/extract acceptance remains outstanding. |
| Research Investigator public sources, metadata and unavailable behavior | **MOCK** | Research agent validates public result shapes/URLs and tests unavailable/fixture results (`test_research_agent_*`) | No live search provider is configured; enable only with approved provider and source policy. |
| Integrity Analyst exact comparison and arithmetic | **PASS** | Registry conflict and deterministic integrity service; `test_integrity_agent_reports_exact_import_conflicts_without_claiming_fraud` | Data coverage is only the supplied/imported registry set. |
| Monitoring Analyst supplied/synthetic data and data gaps | **MOCK** | Monitoring agent tests label synthetic input and do not claim live data | No satellite, IoT or field data source is connected. |
| Independent Review challenges unsupported claims | **MOCK** | `test_independent_review_flags_unsupported_and_overclaim_language`; schema tests | Full real-model adversarial review cannot be verified without live inference. |
| No private chain-of-thought in UI | **PASS** | Frontend renders concise agent summaries/findings; no hidden reasoning field is part of report UI | Recheck if agent output schema changes. |

## AI provider

| Requirement | Status | Evidence | Remaining work |
| --- | --- | --- | --- |
| Provider abstraction, configurable model, Nemotron model guard | **PASS** | `services/api/app/services/ai/`; `test_model_registry_marks_only_configured_nemotron_as_nemotron` | Live account model availability not verified. |
| Strict structured output validation | **PASS** | `structured_output.py`; `test_structured_output_is_parsed_and_validated` | None for local validation. |
| Async HTTP, timeouts, bounded transient retry, 429/5xx/error sanitization | **PASS** | `nebius_client.py`; provider error/retry tests | Live latency and rate behavior unverified. |
| Usage/token tracking, optional cost accounting, budget ceiling | **PASS** | usage service, health/usage APIs and usage tests | Cost rates intentionally unknown until explicitly configured. |
| No key/content in errors or logs | **PASS** | Sanitized provider error and health redaction tests | Recheck before production logging changes. |
| Mock tests and optional live test | **MOCK** | `test_ai_provider.py` mocked HTTP transport | Live test **BLOCKED**: no `NEBIUS_API_KEY` or authorization. |
| `.env.example` placeholders; existing `.env` preserved | **PASS** | `.env.example`; no `.env` file was changed or created by the audit | Configure secrets manually in ignored local configuration when needed. |

## Evidence, data and API

| Requirement | Status | Evidence | Remaining work |
| --- | --- | --- | --- |
| Safe upload validation, original preservation, SHA-256, duplicate handling | **PASS** | Evidence upload/storage services; storage path traversal and upload/hash/idempotent extraction tests | Test additional production object-store provider under configured integration. |
| PDF page, CSV row, JSON path, text source locations | **PASS** | Extraction tests for PDF/CSV/JSON; source-location records | Browser acceptance remains outstanding. |
| Untrusted documents and prompt-injection resistance | **PASS** | Agent wraps evidence as untrusted; `test_evidence_analyst_requires_context_citations_and_wraps_data_as_untrusted` | Expand adversarial corpus before production. |
| Project/tenant ownership and SQLite/PostgreSQL compatibility | **PARTIAL** | SQLAlchemy ownership filters, cross-project evidence denial test, config and production guard | PostgreSQL service unavailable; tenant-isolation acceptance not exercised against a live PG service. |
| Safe Alembic evolution and single head | **PASS** | `python -m alembic -c alembic.ini heads` → `20261103_report_anchors (head)` | Existing non-disposable database backup migration not run in this audit; no destructive reset. |
| Investigation, agent, finding, source, report, usage and audit models | **PASS** | Models, migrations and API/lifecycle/report tests | Full browser lifecycle remains outstanding. |
| Investigation CRUD/run/cancel, agent status, findings, reports and reviews | **PASS** | Routes in `main.py` and intelligence router; API suite (27 passed) | Verify all actions in UI with isolated fixture records. |
| Authentication/RBAC, validation, pagination, ownership, safe errors | **PASS** | Auth/RBAC/API tests and response validation; 27 API tests passed | Auth remains prototype-only and is not production identity. |
| Long-running work is persistent and worker-backed | **PASS** | `services/api/worker.py`; lifecycle/worker resume test | Production queue/service operations require deployment design. |

## Frontend and product surfaces

| Requirement | Status | Evidence | Remaining work |
| --- | --- | --- | --- |
| Landing, auth, dashboard, project/evidence/credit/monitoring surfaces | **PASS** | `frontend/index.html`, `auth.html`, `app.html`, `assets/js/app.js`; local browser smoke and synthetic evidence upload/extraction | Responsive viewport review remains outstanding. |
| Investigation center, activity, risk, report and review queue | **PASS** | Routes and page renderers in `app.js`; isolated browser flow persisted all five agent executions, findings, report v1/v2 and a reviewer request for more evidence | Complete a role-denied browser action in a separate non-reviewer account. |
| Responsive labels, loading/empty/error states, disabled Marketplace copy | **PARTIAL** | Responsive CSS, loading/error branches, “not enabled” preview; removed Marketplace quick action | Browser check across viewport sizes and console remains outstanding. |
| API-backed data, honest demo/synthetic labels and X1 state | **PASS** | Authenticated bootstrap and status calls; source copy in `app.js`; API static boundary test | Current browser console/network inspection remains outstanding. |
| Functional Marketplace, public community posting, live impact tracking | **NOT STARTED** | Marketplace explicitly disabled; community is education preview; impact data is synthetic | Keep hidden/disabled until actual functionality/source exists. |
| Current visible TRIPLEES branding and metadata | **PASS** | HTML titles/source and local browser title/visibility check; old identifiers classified in current-state audit | None for current desktop smoke coverage. |

## X1 EcoChain and reports

| Requirement | Status | Evidence | Remaining work |
| --- | --- | --- | --- |
| Preserve current registry/deployment identifiers | **PASS** | Solidity source, chain utility, docs and phase records preserve `VericarbRegistry` and historical address | No live explorer/RPC read performed in this audit. |
| Local contracts compile and test | **PASS** | `npm test` → 7 passing; `npm run compile` → no changes to compile | None for local contract suite. |
| Store private docs/full reports off-chain; SHA-256/canonical report hash | **PASS** | Evidence storage and report-anchor service; report digest tests in API/contract suite | Independent reproducibility check is documented in report, not a live transaction. |
| Reviewer approval before anchoring; agent cannot sign; no autonomous credit issuance | **PASS** | Separate approval/submission APIs and signer boundary; API and Solidity role tests | Live wallet/network behavior not exercised. |
| Submit no transaction | **PASS** | No transaction command was run | Any future testnet transaction needs explicit approval. |
| Public verification says anchored only with real commitment | **PASS** | Public report verification API/page returns stored chain metadata; mocked/API assertions | No new on-chain commitment exists from this audit. |

## End-to-end and security acceptance

| Requirement | Status | Evidence | Remaining work |
| --- | --- | --- | --- |
| Scenario through sign-in → synthetic PDF/CSV → extraction → worker/agents → review → versioned report/digest | **PASS** | Executed in a temporary SQLite database with synthetic files; worker completed all five agent records with explicit limitations; reviewer requested more evidence; report advanced to v2 and digest approval was recorded with “no X1 submission authorized” reason. | Public verification page was not opened because the browser safety gate rejected navigation to the generated verification URL. API tests cover public verification responses. |
| Real Nebius inference in acceptance flow | **BLOCKED** | Environment variable presence check found no Nebius key; no request sent | Requires valid credential and explicit approval for external/billable request. |
| Security checks for auth, cross-project, upload/path traversal, URL, signing, secret redaction | **PASS** | API, storage and agent safety tests | Production identity, external identity integration, rate limiting and deployed CORS/session configuration remain blockers. |
| PostgreSQL migration/runtime and production infrastructure | **BLOCKED** | SQLite and PostgreSQL-compatible code; no PostgreSQL service/URL configured | Requires a disposable PostgreSQL service and operator-controlled environment. |

See [test report](TRIPLEES_TEST_REPORT.md) for exact executed commands and [roadmap](TRIPLEES_IMPLEMENTATION_ROADMAP.md) for remaining work.
