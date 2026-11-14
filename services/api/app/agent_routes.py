from __future__ import annotations

import json
import math
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import config
from .db import get_db
from .investigation_routes import _event, _get
from .models import (
    AgentAuditEvent, AgentBid, AgentBudget, AgentPermission, AgentTask,
    Investigation, InvestigationBudget, Profile, utcnow,
)
from .security import current_user
from .services.agent_coordination import (
    AGENT_KEYS, DEFAULT_AGENT_BUDGET, UNIT, CoordinationError, ensure_task_plan,
    permission_allowed, task_dict,
)

router = APIRouter()


class TaskPlanRequest(BaseModel):
    investigation_id: str = Field(min_length=1, max_length=80)


class TaskAssignmentRequest(BaseModel):
    bid_id: str = Field(min_length=1, max_length=80)


class BudgetUpdateRequest(BaseModel):
    investigation_id: str = Field(min_length=1, max_length=80)
    budget_limit: float = Field(gt=0, le=10000)
    approval_threshold: float = Field(ge=0, le=10000)
    agent_limits: dict[str, float] = Field(default_factory=dict)

    @field_validator("agent_limits")
    @classmethod
    def validate_agent_limits(cls, value: dict[str, float]) -> dict[str, float]:
        if any(agent not in AGENT_KEYS or not math.isfinite(limit) or limit < 0 or limit > 10000 for agent, limit in value.items()):
            raise ValueError("Agent limits must use a known agent ID and a nonnegative internal-unit amount.")
        return value


class BudgetApprovalRequest(BaseModel):
    task_id: str = Field(min_length=1, max_length=80)
    reason: str = Field(min_length=5, max_length=2000)


class BudgetFreezeRequest(BaseModel):
    frozen: bool
    emergency_stop: bool = False
    reason: str = Field(min_length=5, max_length=2000)


class PermissionUpdateRequest(BaseModel):
    agent_id: str = Field(min_length=1, max_length=64)
    permission: str = Field(pattern="^(execute|external_service|sign_transaction)$")
    allowed: bool


def _require_reviewer(user: Profile) -> None:
    if user.role not in {"reviewer", "admin"}:
        raise HTTPException(403, detail={"code": "reviewer_role_required", "message": "Only an authorized reviewer can change agent budgets, assignments, or permissions."})


def _require_enabled() -> None:
    if not config.AGENT_COORDINATION_ENABLED:
        raise HTTPException(503, detail={"code": "agent_coordination_disabled", "message": "Agent task coordination is disabled by configuration."})


def _task_view(db: Session, task: AgentTask) -> dict:
    bids = list(db.scalars(select(AgentBid).where(AgentBid.task_id == task.id).order_by(AgentBid.selection_status.desc(), AgentBid.agent_id)))
    return task_dict(task, bids)


def _budget_view(db: Session, investigation_id: str) -> dict:
    budget = db.scalar(select(InvestigationBudget).where(InvestigationBudget.investigation_id == investigation_id))
    agent_budgets = list(db.scalars(select(AgentBudget).where(
        AgentBudget.investigation_id == investigation_id,
    ).order_by(AgentBudget.agent_id)))
    if budget is None:
        return {"investigation_id": investigation_id, "budget_limit": 0, "allocated_amount": 0,
                "spent_amount": 0, "remaining_amount": 0, "unit": UNIT,
                "approval_threshold": 0, "frozen": False, "emergency_stop": False, "agents": []}
    return {
        "investigation_id": investigation_id, "budget_limit": budget.budget_limit,
        "allocated_amount": budget.allocated_amount, "spent_amount": budget.spent_amount,
        "remaining_amount": max(0, budget.budget_limit - budget.spent_amount), "unit": budget.unit,
        "approval_threshold": budget.approval_threshold, "frozen": budget.frozen,
        "emergency_stop": budget.emergency_stop,
        "agents": [{
            "agent_id": item.agent_id, "budget_limit": item.budget_limit,
            "allocated_amount": item.allocated_amount, "spent_amount": item.spent_amount,
            "remaining_amount": max(0, item.budget_limit - item.spent_amount), "unit": item.unit,
        } for item in agent_budgets],
    }


