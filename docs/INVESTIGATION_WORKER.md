# Persistent Investigations and Worker

Phase 4 adds a database-backed investigation queue. API requests create and queue work; a separate worker process runs the agents and persists each execution and audit event.

## Start the worker

From the repository root, with the API environment configured:

```powershell
python -m services.api.worker
```

Use `python -m services.api.worker --once` to process at most one available investigation and exit, or `--poll-seconds 5` to change idle polling. The worker uses the same `DATABASE_URL` and object-storage settings as the API. Alembic must be upgraded to head; local API startup applies migrations automatically when `AUTO_MIGRATE=true`. Production releases must run migrations as a controlled one-off step. See [Production operations](PRODUCTION_OPERATIONS.md).

Run the API separately using the existing command:

```powershell
uvicorn services.api.app.main:app --reload
```

## API lifecycle

All endpoints require a bearer token from the existing sign-in flow.

| Method and path | Purpose |
| --- | --- |
| `POST /api/investigations` | Create a draft. Optional `Idempotency-Key` makes retries safe. |
| `GET /api/investigations` | List investigations visible to the signed-in user. |
| `GET /api/investigations/{id}` | Read investigation and persisted agent execution outputs. |
| `POST /api/investigations/{id}/run` | Queue a draft or retryable investigation. Repeated calls are safe while queued/running. |
| `POST /api/investigations/{id}/cancel` | Cancel queued work or request cancellation between running agent steps. |
| `POST /api/investigations/{id}/retry` | Queue a failed or partial investigation again. Completed agent checkpoints are reused. |
| `GET /api/investigations/{id}/audit` | Read the append-only audit event history. |
| `GET /api/investigations/{id}/agents` | Read the latest execution status for each agent. |
| `GET /api/investigations/{id}/findings` | Read paginated structured findings and their citations. |
| `GET /api/investigations/{id}/report` | Read the latest report snapshot or a selected version. |
| `POST /api/findings/{id}/review` | Record an authorized human decision and create a new report version. |

The creation body includes `project_id`, `title`, `scope`, optional `evidence_ids`, and two independent consent flags: `external_ai_authorized` and `public_research_authorized`. `ai_token_budget` defaults to 6,000 and is capped at 100,000. Selecting evidence from another project is rejected. With no evidence IDs, the worker uses the project's available evidence.

## Worker behavior

- The worker claims queued work with a conditional database update, records a lease, and checkpoints each execution before and after it runs.
- Each failed agent gets one retry. Completed agents are reused when a job is resumed; agent outputs and errors remain in the database.
- A worker crash leaves a lease that another worker can recover after expiry. The interrupted execution is marked with the safe code `worker_lease_expired`; the investigation enters retry wait or fails after five job attempts.
- Cancellation is observed between agent steps. An in-progress provider call can finish before cancellation takes effect, bounded by the configured AI client timeout/retry limits.
- The independent review agent receives findings from prior agents. Its output is a traceability and wording review, not a certification decision.
- The token budget uses a conservative input-size estimate plus the configured maximum completion size. If a call cannot fit, the agent returns deterministic output with a limitation rather than contacting the model.
- AI usage stores provider, model, tokens, latency, optional cost, and links to the investigation and execution. Raw prompts and documents are not stored in logs.
- No public research provider is configured by default. An authorized run therefore records that external research was not performed.

Statuses include `draft`, `queued`, `running`, `retry_wait`, `cancel_requested`, `cancelled`, `completed`, `completed_with_limitations`, `partial`, and `failed`. A limited result means configured data or services were unavailable; it is not a validation or certification result.

The API supports local disk and S3-compatible evidence storage. Production queue infrastructure still needs an external identity integration and deployment review. See [Findings and reports](FINDINGS_AND_REPORTS.md) for citation rules, review permissions, and report version behavior.
