import json

import httpx
import pytest

from services.api.app.services.ai.model_registry import describe_model, require_nemotron_model
from services.api.app.services.ai.nebius_client import NebiusClient
from services.api.app.services.ai.provider import AIProviderError
from services.api.app.services.ai.structured_output import AgentOutput, parse_structured_output
from services.api.app.services.ai.usage_tracker import usage_cost


def test_model_registry_marks_only_configured_nemotron_as_nemotron():
    assert describe_model("nvidia/nemotron-3-super-120b-a12b").family == "NVIDIA Nemotron"
    assert describe_model("some-provider/other-model").family == "unverified"
    with pytest.raises(ValueError):
        require_nemotron_model("some-provider/other-model")


def test_structured_output_is_parsed_and_validated():
    result = parse_structured_output(json.dumps({
        "summary": "Reviewed one supplied record.", "findings": [], "claims": [],
        "limitations": ["No external research was performed."], "sources": [],
    }), AgentOutput)
    assert result.summary == "Reviewed one supplied record."
    with pytest.raises(AIProviderError) as error:
        parse_structured_output('{"summary":', AgentOutput)
    assert error.value.code == "invalid_model_output"


def test_nebius_client_sends_openai_compatible_chat_request_and_reads_usage():
    requests = []

    def responder(request):
        requests.append(request)
        return httpx.Response(200, json={
            "model": "nvidia/nemotron-3-super-120b-a12b",
            "choices": [{"message": {"content": "{\"summary\":\"ok\"}"}}],
            "usage": {"prompt_tokens": 21, "completion_tokens": 7},
        })

    client = httpx.Client(transport=httpx.MockTransport(responder))
    provider = NebiusClient(
        api_key="test-secret", base_url="https://unit.test/v1",
        model="nvidia/nemotron-3-super-120b-a12b", max_retries=0, http_client=client,
    )
    result = provider.generate([{"role": "user", "content": "Return JSON."}], json_mode=True)
    request = requests[0]
    body = json.loads(request.content)
    assert request.url.path == "/v1/chat/completions"
    assert request.headers["Authorization"] == "Bearer test-secret"
    assert body["response_format"] == {"type": "json_object"}
    assert body["model"] == "nvidia/nemotron-3-super-120b-a12b"
    assert result.input_tokens == 21
    assert result.output_tokens == 7
    assert result.provider == "nebius_token_factory"
    provider.close()


def test_provider_errors_are_sanitized_and_non_retryable_client_errors_are_not_retried():
    calls = []

    def responder(_request):
        calls.append(1)
        return httpx.Response(401, text="request failed for secret test-secret")

    client = httpx.Client(transport=httpx.MockTransport(responder))
    provider = NebiusClient(
        api_key="test-secret", base_url="https://unit.test/v1",
        model="nvidia/nemotron-3-super-120b-a12b", max_retries=3, http_client=client,
    )
    with pytest.raises(AIProviderError) as error:
        provider.generate([{"role": "user", "content": "test"}])
    assert error.value.code == "provider_rejected_request"
    assert "test-secret" not in str(error.value)
    assert len(calls) == 1
    provider.close()


def test_provider_retries_transient_server_error_with_a_bounded_attempt_count():
    calls = []

    def responder(_request):
        calls.append(1)
        if len(calls) == 1:
            return httpx.Response(503, text="temporary outage")
        return httpx.Response(200, json={
            "choices": [{"message": {"content": "ok"}}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1},
        })

    client = httpx.Client(transport=httpx.MockTransport(responder))
    provider = NebiusClient(
        api_key="test-secret", base_url="https://unit.test/v1",
        model="nvidia/nemotron-3-super-120b-a12b", max_retries=1, http_client=client,
    )
    result = provider.generate([{"role": "user", "content": "test"}])
    assert result.output_tokens == 1
    assert len(calls) == 2
    provider.close()


def test_cost_is_unknown_until_both_rates_are_configured(monkeypatch):
    from services.api.app import config

    monkeypatch.setattr(config, "AI_INPUT_COST_PER_MILLION_USD", "0.30")
    monkeypatch.setattr(config, "AI_OUTPUT_COST_PER_MILLION_USD", "0.90")
    assert usage_cost(1_000_000, 1_000_000) == pytest.approx(1.20)
    monkeypatch.setattr(config, "AI_OUTPUT_COST_PER_MILLION_USD", "")
    assert usage_cost(1_000_000, 1_000_000) is None
