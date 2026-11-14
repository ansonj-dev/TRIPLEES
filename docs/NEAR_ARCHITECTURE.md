# NEAR Architecture

## Status

NEAR is a separate, testnet-only report-commitment path. Contract source and a Wasm build exist, but no NEAR contract has been deployed and no NEAR transaction has been sent. X1 contracts, settings, signers, and report anchoring remain separate.

## Components and Flow

- Rust `TripleESReportRegistry` is under `services/contracts/near-report-registry/`.
- The static workspace uses the officially recommended NEAR Connect package (`@hot-labs/near-connect` 0.12.0) to connect a testnet wallet and request an explicit `signAndSendTransaction`.
- FastAPI preparation, confirmation, and public verification routes are in `services/api/app/near_routes.py`.
- `NearChainClient` checks RPC `chain_id == "testnet"`, validates final transaction signer/receiver/method/arguments, and reads the contract view before a commitment can become confirmed.
- Alembic revision `20261113_near_report_commitments` persists approval and transaction state off-chain.

```text
Reviewer approval -> API prepares digest -> wallet signs -> testnet contract commits
                  -> API checks final transaction and contract view -> public verification
```

## Contract and Data

The contract stores investigation ID, report version, SHA-256 digest as lowercase hex, optional metadata digest, submitter account, and block timestamp. It rejects duplicate `(investigation_id, report_version)` pairs. The initializer requires `owner_id` to equal the initializing predecessor. The owner grants/revokes reviewers; only reviewers can commit. It emits NEP-297-shaped `EVENT_JSON:` events for commits and permission changes.

No report body, evidence, personal data, or reviewer reason is written on-chain. `near_commitments` retains the reviewer reason and confirmation state in the existing database. Public responses expose commitment metadata, not report content.

## Wallet and Network

Official references checked 2026-11-13: [NEAR Connect](https://docs.near.org/tools/near-connect), [wallet login](https://docs.near.org/web3-apps/tutorials/wallet-login), [Rust quickstart](https://docs.near.org/smart-contracts/quickstart), and [RPC providers](https://docs.near.org/api/rpc/providers).

`.env.example` defaults to `NEAR_NETWORK=testnet`, `https://rpc.testnet.near.org`, `https://testnet.mynearwallet.com`, and `https://explorer.testnet.near.org`. `NEAR_ENABLED` and `NEAR_REPORT_COMMITMENTS_ENABLED` default to false. A deployed contract ID and on-chain reviewer grant are needed before a commitment succeeds.

NEAR is not used for app login, so no account-linking nonce or `near_accounts` table is added. The application session authorizes the reviewer; the wallet signs the transaction. No seed phrase or private key is stored.

## Build and Verification

```bash
cd services/contracts/near-report-registry
cargo test
cargo near build non-reproducible-wasm
npm ci
npm run test:sandbox
```

Eight host tests pass and `cargo-near` builds the Wasm. The near-workspaces 5.0.0 sandbox test currently fails with `PrepareError::Deserialization` for both cargo-near and plain cargo output. This is unresolved and is not reported as a passing test. No deployment or transaction has been performed.