def _refresh_allocations(db: Session, investigation_id: str) -> None:
    budget = db.scalar(select(InvestigationBudget).where(InvestigationBudget.investigation_id == investigation_id))
    tasks = list(db.scalars(select(AgentTask).where(AgentTask.investigation_id == investigation_id)))
    if budget is None:
        return
    budget.allocated_amount = sum(task.budget_allocated for task in tasks)
    for agent_budget in db.scalars(select(AgentBudget).where(AgentBudget.investigation_id == investigation_id)):
        agent_budget.allocated_amount = sum(task.budget_allocated for task in tasks if task.agent_id == agent_budget.agent_id)
        agent_budget.updated_at = utcnow()


def _audit(db: Session, investigation_id: str, event_type: str, details: dict) -> None:
    db.add(AgentAuditEvent(
        id=f"AUD-{uuid.uuid4().hex[:12].upper()}", investigation_id=investigation_id,
        execution_id=None, event_type=event_type,
        details_json=json.dumps(details, separators=(",", ":")), created_at=utcnow(),
    ))


@router.post("/api/agents/tasks", status_code=201)
def create_agent_task_plan(body: TaskPlanRequest, db: Session = Depends(get_db), user: Profile = Depends(current_user)):
    _require_enabled()
    investigation = _get(db, body.investigation_id, user)
    try:
        tasks = ensure_task_plan(db, investigation)
    except CoordinationError as exc:
        raise HTTPException(409, detail={"code": "agent_budget_limit", "message": str(exc)}) from exc
    _event(db, investigation, "agent_coordination_plan_created", {"task_count": len(tasks), "unit": UNIT, "bidding": config.AGENT_BIDDING_ENABLED})
    db.commit()
    return {"investigation_id": investigation.id, "items": [_task_view(db, task) for task in tasks], "budget": _budget_view(db, investigation.id)}


@router.get("/api/agents/tasks")
def list_agent_tasks(investigation_id: str | None = None, offset: int = Query(0, ge=0),
                     limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db),
                     user: Profile = Depends(current_user)):
    query = select(AgentTask).join(Investigation, Investigation.id == AgentTask.investigation_id)
    if investigation_id:
        _get(db, investigation_id, user)
        query = query.where(AgentTask.investigation_id == investigation_id)
    elif user.role not in {"reviewer", "admin"}:
        query = query.where(Investigation.created_by == user.id)
    rows = list(db.scalars(query.order_by(AgentTask.created_at.desc(), AgentTask.id).offset(offset).limit(limit)))
    return {"items": [_task_view(db, row) for row in rows], "offset": offset, "limit": limit}


@router.get("/api/agents/tasks/{task_id}")
def get_agent_task(task_id: str, db: Session = Depends(get_db), user: Profile = Depends(current_user)):
    task = db.get(AgentTask, task_id)
    if task is None:
        raise HTTPException(404, detail={"code": "agent_task_not_found", "message": "Agent task was not found."})
    _get(db, task.investigation_id, user)
    return _task_view(db, task)


