from __future__ import annotations

import json
import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import config
from ..models import (
    AgentBid, AgentBudget, AgentPermission, AgentTask, Investigation,
    InvestigationBudget, utcnow,
)

UNIT = "internal_units"
DEFAULT_INVESTIGATION_BUDGET = 10.0
DEFAULT_AGENT_BUDGET = 2.0
TASK_BUDGET = 1.0

TASK_PLAN = (
    ("evidence_analysis", "evidence_analyst", "Analyze extracted evidence for inconsistencies and source gaps.", {"evidence_analyst": 1.0, "independent_review_agent": 0.65}, 2),
    ("registry_integrity", "integrity_analyst", "Compare only the imported registry records scoped to this investigation.", {"integrity_analyst": 1.0, "evidence_analyst": 0.55}, 2),
    ("public_research", "research_investigator", "Review supplied public sources; report unavailable research providers explicitly.", {"research_investigator": 1.0, "evidence_analyst": 0.4}, 3),
    ("monitoring_review", "monitoring_analyst", "Assess imported or synthetic monitoring observations and preserve their provenance.", {"monitoring_analyst": 1.0, "evidence_analyst": 0.4}, 3),
    ("independent_review", "independent_review_agent", "Review findings for support gaps, uncertainty, and overclaim language.", {"independent_review_agent": 1.0, "integrity_analyst": 0.6}, 1),
)
RELIABILITY = {
    "evidence_analyst": 0.91,
    "integrity_analyst": 0.94,
    "research_investigator": 0.78,
    "monitoring_analyst": 0.82,
    "independent_review_agent": 0.88,
}
AGENT_KEYS = tuple(RELIABILITY)


class CoordinationError(ValueError):
    pass


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12].upper()}"


def ensure_permission_defaults(db: Session) -> None:
    now = utcnow()
    for agent_id in AGENT_KEYS:
        defaults = {"execute": True, "external_service": False, "sign_transaction": False}
        for permission, allowed in defaults.items():
            row = db.scalar(select(AgentPermission).where(
                AgentPermission.agent_id == agent_id,
                AgentPermission.permission == permission,
            ))
            if row is None:
                db.add(AgentPermission(
                    id=_id("APR"), agent_id=agent_id, permission=permission,
                    allowed=allowed, created_at=now, updated_at=now,
                ))


def permission_allowed(db: Session, agent_id: str, permission: str = "execute") -> bool:
    row = db.scalar(select(AgentPermission).where(
        AgentPermission.agent_id == agent_id,
        AgentPermission.permission == permission,
    ))
    return bool(row and row.allowed)


def authorize_task_start(db: Session, investigation_id: str, agent_id: str) -> tuple[AgentTask | None, str | None]:
    if not config.AGENT_COORDINATION_ENABLED:
        return None, None
    task = db.scalar(select(AgentTask).where(
        AgentTask.investigation_id == investigation_id,
        AgentTask.agent_id == agent_id,
        AgentTask.status.in_(["assigned", "running", "failed", "awaiting_review"]),
    ).order_by(AgentTask.priority, AgentTask.created_at).limit(1))
    if task is None:
        return None, None
    if task.status == "awaiting_review":
        return task, "review_approval_required"
    if not permission_allowed(db, agent_id, "execute"):
        return task, "agent_execution_not_permitted"
    budget = db.scalar(select(InvestigationBudget).where(InvestigationBudget.investigation_id == investigation_id))
    agent_budget = db.scalar(select(AgentBudget).where(
        AgentBudget.investigation_id == investigation_id, AgentBudget.agent_id == agent_id,
    ))
    if config.AGENT_BUDGETS_ENABLED:
        if budget is None or agent_budget is None:
            return task, "agent_budget_not_configured"
        if budget.frozen or budget.emergency_stop:
            return task, "emergency_stop"
        if not task.budget_charged:
            if budget.spent_amount + task.budget_allocated > budget.budget_limit:
                return task, "investigation_budget_exceeded"
            if agent_budget.spent_amount + task.budget_allocated > agent_budget.budget_limit:
                return task, "agent_budget_exceeded"
            budget.spent_amount += task.budget_allocated
            agent_budget.spent_amount += task.budget_allocated
            task.budget_spent = task.budget_allocated
            task.budget_charged = True
            budget.updated_at = utcnow()
            agent_budget.updated_at = utcnow()
    task.status = "running"
    task.error_info = None
    return task, None


