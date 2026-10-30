from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import get_db
from .models import ModelUsage, Profile
from .security import current_user
from .services.ai.factory import create_ai_provider

router = APIRouter()


@router.get("/api/ai/health")
def ai_health(_user: Profile = Depends(current_user)):
    return create_ai_provider().health_status()


@router.get("/api/ai/usage")
def ai_usage(
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    user: Profile = Depends(current_user),
):
    query = select(ModelUsage)
    if user.role != "admin":
        query = query.where(ModelUsage.requested_by == user.id)
    rows = list(db.scalars(query.order_by(ModelUsage.created_at.desc()).limit(limit)))
    return {
        "items": [{
            "id": row.id,
            "provider": row.provider,
            "model": row.model_name,
            "input_tokens": row.input_tokens,
            "output_tokens": row.output_tokens,
            "latency_ms": row.latency_ms,
            "cost_usd": row.cost_usd,
            "cost_state": "estimated" if row.cost_usd is not None else "rate_not_configured",
            "succeeded": row.succeeded,
            "error_code": row.error_code,
            "created_at": row.created_at.isoformat(),
        } for row in rows],
        "summary": {
            "requests": len(rows),
            "input_tokens": sum(row.input_tokens for row in rows),
            "output_tokens": sum(row.output_tokens for row in rows),
            "known_cost_usd": round(sum(row.cost_usd or 0 for row in rows), 8),
            "cost_estimate_complete": all(row.cost_usd is not None for row in rows),
        },
    }
