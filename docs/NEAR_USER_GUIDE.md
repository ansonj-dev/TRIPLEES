# TRIPLEES — User Guide for NEAR Report Integrity

This guide explains how to use TRIPLEES and where the NEAR wallet fits into the workflow. The TRIPLEES login and NEAR wallet connection are separate.

## 1. Sign in to TRIPLEES

Open the TRIPLEES web application and use your workspace account. For a guided local demonstration, use the demo access option where enabled.

The application login grants access to the project workspace. It does not connect a blockchain wallet and does not prove ownership of a NEAR account.

Do not enter a seed phrase or private key into the application.

## 2. Create a project and add records

From the workspace navigation:

1. Open **Projects** and create or select a project.
2. Open **Evidence** to add supporting files. Uploaded source files remain off-chain in the configured evidence store.
3. Use the evidence extraction action only when you need text extraction. Supported formats include PDF, CSV, JSON and plain text; extraction may retain page, row or field locations.
4. Import registry records and add supplied monitoring observations where relevant.

TRIPLEES checks only the records and sources actually supplied or connected. A missing external source is not treated as a clean result.

## 3. Run an investigation

Open **Investigation Center** and select a project, investigation title, question and scope. Select the evidence files relevant to that scope, then queue the investigation.

The existing five roles are:

- Evidence Analyst
- Research Investigator
- Integrity Analyst
- Monitoring Analyst
- Independent Review Agent

The agents work within the investigation context and available permissions. Their outputs are suggestions for review, not certification or autonomous approval. External AI inference and public research depend on separately configured providers and permissions.

Open **Agent Activity** to see task state, execution history and the internal coordination model. Internal bids and internal_units are estimates used by TRIPLEES; they are not NEAR balances, token payments or on-chain agent fees.

## 4. Review findings and create a report

Open **Risk Intelligence** to inspect structured findings and source links. An authorized reviewer can use **Review Queue** to accept, reject or request more evidence, with a reason recorded in the audit trail.

Open **Investigation Reports** to select a report version. Review the report content, citations, limitations and its SHA-256 digest before preparing any external commitment.

A new review decision or report update can produce a new report version. Treat each version as a distinct record.

## 5. Connect a NEAR testnet wallet

Open **NEAR Wallet & Registry** in the navigation or select the NEAR account link from the workspace header.

The wallet panel shows:

- Whether NEAR wallet support is enabled by server configuration.
- The connected NEAR account, if one is present.
- The configured network and report-registry contract ID.
- Whether report commitments are enabled.
- Saved report commitment history.

Select **Connect NEAR wallet**. NEAR Connect opens the wallet chooser. Choose a wallet that supports the configured network, approve the connection in the wallet, and return to TRIPLEES. The connected account should appear in the wallet panel.

A connection alone does not submit a transaction. It also does not make the NEAR account an application login identity.

Select **Disconnect wallet** to end the wallet session from TRIPLEES.

### Before connecting

A server administrator must first configure the NEAR testnet endpoint and enable wallet support. A valid contract ID and deployed registry are required for report commitments. If NEAR is disabled, the connect button remains unavailable and the existing workspace remains usable.

## 6. Commit an approved report digest to NEAR

The report commitment process is a reviewer action, not an automatic action by an agent.

1. Open a report version in **Investigation Reports**.
2. Confirm that the report has been approved by an authorized reviewer.
3. Select the action to prepare a NEAR report commitment.
4. Confirm the report ID/version and digest shown in the TRIPLEES prompt.
5. In the NEAR wallet, inspect and approve the contract function call.
6. TRIPLEES receives the transaction hash and asks the API to verify the final transaction outcome.
7. The API checks the transaction's network, signer, receiver, method, arguments and contract state. Only a matching final result is marked confirmed.

If the wallet is rejected or the transaction is not final, the report must not be presented as confirmed. Use the report page or commitment history to inspect pending and failed states.

The backend never signs the NEAR transaction for the reviewer. The wallet signs and pays the testnet gas.

## 7. Share a public verification link

When a commitment is confirmed, use the public NEAR verification link shown with the report.

The public page displays commitment metadata without exposing the full report or private evidence. To check a report copy:

1. Download the report JSON from TRIPLEES.
2. Open the public verification link.
3. Select the exact downloaded JSON file.
4. Choose **Verify report copy**.

A VERIFIED result means the canonical digest of that file matches the digest recorded for the report version and confirmed contract state. Editing the report will normally produce a mismatch.

The file is processed for digest calculation; it is not stored by the public verifier.

## 8. Enable NEAR in a local deployment

NEAR is disabled by default. Only configure it after the contract deployment and reviewer permission have been completed and independently checked on NEAR testnet.

In the ignored local .env file, configure the public network values:

~~~dotenv
NEAR_NETWORK=testnet
NEAR_RPC_URL=https://rpc.testnet.near.org
NEAR_WALLET_URL=https://testnet.mynearwallet.com
NEAR_EXPLORER_URL=https://explorer.testnet.near.org
NEAR_REPORT_REGISTRY_CONTRACT_ID=your-registry.testnet
NEAR_ENABLED=true
NEAR_REPORT_COMMITMENTS_ENABLED=true
~~~

Restart the API after changing environment values. The API's GET /api/near/config endpoint reports the effective feature state. Never put a seed phrase, private key or wallet export in .env, source control, logs or the browser application.

The contract must already exist on testnet and the reviewer account must have been granted reviewer permission by the contract owner. Turning on feature flags does not deploy a contract or grant permissions.

For a controlled setup and deployment checklist, read [Report Verification](REPORT_VERIFICATION.md) and [NEAR Architecture](NEAR_ARCHITECTURE.md).

## 9. Common states and troubleshooting

| What you see | What it means | What to check |
| --- | --- | --- |
| NEAR TESTNET / NOT CONFIGURED | Wallet feature flag is off or configuration cannot be loaded | Check NEAR_ENABLED, API startup logs and /api/near/config |
| Connect button disabled | Wallet support is not enabled in the API | Configure NEAR testnet values and restart the API |
| Wallet chooser opens but no account appears | The wallet session did not return an account | Confirm the selected wallet supports NEAR testnet, then reconnect |
| Connected wallet but commitment unavailable | Report commitments or contract configuration is disabled | Check NEAR_REPORT_COMMITMENTS_ENABLED and contract ID |
| Reviewer permission error | The connected account is not authorized by the registry contract | Grant reviewer permission from the contract owner and verify the contract view |
| Commitment remains pending | The transaction is not yet confirmed or the RPC cannot complete verification | Check the transaction in the NEAR testnet explorer and retry confirmation only as instructed by the UI |
| Verification says MISMATCH | The supplied report file does not match the committed canonical digest | Download the exact report version again; do not edit its JSON |
| X1 status differs from NEAR | These are separate integrations | Check the NEAR and X1 status indicators independently |

## 10. Safety and interpretation

- A digest is an integrity fingerprint, not a certificate.
- NEAR does not validate environmental impact, credit eligibility, methodology correctness or source authenticity.
- Full evidence, report content and reviewer reasons remain off-chain.
- Agents cannot approve reports, connect wallets, sign transactions or spend NEAR.
- Internal coordination budgets do not represent NEAR tokens.
- X1 EcoChain remains a separate integration with its own network and contracts.
