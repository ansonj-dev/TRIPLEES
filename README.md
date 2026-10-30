# TRIPLEES

**Investigate. Verify. Trace.**

TRIPLEES is a local prototype for evidence-grounded carbon project investigation. It combines a vanilla JavaScript frontend, FastAPI, SQLite or PostgreSQL persistence, document extraction, five specialized agents, a database-backed worker, and a Solidity registry integration for X1 EcoChain.

**Status:** local prototype with synthetic demo data and a recorded testnet deployment. It is not a production credit registry, certification service, or live marketplace. An on-chain record proves that identifiers and hashes were recorded, not that the underlying environmental claim is true.

## Features

- Project and evidence management with SHA-256 evidence hashing.
- Local text extraction for PDF, CSV, JSON, and TXT evidence, with source locations, chunks, and heuristic claim candidates.
- Scoped evidence, research, registry-integrity, monitoring, and independent-review agent modules with explicit limitations and citations.
- An intelligence workspace for persistent investigations, agent activity, source-linked findings, versioned reports, and reviewer decisions.
- An optional, separately approved X1 flow for reviewer-approved report SHA-256 commitments. Report contents remain off-chain.
- Registry imports and conflict checks against imported records.
- Imported or synthetic monitoring signals, deterministic integrity assessments, and human review workflows. No live satellite, IoT, or field monitoring feed is connected by default.
- Batch issuance, local transfer and retirement workflows, and public verification.
- X1 testnet network status, project registration, evidence anchoring, and batch issuance.

## Repository Structure

```text
TRIPLEES/
|-- frontend/
|   |-- index.html              Public website
|   |-- auth.html               Sign-in and demo access
|   |-- app.html                Application workspace
|   |-- verify.html             Public batch verification
|   `-- assets/
|       |-- css/                Stylesheets
|       |-- js/                 Browser application code
|       `-- images/             Icons and local images
|-- services/
|   |-- api/
|   |   |-- app/                FastAPI routes, models, and business services
|   |   |-- migrations/         Alembic database migrations
|   |   |-- tests/              API and static-hosting tests
|   |   `-- requirements.txt    Python dependencies
|   `-- contracts/
|       |-- contracts/          Solidity registry
|       |-- scripts/            Deployment and testnet operations
|       |-- test/               Hardhat contract tests
|       `-- package.json        Contract tooling and commands
|-- docs/                       Architecture, walkthroughs, and runbooks
|-- sample-data/                Synthetic JSON fixtures and CSV templates
|-- .env.example                Configuration template without secrets
|-- .gitignore                  Local and generated file exclusions
|-- alembic.ini                 Database migration configuration
`-- README.md                   Project overview and getting started
```

The frontend is served at the site root, so moving the source files does not change URLs such as `/auth.html` or `/app.html`. FastAPI serves static content only from [frontend](frontend), not the repository root. API requests remain under `/api/`.

Local-only directories such as `data/`, `.venv/`, `node_modules/`, contract artifacts, and editor settings are intentionally excluded from the tracked project layout. Optional development utilities live under `tools/`.

## Technology

| Area | Stack |
| --- | --- |
| Frontend | HTML, CSS, vanilla JavaScript, Lucide icons |
| Backend | Python 3.11+, FastAPI, Pydantic, SQLAlchemy, httpx |
| Persistence | SQLite/PostgreSQL, Alembic migrations, local/S3-compatible off-chain evidence storage |
| Blockchain | Solidity, Hardhat, ethers, Web3.py, X1 Maculatus testnet |
| Tests | pytest, FastAPI TestClient, Hardhat |

## Getting Started

Use Python 3.11 or newer and Node.js 20+. From the repository root:

