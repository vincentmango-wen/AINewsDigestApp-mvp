from __future__ import annotations

from app.schemas.article import ArticleFetchResult
from app.services.news_service import NewsService


class DummyNewsClient:
    def __init__(self, articles: list[ArticleFetchResult]) -> None:
        self.articles = articles
        self.calls: list[tuple[str, int]] = []

    def fetch_news(self, category: str, page_size: int) -> list[ArticleFetchResult]:
        self.calls.append((category, page_size))
        return self.articles


def test_fetch_latest_articles_filters_missing_required_fields() -> None:
    client = DummyNewsClient(
        [
            ArticleFetchResult(
                title="AI市場が拡大",
                description="生成AIの導入が進んでいる。",
                url="https://example.com/articles/1",
                published_at="2026-04-25T09:00:00Z",
                source_name="Example News",
                category="AI",
            ),
            ArticleFetchResult(
                title=None,
                description="タイトル欠落",
                url="https://example.com/articles/2",
                published_at="2026-04-25T10:00:00Z",
                source_name="Example News",
                category="AI",
            ),
            ArticleFetchResult(
                title="URL欠落",
                description="URLがない",
                url=None,
                published_at="2026-04-25T11:00:00Z",
                source_name="Example News",
                category="AI",
            ),
            ArticleFetchResult(
                title="公開日時欠落",
                description="published_at がない",
                url="https://example.com/articles/4",
                published_at=None,
                source_name="Example News",
                category="AI",
            ),
        ]
    )
    service = NewsService(client)

    results = service.fetch_latest_articles("AI", 20)

    assert client.calls == [("AI", 20)]
    assert len(results) == 1
    assert results[0].title == "AI市場が拡大"


def test_fetch_latest_articles_filters_invalid_published_at() -> None:
    client = DummyNewsClient(
        [
            ArticleFetchResult(
                title="AI市場が拡大",
                description="正常記事",
                url="https://example.com/articles/1",
                published_at="2026-04-25T09:00:00Z",
                source_name="Example News",
                category="AI",
            ),
            ArticleFetchResult(
                title="日時不正",
                description="日付形式が壊れている",
                url="https://example.com/articles/2",
                published_at="not-a-date",
                source_name="Example News",
                category="AI",
            ),
        ]
    )
    service = NewsService(client)

    results = service.fetch_latest_articles("AI", 20)

    assert len(results) == 1
    assert results[0].published_at == "2026-04-25T09:00:00Z"


def test_fetch_latest_articles_filters_blank_required_fields() -> None:
    client = DummyNewsClient(
        [
            ArticleFetchResult(
                title="  ",
                description="タイトルが空白のみ",
                url="https://example.com/articles/1",
                published_at="2026-04-25T09:00:00Z",
                source_name="Example News",
                category="AI",
            ),
            ArticleFetchResult(
                title="URL空白",
                description="URLが空白のみ",
                url="   ",
                published_at="2026-04-25T10:00:00Z",
                source_name="Example News",
                category="AI",
            ),
            ArticleFetchResult(
                title="公開日時空白",
                description="published_at が空白のみ",
                url="https://example.com/articles/3",
                published_at="   ",
                source_name="Example News",
                category="AI",
            ),
            ArticleFetchResult(
                title="正常記事",
                description="正常データ",
                url="https://example.com/articles/4",
                published_at="2026-04-25T11:00:00Z",
                source_name="Example News",
                category="AI",
            ),
        ]
    )
    service = NewsService(client)

    results = service.fetch_latest_articles("AI", 20)

    assert len(results) == 1
    assert results[0].url == "https://example.com/articles/4"
