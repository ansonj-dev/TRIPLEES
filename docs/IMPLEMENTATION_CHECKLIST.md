# X1 Testnet integration checklist

- [x] Inspect existing FastAPI/SQLite app, Alembic schema, static dashboard, Hardhat project, and acceptance tests.
- [x] Check current worktree context; this directory has no `.git` metadata.
- [x] Confirm Maculatus identity through the official X1 developer portal and linked explorer.
- [x] Query the configured X1 RPC candidate: `eth_chainId` returned `0x2a1a` (10778), and `eth_blockNumber` returned a live block.
- [x] Extend the contract for projects, batches, evidence anchors, roles, and lifecycle events.
- [x] Add testnet configuration validation, safe wallet introspection, and read-only network health.
- [x] Add confirmed receipt/state verification for project registration, evidence anchors, and reviewed batch issuance; persist references in project/evidence/batch fields and lifecycle events.
- [x] Expose API and dashboard network/contract/confirmed transaction status without fabricated values.
- [x] Add X1 migration, contract/API checks, and setup/runbook documentation.
- [x] Run compile, migration, contract, backend, JavaScript syntax, and live read-only RPC checks.
- [x] Live three-wallet deployment, role verification, API project/evidence/batch flow, duplicate issuance rejection, and small-quantity transfer/retirement/risk/reviewer testnet lifecycle.

Known implementation gap: transfer, retirement, risk, and reviewer decisions still use local database history and have not yet been wired to on-chain lifecycle methods. A separate pending transaction queue/idempotency table is also future work; current write endpoints wait synchronously for a receipt and use contract uniqueness/state checks on retries.

Network facts and the exact verification time are documented in `docs/X1_TESTNET_SETUP.md`.