@router.post("/api/agents/tasks/{task_id}/assign")
def assign_agent_task(task_id: str, body: TaskAssignmentRequest, db: Session = Depends(get_db), user: Profile = Depends(current_user)):
    _require_enabled()
    _require_reviewer(user)
    task = db.get(AgentTask, task_id)
    if task is None:
        raise HTTPException(404, detail={"code": "agent_task_not_found", "message": "Agent task was not found."})
    investigation = _get(db, task.investigation_id, user)
    if task.status not in {"created", "available", "assigned", "awaiting_review"}:
        raise HTTPException(409, detail={"code": "agent_task_not_assignable", "message": "A running or completed task cannot be reassigned."})
    bid = db.scalar(select(AgentBid).where(AgentBid.id == body.bid_id, AgentBid.task_id == task.id))
    if bid is None:
        raise HTTPException(404, detail={"code": "agent_bid_not_found", "message": "The requested proposal is not eligible for this task."})
    if not permission_allowed(db, bid.agent_id, "execute"):
        raise HTTPException(403, detail={"code": "agent_execution_not_permitted", "message": "This agent is not permitted to execute tasks."})
    competing = db.scalar(select(AgentTask).where(
        AgentTask.investigation_id == investigation.id, AgentTask.agent_id == bid.agent_id,
        AgentTask.id != task.id, AgentTask.status.in_(["assigned", "running"]),
    ))
    if competing:
        raise HTTPException(409, detail={"code": "agent_already_assigned", "message": "An agent cannot hold two active tasks in the same investigation."})
    previous_agent = task.agent_id
    for candidate in db.scalars(select(AgentBid).where(AgentBid.task_id == task.id)):
        candidate.selection_status = "selected" if candidate.id == bid.id else "rejected"
    task.agent_id = bid.agent_id
    task.budget_allocated = bid.estimated_cost
    task.result_reference = None
    task.completed_at = None
    task.error_info = None
    if previous_agent != task.agent_id:
        task.approved_by = None
        task.approval_reason = None
        task.approved_at = None
    task.status = "awaiting_review" if bid.estimated_cost > (db.scalar(select(InvestigationBudget.approval_threshold).where(InvestigationBudget.investigation_id == investigation.id)) or 0) else "assigned"
    _refresh_allocations(db, investigation.id)
    budget = db.scalar(select(InvestigationBudget).where(InvestigationBudget.investigation_id == investigation.id))
    agent_budget = db.scalar(select(AgentBudget).where(AgentBudget.investigation_id == investigation.id, AgentBudget.agent_id == bid.agent_id))
    if budget and budget.allocated_amount > budget.budget_limit or agent_budget and agent_budget.allocated_amount > agent_budget.budget_limit:
        raise HTTPException(409, detail={"code": "agent_budget_limit", "message": "The selected proposal exceeds an investigation or agent allocation limit."})
    _event(db, investigation, "agent_task_assigned", {
        "task_id": task.id, "previous_agent_id": previous_agent, "agent_id": task.agent_id,
        "bid_id": bid.id, "estimated_cost": bid.estimated_cost, "unit": UNIT,
    })
    db.commit()
    return _task_view(db, task)


@router.post("/api/agents/tasks/{task_id}/execute", status_code=202)
def execute_agent_task(task_id: str, response: Response, db: Session = Depends(get_db), user: Profile = Depends(current_user)):
    _require_enabled()
    task = db.get(AgentTask, task_id)
    if task is None:
        raise HTTPException(404, detail={"code": "agent_task_not_found", "message": "Agent task was not found."})
    investigation = _get(db, task.investigation_id, user)
    if task.status != "assigned":
        raise HTTPException(409, detail={"code": "agent_task_not_ready", "message": "Only an assigned, approved task can be executed."})
    if not permission_allowed(db, task.agent_id, "execute"):
        raise HTTPException(403, detail={"code": "agent_execution_not_permitted", "message": "This agent is not permitted to execute tasks."})
    budget = db.scalar(select(InvestigationBudget).where(InvestigationBudget.investigation_id == investigation.id))
    agent_budget = db.scalar(select(AgentBudget).where(
        AgentBudget.investigation_id == investigation.id, AgentBudget.agent_id == task.agent_id,
    ))
    if config.AGENT_BUDGETS_ENABLED and budget and (budget.frozen or budget.emergency_stop):
        raise HTTPException(409, detail={"code": "agent_budget_frozen", "message": "The investigation budget is frozen or the emergency stop is active."})
    if config.AGENT_BUDGETS_ENABLED and budget and not task.budget_charged and budget.spent_amount + task.budget_allocated > budget.budget_limit:
        raise HTTPException(409, detail={"code": "investigation_budget_exceeded", "message": "This task would exceed the investigation budget."})
    if config.AGENT_BUDGETS_ENABLED and agent_budget and not task.budget_charged and agent_budget.spent_amount + task.budget_allocated > agent_budget.budget_limit:
        raise HTTPException(409, detail={"code": "agent_budget_exceeded", "message": "This task would exceed the selected agent budget."})
    if investigation.status not in {"draft", "partial", "failed", "completed", "completed_with_limitations"}:
        raise HTTPException(409, detail={"code": "investigation_not_runnable", "message": "The investigation is not available for another task execution."})
    investigation.status = "queued"
    investigation.requested_agent_keys_json = None
    investigation.requested_agent_task_id = task.id
    investigation.cancel_requested = False
    investigation.failure_summary = None
    investigation.completed_at = None
    investigation.next_attempt_at = utcnow()
    investigation.updated_at = utcnow()
    task.status = "assigned"
    task.error_info = None
    _event(db, investigation, "agent_task_execution_queued", {"task_id": task.id, "agent_id": task.agent_id})
    db.commit()
    response.status_code = 202
    return {"task": _task_view(db, task), "investigation_status": investigation.status}


