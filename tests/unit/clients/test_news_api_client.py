from __future__ import annotations

import httpx

from app.clients.news_api_client import NewsApiClient


def test_fetch_news_clamps_limit_to_free_plan_maximum() -> None:
    recorded_request: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        recorded_request["limit"] = request.url.params["limit"]
        return httpx.Response(
            200,
            json={
                "data": [
                    {
                        "title": "AI市場が拡大",
                        "description": "生成AIの導入が進んでいる。",
                        "url": "https://example.com/articles/1",
                        "published_at": "2026-04-25T09:00:00Z",
                        "source": "Example News",
                    }
                ]
            },
        )

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport)
    client = NewsApiClient(api_key="dummy", http_client=http_client)

    results = client.fetch_news("AI", page_size=20)

    assert recorded_request["limit"] == "3"
    assert len(results) == 1
    assert results[0].title == "AI市場が拡大"
    assert results[0].description == "生成AIの導入が進んでいる。"


def test_fetch_news_uses_snippet_when_description_is_missing() -> None:
    transport = httpx.MockTransport(
        lambda _: httpx.Response(
            200,
            json={
                "data": [
                    {
                        "title": "AI市場が拡大",
                        "snippet": "説明文の代替テキスト。",
                        "url": "https://example.com/articles/1",
                        "published_at": "2026-04-25T09:00:00Z",
                        "source": "Example News",
                    }
                ]
            },
        )
    )
    http_client = httpx.Client(transport=transport)
    client = NewsApiClient(api_key="dummy", http_client=http_client)

    results = client.fetch_news("AI", page_size=1)

    assert results[0].description == "説明文の代替テキスト。"
