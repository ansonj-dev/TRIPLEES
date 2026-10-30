# Nebius AI Foundation

The API contains a small provider boundary and a Nebius Token Factory client. Nebius currently documents an OpenAI-compatible inference API and lists NVIDIA Nemotron models. Configuration lives in `.env`; this repository contains no credentials.

## Configuration

```dotenv
NEBIUS_API_KEY=
NEBIUS_BASE_URL=https://api.tokenfactory.nebius.com/v1
NEBIUS_MODEL=nvidia/nemotron-3-super-120b-a12b
NEBIUS_CONNECT_TIMEOUT_SECONDS=5
NEBIUS_READ_TIMEOUT_SECONDS=60
NEBIUS_MAX_RETRIES=2
AI_MAX_COMPLETION_TOKENS=1800
AI_INPUT_COST_PER_MILLION_USD=
AI_OUTPUT_COST_PER_MILLION_USD=
```

The model and endpoint are configurable. Confirm that the selected model is enabled for the account. The client only identifies a model as NVIDIA Nemotron when its configured identifier is under the NVIDIA namespace and contains `nemotron`. Do not claim that another model is Nemotron.

## API behavior

- `GET /api/ai/health` requires authentication. It reports provider/model configuration and the API host; it never returns the credential or makes a billable inference request.
- `GET /api/ai/usage` requires authentication and scopes rows to the signed-in user, except admins can inspect workspace-wide rows. It contains token counts, latency, success state, and cost only when both rates are configured.
- The shared provider returns token usage and latency metadata. `usage_tracker.record_usage` persists those values for calls made by later workflows.
- `structured_output.parse_structured_output` validates JSON against a strict Pydantic schema. Invalid model output is rejected before persistence or use by other services.
- Requests use explicit connect/read timeouts and retry only bounded transient failures (timeouts, transport failures, HTTP 429, and 5xx). Client errors are not retried. Error messages do not include response bodies or credentials.

## Verification status

The client and validators are covered by mocked HTTP tests. No live inference call has been made in this workspace because no Nebius credential was configured and no billable request was authorized. The health endpoint is a configuration check, not a provider connectivity check.

Pricing changes over time. Cost estimates are intentionally omitted until an operator configures current account-specific input and output rates; token counts and latency remain available independently.

## References

- [Nebius Token Factory API](https://api.tokenfactory.nebius.com/docs)
- [NVIDIA Nemotron on Nebius Token Factory](https://nebius.com/services/token-factory/nemotron)
