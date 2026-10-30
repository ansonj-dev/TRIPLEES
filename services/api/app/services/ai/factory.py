from __future__ import annotations

from ... import config
from .local_mock import LocalMockProvider
from .nebius_client import NebiusClient
from .provider import AIProvider, UnavailableAIProvider


def create_ai_provider(provider_name: str | None = None) -> AIProvider:
    selected = (provider_name or config.AI_PROVIDER).strip().lower()
    if selected == "nebius_token_factory":
        return NebiusClient()
    if selected == "local_mock":
        return LocalMockProvider()
    if selected == "nebius_ai_cloud":
        return UnavailableAIProvider(
            selected,
            "Nebius AI Cloud inference is not configured: verify a deployed endpoint's API protocol and model first.",
            state="unverified_endpoint",
        )
    return UnavailableAIProvider(
        selected or "unconfigured",
        "AI_PROVIDER must be nebius_token_factory, local_mock, or nebius_ai_cloud.",
        state="invalid_configuration",
    )