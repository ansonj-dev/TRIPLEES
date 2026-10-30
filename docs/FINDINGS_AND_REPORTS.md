# Findings, Human Review, and Report Versions

Phase 5 adds database-backed findings, public source references, human decisions, and immutable report snapshots to the Phase 4 investigation workflow.

## Findings and citations

Each finding belongs to one agent execution and stores its category, severity, title, description, claim/value when supplied, confidence estimate, basis, status, recommendation, evidence IDs, and source IDs. Findings are not certifications or legal determinations.

Evidence IDs are resolved to project evidence records. Source IDs may refer to project-scoped registry records, monitoring observations, or persisted public source references. Public references retain their HTTPS URL, publisher/domain, retrieval/published times, and excerpt. Source URLs must pass the existing public URL safety check.

The worker validates every finding citation against the investigation's scoped context. It removes IDs outside that context and downgrades the finding to `unresolved`. A `requires_human_review` finding with no evidence or source citations is also downgraded. `hypothesis` and `unresolved` findings can remain uncited, with their uncertainty shown explicitly. Confidence is labeled as an agent estimate, not calibrated probability.

## API routes

All routes require bearer authentication. Investigation-scoped routes follow the project's existing owner/reviewer access checks. Only `reviewer` and `admin` roles can use the review queue or decide findings.

| Method and path | Purpose |
| --- | --- |
| `GET /api/investigations/{id}/agents` | Latest execution status per agent. |
| `GET /api/investigations/{id}/findings` | Paginated findings; optional `severity`, `status`, and `review_decision` filters. |
| `GET /api/investigations/{id}/sources` | Public source references collected for the investigation. |
| `GET /api/investigations/{id}/report` | Latest versioned report; add `?version=N` for a prior snapshot. Response lists `available_versions`. |
| `GET /api/findings/review-queue` | Paginated findings awaiting a reviewer decision. Reviewer/admin only. |
| `POST /api/findings/{finding_id}/review` | Append a human review decision and create a new report version. Reviewer/admin only. |

Review request example:

```json
{
  "decision": "needs_more_evidence",
  "reason": "The cited registry row does not include an authoritative serial-range record."
}
```

Supported decisions are `confirmed`, `rejected`, and `needs_more_evidence`. The reviewer reason is required. A decision records what the reviewer decided about the finding; it does not establish that a claim is true or false. Review history is append-only, while the finding also exposes the latest decision for filtering.

## Report versions

The worker creates a report snapshot when an investigation reaches a terminal execution state, including `partial` or `failed`. A snapshot captures the investigation status, findings with citations and review state, public sources, agent execution outcomes, and accumulated limitations. Every later human review creates a new version. Earlier versions remain readable and unchanged.

The report includes missing-data, extraction, unavailable-service, and agent-failure limitations when those are present. It does not hide incomplete runs or convert an agent status into a factual conclusion. Reports are not yet anchored to X1; anchoring is reserved for the later approved X1 phase.
