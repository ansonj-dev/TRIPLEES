# TRIPLEES Final Build Audit

Audit date: 2026-11-14 UTC. Audited checkout: `c4e36d8` on `main`.

## 1. Executive Summary

**Overall assessment: PARTIALLY READY.** The local evidence/investigation demonstration works. The complete TRIPLEES-to-NEAR-testnet demonstration is **not verified and is not submission ready as a demonstrated live integration**.

What was actually built:

- A working static browser workspace backed by FastAPI, SQLAlchemy, local evidence storage, and Alembic.
- Evidence upload/fingerprinting, embedded-text PDF/CSV/JSON/TXT extraction, imported-record comparisons, supplied monitoring observations, persisted investigations, five sequential analytical roles, findings, human decisions, and versioned reports.
- A Rust NEAR digest registry with tested reviewer access control and immutable investigation/version records, a real NEAR Connect wallet chooser, pending-commitment APIs, RPC verification code, and a public report-copy verifier.
- A database-backed coordination overlay: five predefined tasks, deterministic simulated bids, internal-unit budgets, permission records, and stop controls. This is not a decentralized swarm or payment system.
- An independent X1 integration. Its previously documented deployment was verified read-only during this audit against current compiled bytecode and stored project/batch state.

What execution established:

- Backend regression: **36 passed** before and after the safe audit fixes.
- X1 Hardhat: **7 passed**; a forced compile built **2 Solidity files**.
- NEAR: **8 Rust tests and 1 near-workspaces sandbox integration test passed**. The earlier deserialization blocker no longer affects the supported optimized artifact.
- Additional independent API/worker probes: initially **30 passed, 3 failed**; after the narrow timestamp fix, **31 passed, 2 failed** across 33 assertions and 80 recorded API calls.
- The browser exercised real login, sample upload, extraction, investigation creation/queueing, five actual worker executions, source-linked findings, review/versioning, local digest approval, persisted budgets, navigation, the real wallet chooser, and cancellation of that chooser.
- Restart preserved the investigation, five executions, five tasks, 4 internal units spent, report versions 1/2, the report digest, and an approval without a transaction. The existing browser session also remained valid with a stable audit-only token secret.

Confirmed remaining defects include task reassignment being accepted but skipped by the worker, completed tasks being reopened by budget changes, unenforced external-service permissions, and invalid monitoring timestamps accepted by the API but unsafe for the frontend formatter. Other code-inspection risks are ranked below.

**No public deployment, reviewer grant, wallet-account connection, wallet signature, token transfer, paid inference, push, or commit was performed.** There is no configured NEAR contract/account or NEAR CLI here. No successful public NEAR commitment or transaction is claimed. Existing tests containing mocked chain/provider fixtures are explicitly identified as mocks, not live evidence.

### Scope and Isolation

The audit began read-only. The implementation was compared with parent commit `3bae980`; commit `c4e36d8` added 18 files and modified 13. Existing uncommitted SDK/toolchain/documentation changes from the preceding compatibility fix were preserved, not attributed to this audit.

Tests used disposable SQLite databases and evidence directories under `/tmp/triplees-final-audit-fdf58363/`. The existing `data/vericarb.sqlite3` workspace was not used for mutation tests. The browser used the repository's explicitly synthetic sample, not newly invented environmental evidence.

## 2. Feature Matrix

Status scope matters: PASS means the stated tested behavior works, not that it is production certified or uses a live external model. PARTIAL means the complete requested workflow is incomplete. UI ONLY and MOCK distinguish placeholders/simulations. NOT TESTED is not a passing claim.

Evidence labels: **B** = existing backend tests; **P** = independent API/actual-worker probes; **U** = real browser/HTTP exercise; **N** = real local NEAR sandbox; **X** = local Hardhat plus read-only public X1 RPC; **S** = source inspection. Mocked evidence is labeled explicitly.

### Existing TRIPLEES Features

| ID | Feature | Status | Evidence | Missing Work / Boundary |
| --- | --- | --- | --- | --- |
| EX-01 | Investigation creation | PASS | B/P/U: real draft API, idempotency checks, UI create-and-queue | UI combines creation and queueing; not a separate draft editor |
| EX-02 | Evidence upload | PASS | B/P/U: HTTP 201, original sample bytes stored; oversized input 413 | No malware scanning; local demo storage only exercised live |
| EX-03 | PDF extraction | PASS | B: generated embedded-text PDF parsed with page-1 provenance | Scanned-document OCR is missing; complex PDF corpus not tested |
| EX-04 | CSV extraction | PASS | B: actual parser preserves row-2 locations | Only bounded supplied files, not a live registry |
| EX-05 | JSON extraction | PASS | B/P/U: existing sample yields 14 chunks | Sample correctly yields zero heuristic claims; no semantic claim invention |
| EX-06 | TXT extraction | PASS | B: line provenance, chunking, candidate claims, reuse, tamper rejection | Heuristic candidates are not verified facts |
| EX-07 | SHA-256 evidence fingerprinting | PASS | P/U: independent digest equals server digest | A hash does not prove source authenticity |
| EX-08 | Source-linked findings | PASS | B/P/U: registry and observation citations persisted/displayed | No live public research sources were retrieved |
| EX-09 | Registry imports | PASS | B: real CSV import endpoint and persistence | Imported rows only; repeat imports can create further conflicts |
| EX-10 | Registry conflict detection | PASS | B/P/U: normalized exact duplicate serial found in supplied rows | No global registry coverage or serial-range semantics |
| EX-11 | Monitoring observations | PARTIAL | B/U: supplied/synthetic records and review alerts work | Invalid timestamp accepted; no satellite/IoT feed |
| EX-12 | Evidence Analyst | PARTIAL | P/U: actual deterministic inventory executed; B mocks model boundary | Live Nemotron interpretation NOT TESTED |
| EX-13 | Research Investigator | PARTIAL | P/U: actual role reports research unavailable | Default provider is unconfigured; no deployed search integration |
| EX-14 | Integrity Analyst | PASS | B/P/U: actual project-scoped imported-row comparison | Deterministic exact matching, not AI fraud detection |
| EX-15 | Monitoring Analyst | PASS | B/P/U: actual supplied-observation summary retains synthetic status | No external monitoring queried |
| EX-16 | Independent Review Agent | PARTIAL | B/P/U: actual deterministic support/citation review | Live adversarial model call NOT TESTED; model-success limitation text needs review |
| EX-17 | Agent orchestration | PASS | B/P/U: default five-role sequence, real failure/retry recovery | Sequential pipeline, not a swarm; alternate task execution has a separate defect |
| EX-18 | Investigation history | PASS | B/P/U: audit events and executions survive restart | No concurrency/long-term retention test |
| EX-19 | Report generation | PASS | B/P/U: actual worker creates persisted report | Narrative is a structured summary, not a live-model-authored environmental opinion |
| EX-20 | Report versioning | PASS | B/P/U: review creates version 2; version 1 unchanged | Concurrent version allocation not stress tested |
| EX-21 | Human reviewer approval | PASS | B/P/U: role/reason checks, finding decision, separate local digest approval | Prototype demo identity only; approval is not certification |
| EX-22 | Existing X1 integration | PARTIAL | X: deployed bytecode and historical records verified; 7 local tests | No new signed X1 workflow run; transfers/retirements/reviews in API remain local |