### 1. Install dependencies

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r services\api\requirements.txt
npm --prefix services\contracts ci
```

### 2. Configure the application

For a fresh checkout, create a local configuration file:

```powershell
Copy-Item .env.example .env
```

Keep an existing `.env` rather than overwriting it. `VERICARB_TOKEN_SECRET` is a legacy-compatible setting; use a long random value. The default database and evidence directories are created locally when the application starts. Production startup stays blocked until production identity and session controls are integrated; see [Production operations](docs/PRODUCTION_OPERATIONS.md).

### 3. Start the application

```powershell
python -m uvicorn services.api.app.main:app --reload --host 127.0.0.1 --port 8000
```

| Page | Local URL |
| --- | --- |
| Public website | [localhost:8000](http://localhost:8000/) |
| Sign-in and demo access | [localhost:8000/auth.html](http://localhost:8000/auth.html) |
| Application workspace | [localhost:8000/app.html](http://localhost:8000/app.html) |
| Interactive API documentation | [localhost:8000/api/docs](http://localhost:8000/api/docs) |

Select **Explore the demo workspace** on the sign-in page to load synthetic records. No separate frontend server or JavaScript build step is required. Use the FastAPI origin rather than opening the HTML directly for authenticated workflows.

The example configuration targets X1 EcoChain Maculatus Testnet (chain ID `10778`) but contains no private keys or registry address. Configure those values in your ignored local `.env` to enable chain actions. Never commit credentials, wallet keys, local databases, or uploaded evidence. Set `VERICARB_TOKEN_SECRET` to a long random value before sharing a running instance.

### Nebius AI foundation

The API includes an OpenAI-compatible Nebius Token Factory client for a configurable NVIDIA Nemotron model. Set `NEBIUS_API_KEY`, `NEBIUS_BASE_URL`, and `NEBIUS_MODEL` in your ignored local `.env` to enable inference in investigation workflows. The default model identifier is configurable and can be changed to a Nemotron model available to your account. `/api/ai/health` reports configuration without sending a model request; `/api/ai/usage` reports persisted token and latency data. Cost remains marked unknown unless both current per-million-token rates are explicitly configured. No real inference call is made by startup or health checks. A real inference call sends consented prompt content to Nebius and may incur account charges.

The provider rejects non-Nemotron model identifiers so the application does not label an unrelated model as Nemotron. Provider errors are sanitized, request retries are bounded, and structured model output must pass Pydantic validation before later code can use it. Never send API keys or private uploaded evidence in logs or source control.

## Sample Data

The sample data is synthetic and does not represent certified credits or real monitoring observations.

Document extraction is opt-in per uploaded file using `POST /api/evidence/{evidence_id}/extract`. The backend verifies the stored file against its SHA-256 digest before processing. See [Evidence intelligence](docs/EVIDENCE_INTELLIGENCE.md) for supported formats, limits, source locations, and the distinction between heuristic candidates and reviewed findings.

The five specialized agents now run through persisted investigations and a database-backed worker. See [Agent design](docs/AGENT_DESIGN.md) and the [investigation worker guide](docs/INVESTIGATION_WORKER.md). Agents do not have arbitrary tools; public research reports when no provider is configured, and project evidence is sent to Nebius only when a caller explicitly sets per-run external-AI authorization.

Start the worker separately from the API with `python -m services.api.worker` from the repository root. It uses the configured `DATABASE_URL`; see the worker guide for lifecycle endpoints, retries, cancellation, and lease recovery.

### Run the local demo

In one terminal, start the API with the command above. In a second terminal, start the investigation worker:

```powershell
python -m services.api.worker
```

Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) and choose **Explore the demo workspace**. The demo uses synthetic records. Do not upload private documents to a demo or enable external AI unless you intend to send the authorized prompt content to Nebius.

### Run local checks

From the project root:

```powershell
python -m pytest services/api/tests -q
python -m compileall -q services/api/app services/api/worker.py services/api/migrations
node --check frontend/assets/js/app.js
python -m alembic -c alembic.ini heads
npm --prefix services/contracts test
npm --prefix services/contracts run compile
```

The current local results are recorded in [the test report](docs/TRIPLEES_TEST_REPORT.md). The [current-state audit](docs/TRIPLEES_CURRENT_STATE_AUDIT.md), [requirements traceability](docs/TRIPLEES_REQUIREMENTS_TRACEABILITY.md), and [implementation roadmap](docs/TRIPLEES_IMPLEMENTATION_ROADMAP.md) describe verified coverage and remaining work.

Completed investigations persist structured findings, source references, limitations, report versions, and reviewer decisions. See the [findings and reports guide](docs/FINDINGS_AND_REPORTS.md) for review roles and API routes.

The authenticated app also includes an intelligence dashboard, investigation center, agent activity view, risk filters, report reader, and reviewer queue. See the [intelligence workspace guide](docs/INTELLIGENCE_WORKSPACE.md) for screen behavior and role access.

- [demo_project.json](sample-data/demo_project.json): example project record.
- [demo_monitoring_observation.json](sample-data/demo_monitoring_observation.json): example monitoring signal.
- [demo_registry_records.csv](sample-data/demo_registry_records.csv): registry import examples, including a duplicate serial for conflict checking.
- [registry_import_template.csv](sample-data/registry_import_template.csv): header-only registry import template.

The JSON files are illustrative fixtures, not a guarantee of compatibility with every API request schema. Use `/api/docs` for current endpoint payloads.

## X1 Testnet

From `services/contracts`:

```powershell
npm test
npm run compile
npm run chain:check
npm run chain:deploy:testnet -- --confirm-testnet
npm run chain:configure:testnet -- --confirm-testnet
npm run chain:verify:testnet
```

The live deploy/configure scripts require local `X1_DEPLOYER_PRIVATE_KEY`, `X1_REGISTRAR_PRIVATE_KEY`, and `X1_REVIEWER_PRIVATE_KEY` values in ignored `.env`. Never paste keys into chat or put them in source control. Deployment and role assignment are separate explicit commands; neither is part of ordinary tests. Review the printed address and cost plan before running the confirmation form. Use the deployment commands only when intentionally creating or configuring a testnet deployment.

A confirmed testnet deployment and QA transaction flow are recorded in [docs/DEPLOYMENT_AND_VERIFICATION.md](docs/DEPLOYMENT_AND_VERIFICATION.md). This does not configure a fresh checkout: its local keys and registry address must still be set explicitly.

After deployment, the backend supports project registration (`POST /api/projects/{id}/register-chain`), evidence hash anchoring (`POST /api/evidence/{id}/anchor`), and reviewed batch issuance (`POST /api/batches/{id}/issue`). The first two require a deployed registry and registrar role. Transfer, retirement, risk alert, and reviewer decisions are currently database workflows; on-chain lifecycle calls are not yet connected to those API actions.

The live testnet lifecycle harness can verify a confirmed, active batch and run the contract-only lifecycle with the separate registrar/reviewer signers: `npm run chain:test:lifecycle -- <batch-id>`. This is an explicit testnet command and is not part of local tests. The completed QA run and its actual transaction links are documented in `docs/DEPLOYMENT_AND_VERIFICATION.md`.

## Tests

```powershell
python -m pytest services\api\tests -q
node --check frontend/assets/js/app.js
node --check frontend/assets/js/auth.js
node --check frontend/assets/js/public-verify.js
node --check frontend/assets/js/script.js
python -m compileall -q services/api/app
npm --prefix services\contracts test
```

API workflow tests use a temporary SQLite database and evidence directory. Static-hosting tests check the public pages and assets and confirm that private repository paths return 404. Contract tests run locally; ordinary tests do not broadcast testnet transactions.

## Documentation

| Guide | Contents |
| --- | --- |
| [Project explained](docs/PROJECT_EXPLAINED_A_TO_Z.md) | Product context, architecture, trust boundaries, and roadmap |
| [Demo walkthrough](docs/DEMO_WALKTHROUGH.md) | Demonstration flow and expected behavior |
| [Blockchain architecture](docs/BLOCKCHAIN_ARCHITECTURE.md) | Off-chain and on-chain responsibilities |
| [Contract reference](docs/CONTRACTS.md) | Registry roles, operations, and lifecycle |
| [X1 setup](docs/X1_TESTNET_SETUP.md) | Network configuration and operational prerequisites |
| [Deployment and verification](docs/DEPLOYMENT_AND_VERIFICATION.md) | Recorded deployment and explicit testnet operations |
| [Test report](docs/TEST_REPORT.md) | Recorded verification results and known dependency findings |
| [Investigation worker](docs/INVESTIGATION_WORKER.md) | Persistent job lifecycle, worker startup, API routes, retries, and recovery |
| [Findings and reports](docs/FINDINGS_AND_REPORTS.md) | Citation handling, report versions, reviewer permissions, and review decisions |
| [Intelligence workspace](docs/INTELLIGENCE_WORKSPACE.md) | Frontend screens, API behavior, and reviewer access |
| [Report anchoring](docs/REPORT_ANCHORING.md) | Canonical digest format, reviewer approval, local verification, and separately approved deployment instructions |
| [Production operations](docs/PRODUCTION_OPERATIONS.md) | PostgreSQL, S3-compatible evidence storage, worker operation, security limits, backups, and production readiness gate |

## Security and Limitations

Only [frontend](frontend) is publicly mounted. Original evidence downloads use authenticated API routes; hashes are not encryption. Production startup currently fails closed because the application still uses prototype authentication; see [Production operations](docs/PRODUCTION_OPERATIONS.md) for required production controls. Protect signing keys and assess dependency findings before exposing an instance publicly.

- Synthetic demo data and deterministic assessments are not certifications or live environmental observations.
- Registry conflict checks cover only imported records.
- Evidence files remain off-chain; only SHA-256 digests are sent to the registry.
- Local transfer, retirement, risk, and review flows do not yet submit chain transactions.
- The Solidity registry has a recorded testnet deployment but has not been audited or source-verified on the explorer. No mainnet deployment is supported.
- The marketplace remains a preview and does not sell credits.

Reset synthetic data from **Settings > Reset demo workspace** or the authenticated `POST /api/demo/reset` endpoint.
