from __future__ import annotations

import time

from .provider import ChatResult


class LocalMockProvider:
    provider_name = "local_mock"
    model = "local-mock-v1"

    def health_status(self) -> dict[str, str | bool]:
        return {
            "provider": self.provider_name,
            "configured": True,
            "state": "mock_only",
            "model": self.model,
            "real_inference": False,
        }

    def generate(self, _messages: list[dict[str, str]], *, json_mode: bool = False) -> ChatResult:
        started = time.monotonic()
        content = (
            '{"summary":"Local mock response; no external model inference was performed.",'
            '"findings":[],"claims":[],'
            '"limitations":["This is simulated output, not Nemotron inference."],"sources":[]}'
        )
        return ChatResult(
            content=content,
            provider=self.provider_name,
            model=self.model,
            input_tokens=0,
            output_tokens=0,
            latency_ms=max(0, round((time.monotonic() - started) * 1000)),
        )