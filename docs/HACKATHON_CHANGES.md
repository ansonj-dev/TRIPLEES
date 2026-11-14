# NEAR Hackathon Changes

The repository history in this checkout contains TRIPLEES baseline commits through 2026-10-30. The existing product was not created during the hackathon. TRIPLEES evolved from the earlier VERICARB project; legacy environment names, browser storage keys, and the deployed Solidity contract identifier remain for compatibility.

## 1. Functionality Present Before This Extension

- Project/evidence workflows, SHA-256 evidence fingerprints, opt-in PDF/CSV/JSON/TXT extraction, registry-import conflict checks, and imported/synthetic monitoring observations.
- Five bounded agents: Evidence Analyst, Research Investigator, Integrity Analyst, Monitoring Analyst, and Independent Review Agent.
- Persistent investigations, worker retry/cancellation, findings with source references, audit history, reviewer decisions, versioned reports, and canonical report hashing.
- Existing X1 EcoChain contracts/workflows and the separate reviewer-approved X1 report anchor.
- Existing Nebius Token Factory integration code; live inference still depends on credentials and explicit per-investigation authorization.

These features remain in place. X1 contracts/addresses, AI provider, database history, and existing agents were not replaced.

## 2. Functionality Added During the Hackathon Extension

- Persisted task planning, internal proposals, deterministic agent selection, assignment history, and task results using the existing five agent implementations.
- Internal-unit investigation/agent budgets, thresholded reviewer approvals, permission history, and emergency stop.
- Authenticated coordination APIs, Alembic migrations, and Agent Activity UI.

Bids are internal software scheduling estimates, not external economic actors. `internal_units` are not NEAR tokens or money. Agent-to-agent payments are not implemented.

## 3. NEAR-Specific Functionality

- Rust `TripleESReportRegistry` with reviewer permissions, immutable report versions, digest-only records, and NEP-297-shaped events.
- NEAR Connect testnet wallet flow; the user wallet signs. The backend does not hold a NEAR signing key.
- Reviewer-approved pending commitments, RPC transaction validation, final state read-back, persistence, and public report JSON verification.
- Separate NEAR configuration and database state; X1 remains unchanged.

The NEAR registry builds and its local test suite passes: 8 host tests plus the near-workspaces sandbox test, which exercises the optimized `cargo-near` artifact. The sandbox compatibility fix pins near-sdk 5.17.2 and Rust 1.86.0 for the bundled protocol-77 sandbox. Raw `cargo build` output requires cargo-near's `wasm-opt` post-step. No live NEAR deployment or transaction is claimed.

## 4. Known Limitations

- No NEAR contract deployment, reviewer grant, wallet signature, or testnet transaction has occurred; no NEAR address or transaction hash is claimed.
- NEAR flags default to disabled. A deployed contract and on-chain reviewer grant are required to exercise the wallet flow.
- Local sandbox compatibility is verified. Backend tests mock RPC responses; there is no live NEAR end-to-end test. No browser automation test was run.
- NEAR is not application authentication. Optional payments, NEAR Intents, mainnet, live public research, and live Nemotron inference are not enabled or claimed.
- Production authentication is not integrated. TRIPLEES is an evidence-intelligence prototype, not a production certification authority.

## Submission Boundary

The official [NEAR HACKATHON guide](https://nearhackathon.com/HACKATHON.md) requires a public repository/demo post and human confirmation before submission, posting, pushing/publicizing, deployment, or token spending. None of those actions has been performed. The guide lists the submission deadline as 2026-11-14 at 23:59 UTC; check it again before submitting.