### New NEAR Features

| ID | Feature | Status | Evidence | Missing Work / Boundary |
| --- | --- | --- | --- | --- |
| NE-01 | NEAR wallet connection | PARTIAL | U: real pinned connector initializes and chooser opens | No wallet was selected/connected |
| NE-02 | Wallet disconnection | NOT TESTED | S: disconnect/sign-out handlers exist | No connected account available; chooser cancellation is a different action |
| NE-03 | NEAR account identification | NOT TESTED | S: reads `wallet.getAccounts()` | No genuine connected account ID was displayed |
| NE-04 | Network detection | PARTIAL | Live RPC reports testnet; client rejects actual mainnet RPC | UI labels connector configuration; no independent connected-wallet network test |
| NE-05 | Incorrect-network handling | PARTIAL | B: mainnet configuration rejected; live read-only RPC guard rejects mainnet | Actual wrong-network wallet interaction NOT TESTED |
| NE-06 | Authentication and account ownership verification | MISSING | S: no wallet challenge, ownership binding, nonce store, or expiry | Application bearer login is separate; wallet is intentionally not app login |
| NE-07 | NEAR smart contract compilation | PASS | N: cargo-near build produces optimized Wasm | Requires pinned compatible dependencies/toolchain |
| NE-08 | Contract tests | PASS | N: 8 host tests plus 1 actual sandbox test | Not a public-testnet wallet/API end-to-end test |
| NE-09 | Contract deployment configuration | PARTIAL | S: public env settings and atomic deployment example exist | No CLI, account, deployed contract ID, manifest, or reviewer configuration |
| NE-10 | Actual testnet deployment | MISSING | No configured deployment or account; none performed | Human-approved deployment and independent read-back required |
| NE-11 | Reviewer permissions in contract | PASS | N: owner grant/revoke and unauthorized commitment rejection | Public-testnet grant NOT TESTED |
| NE-12 | Report commitment | PARTIAL | N: real local contract commitment; P: actual pending API record | No browser-to-public-testnet commitment |
| NE-13 | SHA-256 report digest | PASS | P/U: exported API representation rehashes identically; changed summary differs | Covers defined canonical fields, not all whitespace/extra fields in an arbitrary JSON file |
| NE-14 | Transaction signing | NOT TESTED | S: real wallet `signAndSendTransaction` call path | No signature requested or supplied |
| NE-15 | Transaction confirmation | PARTIAL | B: pending/confirmed and RPC-shape checks with mocks; S inspected | No actual public NEAR transaction tested; recovery defect below |
| NE-16 | On-chain report verification | NOT TESTED | N local contract views work; public API success tests are mocked | No real public NEAR commitment retrieved and compared |
| NE-17 | Report mismatch detection | PARTIAL | P: local digest changes; B: mocked public MISMATCH | Real public NEAR mismatch workflow NOT TESTED |
| NE-18 | Transaction history | PARTIAL | P: persisted pending records/list API; U: honest empty live history | No genuine NEAR transaction history available |

### Agent Coordination Features

| ID | Feature | Status | Evidence | Missing Work / Boundary |
| --- | --- | --- | --- | --- |
| AC-01 | Task creation | PASS | P: five persisted predefined tasks; duplicate plan reuses IDs | Not arbitrary free-form task authoring |
| AC-02 | Task assignment | PARTIAL | P: assignment persists, but reassigned task can be skipped | Fix task/execution identity binding |
| AC-03 | Agent execution | PARTIAL | P/U: default five roles and individual primary task execute | Reusing an already-completed agent for a different task does not execute it |
| AC-04 | Agent task status tracking | FAIL | P: budget change reopens five completed tasks as awaiting review | Preserve terminal states; reconcile task/execution results |
| AC-05 | Structured agent results | PASS | B/P/U: Pydantic outputs, saved findings and execution references | No live LLM output verified |
| AC-06 | Agent bidding | MOCK | S/P: software inserts hardcoded cost/duration/capability estimates | No independent economic agents, external bids, or learned reputation |
| AC-07 | Coordinator selection logic | MOCK | P: deterministic weighted choice selects default specialists | Real algorithm over simulated scores, not a negotiated swarm |
| AC-08 | Failed-task handling | PASS | B/P: permission-denied partial run recovers on retry; prior results retained | Concurrent crashes/provider hangs not stress tested |
| AC-09 | Investigation budgets | PASS | P/U: persistent 10 total/4 spent/6 remaining; under-allocation 409 | Internal units only, not token balance or verified compute cost |
| AC-10 | Agent spending limits | PASS | P/B: per-agent cap/threshold checks, rejected lower limits, once-per-task accounting | Retries/inference costs are not actual financial settlement |
| AC-11 | Reviewer authorization | PASS | B/P/U: non-reviewer budget/permission calls rejected; approval reasons persisted | Public demo admin is not production identity |
| AC-12 | Emergency stop | PASS | P: stop before execution yields cancelled investigation and zero executions | Stops at worker boundaries, not during an in-flight provider call |
| AC-13 | Agent payment workflow | MISSING | S: no payment service or NEAR transfers; example flag is unused | Do not represent internal units as payments |

### Additional UI/Mock Surfaces

- **UI ONLY:** Marketplace and Community explicitly show future/preview content. Settings' Organization/Security/Notifications tabs are labels, not full settings workflows.
- **MOCK:** `/api/admin/data-sources` returns hardcoded availability descriptions. Prototype integrity weights/scores are assumptions, not calibrated environmental measurements.
- Legacy evidence assessment is deterministic metadata review, not proof of external AI inference.
- JSON report data is retrievable and hashable. The browser download action ran, but completed file delivery was NOT TESTED successfully because the integrated browser did not expose a download event.

## 3. Architecture Discovered

