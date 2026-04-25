"""TheNewsAPI client implementation."""

from __future__ import annotations

from collections.abc import Sequence
from json import JSONDecodeError
from typing import Any

import httpx

from app.core.exceptions import ExternalApiError
from app.schemas.article import ArticleFetchResult

NEWS_API_BASE_URL = "https://api.thenewsapi.com/v1/news/all"
DEFAULT_TIMEOUT_SECONDS = 10.0
FREE_PLAN_MAX_PAGE_SIZE = 3


class NewsApiClient:
    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = NEWS_API_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        max_page_size: int = FREE_PLAN_MAX_PAGE_SIZE,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url
        self._timeout = timeout
        self._max_page_size = max_page_size
        self._http_client = http_client

    def fetch_news(self, category: str, page_size: int) -> list[ArticleFetchResult]:
        response_payload = self._request(category=category, page_size=page_size)
        articles = response_payload.get("data")
        if not isinstance(articles, Sequence) or isinstance(articles, (str, bytes)):
            raise ExternalApiError("TheNewsAPI のレスポンス形式が不正です")

        return [
            ArticleFetchResult(
                title=self._read_text(article, "title"),
                description=self._read_description(article),
                url=self._read_text(article, "url"),
                published_at=self._read_text(article, "published_at"),
                source_name=self._read_source_name(article),
                category=category,
            )
            for article in articles
            if isinstance(article, dict)
        ]

    def _request(self, *, category: str, page_size: int) -> dict[str, Any]:
        effective_page_size = min(page_size, self._max_page_size)
        params = {
            "api_token": self._api_key,
            "search": category,
            "limit": effective_page_size,
        }

        if self._http_client is not None:
            return self._send_request(self._http_client, params=params)

        with httpx.Client(timeout=self._timeout) as client:
            return self._send_request(client, params=params)

    def _send_request(
        self,
        client: httpx.Client,
        *,
        params: dict[str, str | int],
    ) -> dict[str, Any]:
        try:
            response = client.get(
                self._base_url,
                params=params,
                timeout=self._timeout,
            )
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise ExternalApiError("TheNewsAPI の呼び出しがタイムアウトしました") from exc
        except httpx.HTTPStatusError as exc:
            raise ExternalApiError(
                f"TheNewsAPI の呼び出しに失敗しました: HTTP {exc.response.status_code}"
            ) from exc
        except httpx.HTTPError as exc:
            raise ExternalApiError("TheNewsAPI の呼び出しに失敗しました") from exc

        try:
            payload = response.json()
        except JSONDecodeError as exc:
            raise ExternalApiError("TheNewsAPI のレスポンス JSON 解析に失敗しました") from exc

        if not isinstance(payload, dict):
            raise ExternalApiError("TheNewsAPI のレスポンス形式が不正です")

        error = payload.get("error")
        if isinstance(error, dict):
            message = error.get("message")
            if isinstance(message, str) and message.strip() != "":
                raise ExternalApiError(f"TheNewsAPI エラー: {message.strip()}")
            raise ExternalApiError("TheNewsAPI がエラーレスポンスを返しました")

        return payload

    @staticmethod
    def _read_text(article: dict[str, Any], field_name: str) -> str | None:
        value = article.get(field_name)
        if isinstance(value, str):
            normalized = value.strip()
            return normalized or None
        return None

    @classmethod
    def _read_description(cls, article: dict[str, Any]) -> str | None:
        description = cls._read_text(article, "description")
        if description is not None:
            return description
        return cls._read_text(article, "snippet")

    @classmethod
    def _read_source_name(cls, article: dict[str, Any]) -> str | None:
        return cls._read_text(article, "source")
