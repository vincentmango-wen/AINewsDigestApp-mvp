from __future__ import annotations

from types import SimpleNamespace

import httpx
import pytest
from openai import APITimeoutError

from app.clients.openai_client import DEFAULT_REASONING, OpenAiClient
from app.core.exceptions import ExternalApiError


class DummyResponses:
    def __init__(self, response: object | None = None, error: Exception | None = None) -> None:
        self._response = response
        self._error = error
        self.calls: list[dict[str, object]] = []

    def create(self, **kwargs: object) -> object:
        self.calls.append(kwargs)
        if self._error is not None:
            raise self._error
        return self._response


class DummyOpenAIClient:
    def __init__(self, responses: DummyResponses) -> None:
        self.responses = responses


def test_summarize_returns_output_text() -> None:
    responses = DummyResponses(response=SimpleNamespace(output_text="要約1。要約2。"))
    client = OpenAiClient(api_key="dummy", openai_client=DummyOpenAIClient(responses))

    result = client.summarize("AI市場が拡大", "生成AIの導入が企業で進んでいる。")

    assert result == "要約1。要約2。"
    assert responses.calls[0]["model"] == "gpt-5-mini"
    assert responses.calls[0]["max_output_tokens"] == 768
    assert responses.calls[0]["reasoning"] == DEFAULT_REASONING
    assert "400文字から500文字" in str(responses.calls[0]["instructions"])
    assert "タイトル: AI市場が拡大" in str(responses.calls[0]["input"])
    assert "説明文: 生成AIの導入が企業で進んでいる。" in str(responses.calls[0]["input"])


def test_summarize_uses_title_only_when_description_is_missing() -> None:
    responses = DummyResponses(response=SimpleNamespace(output_text="要約1。要約2。"))
    client = OpenAiClient(api_key="dummy", openai_client=DummyOpenAIClient(responses))

    client.summarize("AI市場が拡大", None)

    assert "説明文: なし" in str(responses.calls[0]["input"])


def test_summarize_raises_when_output_is_empty() -> None:
    responses = DummyResponses(response=SimpleNamespace(output_text="   "))
    client = OpenAiClient(api_key="dummy", openai_client=DummyOpenAIClient(responses))

    with pytest.raises(ExternalApiError, match="空の要約"):
        client.summarize("AI市場が拡大", "生成AIの導入が企業で進んでいる。")


def test_summarize_converts_timeout_to_external_api_error() -> None:
    request = httpx.Request("POST", "https://api.openai.com/v1/responses")
    responses = DummyResponses(error=APITimeoutError(request=request))
    client = OpenAiClient(api_key="dummy", openai_client=DummyOpenAIClient(responses))

    with pytest.raises(ExternalApiError, match="タイムアウト"):
        client.summarize("AI市場が拡大", "生成AIの導入が企業で進んでいる。")
