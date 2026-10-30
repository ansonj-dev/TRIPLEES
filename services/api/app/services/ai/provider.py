from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


class AIProviderError(RuntimeError):
    """Safe provider error carrying a non-secret machine-readable code."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


class ProviderNotConfigured(AIProviderError):
    def __init__(self):
        super().__init__("provider_not_configured", "Nebius Token Factory credentials are not configured.")


class InvalidModelOutput(AIProviderError):
    def __init__(self, message: str = "The model response did not match the required structured format."):
        super().__init__("invalid_model_output", message)


@dataclass(frozen=True)
class ChatResult:
    content: str
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: int


class AIProvider(Protocol):
    provider_name: str

    def generate(self, messages: list[dict[str, str]], *, json_mode: bool = False) -> ChatResult:
        ...

    def health_status(self) -> dict[str, Any]:
        ...