def ensure_task_plan(db: Session, investigation: Investigation) -> list[AgentTask]:
    if not config.AGENT_COORDINATION_ENABLED:
        return []
    ensure_permission_defaults(db)
    now = utcnow()
    budget = db.scalar(select(InvestigationBudget).where(
        InvestigationBudget.investigation_id == investigation.id,
    ))
    if budget is None:
        budget = InvestigationBudget(
            id=_id("IBG"), investigation_id=investigation.id,
            budget_limit=DEFAULT_INVESTIGATION_BUDGET, allocated_amount=0,
            spent_amount=0, unit=UNIT, approval_threshold=1.25,
            frozen=False, emergency_stop=False, created_at=now, updated_at=now,
        )
        db.add(budget)
        db.flush()

    agent_budgets: dict[str, AgentBudget] = {}
    for agent_id in AGENT_KEYS:
        agent_budget = db.scalar(select(AgentBudget).where(
            AgentBudget.investigation_id == investigation.id,
            AgentBudget.agent_id == agent_id,
        ))
        if agent_budget is None:
            agent_budget = AgentBudget(
                id=_id("ABG"), investigation_id=investigation.id, agent_id=agent_id,
                budget_limit=DEFAULT_AGENT_BUDGET, allocated_amount=0,
                spent_amount=0, unit=UNIT, updated_at=now,
            )
            db.add(agent_budget)
        agent_budgets[agent_id] = agent_budget

    for task_type, preferred_agent, description, capabilities, priority in TASK_PLAN:
        task = db.scalar(select(AgentTask).where(
            AgentTask.investigation_id == investigation.id,
            AgentTask.task_type == task_type,
        ))
        if task is None:
            task = AgentTask(
                id=_id("ATK"), investigation_id=investigation.id, task_type=task_type,
                agent_id=preferred_agent, description=description,
                required_input_json=json.dumps({"investigation_id": investigation.id}, separators=(",", ":")),
                expected_output_schema="AgentOutput.v1", status="created", priority=priority,
                budget_allocated=TASK_BUDGET, budget_spent=0, budget_charged=False,
                created_at=now,
            )
            db.add(task)
            db.flush()

        bids = list(db.scalars(select(AgentBid).where(AgentBid.task_id == task.id)))
        if not bids and config.AGENT_BIDDING_ENABLED:
            for agent_id, capability in capabilities.items():
                estimated_cost = 0.8 if agent_id == preferred_agent else 0.9
                duration = 12 if agent_id == preferred_agent else 18
                db.add(AgentBid(
                    id=_id("BID"), task_id=task.id, agent_id=agent_id,
                    estimated_cost=estimated_cost, estimated_duration_seconds=duration,
                    capability_score=capability, reliability_score=RELIABILITY[agent_id],
                    selection_status="rejected",
                    reason="Internal capability/cost estimate for TRIPLEES software agents; not an external offer.",
                    created_at=now,
                ))
            db.flush()
            bids = list(db.scalars(select(AgentBid).where(AgentBid.task_id == task.id)))

        if task.status in {"created", "available", "failed", "cancelled"} and bids:
            def score(bid: AgentBid) -> tuple[float, float, str]:
                active = db.scalar(select(func.count()).select_from(AgentTask).where(
                    AgentTask.investigation_id == investigation.id,
                    AgentTask.agent_id == bid.agent_id,
                    AgentTask.id != task.id,
                    AgentTask.status.in_(["assigned", "running"]),
                )) or 0
                availability = 1.0 if active == 0 else 0.5
                total = (bid.capability_score * 0.65 + bid.reliability_score * 0.25
                         + availability * 0.10 - bid.estimated_cost * 0.02)
                return (total, -bid.estimated_cost, bid.agent_id)

            chosen = max(bids, key=score)
            for bid in bids:
                bid.selection_status = "selected" if bid.id == chosen.id else "rejected"
            task.agent_id = chosen.agent_id
            task.budget_allocated = chosen.estimated_cost
            task.completed_at = None
            task.error_info = None
            task.status = "awaiting_review" if chosen.estimated_cost > budget.approval_threshold else "assigned"
            if task.status == "assigned":
                task.approved_by = None
                task.approval_reason = None
                task.approved_at = None
        elif task.status in {"created", "available", "failed", "cancelled"} and not bids:
            task.agent_id = preferred_agent
            task.budget_allocated = TASK_BUDGET
            task.status = "awaiting_review" if TASK_BUDGET > budget.approval_threshold else "assigned"
            task.completed_at = None
            task.error_info = None

    db.flush()
    tasks = list(db.scalars(select(AgentTask).where(
        AgentTask.investigation_id == investigation.id,
    ).order_by(AgentTask.priority, AgentTask.created_at, AgentTask.id)))
    budget.allocated_amount = sum(task.budget_allocated for task in tasks)
    if budget.allocated_amount > budget.budget_limit:
        raise CoordinationError("Allocated agent task units exceed the investigation budget limit.")
    for agent_id, agent_budget in agent_budgets.items():
        agent_budget.allocated_amount = sum(task.budget_allocated for task in tasks if task.agent_id == agent_id)
        if agent_budget.allocated_amount > agent_budget.budget_limit:
            raise CoordinationError(f"Allocated task units exceed the {agent_id} budget limit.")
        agent_budget.updated_at = now
    budget.updated_at = now
    return tasks


def task_dict(task: AgentTask, bids: list[AgentBid] | None = None) -> dict:
    return {
        "id": task.id, "investigation_id": task.investigation_id, "task_type": task.task_type,
        "agent_id": task.agent_id, "description": task.description,
        "required_input": json.loads(task.required_input_json),
        "expected_output_schema": task.expected_output_schema, "status": task.status,
        "priority": task.priority, "budget_allocated": task.budget_allocated,
        "budget_spent": task.budget_spent, "result_reference": task.result_reference,
        "error_info": task.error_info, "approved_by": task.approved_by,
        "approval_reason": task.approval_reason,
        "created_at": task.created_at.isoformat(),
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        "bids": [{
            "id": bid.id, "agent_id": bid.agent_id, "estimated_cost": bid.estimated_cost,
            "estimated_duration_seconds": bid.estimated_duration_seconds,
            "capability_score": bid.capability_score, "reliability_score": bid.reliability_score,
            "selection_status": bid.selection_status, "reason": bid.reason,
        } for bid in (bids or [])],
    }