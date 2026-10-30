from __future__ import annotations

import json
import re
from typing import TypeVar

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .provider import InvalidModelOutput


class StrictOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class FindingOutput(StrictOutput):
    category: str = Field(min_length=2, max_length=64)
    severity: str = Field(pattern="^(info|low|medium|high|critical)$")
    title: str = Field(min_length=3, max_length=300)
    description: str = Field(min_length=5, max_length=4000)
    claim: str | None = Field(default=None, max_length=4000)
    observed_value: str | None = Field(default=None, max_length=2000)
    evidence_ids: list[str] = Field(default_factory=list, max_length=30)
    source_ids: list[str] = Field(default_factory=list, max_length=30)
    confidence: float = Field(ge=0, le=1)
    status: str = Field(default="requires_human_review", pattern="^(requires_human_review|hypothesis|unresolved)$")
    basis: str = Field(default="inference", pattern="^(record_fact|observation|inference|unresolved)$")
    recommendation: str | None = Field(default=None, max_length=2000)


class ClaimOutput(StrictOutput):
    text: str = Field(min_length=1, max_length=1000)
    evidence_id: str = Field(min_length=2, max_length=80)
    source_location: str = Field(min_length=1, max_length=160)
    method: str = Field(default="model_extraction", pattern="^(heuristic_candidate|model_extraction|model_interpretation)$")
    confidence: float = Field(default=0.25, ge=0, le=1)


class SourceOutput(StrictOutput):
    id: str | None = Field(default=None, max_length=80)
    title: str = Field(min_length=1, max_length=300)
    url: str = Field(min_length=8, max_length=2000, pattern="^https://")
    publisher: str | None = Field(default=None, max_length=200)
    domain: str | None = Field(default=None, max_length=255)
    retrieved_at: str | None = Field(default=None, max_length=40)
    published_at: str | None = Field(default=None, max_length=40)
    excerpt: str | None = Field(default=None, max_length=2000)


class AgentOutput(StrictOutput):
    summary: str = Field(min_length=1, max_length=4000)
    findings: list[FindingOutput] = Field(default_factory=list, max_length=40)
    claims: list[ClaimOutput] = Field(default_factory=list, max_length=80)
    limitations: list[str] = Field(default_factory=list, max_length=40)
    sources: list[SourceOutput] = Field(default_factory=list, max_length=40)


T = TypeVar("T", bound=BaseModel)


def parse_structured_output(content: str, schema: type[T]) -> T:
    candidate = content.strip()
    if candidate.startswith("```"):
        candidate = re.sub(r"^```(?:json)?\s*|\s*```$", "", candidate, flags=re.IGNORECASE).strip()
    try:
        value = json.loads(candidate)
        if not isinstance(value, dict):
            raise ValueError("Expected a JSON object")
        return schema.model_validate(value)
    except (json.JSONDecodeError, ValidationError, ValueError, TypeError) as exc:
        raise InvalidModelOutput() from exc
