from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from ... import config
from ...models import ModelUsage, utcnow
from .provider import ChatResult


def _rate(value: str) -> float | None:
    if not value:
        return None
    try:
        parsed = float(value)
        return parsed if parsed >= 0 else None
    except ValueError:
        return None


def usage_cost(input_tokens: int, output_tokens: int) -> float | None:
    input_rate = _rate(config.AI_INPUT_COST_PER_MILLION_USD)
    output_rate = _rate(config.AI_OUTPUT_COST_PER_MILLION_USD)
    if input_rate is None or output_rate is None:
        return None
    return (max(0, input_tokens) * input_rate + max(0, output_tokens) * output_rate) / 1_000_000


def record_usage(
    db: Session,
    result: ChatResult,
    *,
    requested_by: str | None,
    succeeded: bool = True,
    error_code: str | None = None,
) -> ModelUsage:
    row = ModelUsage(
        id=f"USG-{uuid.uuid4().hex[:16].upper()}", requested_by=requested_by,
        provider=result.provider, model_name=result.model,
        input_tokens=result.input_tokens, output_tokens=result.output_tokens,
        latency_ms=result.latency_ms,
        cost_usd=usage_cost(result.input_tokens, result.output_tokens),
        succeeded=succeeded, error_code=error_code, created_at=utcnow(),
    )
    db.add(row)
    return row
