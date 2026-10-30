from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelDescriptor:
    model_id: str
    provider: str
    family: str
    source: str


def describe_model(model_id: str) -> ModelDescriptor:
    normalized = model_id.strip()
    lower = normalized.lower()
    if lower.startswith("nvidia/") and "nemotron" in lower:
        return ModelDescriptor(normalized, "nebius_token_factory", "NVIDIA Nemotron", "configured")
    return ModelDescriptor(normalized, "nebius_token_factory", "unverified", "configured")


def require_nemotron_model(model_id: str) -> ModelDescriptor:
    descriptor = describe_model(model_id)
    if descriptor.family != "NVIDIA Nemotron":
        raise ValueError("NEBIUS_MODEL must identify an NVIDIA Nemotron model (nvidia/...nemotron...).")
    return descriptor
