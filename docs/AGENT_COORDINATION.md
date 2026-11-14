# Agent Coordination

TRIPLEES already had a database-backed worker and five scoped analysis agents. This layer extends that workflow; it does not create external agents or replace the existing agent implementations.

## Task Flow

The coordinator creates five task types: evidence analysis, registry integrity, public research, monitoring review, and independent review. It creates internal proposals from agents with matching capabilities. Each proposal records capability/reliability scores, estimated duration/cost, and a reason identifying it as an internal estimate.

Selection is deterministic using capability match, configured reliability, availability, and estimated cost. The existing worker still invokes the existing agent classes and persists structured outputs, source/evidence references, result references, and audit events. Public research and external AI still require their existing providers and consent.

Full investigations run the selected tasks through the existing worker. A reviewer may also queue an individual assigned task. The normal full run retains the Independent Review Agent.

## Budgets and Permissions

Budgets are `internal_units`, not NEAR, fiat, or a payment balance. Defaults are a 10-unit investigation budget, 2-unit per-agent limits, a 1.25-unit approval threshold, and bid-estimated task costs. They are accounting controls, not claims about compute cost.

Budget and permission checks are server-side. Work above the threshold enters `awaiting_review` until a reviewer approves it with a reason. Internal units are charged once per task and audited. Existing AI token budgets and provider usage are separate.

Each agent has `execute`, `external_service`, and `sign_transaction` permissions. Execution is allowed by default for the five agents; external service and signing are denied. The API refuses to grant signing permission. Emergency stop blocks work at the next worker boundary; an in-flight provider call cannot be interrupted.

## APIs

- `POST /api/agents/tasks`, `GET /api/agents/tasks`, and `GET /api/agents/tasks/{task_id}` create/list/inspect tasks and bids.
- `POST /api/agents/tasks/{task_id}/assign`, `/execute`, and `/cancel` assign, queue, or cancel a task.
- `GET /api/agents/coordination/{investigation_id}` returns the task plan and budget.
- `GET /api/agents/budgets/{investigation_id}`, `POST /api/agents/budgets`, `POST /api/agents/budgets/{investigation_id}/approve`, and `/freeze` manage budgets and stop controls.
- `GET /api/agents/permissions` and `POST /api/agents/permissions` inspect/change reviewer-managed permissions.

## Limits

API tests use isolated SQLite and cover task planning, bid selection, budget enforcement, reviewer approval, permissions, emergency stop, worker execution, and audit state. Bids are a deterministic internal simulation, not independent economic actors or learned reputation. No marketplace, agent-to-agent payments, automatic NEAR spending, or NEAR Intents are implemented. Coordination can be disabled with `AGENT_COORDINATION_ENABLED=false`.