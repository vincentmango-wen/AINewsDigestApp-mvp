"""OpenAI client for Japanese news summaries."""

from __future__ import annotations

from typing import Any

from openai import APIConnectionError, APIError, APIStatusError, APITimeoutError, OpenAI

from app.core.exceptions import ExternalApiError

DEFAULT_OPENAI_MODEL = "gpt-5-mini"
DEFAULT_TIMEOUT_SECONDS = 20.0
DEFAULT_MAX_OUTPUT_TOKENS = 220
SUMMARY_INSTRUCTIONS = (
    "あなたはニュース要約アシスタントです。"
    "入力された記事タイトルと説明文をもとに、自然な日本語で2文から3文に要約してください。"
    "誇張や推測は避け、本文にない情報は補わないでください。"
)


class OpenAiClient:
    def __init__(
        self,
        *,
        api_key: str,
        model: str = DEFAULT_OPENAI_MODEL,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        max_output_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS,
        openai_client: OpenAI | None = None,
    ) -> None:
        self._model = model
        self._max_output_tokens = max_output_tokens
        self._client = openai_client or OpenAI(api_key=api_key, timeout=timeout)

    def summarize(self, title: str, description: str | None) -> str:
        prompt = self._build_prompt(title=title, description=description)

        try:
            response = self._client.responses.create(
                model=self._model,
                instructions=SUMMARY_INSTRUCTIONS,
                input=prompt,
                max_output_tokens=self._max_output_tokens,
            )
        except APITimeoutError as exc:
            raise ExternalApiError("OpenAI API の呼び出しがタイムアウトしました") from exc
        except APIStatusError as exc:
            raise ExternalApiError(
                f"OpenAI API の呼び出しに失敗しました: HTTP {exc.status_code}"
            ) from exc
        except APIConnectionError as exc:
            raise ExternalApiError("OpenAI API への接続に失敗しました") from exc
        except APIError as exc:
            raise ExternalApiError("OpenAI API の呼び出しに失敗しました") from exc

        summary = self._extract_text(response)
        if summary is None:
            raise ExternalApiError("OpenAI API が空の要約を返しました")
        return summary

    @staticmethod
    def _build_prompt(*, title: str, description: str | None) -> str:
        normalized_title = title.strip()
        if normalized_title == "":
            raise ExternalApiError("要約対象のタイトルが空です")

        lines = [f"タイトル: {normalized_title}"]
        if description is not None and description.strip() != "":
            lines.append(f"説明文: {description.strip()}")
        else:
            lines.append("説明文: なし")
        return "\n".join(lines)

    @staticmethod
    def _extract_text(response: Any) -> str | None:
        output_text = getattr(response, "output_text", None)
        if isinstance(output_text, str):
            normalized = output_text.strip()
            return normalized or None
        return None