| Layer | Actual Implementation |
| --- | --- |
| Frontend | Plain HTML/CSS/JavaScript, hash routing and DOM rendering; bearer token in localStorage; FastAPI serves only the frontend directory |
| API | FastAPI routers for documents, investigations, X1 report anchors, NEAR, AI status, and agent coordination; authorization is enforced server-side on inspected write paths |
| Database | SQLite locally; PostgreSQL driver/configuration exists but was not exercised; SQLAlchemy models plus a single Alembic head `20261113_agent_coordination` |
| New persistence | `near_commitments`, `investigation_budgets`, `agent_budgets`, `agent_permissions`, `agent_tasks`, `agent_bids`; one requested-agent column added to investigations |
| Evidence | Local/S3-compatible storage interface; upload limits/type checks; SHA-256 verification before extraction/download; extraction chunks/claims and provenance stored separately |
| Worker | Database job claim, lease recovery, two per-agent attempts, sequential agent suite, audit records, usage records, finding/report persistence |
| Coordination | Fixed five-task plan and deterministic bid simulation overlay; worker still selects agent classes, not arbitrary task-specific executors |
| AI | Nebius Token Factory adapter; only Evidence Analyst and Independent Review optionally invoke a model; `local_mock` is explicit, AI Cloud fails closed |
| NEAR | Browser NEAR Connect wallet, Rust digest registry, prepare/confirm APIs, read-only RPC verification; no backend NEAR signer |
| X1 | Separate Solidity contracts and backend-controlled role signers from environment variables; does not share NEAR keys/settings |
| Operations | No tracked Dockerfile, Compose file, CI workflow, frontend build/test/lint configuration, or type-check configuration was found |

The NEAR change extends the earlier architecture rather than replacing the five agents, AI provider, worker, database, or X1 contracts. See the complete changed-file inventory at the end of this report.

## 4. NEAR Integration Results

### Build and Contract Audit

- Current pins: near-sdk **5.17.2**, Rust **1.86.0**, near-sys **0.2.5**, with Rust-compatible transitive dependencies locked. near-workspaces **5.0.0** uses near-sandbox **0.1.5**, whose bundled nearcore is **2.6.2/protocol 77**.
- The prior locked SDK targeted protocol 85. The supported optimized cargo-near artifact now builds and executes successfully in the actual sandbox. Raw compiler output is not the supported deploy/test artifact; use the cargo-near post-processing path.
- Observed optimized artifact: **190,510 bytes**, SHA-256 `c1891032e6035beb99818e7a85289e62c33ab708fcbaa3c54f2e3adb0fd5ec5f`.
- Source and tests establish owner-managed reviewers, reviewer-only commits, lowercase 64-hex digest validation, optional metadata digest validation, positive versions, bounded investigation IDs, duplicate-version rejection, new versions, public views, and `EVENT_JSON:` events with the intended NEP-297-style envelope.
- On-chain fields are investigation ID, version, digests, submitter, and timestamp. Report text, findings, evidence, and approval reason are not stored by the contract.
- A separate local sandbox probe proved that any first caller can initialize an uninitialized instance as themselves. **Deploy and initialize atomically**, as the existing documented command does. Do not leave an uninitialized public deployment.
- No gas/storage exhaustion audit, fuzzing, upgrade/key-management proof, or full event-schema conformance suite was performed. Full-access account keys can still upgrade deployed code; append-only methods are not an independent upgrade lock.

**Deployment classification:** compiled and locally exercised, not merely source-only; public-testnet deployment/configuration is missing. No NEAR explorer verification is claimed.

### Wallet, Authentication, and Transaction Chain

The exact pinned ESM URL resolved, the real connector initialized for testnet, and its chooser displayed actual wallet options. Escape/cancellation produced `User rejected` and left the account disconnected. This is stronger than a clickable placeholder, but it does not prove account connection, disconnection, correct-account signing, or wallet-network switching.

The intended chain is:

```text
Persisted report -> canonical JSON fields -> SHA-256 -> reviewer preparation
  -> pending DB record -> wallet signature -> NEAR transaction
  -> independent RPC outcome + contract-state comparison -> confirmed DB record
  -> supplied report canonicalization + digest/state comparison
```

The report/digest/pending-record portions were independently exercised. The local contract portion was exercised in sandbox. The public wallet/transaction/confirmation chain was **not** exercised end to end.

The backend does not accept browser success as proof: inspected code compares testnet chain ID, transaction signer/receiver, one function call, exact method/arguments, success status, and contract state. Existing tests mock those responses. Finality/RPC behavior against a genuine TRIPLEES public transaction remains unverified.

There is no wallet-signature ownership challenge, application nonce/expiry/replay store, or durable account association. NEAR transaction nonces belong to the blockchain protocol and do not implement application ownership authentication. Pending commitment approvals have no expiry/cancel/rebind workflow. Preparation itself records a reviewer approval; it does not require every finding to have been reviewed or the report to be in a particular final state.

### Public Chain Checks

- Actual NEAR testnet RPC returned `chain_id=testnet`, nearcore 2.14.1, and block 277620009 at the read-only checkpoint. This proves connectivity, not deployment.
- The client pointed at the actual mainnet RPC while configured for testnet raised `NearNetworkError`. No transaction was sent.
- No NEAR CLI, credential directory, configured registry account, Nebius key, or X1 signing key was present in the inspected environment. No secret values were printed.
- Public X1 RPC returned chain **10778**. Address `0x5BF650b0b46D40794B116c36f75DABAcF5ed9e8b` contains **14,359 bytes** matching the current compiled deployed bytecode exactly.
- X1 code keccak: `0x7332f12254ad8082ac69623231eb488fa9b840b362a8edb1b7fdb87567cb677a`.
- Historical deployment transaction `0x5d5faa4233d59bb941475cd38cd86d08c7ebc32cc93954343372f3be83edab78` returned receipt status `0x1`, contract address matching the documented registry, block 11860437.
- The documented X1 project exists; documented batch quantity is 1,000,000 kg, retired quantity 500 kg, state Active, history count 6. Its issuer still has the issuer role. No new X1 transaction was made and no explorer source-verification claim is made.

### New NEAR Endpoint Inventory

Auth: **R** = reviewer/admin bearer session plus project access; **U** = authenticated user with scoped access; **Public** = no bearer required. Test-only prepared records used an explicitly undeployed configuration and no successful RPC response. They are not deployment evidence.