@router.post("/api/agents/tasks/{task_id}/cancel")
def cancel_agent_task(task_id: str, db: Session = Depends(get_db), user: Profile = Depends(current_user)):
    task = db.get(AgentTask, task_id)
    if task is None:
        raise HTTPException(404, detail={"code": "agent_task_not_found", "message": "Agent task was not found."})
    investigation = _get(db, task.investigation_id, user)
    if task.status in {"completed", "failed", "cancelled"}:
        return _task_view(db, task)
    if task.status == "running":
        investigation.cancel_requested = True
        investigation.status = "cancel_requested"
    else:
        task.status = "cancelled"
        task.completed_at = utcnow()
    _event(db, investigation, "agent_task_cancelled", {"task_id": task.id, "status": task.status})
    db.commit()
    return _task_view(db, task)


@router.get("/api/agents/coordination/{investigation_id}")
def get_agent_coordination(investigation_id: str, db: Session = Depends(get_db), user: Profile = Depends(current_user)):
    investigation = _get(db, investigation_id, user)
    tasks = db.scalars(select(AgentTask).where(AgentTask.investigation_id == investigation.id).order_by(AgentTask.priority, AgentTask.created_at))
    return {"investigation_id": investigation.id, "investigation_status": investigation.status,
            "tasks": [_task_view(db, task) for task in tasks], "budget": _budget_view(db, investigation.id),
            "coordination_mode": "internal deterministic bid simulation"}


@router.get("/api/agents/budgets/{investigation_id}")
def get_agent_budget(investigation_id: str, db: Session = Depends(get_db), user: Profile = Depends(current_user)):
    investigation = _get(db, investigation_id, user)
    return _budget_view(db, investigation.id)


@router.post("/api/agents/budgets")
def update_agent_budget(body: BudgetUpdateRequest, db: Session = Depends(get_db), user: Profile = Depends(current_user)):
    _require_reviewer(user)
    _require_enabled()
    investigation = _get(db, body.investigation_id, user)
    try:
        ensure_task_plan(db, investigation)
    except CoordinationError as exc:
        raise HTTPException(409, detail={"code": "agent_budget_limit", "message": str(exc)}) from exc
    budget = db.scalar(select(InvestigationBudget).where(InvestigationBudget.investigation_id == investigation.id))
    if budget.spent_amount > body.budget_limit or budget.allocated_amount > body.budget_limit:
        raise HTTPException(409, detail={"code": "budget_below_existing_allocation", "message": "The new limit cannot be lower than already spent or allocated internal units."})
    budget.budget_limit = body.budget_limit
    budget.approval_threshold = body.approval_threshold
    for agent_budget in db.scalars(select(AgentBudget).where(AgentBudget.investigation_id == investigation.id)):
        agent_limit = body.agent_limits.get(agent_budget.agent_id, agent_budget.budget_limit)
        if agent_budget.spent_amount > agent_limit or agent_budget.allocated_amount > agent_limit:
            raise HTTPException(409, detail={"code": "agent_budget_below_existing_allocation", "message": f"The new {agent_budget.agent_id} limit is below allocated or spent units."})
        agent_budget.budget_limit = agent_limit
        agent_budget.updated_at = utcnow()
    for task in db.scalars(select(AgentTask).where(AgentTask.investigation_id == investigation.id)):
        # Budget edits must not rewrite the history or terminal state of completed,
        # failed, cancelled, or currently running work.
        if task.status not in {"created", "available", "assigned", "awaiting_review"}:
            continue
        if task.budget_allocated > budget.approval_threshold and task.approved_by is None:
            task.status = "awaiting_review"
        elif task.status == "awaiting_review":
            task.status = "assigned"
    budget.updated_at = utcnow()
    _event(db, investigation, "agent_budget_updated", {
        "budget_limit": budget.budget_limit, "allocated_amount": budget.allocated_amount,
        "approval_threshold": budget.approval_threshold, "unit": UNIT, "updated_by": user.id,
    })
    db.commit()
    return _budget_view(db, investigation.id)


