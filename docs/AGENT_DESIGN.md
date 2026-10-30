# TRIPLEES Specialized Agents — Phases 3 and 4

Phase 3 added bounded Python service modules for the Evidence Analyst, Research Investigator, Integrity Analyst, Monitoring Analyst, and Independent Review Agent. Phase 4 connects them to persisted investigations, authenticated lifecycle APIs, and a database-backed worker. Findings/report versioning and user-facing screens remain later work. See [Persistent investigations and worker](INVESTIGATION_WORKER.md).

## Scoped roles

| Agent | Current behavior | Boundaries |
| --- | --- | --- |
| Evidence Analyst | Inventories extracted candidate claims and extraction limitations; may request structured Nemotron analysis when explicitly authorized. | Cites supplied evidence IDs/locations; source text is untrusted input. |
| Research Investigator | Uses an injected public research provider only when per-run public research is authorized; otherwise reports that research was not performed. | No provider is configured by default. Filters non-HTTPS and local/private URL forms; search leads are not verified facts. |
| Integrity Analyst | Exact normalized serial comparison and deterministic quantity-conflict checks over supplied import rows. | Limited to provided rows; conflicts are not a fraud finding or proof of duplicate issuance. |
| Monitoring Analyst | Describes supplied observation severity, date, evidence link, and synthetic status. | No satellite, remote-sensing, or IoT connector; absence of observations is not evidence of no change. |
| Independent Review Agent | Checks source-ID validity, missing support, and overclaim wording; can make a separate adversarial model call when authorized. | Without authorization, it reports a deterministic traceability review and clearly states that the adversarial model call was not performed. |

## Data and model controls

- Agents have no arbitrary shell, SQL, URL-fetch, or signing tools. They receive only the fields assembled by the caller.
- External model access is gated by `AgentContext.external_ai_authorized`; it defaults to `False`. Do not set it without explicit per-run authorization to send the selected fields to the configured provider.
- External research access is separately gated by `AgentContext.public_research_authorized`. The default research provider is unconfigured and performs no network requests.
- Prompt text identifies project documents and findings as untrusted data. Model output is parsed into strict Pydantic structures before use.
- Evidence IDs and source IDs are validated against the context. Unknown IDs are removed, their findings are downgraded to unresolved, and a limitation is added. Model-supplied URLs must exactly match a safe HTTPS URL in the source context.
- Output summaries do not request or store hidden chain-of-thought. They contain concise results, evidence/source references, confidence estimates, and limitations.
- Deterministic checks operate only on caller-supplied rows. The Phase 4 worker scopes evidence and monitoring observations to the project, and imported registry rows to the investigation owner and project references, before building context.

## Local use

Agent modules live under `services/api/app/services/agents/`. Construct a bounded `AgentContext` from authorized project data, then invoke the specific role. Do not put raw private documents in the context unless external-AI consent is explicitly set and the minimum necessary excerpt has been selected.

The tests use fake providers and local records; they make no external model or research requests. See `services/api/tests/test_agents.py`.
