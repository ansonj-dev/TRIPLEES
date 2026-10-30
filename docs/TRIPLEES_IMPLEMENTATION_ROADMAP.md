# TRIPLEES implementation roadmap

This roadmap follows the local audit and avoids work that would require external credentials, spending, data destruction, deployment, or blockchain transactions without separate authorization.

## P0 — Complete local demo acceptance and remove misleading UI

1. Run an isolated browser acceptance flow against a disposable SQLite database: demo login, synthetic project, evidence upload and hash, investigation queue/worker, agent execution, source-linked findings, independent review, report version, reviewer decision, canonical digest, and public verification.
2. Verify responsive layouts, keyboard navigation, browser console/network errors, title and primary page branding at desktop/tablet/mobile sizes.
3. Keep Marketplace hidden or disabled and keep Community clearly education-only until backed by complete functionality. The dashboard shortcut to Marketplace has been removed.
4. If any acceptance path fails, fix it and repeat the isolated flow; do not mutate the existing local `data/` workspace for this test.

## P1 — Enable and validate real AI demonstration (requires a user decision)

1. Obtain/configure a valid Nebius Token Factory credential and a currently available Nemotron model identifier in ignored local configuration.
2. Confirm prompt/data sharing scope and authorize one billable test request. Use only synthetic data, never confidential uploads.
3. Verify returned model identity, structured output, source references, token accounting, timeout/rate-limit handling, sanitized logs, and daily budget behavior.
4. Repeat the five-agent workflow and label the provider/model accurately in the UI and demo materials. Until then, all provider behavior shown by tests remains mocked/configuration-only.

## P2 — Strengthen data and integration coverage

1. Exercise PostgreSQL migrations/runtime against a disposable PostgreSQL service; retain SQLite as the local path.
2. Add property/adversarial tests for malformed and oversized uploads, duplicate extraction, prompt injection, SSRF and unsupported model output.
3. Validate S3-compatible object storage against an operator-controlled disposable bucket and review recovery behavior.
4. Connect approved public research or monitoring sources only after source governance, retention, licensing and consent are specified. Until connected, preserve imported/synthetic labels.

## P3 — Production identity and operations (release blocker)

1. Integrate a maintained external identity provider, MFA/account recovery policy, secure cookie/session handling, logout/revocation, and tenant authorization.
2. Review CORS, TLS, rate limits, audit retention, key rotation, backups/restore, vulnerability management and incident operations.
3. Configure PostgreSQL, durable private evidence storage, production secrets and release-managed migrations.
4. Run security review and load/recovery checks in a staging environment. Only then reassess the intentional production startup guard.

## P4 — X1 release work (separately approved)

1. Independently verify current chain ID, deployed registry address/code and contract interfaces using an authorized read-only provider.
2. Exercise transaction preparation, reviewer approval, wallet separation and reconciliation with a local/mock signer first.
3. If a testnet transaction is desired, obtain explicit approval, use a dedicated test wallet and confirm the exact contract/network/action before submission.
4. Do not grant signing authority to agents or automate credit issuance, transfer, or retirement.

## Demo boundary today

The app can demonstrate a local evidence/agent/report workflow with synthetic records and mocked provider behavior. It cannot yet demonstrate real Nemotron inference in this environment, live registry/satellite/IoT integrations, production identity, PostgreSQL deployment, or an end-to-end browser acceptance result from this audit. No external service or chain action is necessary for the local demo.
