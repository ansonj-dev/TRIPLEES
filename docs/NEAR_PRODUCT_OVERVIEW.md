# TRIPLEES — Product Overview

## What TRIPLEES is

TRIPLEES is an environmental evidence intelligence and report-integrity platform for carbon and climate projects. It helps teams collect project records, inspect supporting documents, compare available registry data, review monitoring observations, run scoped analytical investigations, and preserve human decisions in a traceable workflow.

NEAR is the public integrity layer for approved report versions. It lets an authorized reviewer sign a transaction that records a canonical SHA-256 digest and minimal report identifiers in a NEAR smart contract. A third party can later compare a report copy with that on-chain commitment.

**Product principle:** evidence stays inspectable, decisions stay human, and approved report integrity can be checked independently.

## The problem TRIPLEES addresses

A climate or carbon project claim is usually supported by many disconnected records: project documents, monitoring observations, registry entries, methodology references, reviewer notes, and reports. Reviewing a claim means understanding where information came from, which checks were performed, what remains uncertain, and who approved the resulting report.

A single dashboard or a blockchain transaction cannot solve that by itself. TRIPLEES connects the evidence and review process first, then uses a public chain to make a specific approved report version tamper-evident.

## The platform

| Product area | What it does | What it preserves |
| --- | --- | --- |
| Projects | Organizes project identity, scope, methodology and supplied references | Project record and update history |
| Evidence library | Stores uploaded source files, calculates SHA-256 fingerprints and supports opt-in extraction | Original file, fingerprint and extraction locations |
| Registry comparison | Checks imported rows for possible serial or project overlaps | Compared records and source rows |
| Monitoring review | Organizes supplied observations and flags that need attention | Source, observed time, review state and uncertainty |
| Investigations | Runs five bounded analytical roles over a defined project scope | Agent runs, findings, references and limitations |
| Human review | Lets authorized reviewers decide findings and approve report versions | Decision, reason, reviewer and report version |
| NEAR report registry | Commits a reviewer-approved report digest to a NEAR smart contract | Digest, investigation/version identifiers, submitting account and contract timestamp |
| Public verification | Recalculates a digest from a supplied report copy and compares it with the commitment | Verification result and public commitment metadata |

The agents are assistive. They do not certify projects, approve their own findings, sign transactions, or determine environmental outcomes. Deterministic checks, model-generated suggestions, imported facts and synthetic examples remain distinct.

## Why NEAR is part of TRIPLEES

NEAR provides the public, independently readable smart-contract record for a report version after the review process has finished.

Without that layer, a person outside the TRIPLEES workspace would need to trust the application operator's database or a shared copy of a report. With a NEAR commitment, the reviewer can publish a digest of the approved report version. Later, a user can calculate the digest of a downloaded copy and compare it with the record stored by the contract.

NEAR contributes four things to this workflow:

1. **User-controlled signing.** The connected NEAR wallet signs the commitment transaction. TRIPLEES does not hold or request a NEAR seed phrase or private key.
2. **Contract-enforced reviewer permission.** The registry accepts commitments from accounts that have been granted reviewer permission by the contract owner.
3. **Version-specific integrity.** Investigation identifier, report version and digest are committed together. A later report version can be committed separately; an existing version is not silently overwritten.
4. **Independent verification.** A public verifier can compare the canonical digest of a supplied report file with the contract record.

NEAR is not used as an environmental oracle. It does not observe a forest, verify a satellite image, validate a methodology, or establish that a carbon claim is true. It makes the integrity of a particular reviewed report independently checkable.

## What is stored on-chain and off-chain

### Off-chain in TRIPLEES

- Original evidence files and uploaded documents.
- Full report contents and source excerpts.
- Personal, confidential or commercially sensitive information.
- Agent outputs, research notes, citations and uncertainty.
- Reviewer comments, reasons and internal workspace data.

### On-chain in the NEAR registry

- Investigation identifier.
- Report version.
- Canonical report SHA-256 digest.
- Submitting NEAR account.
- Contract timestamp.
- Optional non-sensitive metadata digest.

Only a digest and minimal identifiers are required for the NEAR integrity check. The application does not put the evidence bundle or full report on-chain.

**Meaning of verification:** a matching digest shows that the supplied file bytes match the digest committed for that report version. It does not prove that the file is authentic, that its statements are correct, that an environmental outcome occurred, or that credits are certified.

## End-to-end workflow

1. **Create a project.** Add the project information and relevant registry references.
2. **Add evidence.** Upload documents or import the records available to the workspace. TRIPLEES fingerprints files and can extract supported text on request.
3. **Investigate.** Define a project-specific question and scope. The five analytical roles inspect bounded context and record structured findings, source references and limitations.
4. **Review.** An authorized human reviewer inspects the evidence trail and decides which findings can be accepted, rejected or returned for more evidence.
5. **Create a report version.** The report captures the reviewed state and a canonical SHA-256 digest.
6. **Prepare a NEAR commitment.** The API checks report access, reviewer permission and NEAR configuration, then prepares the contract call.
7. **Sign in the wallet.** The connected NEAR testnet wallet asks the reviewer to approve the function call. The user, not the backend, authorizes the transaction.
8. **Verify finality and state.** The API independently checks the submitted transaction and reads the contract record. It marks a commitment confirmed only when those values match.
9. **Share and verify.** The public link shows minimal commitment metadata. A viewer can upload the original report JSON to check whether its digest matches.

## How TRIPLEES differs from a typical NEAR dApp

TRIPLEES uses NEAR as one component of a larger evidence-to-review workflow, rather than centering the product on a token, trading screen or generic wallet dashboard.

| Common dApp emphasis | TRIPLEES emphasis |
| --- | --- |
| Wallet-first account experience | Project and evidence workflow first; NEAR wallet connects when a reviewer signs |
| Token issuance or transfer | Versioned integrity commitments for reviewed reports |
| Publicly publishing application content | Keeping source files and full reports off-chain |
| Treating a transaction as the final outcome | Human review before signing and independent state verification afterwards |
| A blockchain record presented as proof | A clearly limited digest-integrity statement |

This describes TRIPLEES's product scope, not a claim that other NEAR applications cannot support evidence review.

## NEAR and X1 are separate integrations

TRIPLEES also contains an existing X1 EcoChain integration for its own project, evidence and batch workflows, and a separate X1 report-anchor path. NEAR is used for the NEAR report registry and public report verification flow.

They have separate network configuration, contract addresses, transaction checks and UI status. Enabling NEAR does not migrate records to NEAR, change X1 contract addresses, or disable X1 workflows.

## Current implementation and deployment gates

- The repository contains a Rust TripleESReportRegistry contract, its local test suite, NEAR testnet RPC handling, API preparation and confirmation routes, a browser wallet integration and a public report verifier.
- The browser uses @hot-labs/near-connect 0.12.0 to open a NEAR wallet chooser and request user-authorized signing.
- NEAR is disabled by default in .env.example.
- A deployed testnet contract account and an on-chain reviewer permission are required before real report commitments can be confirmed.
- No deployment, wallet signing or testnet transaction should be inferred from the presence of code or a local test.
- Production identity and session controls are separate from the current prototype login and remain a production requirement.

Read next:

- [NEAR User Guide](NEAR_USER_GUIDE.md)
- [NEAR Architecture](NEAR_ARCHITECTURE.md)
- [Report Verification](REPORT_VERIFICATION.md)
- [Security and Trust Boundaries](SECURITY.md)
- [Agent Coordination](AGENT_COORDINATION.md)
