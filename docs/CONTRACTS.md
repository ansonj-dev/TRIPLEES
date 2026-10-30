# Smart contract reference

## `VericarbRegistry`

Existing registry contract, compiled with the repository's Hardhat Solidity toolchain. A separate report-anchor contract exists in source but has not been deployed.

- **Project:** `registerProject`, `getProject`; project ID is unique `bytes32`, and registry/methodology references are stored as hashes with vintage years and registrar.
- **Batch:** `registerCreditBatch`, `getCreditBatch`; batch IDs cannot repeat, quantities are positive integer kg CO2e, balances are integer kg, and batches link to a project and evidence/reference hash.
- **Evidence:** `anchorEvidence`, `getEvidenceAnchor`; unique evidence ID, exact backend SHA-256 digest, project/batch references, evidence type hash, submitter, and timestamp. File bytes stay off-chain.
- **Roles:** admin, issuer, oracle, verifier; role updates are admin-only. Registration/anchoring require issuer, risk updates require oracle, reviewer decisions require verifier.
- **Lifecycle:** transfers enforce balance and active state; retirement consumes only held balance; risk/review actions preserve history and cannot undo a retirement.
- **Audit:** state-change events and append-only `getBatchHistory` records.

The registry is recorded as deployed on X1 EcoChain Maculatus Testnet; see [Deployment and verification](DEPLOYMENT_AND_VERIFICATION.md). Explorer source verification was not performed, and the contract has not received an independent audit. The report-anchor contract is separate and its deployment was not performed.

## Unit model

All quantities are integer **kilograms of CO2 equivalent** (`kg CO2e`). `1 tCO2e = 1,000 kg CO2e`. Solidity uses integer amounts; no floating-point balances.

## Local validation

From `services/contracts`, run `npm test` and `npm run compile`. Tests use Hardhat's local chain and do not use X1 funds. Testnet deployment, role setup, and verification are separate commands.