| ID | Method / URL | Auth | Input Schema | Actual Result / Database Effect | Errors / Limits Checked |
| --- | --- | --- | --- | --- | --- |
| EP-01 | GET `/api/near/config` | Public | None | 200; primary disabled/testnet/contract null; secondary enabled with commitments false; no writes | Feature gate correctly represented in UI |
| EP-02 | POST `/api/near/commitments/prepare` | R | report_id 1-80; valid account ID 2-64; reason 5-2000 | 201 pending with digest, receiver/method/args; creates/reuses commitment plus audit event | 401/403/404/409/422/503 covered; same account reuses row, different pending account conflicts |
| EP-03 | POST `/api/near/commitments/{id}/confirm` | R | Base58-shaped transaction_hash 43-44 | Real invalid input 422; unauthenticated 401. 202 pending/200 confirmed only in mocked tests; stores hash/status in DB | No live successful confirmation; hash saved before RPC validation is a recovery risk |
| EP-04 | GET `/api/near/commitments` | U; reviewers see all | offset >=0; limit 1-200 | 200 items list; runtime honestly empty; no writes | Authentication enforced; actual on-chain history absent |
| EP-05 | GET `/api/near/commitments/{investigation_id}` | U | Investigation path ID | 200 scoped items; runtime empty; tests list persisted records | 401 and investigation ownership boundary; no writes |
| EP-06 | GET `/api/public/near/commitments/{id}` | Public | Commitment path ID | Pending record returns status and `verified_on_chain:null` during unavailable RPC; no report body/reason; no writes | Missing ID 404; never elevates unavailable state to verified |
| EP-07 | POST `/api/public/near/commitments/{id}/verify` | Public | report object; serialized limit 2 MB; required canonical field shapes | Actual original report gives UNAVAILABLE with matching local digest when chain unavailable; no writes | Malformed timestamp originally 500, now 422; VERIFIED/MISMATCH success coverage is mocked only |

## 5. Agent System Results

**Classification: sequential multi-role orchestrator with a deterministic internal coordination simulation. It is not a genuine autonomous or decentralized agent swarm.** Roles share scoped context and database records; independent review receives earlier drafts. They do not negotiate with each other or pay external agents.

| Agent | Input / Prompt / Provider | Actual Processing and Output | Persistence / Error Handling / Invocation |
| --- | --- | --- | --- |
| Evidence Analyst | Selected extracted evidence/claims; untrusted-data, cite-only-supplied-IDs system prompt; optional configured Nemotron adapter | Actual local run inventoried 1 file/0 candidate claims; model call not authorized | Actually invoked; typed output persisted; provider unavailable/invalid output codes and no-consent fallback exist; live inference NOT TESTED |
| Research Investigator | Project identity and existing references; no model prompt by default; `UnconfiguredResearchProvider` | Actual role reports unavailable/unauthorized research; provider injection interface can retain safe source metadata | Actually invoked; limitations persisted; no external research was fetched |
| Integrity Analyst | Project-scoped imported registry rows; no LLM/provider | Normalized exact serial/quantity comparisons; actual synthetic duplicate found | Actually invoked; linked registry IDs persisted; scope limitations retained |
| Monitoring Analyst | Supplied observations and evidence IDs; no LLM/provider | Preserves synthetic status; actual forest-loss fixture remains a hypothesis, not a reversal finding | Actually invoked; linked observation persisted; no live feeds |
| Independent Review Agent | Earlier findings plus scoped evidence/source IDs; adversarial citation/overclaim prompt; optional Nemotron adapter | Actual deterministic support/citation/wording checks; not an independent external investigation | Actually invoked last; findings/report persisted; live model NOT TESTED; successful-model branch appears to retain a contradictory local-only limitation |

In the browser run, all five executions ended `completed_with_limitations`, honestly reflecting unavailable/unauthorized external capabilities. Two findings were saved. The reviewer confirmed only the synthetic duplicate-record fact, creating report version 2. No environmental conclusion or model inference was fabricated.

Task priority fields do not replace the worker's fixed agent-suite order. Individual task execution currently addresses an agent key rather than a distinct task execution identity; that is the root of the confirmed reassignment problem. Bids have hardcoded reliability/capability/cost/duration inputs. Internal-unit charging is once per task, not settlement of actual retries, token usage, or compute cost.

### New Coordination Endpoint Inventory

All these routes require bearer authentication. **R** below additionally requires reviewer/admin. Normal user operations are scoped through investigation/project access.

| ID | Method / URL | Auth | Input Schema | Actual Result / Database Effect | Errors / Limits Checked |
| --- | --- | --- | --- | --- | --- |
| EP-08 | POST `/api/agents/tasks` | U | investigation_id 1-80 | 201; creates five tasks, bids, default budgets/permissions, audit; duplicate plan reuses IDs | 401/404/422; allocation checks present |
| EP-09 | GET `/api/agents/tasks` | U | optional investigation_id; offset >=0; limit 1-200 | 200 persisted task/bid items; no writes | 401; invalid limit 0 gives 422 |
| EP-10 | GET `/api/agents/tasks/{task_id}` | U | Task path ID | 200 task, budget allocation, result reference, bids; no writes | Missing task 404; authentication/scope checks |
| EP-11 | POST `/api/agents/tasks/{task_id}/assign` | R | bid_id 1-80 | 200 persists selected bid/agent, allocation and audit | Missing bid 404, busy/invalid status/allocation guards; downstream execution defect reproduced |
| EP-12 | POST `/api/agents/tasks/{task_id}/execute` | U | No body fields | 202 queues investigation with requested agent key; real primary task executes | Threshold/freeze/state 409; revoked permission 403; reassigned completed agent silently skipped later |
| EP-13 | POST `/api/agents/tasks/{task_id}/cancel` | U | No body fields | 200 cancelled task; terminal calls idempotent; audit written | Running-task cancellation requests cancellation of the whole investigation, not an isolated provider call |
| EP-14 | GET `/api/agents/coordination/{investigation_id}` | U | Investigation path ID | 200 tasks, persisted budget, investigation status, explicit simulation mode | Authentication/scope checks; no writes |
| EP-15 | GET `/api/agents/budgets/{investigation_id}` | U | Investigation path ID | 200 actual totals and per-agent limits; UI agrees with DB | Authentication/scope checks; no writes |
| EP-16 | POST `/api/agents/budgets` | R | investigation_id; limit >0 <=10000; threshold 0-10000; finite known-agent limits 0-10000 | 200 persists budget; lowering threshold also incorrectly changes completed task statuses | Invalid values 422; below existing total/agent allocation 409; non-reviewer 403 |
| EP-17 | POST `/api/agents/budgets/{investigation_id}/approve` | R | task_id 1-80; reason 5-2000 | Existing suite: 200 assigned, approval identity/reason/time persisted | Not-ready execution 409; reviewer enforcement inspected/tested in surrounding controls |
| EP-18 | POST `/api/agents/budgets/{investigation_id}/freeze` | R | frozen bool; emergency_stop bool default false; reason 5-2000 | 200 stores freeze/stop and audit; actual worker halted before first execution | Non-reviewer boundary; in-flight interruption not claimed |
| EP-19 | GET `/api/agents/permissions` | R | None | 200; 15 default records after plan, including change history | Unauthenticated 401; non-reviewer 403; no writes |
| EP-20 | POST `/api/agents/permissions` | R | known agent_id; execute/external_service/sign_transaction; allowed bool | 200 persists execute toggle/history; actual denied execution/retry tested | Unknown agent 422; granting signing 422; external_service setting is not enforced on provider calls |

