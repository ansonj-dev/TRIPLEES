# Investigation report anchoring on X1

Phase 7 adds an optional X1 Maculatus commitment flow. It preserves the existing `VericarbRegistry` deployment and uses a separate, append-only `InvestigationReportAnchorRegistry` contract for report hashes.

## Data stored on X1

The contract stores only an opaque random anchor key, the 32-byte SHA-256 digest, the report version, the anchorer address, and the block timestamp. It does not store report text, findings, project identifiers, evidence, reviewer identity, or approval reason. The old registry source, ABI behavior, and configured address remain unchanged.

The report digest uses `triplees-canonical-json-v1`: JSON containing the report schema name and the stable report fields `id`, `version`, `status`, `summary`, `limitations`, `content`, and `created_at`; object keys are sorted, whitespace is removed, UTF-8 is used, and non-finite numbers are rejected. Mutable anchor metadata and `available_versions` are excluded. SHA-256 is computed over those canonical bytes.

## Approval and submission

1. The API returns the digest for an authenticated report version.
2. A reviewer or admin approves that exact digest with a reason. This writes an append-only audit event and creates an opaque anchor reference; it does not contact X1.
3. A separate confirmation screen names the X1 network, chain ID, destination contract, digest, report version, and gas-paying reviewer signer. The reviewer must confirm that transaction before the server uses `X1_REVIEWER_PRIVATE_KEY` to submit it.
4. The API stores the transaction hash immediately after broadcast, waits for confirmation, reads the commitment back from the contract, and stores chain ID, contract address, block, and time.
5. If transaction state is uncertain, the API requires reconciliation before another submission. The contract also rejects a duplicate anchor key.
6. The public verification page shows commitment metadata and checks the on-chain digest without returning report content.

The AI agents do not receive signer credentials and cannot call the submission endpoint. Reviewer approval and transaction confirmation are separate human actions.

## Local checks

The contract tests run on Hardhat's local in-memory chain:

```powershell
npm --prefix services\contracts run compile
npm --prefix services\contracts test
```

The backend tests use an isolated SQLite database and mock the chain when exercising writes. No X1 RPC call or transaction is needed for the test suite.

## Optional testnet deployment (not performed)

Deployment creates a **new separate contract**; it does not replace or upgrade the existing registry. Do not run these steps until deployment has separate explicit approval.

1. Compile the contracts and review the generated artifact and deployment script.
2. Set `X1_TESTNET_RPC_URL`, `X1_TESTNET_CHAIN_ID=10778`, `X1_DEPLOYER_PRIVATE_KEY`, and `X1_REVIEWER_PRIVATE_KEY` in the ignored local `.env`. Use distinct deployer and reviewer wallets. Never place keys in tracked files.
3. Run preflight only:

   ```powershell
   node services\contracts\scripts\deploy-report-anchor-testnet.js
   ```

   It prints the chain, public addresses, and maximum estimated gas, then stops without a transaction.

4. After separately approving deployment and role assignment, run:

   ```powershell
   node services\contracts\scripts\deploy-report-anchor-testnet.js --confirm-testnet
   ```

5. Copy the resulting address into the ignored `.env` as `X1_REPORT_ANCHOR_CONTRACT_ADDRESS=...`, then restart the API. The script grants the reviewer wallet the anchoring role and revokes the deployer's anchoring role. The deployer remains contract admin.

There is no verified X1 deployment address for this new contract until a user separately approves and completes the deployment. The existing registry address must remain as configured.

## API

- `POST /api/investigations/{investigation_id}/reports/{report_id}/anchor/approve` — reviewer/admin approval with reason.
- `POST /api/report-anchors/{anchor_id}/submit` — requires `{"confirm_submission": true}` and configured chain, contract, and reviewer signer.
- `POST /api/report-anchors/{anchor_id}/reconcile` — read-only chain check used to resolve an uncertain submission.
- `GET /api/public/report-anchors/{anchor_id}` — public digest and transaction verification metadata; no report content.
