# TRIPLEES Intelligence Workspace

The intelligence workspace presents saved investigations and findings from the authenticated API. It does not run hidden reasoning in the browser and does not send requests to X1.

## Screens

- **Intelligence Dashboard** summarizes investigations, finding severity counts, reviewer queue visibility, saved model usage, and provider configuration.
- **Investigation Center** creates an investigation with project-scoped evidence and explicit per-run consent for external AI or public research. Creation uses an idempotency key, then queues the worker.
- **Agent Activity** shows execution status, safe error codes, structured output summaries, limitations, retries, cancellation requests, and audit events. It does not display private chain-of-thought.
- **Risk Intelligence** filters saved findings by severity, status, and search text. Findings retain citations and uncertainty notes.
- **Investigation Reports** reads immutable report versions and supports JSON download and browser printing.
- **Review Queue** is restricted to reviewer and admin roles. Each decision requires a reason and causes a new report version to be written.

## Data and access

The screens call the authenticated APIs described in [Findings and Reports](FINDINGS_AND_REPORTS.md) and [Investigation Worker](INVESTIGATION_WORKER.md). Developers see investigations they created; reviewer and admin roles can see broader project data under the existing project authorization policy. Only reviewer and admin roles can fetch the review queue or record finding decisions.

The dashboard's severity totals are counts, not a calibrated risk score. Agent findings are advisory and do not establish fraud, environmental harm, credit validity, or certification. Missing or unsupported source references remain visible as limitations.

## Local verification

From the repository root:

```powershell
python -m uvicorn services.api.app.main:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/auth.html`, sign in, then select **Intelligence** from the application sidebar. The existing project and evidence screens remain available. The workspace uses the same vanilla JavaScript application and authenticated API session.
