# Blockchain architecture

## Data flow

1. FastAPI validates the request, authorization, local record ownership, and eligibility.
2. The API hashes uploaded evidence bytes with SHA-256. Raw files stay off-chain in local disk storage or an explicitly configured S3-compatible object store.
3. `X1ChainClient` verifies the configured chain ID and latest RPC block before it reads or signs.
4. Signing keys are read only by the backend from the ignored `.env`. Registrar actions use the registrar key; role separation is enforced by the contract as well as the UI/API.
5. The API estimates gas, checks signer balance, signs, broadcasts, waits for a receipt, and reads expected state back from the contract.
6. Only a successful receipt plus matching state is written as a confirmed transaction event in `credit_events`. Local application events are marked demo and carry no transaction hash.

The frontend calls authenticated `/api/blockchain/status`, shows network/contract state and confirmed transaction links, and never receives private keys. If no deployed address exists, chain write controls stay disabled. The public network endpoint is read-only.

## Current contract surface

`VericarbRegistry.sol` stores project reference hashes, credit batches with integer kg CO2e balances, evidence hash anchors, role grants, transfers, retirements, risk state, and reviewer outcomes. Important transitions emit events and append batch history. Project and evidence writes, plus batch issuance, have FastAPI paths. Existing transfer/retire/risk/review application flows remain local database workflows pending chain integration.

## Data limits

Only identifiers and hashes belong on-chain. Never put raw documents, personal data, or large payloads on-chain. A hash provides tamper evidence for the specific submitted bytes; it does not establish truth, quality, ownership rights, or regulatory status. TRIPLEES does not reverse an external registry retirement.

## Persistence and failure handling

Existing `CreditEvent` rows hold confirmed `chain_id`, `tx_hash`, and `block_number`; `CreditBatch` holds contract address and latest issuance transaction. Receipt failure or read-back mismatch does not mark an action successful. The current implementation waits synchronously for receipt and does not yet persist a separate pending transaction row, retry queue, or idempotency-key table. Contract duplicate checks make project/evidence/batch registration fail closed on retry.
