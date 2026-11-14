# Security and Trust Boundaries

## Wallet and Signing

- NEAR Connect (`@hot-labs/near-connect` 0.12.0) is initialized for testnet.
- Seed phrases/private keys are never requested or stored. NEAR signing occurs in the connected wallet after a user action.
- The backend never signs NEAR transactions. Existing X1 signer configuration is unchanged and is not reused for NEAR.
- NEAR accounts are not application login identities and are not linked to profiles. No ownership nonce is needed for this design; the existing app session/reviewer role authorizes preparation.

## Transaction and Contract Checks

- The API rejects non-testnet configuration and checks RPC `chain_id` before reads/submission verification.
- Account IDs, transaction hash, contract ID, report access/version/digest, signer, receiver, method, and call arguments are validated.
- A browser hash is untrusted. Confirmation requires actual RPC finality and a matching contract view.
- The contract allows only owner-granted reviewers and rejects overwriting a report version. The initializer requires its owner to be the initializing caller.
- Report bodies, evidence, personal data, and reviewer reasons remain off-chain. Public verification returns commitment metadata only; report JSON is hashed in memory and not persisted.

## Agents and Application Limits

- Existing agents have no arbitrary shell, database, URL-fetch, wallet, or signing tools.
- Bids and `internal_units` are internal estimates, not NEAR balances or payments. `sign_transaction` remains denied and cannot be granted through the API. Optional service payments are disabled.
- Budget/permission/stop checks run server-side. Emergency stop halts at the next worker boundary and cannot interrupt an in-flight external call.
- Existing bearer-token/demo authentication is prototype-only. Production startup remains blocked pending a production identity provider and session controls.
- Live Nebius inference and public research are not claimed unless separately configured and exercised. Imported/synthetic monitoring is not live satellite or IoT data.

A blockchain digest establishes that bytes match a recorded digest. It does not establish document authenticity, environmental outcomes, project eligibility, or credit certification. X1 and NEAR have separate networks and confirmation states. No NEAR deployment, grant, transaction, or token transfer has been made.