Sixteen protected route forms were probed without authentication and returned 401; confirmation was checked separately and also returned 401. Existing suites supplement the independent probes, especially threshold approval and mocked confirmation. This is not an exhaustive cross-product of every payload, role, concurrency state, and endpoint.

## 6. Test Results

### Commands and Outcomes

Commands ran from `/workspaces/TRIPLEES`. Backend/Alembic commands used explicit temporary `VERICARB_DATA_DIR` and `DATABASE_URL`, development mode, and cleared signing/inference credentials; no ordinary test command targeted the existing workspace database.

| Command / Check | Outcome |
| --- | --- |
| `python -m pytest services/api/tests -q` | 36 passed initially in 9.91s; 36 passed after fixes in 8.84s; 3 deprecation warnings |
| `python -m pytest services/api/tests/test_api.py::test_public_near_verification_rehashes_the_supplied_report -q` | 1 passed; includes numeric/bool/list/object timestamp rejection after fix |
| `python -m compileall -q services/api/app services/api/worker.py services/api/migrations` | PASS |
| `for script in frontend/assets/js/*.js; do node --check "$script"; done` | All 5 JavaScript files PASS |
| `npm --prefix /workspaces/TRIPLEES/services/contracts test` | 7 passing Hardhat tests |
| `npm --prefix /workspaces/TRIPLEES/services/contracts run compile` | PASS, initially cached |
| `npm --prefix /workspaces/TRIPLEES/services/contracts run compile -- --force` | 2 Solidity files compiled, EVM target paris |
| `npm --prefix /workspaces/TRIPLEES/services/contracts/near-report-registry test` | 8 Rust tests + 1 actual near-workspaces sandbox test PASS |
| `python -m alembic -c alembic.ini upgrade head` on fresh scratch SQLite | PASS, full chain |
| `python -m alembic -c alembic.ini downgrade 20261103_report_anchors` then `upgrade head` | PASS, both new revisions reversed and reapplied |
| `python -m alembic -c alembic.ini current` | `20261113_agent_coordination (head)` |
| `python -m alembic -c alembic.ini check` | Initially FAIL on model-usage timestamp index drift; PASS after ORM metadata fix |
| `python /tmp/triplees-final-audit-fdf58363/api_probe.py` with isolated env | Initial 30 PASS/3 FAIL; fresh-state retest 31 PASS/2 FAIL; 80 recorded calls |
| Actual `python -m services.api.worker --once` against browser runtime DB | PASS; all five actual agents, report generation and budget charging |
| Failure-only provider spy through actual worker | External permission false, provider generation attempted once, network calls zero: enforcement defect confirmed |
| Additional local NEAR initializer probe | First caller can initialize uninitialized instance; atomic init required |
| Real read-only NEAR/X1 RPC checks | PASS for network identity, X1 code/receipt/records; no TRIPLEES NEAR commitment available |
| Direct security probes | 10 MB+1 upload 413; four private static paths 404; untrusted CORS preflight 400/no allow-origin; unauthenticated confirm 401 |
| Budget/query boundary probes | Total/per-agent limits below allocations 409; task limit=0 gives 422 |
| Browser navigation/responsiveness/restart | PASS for exercised happy path, 390px and 1440px views; report/task/budget state and session survive restart |
| Browser report download completion | NOT TESTED successfully: handler/toast ran, integrated browser download event timed out |
| Frontend build/lint/unit-test and static type check | NOT CONFIGURED; no such scripts/configuration found; syntax/browser checks are not substitutes |
| `git diff --check` and editor diagnostics for touched Python files | PASS at audit checks; no reported diagnostics |

Tested environment: Python 3.14.2, Node 24.22.2, npm 11.19.1, cargo-near 0.23.0, contract-local Rust 1.86.0. Warnings concern FastAPI/Starlette httpx test-client usage, legacy websockets, and Alembic path separator configuration, not failing assertions. A dev pytest dependency is not declared in the runtime requirements; pytest was already available here.

### Independent Failure Reproductions

1. Execute the Evidence task alone. Reassign the still-assigned Registry Integrity task to its alternative Evidence Analyst bid. Assignment returns 200 and execution returns 202. Worker finishes the investigation as completed, but execution count stays **1**, and the reassigned task remains **assigned**. Root: completed-agent-key deduplication is not task execution tracking.
2. Complete a normal five-task run. Update its budget threshold from 1.25 to 0.1. Response is 200, but **all five completed tasks become awaiting_review**, retaining terminal timestamps/results. Root: budget update mutates every task without terminal-state guards.
3. Before the audit fix, public verification with `created_at:123` returned 500. The focused regression and fresh independent retest now receive 422.
4. A monitoring observation with `observed_at:"not-a-date"` still returns 201. Calling the actual frontend `niceDateTime` with that value raises `RangeError: Invalid time value`. This was isolated from the working browser demo data.

### Browser Evidence and Limits

The actual uploaded sample SHA-256 was `eef7cfd7fcd188c7c5b270a8d3be833ebf2361742236f43f85d84317938c8df9`. Runtime investigation: `INV-F99DC4764770`. Version-2 digest: `4deefd82286435b702254185485193a4350a7dd3c36d38e8bd4d99f0ef371bea`.

The browser displayed five executions, five tasks, two findings, both report versions, and budget values 10 total/4 allocated/4 spent/6 remaining. A reasoned finding review returned HTTP 200; local digest approval returned approved with a null transaction hash. Screens for Projects, Credits, Monitoring, Evidence, Verification, Registry Conflicts, Exports, Public Explorer, Marketplace, Community, Settings, and Intelligence Dashboard loaded their intended headings. No uncaught page errors were captured on these valid-data paths.

