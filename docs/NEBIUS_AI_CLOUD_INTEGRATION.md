# Nebius AI Cloud Integration Status

Audit date: 2026-10-30

## Verified Versus Unknown

| Item | Status | Evidence |
| --- | --- | --- |
| Active tenant/project and region | Unknown | MCP did not initialize; CLI and profile are unavailable. The user-supplied project identifier was not confirmed active and is intentionally omitted here. |
| AI Cloud services and regions | Unknown | No authenticated read-only account query could be made. |
| Nemotron model availability in AI Cloud | Unknown | The backend's default `nvidia/nemotron-3-super-120b-a12b` is a Token Factory configuration value, not proof of AI Cloud availability. |
| Serverless Endpoint / Jobs | Unknown | Not inspected. No endpoint or job was created. |
| NVIDIA NIM availability | Unknown | Not inspected. |
| AI Cloud API protocol, model ID, auth | Unknown | Must be confirmed from the selected product and deployed endpoint documentation. |
| Pricing, idle behavior, account billing | Unknown | No account pricing data was available. No prices are estimated here. |

No Nebius AI Cloud request or paid inference was made. No tenant, project, region, resource, or billing setting was changed.

## Existing Token Factory Contract

The existing FastAPI provider is specifically a Token Factory client. It sends OpenAI-compatible `POST {NEBIUS_BASE_URL}/chat/completions` requests with bearer authentication, a configured model ID, and bounded retries/timeouts. The configured default host and model identifier are in `services/api/app/config.py`; neither establishes that an AI Cloud endpoint supports the same protocol or model. Local tests use an HTTP mock transport, not the Nebius service.

The available environment variable names in the current source are `AI_PROVIDER`, `NEBIUS_API_KEY`, `NEBIUS_BASE_URL`, `NEBIUS_MODEL`, `NEBIUS_CONNECT_TIMEOUT_SECONDS`, `NEBIUS_READ_TIMEOUT_SECONDS`, `NEBIUS_MAX_RETRIES`, `AI_MAX_COMPLETION_TOKENS`, `AI_DAILY_TOKEN_LIMIT`, `AI_INPUT_COST_PER_MILLION_USD`, and `AI_OUTPUT_COST_PER_MILLION_USD`. No variable values are included in this report. The local `.env` file was absent during the audit.

## Cost And Deployment Position

No numeric estimate is justified until Nebius confirms the account's model offering, service mode, region, billing rate, minimum allocation, idle billing, storage/network charges, and any account/payment restrictions.

The preferred evaluation order is:

1. Check whether the selected Nemotron model is offered as an AI Cloud Serverless Endpoint in the user's region, and obtain its current rate and idle semantics.
2. Compare a supported NVIDIA NIM deployment only if serverless is unavailable or unsuitable. Require an explicit GPU shape, minimum runtime, storage/network estimate, and stop/delete procedure before considering it.
3. Avoid a GPU VM, Kubernetes, or a long-running job for the initial hackathon integration unless provider requirements make those unavoidable.

Serverless is not assumed to be free. Endpoint creation and inference remain gated on the user's explicit approval after the required cost breakdown.

## Next Verification

After MCP and CLI authentication work, use service discovery and service-specific CLI help first. Then perform documented read-only queries for project, region, available services, model catalogs, and pricing. Record each result as confirmed, documented but not enabled, unavailable, or unknown. Do not infer a model identifier or endpoint URL from the Token Factory configuration.