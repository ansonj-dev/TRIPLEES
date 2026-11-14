# NEAR Implementation Plan

Audit date: 2026-11-13

## Existing Architecture

- Frontend: static HTML, CSS, and vanilla JavaScript under `frontend/`; FastAPI serves the pages and authenticated workspace.
- API: FastAPI routes and services under `services/api/app/`, authenticated by the existing prototype bearer-token system.
- Persistence: SQLAlchemy models with Alembic migrations; SQLite is the local default and PostgreSQL is supported. Changes must be additive.
- Investigations: `investigation_routes.py`, five scoped agent implementations, and `services/api/worker.py` provide queued, retryable, cancellable execution, structured findings, audit history, reviewer decisions, and immutable report snapshots.
- Reports: `services/report_anchoring.py` defines `triplees-canonical-json-v1` and SHA-256. Existing report commitments are implemented separately for X1 in `report_anchor_routes.py` and `InvestigationReportAnchor`.
- Existing blockchain: `services/api/app/services/x1_chain.py` and `services/contracts/` support X1 EcoChain. This implementation, its addresses, configuration, and workflows remain independent and unchanged.
- Existing AI: five specialized agents and a configurable Nebius Token Factory provider. Live inference and external research depend on separately configured credentials/providers.

## Existing Working Functionality

- Evidence upload, SHA-256 fingerprinting, opt-in PDF/CSV/JSON/TXT extraction, source references, registry import conflict checks, and imported/synthetic monitoring observations.
- Five bounded agents: Evidence Analyst, Research Investigator, Integrity Analyst, Monitoring Analyst, and Independent Review Agent.
- Persistent investigation runs, structured findings, audit events, versioned reports, reviewer decisions, and deterministic report hashing.
- Separately configured X1 project/evidence/batch actions and reviewer-approved X1 report-digest anchoring. X1 transfers and retirements in the main application remain local workflows.
- Local API and Solidity test paths; no live Nebius inference, new-chain deployment, or production authentication is implied by those tests.

## Baseline and Environment

- Repository worktree was clean before this audit.
- Pre-change baseline: `python -m pytest services/api/tests -q` passed 30 tests after installing pytest; `npm --prefix services/contracts test && npm --prefix services/contracts run compile` passed 7 Hardhat tests and compilation.
- Current regression: 36 API tests, 8 NEAR host contract tests, and 7 X1 Hardhat tests pass. Both modified frontend scripts pass `node --check`; the complete Alembic chain upgrades on temporary SQLite.
- Rust and `cargo-near` were installed locally. `cargo near build non-reproducible-wasm` builds the registry. The near-workspaces 5.0.0 sandbox test was attempted with both cargo-near and plain cargo Wasm; both fail with `PrepareError::Deserialization`. This remains unresolved and is not reported as passing.
- No NEAR deployment, reviewer grant, wallet signature, or testnet transaction has been attempted.
- The current official hackathon guide is linked at `https://nearhackathon.com/HACKATHON.md`; its submission instructions require human confirmation before submission, publicizing, posting, transactions, or deployments.

## Files To Extend

- `services/api/app/config.py` and `.env.example`: non-secret NEAR testnet settings and fail-closed feature flags.
- `services/api/app/models.py`, a new Alembic revision, and the API migration chain: append-only NEAR report commitment records.
- `services/api/app/main.py` or a focused router, plus the existing investigation/report service: prepare and verify wallet-signed commitments without changing X1.
- `frontend/app.html`, `frontend/assets/js/app.js`, and existing styles: a restrained NEAR account/commitment panel in the report workspace.
- `README.md` and focused NEAR documentation: actual setup, demo, and limitations.

## New Files Planned

- `services/contracts/near-report-registry/`: Rust contract, Cargo/npm manifests, host tests, and near-workspaces sandbox test, separate from Hardhat/X1.
- Additive API routes/models/migrations for commitments and agent coordination, plus focused tests in the existing pytest suite.
- `docs/NEAR_ARCHITECTURE.md`, `docs/AGENT_COORDINATION.md`, `docs/REPORT_VERIFICATION.md`, `docs/SECURITY.md`, and `docs/HACKATHON_CHANGES.md`.

## NEAR Integration Design

