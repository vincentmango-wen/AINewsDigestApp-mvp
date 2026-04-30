from __future__ import annotations

import httpx

from app.clients.news_api_client import NewsApiClient


def test_fetch_news_clamps_limit_to_free_plan_maximum_and_queries_supported_languages() -> None:
    recorded_requests: list[dict[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        recorded_requests.append(
            {
                "limit": request.url.params["limit"],
                "language": request.url.params.get("language", ""),
                "locale": request.url.params.get("locale", ""),
            }
        )
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

    assert recorded_requests == [
        {"limit": "3", "language": "en", "locale": ""},
        {"limit": "3", "language": "ja", "locale": ""},
        {"limit": "3", "language": "", "locale": "tw,hk"},
    ]
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


def test_fetch_news_deduplicates_articles_across_language_queries() -> None:
    request_count = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal request_count
        request_count += 1
        return httpx.Response(
            200,
            json={
                "data": [
                    {
                        "title": f"AI市場が拡大 {request_count}",
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

    results = client.fetch_news("AI", page_size=5)

    assert request_count == 3
    assert len(results) == 1
    assert results[0].url == "https://example.com/articles/1"