@router.post("/api/agents/budgets/{investigation_id}/approve")
def approve_agent_task_budget(investigation_id: str, body: BudgetApprovalRequest,
                              db: Session = Depends(get_db), user: Profile = Depends(current_user)):
    _require_reviewer(user)
    investigation = _get(db, investigation_id, user)
    task = db.scalar(select(AgentTask).where(
        AgentTask.id == body.task_id, AgentTask.investigation_id == investigation.id,
    ))
    if task is None:
        raise HTTPException(404, detail={"code": "agent_task_not_found", "message": "Agent task was not found in this investigation."})
    if task.status != "awaiting_review":
        raise HTTPException(409, detail={"code": "agent_task_approval_not_required", "message": "This task is not awaiting reviewer budget approval."})
    task.status = "assigned"
    task.approved_by = user.id
    task.approval_reason = body.reason.strip()
    task.approved_at = utcnow()
    _event(db, investigation, "agent_task_budget_approved", {
        "task_id": task.id, "agent_id": task.agent_id, "budget_allocated": task.budget_allocated,
        "unit": UNIT, "approved_by": user.id,
    })
    db.commit()
    return _task_view(db, task)


@router.post("/api/agents/budgets/{investigation_id}/freeze")
def freeze_agent_budget(investigation_id: str, body: BudgetFreezeRequest,
                        db: Session = Depends(get_db), user: Profile = Depends(current_user)):
    _require_reviewer(user)
    investigation = _get(db, investigation_id, user)
    budget = db.scalar(select(InvestigationBudget).where(InvestigationBudget.investigation_id == investigation.id))
    if budget is None:
        raise HTTPException(404, detail={"code": "agent_budget_not_found", "message": "Create an agent task plan before changing its budget controls."})
    budget.frozen = body.frozen or body.emergency_stop
    budget.emergency_stop = body.emergency_stop
    budget.updated_at = utcnow()
    _event(db, investigation, "agent_emergency_stop_changed", {
        "frozen": budget.frozen, "emergency_stop": budget.emergency_stop,
        "reason": body.reason.strip(), "updated_by": user.id,
    })
    db.commit()
    return _budget_view(db, investigation.id)


@router.get("/api/agents/permissions")
def list_agent_permissions(db: Session = Depends(get_db), user: Profile = Depends(current_user)):
    if user.role not in {"reviewer", "admin"}:
        raise HTTPException(403, detail={"code": "reviewer_role_required", "message": "Only reviewers can inspect agent execution permissions."})
    rows = list(db.scalars(select(AgentPermission).order_by(AgentPermission.agent_id, AgentPermission.permission)))
    return {"items": [{"agent_id": row.agent_id, "permission": row.permission, "allowed": row.allowed,
                       "history": json.loads(row.change_history_json),
                       "updated_by": row.updated_by, "updated_at": row.updated_at.isoformat()} for row in rows]}


@router.post("/api/agents/permissions")
def update_agent_permission(body: PermissionUpdateRequest, db: Session = Depends(get_db), user: Profile = Depends(current_user)):
    _require_reviewer(user)
    if body.agent_id not in AGENT_KEYS:
        raise HTTPException(422, detail={"code": "unknown_agent", "message": "Permission updates must refer to one of the five registered TRIPLEES agents."})
    if body.permission == "sign_transaction" and body.allowed:
        raise HTTPException(422, detail={"code": "agent_signing_prohibited", "message": "Agents cannot be granted wallet signing or transaction submission authority."})
    row = db.scalar(select(AgentPermission).where(
        AgentPermission.agent_id == body.agent_id, AgentPermission.permission == body.permission,
    ))
    now = utcnow()
    if row is None:
        row = AgentPermission(id=f"APR-{uuid.uuid4().hex[:12].upper()}", agent_id=body.agent_id,
                              permission=body.permission, allowed=body.allowed,
                              change_history_json="[]", updated_by=user.id,
                              created_at=now, updated_at=now)
        db.add(row)
        history = []
    else:
        history = json.loads(row.change_history_json or "[]")
        row.allowed = body.allowed
        row.updated_by = user.id
        row.updated_at = now
    history.append({"allowed": body.allowed, "updated_by": user.id, "at": now.isoformat()})
    row.change_history_json = json.dumps(history[-100:], separators=(",", ":"))
    db.commit()
    return {"agent_id": row.agent_id, "permission": row.permission, "allowed": row.allowed,
            "history": history[-100:], "updated_by": row.updated_by, "updated_at": row.updated_at.isoformat()}