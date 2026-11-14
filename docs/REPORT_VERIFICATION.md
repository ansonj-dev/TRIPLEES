# Report Verification

## Canonical Digest

NEAR reuses the existing `triplees-canonical-json-v1` and `report_sha256()` implementation. The digest covers report ID, version, status, summary, limitations, content, and UTC creation timestamp. JSON uses sorted keys, compact separators, UTF-8, and rejects non-finite numbers. Mutable commitment metadata and available-version lists are excluded.

The public verifier accepts the downloaded report JSON, selects the same canonical fields, recalculates SHA-256, then compares it with the saved commitment and contract view. The API processes the supplied file in memory and does not store it. A matching digest proves integrity relative to that digest, not that the environmental claims are true.

## Reviewer and Wallet Flow

1. Generate an immutable report version through the existing investigation/review pipeline.
2. An authorized reviewer records an approval reason. The API creates a pending commitment; no transaction is sent yet.
3. NEAR Connect is configured for testnet. The connected account must already have reviewer permission in `TripleESReportRegistry`.
4. The browser asks the wallet to sign `commit_report` with investigation ID, version, digest, and null metadata digest. The user wallet pays testnet gas.
5. The API checks testnet status, transaction finality, signer, receiver, method, exact arguments, successful outcome, and `verify_report` state.
6. Only matching final state becomes `confirmed`. RPC errors leave the record pending; on-chain execution failure becomes failed.
7. The public link exposes commitment metadata. Uploading an unmodified report JSON should verify; editing it should mismatch.

## API

- `GET /api/near/config`
- `POST /api/near/commitments/prepare`
- `POST /api/near/commitments/{commitment_id}/confirm`
- `GET /api/near/commitments` and `GET /api/near/commitments/{investigation_id}`
- `GET /api/public/near/commitments/{commitment_id}`
- `POST /api/public/near/commitments/{commitment_id}/verify` (2 MB report JSON limit)

X1 report anchors and NEAR commitments use separate routes and settings. The existing public verification page selects the NEAR path with its `near` query parameter.

## Configuration and Deployment Gate

NEAR is disabled by default. After an approved deployment and reviewer grant, set these public values in ignored `.env`:

```dotenv
NEAR_NETWORK=testnet
NEAR_RPC_URL=https://rpc.testnet.near.org
NEAR_WALLET_URL=https://testnet.mynearwallet.com
NEAR_EXPLORER_URL=https://explorer.testnet.near.org
NEAR_REPORT_REGISTRY_CONTRACT_ID=your-registry.testnet
NEAR_ENABLED=true
NEAR_REPORT_COMMITMENTS_ENABLED=true
```

Build and run host tests with `cargo test` and `cargo near build non-reproducible-wasm` in `services/contracts/near-report-registry`. Eight host tests pass. The local near-workspaces test currently fails with `PrepareError::Deserialization` for both cargo-near and plain cargo Wasm; resolve this before deployment. No NEAR deployment/transaction has been performed.

After that blocker is resolved and a human explicitly approves, the official [NEAR Rust quickstart](https://docs.near.org/smart-contracts/quickstart) shows the testnet deployment form:

```bash
export CONTRACT_ID=triplees-report-registry.testnet
near create-account "$CONTRACT_ID" --useFaucet --networkId testnet
cd services/contracts/near-report-registry
cargo near build non-reproducible-wasm
near contract deploy "$CONTRACT_ID" \
  use-file ./target/near/triplees_report_registry.wasm \
  with-init-call new json-args "{\"owner_id\":\"$CONTRACT_ID\"}" \
  prepaid-gas '100 Tgas' attached-deposit '0 NEAR' \
  network-config testnet sign-with-keychain send
```

Then use the installed `near` CLI's `contract call-function as-transaction` command to invoke `grant_reviewer` with `{"account_id":"$REVIEWER_ID"}` from the owner account. Confirm account/network in CLI prompts and verify with `is_reviewer`; inspect `near contract call-function as-transaction --help` because flags vary by CLI version. Deployment, reviewer grants, wallet signatures, and spending require human approval. No address or real transaction hash is claimed.