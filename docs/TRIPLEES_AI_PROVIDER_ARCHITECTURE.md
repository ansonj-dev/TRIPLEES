# TRIPLEES AI Provider Architecture

## Current Provider Selection

`AI_PROVIDER` selects the provider factory used by model-backed agents and `/api/ai/health`:

| Value | Behavior |
| --- | --- |
| `nebius_token_factory` | Default, preserving the existing OpenAI-compatible Token Factory client and current API behavior. Requires `NEBIUS_API_KEY`; base URL/model remain configurable as before. |
| `local_mock` | Explicit local-only deterministic JSON output for development/tests. Health identifies `mock_only`, model is `local-mock-v1`, and responses state that no external inference occurred. It is never selected automatically. |
| `nebius_ai_cloud` | Fails closed with `unverified_endpoint`. It does not issue requests or fall back to Token Factory/mock until an actual endpoint protocol and model are verified. |

If `AI_PROVIDER` is unset, the provider remains `nebius_token_factory`, preserving prior behavior. Unknown values return an invalid-configuration health state and fail on generation; no fallback is attempted.

## Verified Integration Boundary

The current Token Factory implementation uses bearer auth and an OpenAI-compatible chat-completions route, bounded retries/timeouts, structured JSON mode, usage extraction, sanitized provider errors, and existing cost estimation when both token rates are configured. Unit tests use `httpx.MockTransport`; no paid request was made.

Nebius AI Cloud endpoint URL, API key semantics, model identifier, protocol, usage response shape, rate limits, and billing are unverified. Do not map `NEBIUS_BASE_URL` or the Token Factory model ID onto AI Cloud by assumption. Once an endpoint has been separately approved and created by the user, verify its official endpoint documentation and implement a distinct adapter/configuration; retain Token Factory compatibility.

## Agent And Orchestration Boundaries

- Evidence Analyst and Independent Review Agent share the factory-selected model provider when per-run external-AI consent is present.
- Research Investigator uses its separate public-research provider interface; it is unconfigured by default and is not the inference client.
- Integrity Analyst and Monitoring Analyst currently perform deterministic local analysis of supplied records/observations.
- The persisted investigation worker records each agent execution and failure status, validates structured outputs, preserves evidence/source references, and creates versioned auditable report snapshots.
- Prompt inputs are bounded and marked untrusted; citation identifiers and URLs are validated against authorized context. Existing local analysis remains available when external AI is not authorized/configured.
- Model output is advisory. It must not autonomously approve carbon credits, sign transactions, or issue/retire credits.

All agents can share one verified provider/model initially. Separate endpoints per agent are not required by this code architecture. Existing token usage is recorded from provider responses; cost remains unknown unless both applicable token rates are explicitly configured.

## Test And Safety Contract

Use injected fake providers or the explicitly selected `local_mock` for local tests. Never use mock output as evidence that Nemotron inference works. Keep `AgentContext.external_ai_authorized` false unless the caller explicitly consents to send the selected fields to the configured external provider. Provider errors and unavailable AI Cloud configuration must remain visible as failure/limitations, not be silently substituted.