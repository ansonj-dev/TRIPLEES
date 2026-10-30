# Test report

## Latest local verification — 2026-10-30 UTC

| Check | Result |
|---|---|
| Backend workflow tests (`python -m pytest services/api/tests -q`) | **Passed** — 27 tests, including production startup blocking, S3 adapter behavior, local evidence upload/extract/download, readiness, request IDs, worker lifecycle, and daily AI token limit. One third-party deprecation warning. |
| Python syntax (`python -m compileall -q services/api/app services/api/worker.py services/api/migrations`) | **Passed**. |
| Alembic migration graph (`python -m alembic -c alembic.ini heads`) | **Passed** — `20261103_report_anchors` is the single head. |
| PostgreSQL driver | **Installed and import-checked** — psycopg 3.3.6. No live PostgreSQL server was configured. |
| S3-compatible storage | **Adapter tested with a local fake client** — no remote bucket was configured or modified. |
| Production deploy, remote migration, GitHub push, or X1 transaction | **Not performed**. Production startup remains blocked pending production identity integration. |

The older checks below record prior contract and X1 testnet work; they were not rerun during Phase 8.

## Previously recorded checks — 2026-10-25 UTC

| Check | Result |
|---|---|
| Hardhat Solidity compile + contract tests (`npm test`) | **Passed** — 5 contract tests. |
| Backend workflow tests (`python -m pytest services/api/tests -q`) | **Passed** — 2 tests, including network/status endpoint shape, no secret response fields, and invalid wallet-address validation. |
| JavaScript syntax (`node --check frontend/assets/js/app.js`; `node --check frontend/assets/js/public-verify.js`) | **Passed** after the final UI changes. |
| Python syntax (`python -m compileall -q services/api/app`) | **Passed** after the final API changes. |
| Hardhat live network check (`npm run chain:check`) | **Passed** — connected to chain ID 10778, latest block 11859261 at check; all 3 wallet keys absent. |
| Python live RPC check | **Passed** — chain ID 10778; latest app health check block 11859271; contract address unset. |
| API migration and network/status/contracts routes via TestClient | **Passed** — migration applied; `/api/blockchain/network`, authenticated `/api/blockchain/status`, and contracts returned 200; malformed balance address returned 422. |
| Testnet deployment | **Passed** — deployed `VericarbRegistry` to `0x5BF650b0b46D40794B116c36f75DABAcF5ed9e8b`; receipt confirmed and runtime bytecode present. |
| Three-wallet role setup | **Passed** — deployer retains admin only; distinct registrar has issuer/oracle; distinct reviewer has verifier. Grants and deployer operational-role removals read back as expected. |
| API → X1 project/evidence/batch flow | **Passed** — project registered, server-computed SHA-256 anchored, 1,000,000 kg batch issued after reviewer approval, and public verification matched the confirmed values. |
| Live lifecycle contract harness | **Passed** — duplicate issuance rejected read-only; 1,000 kg transfer, 500 kg retirement, oracle risk/review opening, and reviewer decision confirmed; final state and six history entries read back. |
| Explorer source verification | **Not performed** — contract address and transaction receipts are linked, but source code has not been verified through the explorer. |

The first Hardhat run failed because `dotenv` was declared but not installed in the existing `node_modules`; `npm install --ignore-scripts` installed it, then the full suite passed. `npm install` reported 49 dependency audit findings (14 low, 10 moderate, 20 high, 5 critical); no audit remediation was applied.

The backend test fixture now uses a temporary SQLite database and evidence directory. Running the suite does not reset the local developer workspace or the persisted X1 QA passport.

Live testnet transactions were broadcast only after verified chain, signer balances, gas estimates, and role configuration. The first lifecycle harness attempt correctly rejected a duplicate batch during gas estimation; no transaction was broadcast by that attempt. After correcting the read-only duplicate-call check and post-retirement balance expectation, the lifecycle harness passed. Main app transfer/retirement/risk/reviewer routes remain local-only; the live lifecycle evidence comes from the explicit contract testnet harness.
