from __future__ import annotations

import time
from typing import Any

import httpx

from ... import config
from .model_registry import require_nemotron_model
from .provider import AIProviderError, ChatResult, ProviderNotConfigured


class NebiusClient:
    provider_name = "nebius_token_factory"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        max_retries: int | None = None,
        http_client: httpx.Client | None = None,
    ):
        self.api_key = config.NEBIUS_API_KEY if api_key is None else api_key
        self.base_url = (config.NEBIUS_BASE_URL if base_url is None else base_url).rstrip("/")
        self.model = config.NEBIUS_MODEL if model is None else model
        self.max_retries = config.NEBIUS_MAX_RETRIES if max_retries is None else max(0, min(max_retries, 4))
        self._client = http_client

    def _http(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(timeout=httpx.Timeout(
                connect=config.NEBIUS_CONNECT_TIMEOUT_SECONDS,
                read=config.NEBIUS_READ_TIMEOUT_SECONDS,
                write=10.0,
                pool=5.0,
            ))
        return self._client

    def health_status(self) -> dict[str, Any]:
        from urllib.parse import urlparse

        try:
            model = require_nemotron_model(self.model)
            model_family = model.family
            state = "ready" if self.api_key else "needs_api_key"
        except ValueError:
            model_family = "unverified"
            state = "invalid_model_configuration"
        return {
            "provider": self.provider_name,
            "configured": bool(self.api_key),
            "state": state,
            "model": self.model,
            "model_family": model_family,
            "api_host": urlparse(self.base_url).hostname,
            "credential_configured": bool(self.api_key),
        }

    def generate(self, messages: list[dict[str, str]], *, json_mode: bool = False) -> ChatResult:
        if not self.api_key:
            raise ProviderNotConfigured()
        descriptor = require_nemotron_model(self.model)
        if not messages or any(item.get("role") not in {"system", "user", "assistant"} for item in messages):
            raise AIProviderError("invalid_request", "At least one valid chat message is required.")
        if any(not isinstance(item.get("content"), str) for item in messages):
            raise AIProviderError("invalid_request", "Chat message content must be text.")
        payload: dict[str, Any] = {
            "model": descriptor.model_id,
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": config.AI_MAX_COMPLETION_TOKENS,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        for attempt in range(self.max_retries + 1):
            started = time.monotonic()
            try:
                response = self._http().post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
                response.raise_for_status()
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                if not isinstance(content, str) or not content.strip():
                    raise AIProviderError("empty_model_output", "The configured model returned an empty response.")
                usage = result.get("usage") or {}
                return ChatResult(
                    content=content,
                    provider=self.provider_name,
                    model=str(result.get("model") or descriptor.model_id),
                    input_tokens=max(0, int(usage.get("prompt_tokens") or usage.get("input_tokens") or 0)),
                    output_tokens=max(0, int(usage.get("completion_tokens") or usage.get("output_tokens") or 0)),
                    latency_ms=max(0, round((time.monotonic() - started) * 1000)),
                )
            except AIProviderError:
                raise
            except httpx.HTTPStatusError as exc:
                code = exc.response.status_code
                if (code == 429 or code >= 500) and attempt < self.max_retries:
                    time.sleep(min(0.5 * (2**attempt), 4.0))
                    continue
                safe_code = "rate_limited" if code == 429 else ("provider_unavailable" if code >= 500 else "provider_rejected_request")
                raise AIProviderError(safe_code, f"Nebius Token Factory returned HTTP {code}.") from None
            except httpx.TimeoutException:
                if attempt < self.max_retries:
                    time.sleep(min(0.5 * (2**attempt), 4.0))
                    continue
                raise AIProviderError("provider_timeout", "Nebius Token Factory did not respond before the configured timeout.") from None
            except httpx.HTTPError:
                if attempt < self.max_retries:
                    time.sleep(min(0.5 * (2**attempt), 4.0))
                    continue
                raise AIProviderError("provider_connection_error", "Could not connect to Nebius Token Factory.") from None
            except (KeyError, TypeError, ValueError):
                raise AIProviderError("invalid_provider_response", "Nebius Token Factory returned an invalid response shape.") from None
        raise AIProviderError("provider_unavailable", "Nebius Token Factory request failed.")

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None