At a 390px viewport the document measured 375px wide, report right edge 359px, NEAR panel right edge 343px. Mobile navigation opened and closed after navigation. Screenshots of the desktop dashboard, real wallet chooser, and mobile report were captured in the audit conversation; no screenshot image files were added to the repository. Host browser focus/file-path limitations required DOM event dispatch and an in-memory upload of the exact repository bytes; no successful API/chain response was injected.

Artifacts retained locally: temporary probe script/results, public-chain check JSON, X1 read-back JSON, and restart baseline under `/tmp/triplees-final-audit-fdf58363/`. These are not checked-in application features or permanent CI tests.

### Not Tested

Live NEAR deployment/reviewer grants/signatures/transaction reconciliation/real public digest matches or mismatches; real connected-wallet account identification/disconnection/network switching; live Nemotron inference, billing, research or monitoring feeds; PostgreSQL, live S3, container deployment, production identity, multi-worker concurrency/lease races, load/DoS, browser matrix/accessibility conformance, complex/scanned PDF corpus, complete artifact download delivery, and mainnet operation. No explorer source-verification result is claimed for either chain.

## 7. Security Findings

No Critical exploit was established within this audit. This is not a formal security certification. Severity below distinguishes verified behavior from source-only risks.

### High

**H1. Public demo access grants administrative power if exposed beyond a disposable demo.** [Demo authentication](../services/api/app/main.py#L392) issues the shared seeded admin session without a password. The browser actually used that admin to review/approve records. Production startup is deliberately blocked, but publicly hosting development mode with private data or X1 signing keys would expose trusted controls. Keep it isolated, synthetic, keyless, and access-restricted; do not treat changing the token secret as fixing shared demo-admin access.

**H2. External-service permissions do not gate external provider calls.** [Permission defaults](../services/api/app/services/agent_coordination.py#L45) deny external_service, but [worker context](../services/api/worker.py#L141) and [model invocation](../services/api/app/services/agents/common.py#L123) use per-investigation consent without consulting that permission. The failure-only spy confirmed one generation attempt while the permission was false, with no network call. Enforce both controls or remove the misleading blocked-service guarantee before using sensitive evidence.

### Medium

**M1. Reassignment can report successful investigation completion without executing the task.** [Worker completed-key logic](../services/api/worker.py#L205) skips an agent already completed on another task. Confirmed with real agents/API, not a fake successful output. Bind executions and deduplication to task IDs and requested task work; do not mark the investigation complete while assigned work is silently outstanding.

**M2. Budget updates corrupt terminal task states.** [Budget update loop](../services/api/app/agent_routes.py#L296) changes completed tasks to awaiting_review when the threshold is lowered. All five terminal tasks were affected in the probe. Restrict approval-state changes to eligible pending tasks and preserve completed/failed/cancelled history.

**M3. Wrong transaction/account choices can leave pending commitments without a recovery path.** [Confirmation](../services/api/app/near_routes.py#L199) saves the hash before verification; mismatch errors do not clear it. Preparation/confirmation reject replacement hashes, and a different pending account also conflicts. This is a source-inspection finding; no live wrong transaction was invented to demonstrate it. Add explicit, audited reconciliation/cancel/expiry/rebind behavior before a wallet demo.

**M4. Invalid observation dates are accepted and unsafe to render.** [Observation schema](../services/api/app/schemas.py#L109) accepts arbitrary length-bounded strings, while [frontend formatter](../frontend/assets/js/app.js#L108) throws on invalid dates. Confirmed API 201 plus actual formatter RangeError. Validate dates and make rendering defensive; test malformed data without poisoning a shared demo.

### Low / Operational Risks

- **L1. Initialization/storage/upgrade trust:** a first caller can initialize an undeclared owner; use atomic initialization. Reviewer writes consume contract-funded storage, with no tested storage-deposit/capacity policy. Full-access account keys remain an upgrade trust boundary. No public deployment existed to assess key custody.
- **L2. Inference-success limitation text:** [Independent Review](../services/api/app/services/agents/review.py#L100) merges local-output limitations into the successful model path, apparently retaining the statement that the adversarial model call was not performed. Source-only observation; add a focused model-success regression before making live inference claims.
- **L3. Deployment/test hardening:** no CI/container recipe or declared dev pytest requirement; dynamic wallet CDN delivery has no application-level integrity pin; no complete request-rate/ingress-body/parser-resource policy was verified. Existing source escaping/parameterized ORM queries reduce common XSS/SQL-injection risks but do not constitute penetration-test coverage.
- Wallet ownership challenge/nonces/expiry are absent, not silently provided by application bearer sessions. No public claim should imply wallet-based authentication.

### Safe Issues Fixed During This Audit

| Issue | Before | Change | Verification |
| --- | --- | --- | --- |
| Malformed public report timestamp | Anonymous verification could return 500 for numeric/object/list/bool timestamps | Type guard in `_utc_iso`; added four malformed-shape cases to existing API test | Focused test PASS; independent probe now 422; full 36-test suite PASS |
| ORM/migration timestamp-index mismatch | `alembic check` proposed removing existing `ix_model_usage_created_at` | Added `index=True` to ModelUsage timestamp declaration; no migration history rewrite | Scratch-schema `alembic check`: no new operations |
| Obsolete sandbox status text | README still claimed current sandbox failure | Corrected three status paragraphs and one stale deployment-gate sentence | Targeted stale-text/whitespace checks PASS |

No coordination redesign, authentication change, payment feature, or deployment was attempted. Pre-existing NEAR dependency/toolchain fixes and documentation edits were preserved. A local ignored VS Code audit-server task was generated; temporary probe code/data stayed outside the repository.

## 8. End-to-End Workflow

The UI combines creation with queueing, so the browser audit uploaded/extracted the sample before using Create and queue. Separate draft/run APIs were also exercised. The numbered capability checks below do not pretend the UI offers a separate draft/attach/run wizard.

| Step | Requested Action | Result | Evidence / Missing Dependency |
| --- | --- | --- | --- |
| 1 | Open application | PASS | Actual API-served auth/dashboard, health/readiness 200 |
| 2 | Create investigation | PASS | Real browser form created the persisted scoped investigation |
| 3 | Upload sample environmental evidence | PASS | Existing explicitly synthetic repository sample, HTTP 201; not real environmental evidence |
| 4 | Run extraction | PASS | Actual extraction saved 14 source chunks and zero invented claims |
| 5 | Start agent investigation | PASS | Actual queued job processed with documented worker entry point |
| 6 | Verify five agents execute | PASS | Five actual persisted executions, all completed with limitations |
| 7 | Inspect task assignments | PASS | Five persisted default tasks/proposals displayed; alternate reassignment defect separately reported |
| 8 | Inspect findings | PASS | Actual duplicate import finding and synthetic monitoring hypothesis with references |
| 9 | Generate final investigation report | PASS | Worker report version 1; review-generated version 2; this is not an externally validated final opinion |
| 10 | Approve report using reviewer workflow | PASS | Reasoned finding review plus separate local X1 digest approval; not NEAR transaction approval/confirmation |
| 11 | Generate SHA-256 report digest | PASS | Actual report digest rehash matches; unchanged through restart |
| 12 | Connect NEAR testnet wallet | NOT TESTED | Real chooser opened/cancelled, but no user wallet/account connected |
| 13 | Prepare report commitment | PARTIAL | Actual pending-record API tested only with undeployed isolated config; main demo correctly disabled |
| 14 | Sign transaction | NOT TESTED | No wallet/account or deployed registry; no signature requested |
| 15 | Confirm transaction | NOT TESTED | No real TRIPLEES NEAR transaction; mocked suite is not this demo step |
| 16 | Retrieve smart-contract commitment | NOT TESTED | No public TRIPLEES NEAR deployment/commitment; local sandbox view is separate |
| 17 | Verify original report against NEAR | NOT TESTED | Local canonical digest PASS, but no real public record to compare |
| 18 | Modify report | PASS | Independent probe changed only an in-memory report-copy summary, preserving stored original |
| 19 | Verify modified report against NEAR | NOT TESTED | Local digest differs; public chain comparison cannot run |
| 20 | Confirm modified report is a mismatch | NOT TESTED | Mocked API mismatch test passes, but real public NEAR mismatch not demonstrated |

## 9. Missing Features and Coverage

- A deployed NEAR registry, user-controlled reviewer wallet, on-chain reviewer grant, and genuine end-to-end signed commitment/mismatch demonstration.
- Wallet ownership authentication/challenge/nonce expiry if account identity becomes a product/security promise. It is not currently app login.
- Recovery/cancellation/expiry for abandoned or incorrectly bound pending commitments.
- Correct task-level execution identity and terminal-state handling under reassignment/budget updates.
- Enforced external-service permissions; safe observation-date validation/rendering.
- Live research provider wiring, satellite/IoT feeds, live model inference verification, and real agent payments. Do not build payments merely to relabel internal accounting.
- Production identity/session/recovery controls and a safe reviewer provisioning process. Production startup is intentionally blocked.
- Reproducible frontend/browser CI, declared development test dependencies, container/release automation, PostgreSQL/live-storage/concurrency testing, and broader contract negative/fuzz/storage testing.
- OCR for scanned PDFs and completed-browser-download evidence. These are not supplied by existing embedded-text extraction or API JSON retrieval.

## 10. Immediate Fixes

| Priority | Work | Acceptance Evidence |
| --- | --- | --- |
| P0 | Repair task/execution identity, reassignment, and investigation completion criteria | Reproduce the accepted alternate assignment with real roles; task completes with a new execution/result; no silent outstanding work |
| P0 | Enforce external-service permission as well as explicit per-run consent | Blocked permission produces zero provider-generation attempts; allowed+consented test reaches only the intended provider |
| P0 before any live NEAR claim | User-reviewed account/deployment/reviewer setup, then genuine signed report commitment and public original/modified verification | Real transaction hash/receipt, contract read-back, original VERIFIED, modified MISMATCH; do not fabricate these results |
| P1 | Preserve terminal tasks during budget edits; repair pending-commitment recovery | Terminal-state regression and wrong-account/hash/RPC-outage recovery tests |
| P1 | Validate monitoring timestamps and make date rendering defensive | Invalid strings rejected with 422; legacy bad data cannot crash a page |
| P1 before sharing beyond a disposable demo | Restrict shared admin/demo access and keep all signer/provider secrets and private evidence out | Explicit access boundary; no untrusted user obtains operational privileges |
| P2 | Add missing test/deployment tooling and negative/concurrency tests; fix contradictory model-success limitation text | Repeatable clean setup/CI, correct model-success metadata, lease/concurrency and storage-capacity evidence |

These priorities do not authorize deployment or token spending. The audit did not verify any external hackathon submission rules or submit anything.

## 11. Hackathon Readiness

**PARTIALLY READY overall.** A truthful local product demonstration is ready: evidence hashing/extraction, supplied registry/monitoring analysis, five sequential analytical roles, findings, review/versioning, report digest, and internal simulated coordination. The real wallet chooser can also be shown without implying a connected account or transaction.

**Not submission ready as a completed live NEAR integration.** The public deployment/signature/confirmation/verification chain is missing, and the coordination overlay has confirmed execution/state defects. Do not describe the system as a swarm, live environmental monitoring/research service, live Nemotron deployment, payment system, or production certification platform.

The X1 component has stronger public-chain evidence: current compiled bytecode and historical records were independently checked. That does not establish that new application actions are currently configured to sign X1 transactions, nor does it substitute for NEAR evidence.

## 12. Demo Instructions

### Current Verified Instance

The isolated API was left running at **http://127.0.0.1:8001/auth.html** using temporary audit data. The secondary port-8002 wallet-test server was stopped. In VS Code the ignored task is named **TRIPLEES isolated audit API**. Do not start a second listener on port 8001 while it is already running.

1. Choose Explore the demo workspace. It is a synthetic shared-admin demo; enter no confidential data.
2. Open Evidence. Inspect `demo_project.json`, its hash above, and its saved extraction. The existing synthetic baseline fixture is separate.
3. Open Investigation Center. Select Demo Forest Project and the uploaded JSON, enter a bounded question, and leave both external-service consent boxes unchecked. Create and queue a new investigation.
4. From a repository-root terminal, process the queued work against the **same** isolated database:

```bash
cd /workspaces/TRIPLEES
env APP_ENV=development \
  VERICARB_DATA_DIR=/tmp/triplees-final-audit-fdf58363/runtime \
  DATABASE_URL=sqlite:////tmp/triplees-final-audit-fdf58363/runtime/audit.sqlite3 \
  NEBIUS_API_KEY= X1_TESTNET_RPC_URL= \
  X1_DEPLOYER_PRIVATE_KEY= X1_REGISTRAR_PRIVATE_KEY= X1_REVIEWER_PRIVATE_KEY= \
  python -m services.api.worker --once
```

5. Refresh Agent Activity. Show the five executions, limitations, default task plan, simulated proposals, and real persisted internal-unit totals. Do not demonstrate alternate-agent reassignment as working until M1 is fixed.
6. Inspect Risk Intelligence/Review Queue. Confirm only the supplied-record fact with a clear reason, not an environmental conclusion. Open Investigation Reports and compare versions.
7. Show the digest and local approval. Submit-to-X1 remains disabled without configuration; NEAR remains disabled. Do not click or claim chain submission.
8. Show existing investigation `INV-F99DC4764770` to reproduce the saved audit result. Report version 2 and its digest survived restart.
9. Explain that local digest comparison detects canonical-field changes. Do not show a mocked transaction or simulated VERIFIED result as a public-chain demonstration.

If the API task has stopped, this is the tested entry point, with equivalent isolated settings. A fresh token secret requires a new browser login; generate it locally without printing it:

```bash
cd /workspaces/TRIPLEES
export APP_ENV=development AUTO_MIGRATE=true SEED_DEMO_DATA=true
export VERICARB_DATA_DIR=/tmp/triplees-final-audit-fdf58363/runtime
export DATABASE_URL="sqlite:///${VERICARB_DATA_DIR}/audit.sqlite3"
export VERICARB_TOKEN_SECRET="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
export NEAR_ENABLED=false NEAR_REPORT_COMMITMENTS_ENABLED=false
export NEAR_REPORT_REGISTRY_CONTRACT_ID= OBJECT_STORAGE_BUCKET= NEBIUS_API_KEY=
export X1_TESTNET_RPC_URL= X1_REGISTRY_CONTRACT_ADDRESS= X1_REPORT_ANCHOR_CONTRACT_ADDRESS=
export X1_DEPLOYER_PRIVATE_KEY= X1_REGISTRAR_PRIVATE_KEY= X1_REVIEWER_PRIVATE_KEY=
python -m uvicorn services.api.app.main:app --host 127.0.0.1 --port 8001
```

Dependencies are already installed in this environment. A fresh environment needs the API requirements, an explicitly installed pytest for tests, contract npm dependencies, Rust/rustup, and cargo-near for the optional NEAR checks. No frontend build command is required. For a source-only contract demonstration without a public transaction, run the tested npm test command in Section 6.

## Appendix: Complete NEAR Change Inventory

Commit `c4e36d8` compared with `3bae980`: **18 added, 13 modified**. These paths were inspected as implementation, integration, test, or documentation surfaces; file existence alone was not used as PASS evidence.

| Change | Path | Purpose |
| --- | --- | --- |
| Added | [docs/AGENT_COORDINATION.md](AGENT_COORDINATION.md) | Coordination design/limits |
| Added | [docs/HACKATHON_CHANGES.md](HACKATHON_CHANGES.md) | Extension summary |
| Added | [docs/NEAR_ARCHITECTURE.md](NEAR_ARCHITECTURE.md) | NEAR architecture/build |
| Added | [docs/NEAR_IMPLEMENTATION_PLAN.md](NEAR_IMPLEMENTATION_PLAN.md) | Plan/baseline/gates |
| Added | [docs/REPORT_VERIFICATION.md](REPORT_VERIFICATION.md) | Canonical digest and deployment procedure |
| Added | [docs/SECURITY.md](SECURITY.md) | Stated security boundaries |
| Added | [services/api/app/agent_routes.py](../services/api/app/agent_routes.py) | 13 coordination endpoints |
| Added | [services/api/app/near_routes.py](../services/api/app/near_routes.py) | 7 NEAR endpoints |
| Added | [services/api/app/services/agent_coordination.py](../services/api/app/services/agent_coordination.py) | Task/bid/budget/permission logic |
| Added | [services/api/app/services/near_chain.py](../services/api/app/services/near_chain.py) | Read-only RPC verification |
| Added | [services/api/migrations/versions/20261113_agent_coordination.py](../services/api/migrations/versions/20261113_agent_coordination.py) | Five coordination tables/requested-agent column |
| Added | [services/api/migrations/versions/20261113_near_report_commitments.py](../services/api/migrations/versions/20261113_near_report_commitments.py) | NEAR commitment table |
| Added | [services/contracts/near-report-registry/Cargo.toml](../services/contracts/near-report-registry/Cargo.toml) | Rust package |
| Added | [services/contracts/near-report-registry/Cargo.lock](../services/contracts/near-report-registry/Cargo.lock) | Rust dependency lock |
| Added | [services/contracts/near-report-registry/package.json](../services/contracts/near-report-registry/package.json) | Build/test scripts |
| Added | [services/contracts/near-report-registry/package-lock.json](../services/contracts/near-report-registry/package-lock.json) | Sandbox dependency lock |
| Added | [services/contracts/near-report-registry/src/lib.rs](../services/contracts/near-report-registry/src/lib.rs) | Contract/host tests |
| Added | [services/contracts/near-report-registry/tests/report-registry.sandbox.test.mjs](../services/contracts/near-report-registry/tests/report-registry.sandbox.test.mjs) | Actual sandbox integration test |
| Modified | [.env.example](../.env.example) | Public NEAR settings/internal-coordination flags |
| Modified | [.gitignore](../.gitignore) | Rust target exclusion |
| Modified | [README.md](../README.md) | Extension/setup/status |
| Modified | [frontend/assets/css/workspace-ui.css](../frontend/assets/css/workspace-ui.css) | Wallet/task/budget styles |
| Modified | [frontend/assets/js/app.js](../frontend/assets/js/app.js) | Wallet, task/budget, report UI and actions |
| Modified | [frontend/assets/js/report-verify.js](../frontend/assets/js/report-verify.js) | NEAR public report-copy UI |
| Modified | [services/api/app/config.py](../services/api/app/config.py) | NEAR and coordination settings |
| Modified | [services/api/app/investigation_routes.py](../services/api/app/investigation_routes.py) | Plan/queue/budget coordination gates |
| Modified | [services/api/app/main.py](../services/api/app/main.py) | Router registration |
| Modified | [services/api/app/models.py](../services/api/app/models.py) | New persistence models |
| Modified | [services/api/app/services/report_anchoring.py](../services/api/app/services/report_anchoring.py) | Rehash downloaded report representation |
| Modified | [services/api/tests/test_api.py](../services/api/tests/test_api.py) | Mocked NEAR API and coordination coverage |
| Modified | [services/api/worker.py](../services/api/worker.py) | Task selection/accounting/status overlay |

At audit start, six of the above files already had uncommitted compatibility/documentation edits, and [rust-toolchain.toml](../services/contracts/near-report-registry/rust-toolchain.toml) was a new uncommitted file. This audit preserved them. Audit-created application edits are limited to the timestamp validation/test, ORM index metadata, README/deployment-gate wording, and this report. No migration, contract, frontend, or coordination implementation was changed by this audit.