- Testnet only. Wallet integration follows current official NEAR Connect documentation (`@hot-labs/near-connect` 0.12.0); the RPC is checked for `chain_id == "testnet"` before use.
- `TripleESReportRegistry` stores only a validated report digest, investigation identifier, version, optional non-sensitive metadata digest, submitter account, and block timestamp. It uses owner-managed reviewer permissions, rejects duplicate investigation/version pairs, and emits NEP-297 events.
- The existing canonical report payload and SHA-256 are reused; report bytes, evidence, personal details, and reviewer reasons remain off-chain.
- The API prepares a reviewer-approved commitment. The browser wallet signs the contract call; no shared signing key is introduced. Confirmation is pending until the API independently checks the NEAR transaction outcome and reads the expected commitment from the configured contract.
- Public verification compares the digest of the exact canonical report bytes with a testnet contract view result. It attests only to digest integrity, not claim truth.
- X1 and NEAR have separate network labels, settings, contract addresses, and code paths.
- Optional service payments remain disabled; internal budgets are not NEAR token balances.

## Database Migration Plan

- Add a new Alembic revision after `20261103_report_anchors`; do not edit or squash existing revisions.
- Add a `near_commitments` table with unique `(investigation_id, report_version)`, report digest, NEAR account, contract, transaction hash, testnet network, pending/confirmed/failed status, timestamps, and a report foreign key.
- Store no wallet secret, seed phrase, full report, or confidential evidence. Avoid adding account ownership/authentication claims until a documented wallet-signature challenge flow is implemented.
- Preserve existing records and keep migrations reversible where practical.

## Security Considerations

- Reject any non-testnet network and any contract ID that does not match server configuration.
- Validate NEAR account IDs, digest length/hex, report ownership, reviewer role, report version, and transaction hash.
- A browser-provided transaction hash is an untrusted lookup key, never proof of success; verify signer, receiver, method arguments, execution status, and final contract state on the configured testnet RPC.
- Do not request or persist wallet secrets. Do not submit transactions from the API. Keep public verification responses free of report contents and confidential identifiers.
- Fail closed when the contract or RPC is unavailable. Do not report confirmation before successful receipt and state verification.
- Agent outputs cannot approve reports, sign transactions, or spend NEAR. Existing X1 private-key behavior is not reused for NEAR.

## Testing Plan

- Contract: commitment success, unauthorized rejection, duplicate rejection, new version, verification, missing record, malformed digest, reviewer grant/revoke, and event behavior.
- Backend: configuration/network fail-closed behavior, report digest reuse, reviewer-only preparation, pending/confirmed/failed state, RPC transaction validation, public verification, and non-owner access.
- Frontend: disconnected/connected account, wrong network, wallet rejection, pending/success/failure, and digest match/mismatch.
- Regression: existing API/agent tests, existing X1 Hardhat tests, Python compilation, frontend JavaScript syntax, Alembic head, and contract compilation.
- Live testnet transaction and deployment are intentionally excluded without explicit human approval and configured testnet wallet/account.

## Implementation Phases

1. Audit and baseline: recorded above; add this plan before implementation.
2. NEAR report registry: add the testnet-only contract and local tests; do not deploy until compilation and tests pass and deployment is explicitly approved.
3. Wallet integration: connect/disconnect testnet wallet and use it to sign a report-commitment function call.
4. Report verification: reuse canonical SHA-256, persist pending/confirmed/failed state, verify through RPC, and expose public digest verification.
5. Coordination/budgets: extend the existing worker and agents only where practical; do not duplicate the existing five-agent workflow. Mark internal bidding/accounting as simulation, not real agents or NEAR payments.
6. Frontend: integrate account, task/coordination, budget, and report verification states into existing workspace conventions.
7. Integration/docs: test available local paths, update README and the requested focused docs, and identify manual deployment/demo gates.

## Scope Limits

No NEAR contract is deployed or configured in this checkout. Deployment and real transaction claims require a user-controlled testnet account, reviewer grant, explicit approval, and independent testnet verification. Resolve the local sandbox `PrepareError::Deserialization` before deployment. Production identity is not supported by the existing prototype. No live external research or AI inference is claimed unless separately configured and exercised.