from __future__ import annotations

import logging

from app.core.exceptions import ExternalApiError
from app.schemas.article import Article
from app.services.summary_service import SummaryService


def build_article(article_id: int, *, title: str = "記事タイトル", description: str | None = "説明文") -> Article:
    return Article(
        article_id=article_id,
        url=f"https://example.com/articles/{article_id}",
        title=title,
        description=description,
        source_name="Example News",
        published_at="2026-04-25T09:00:00Z",
        category="AI",
        summary=None,
        summary_status="pending",
        fetched_at="2026-04-25T00:00:00Z",
        last_sent_run_id=None,
        created_at="2026-04-25T00:00:00Z",
        updated_at="2026-04-25T00:00:00Z",
    )


class DummyOpenAIClient:
    def __init__(self, responses: dict[int, str | Exception]) -> None:
        self._responses = responses
        self.calls: list[tuple[str, str | None]] = []

    def summarize(self, title: str, description: str | None) -> str:
        self.calls.append((title, description))
        article_index = len(self.calls)
        response = self._responses[article_index]
        if isinstance(response, Exception):
            raise response
        return response


class DummyArticleRepository:
    def __init__(self, articles: dict[int, Article]) -> None:
        self._articles = articles
        self.updates: list[tuple[int, str | None, str]] = []

    def update_summary(
        self,
        article_id: int,
        *,
        summary: str | None,
        summary_status: str,
    ) -> Article:
        self.updates.append((article_id, summary, summary_status))
        article = self._articles[article_id]
        updated_article = Article(
            article_id=article.article_id,
            url=article.url,
            title=article.title,
            description=article.description,
            source_name=article.source_name,
            published_at=article.published_at,
            category=article.category,
            summary=summary,
            summary_status=summary_status,
            fetched_at=article.fetched_at,
            last_sent_run_id=article.last_sent_run_id,
            created_at=article.created_at,
            updated_at=article.updated_at,
        )
        self._articles[article_id] = updated_article
        return updated_article


def test_summarize_articles_marks_success_for_each_successful_article() -> None:
    articles = [build_article(1), build_article(2), build_article(3)]
    repository = DummyArticleRepository({article.article_id: article for article in articles})
    openai_client = DummyOpenAIClient({1: "要約1。要約2。", 2: "要約3。要約4。", 3: "要約5。要約6。"})
    service = SummaryService(openai_client=openai_client, article_repository=repository)

    results = service.summarize_articles(1, articles)

    assert len(results) == 3
    assert repository.updates == [
        (1, "要約1。要約2。", "success"),
        (2, "要約3。要約4。", "success"),
        (3, "要約5。要約6。", "success"),
    ]


def test_summarize_articles_continues_when_one_article_fails() -> None:
    articles = [build_article(1), build_article(2), build_article(3)]
    repository = DummyArticleRepository({article.article_id: article for article in articles})
    openai_client = DummyOpenAIClient(
        {1: "要約1。要約2。", 2: ExternalApiError("failed"), 3: "要約5。要約6。"}
    )
    service = SummaryService(openai_client=openai_client, article_repository=repository)

    results = service.summarize_articles(1, articles)

    assert [article.article_id for article in results] == [1, 3]
    assert repository.updates == [
        (1, "要約1。要約2。", "success"),
        (2, None, "failed"),
        (3, "要約5。要約6。", "success"),
    ]


def test_summarize_articles_uses_title_only_when_description_is_missing() -> None:
    article = build_article(1, description=None)
    repository = DummyArticleRepository({1: article})
    openai_client = DummyOpenAIClient({1: "要約1。要約2。"})
    service = SummaryService(openai_client=openai_client, article_repository=repository)

    results = service.summarize_articles(1, [article])

    assert len(results) == 1
    assert openai_client.calls == [("記事タイトル", None)]
    assert repository.updates == [(1, "要約1。要約2。", "success")]


def test_summarize_articles_skips_articles_with_blank_title() -> None:
    article = build_article(1, title=" ")
    repository = DummyArticleRepository({1: article})
    openai_client = DummyOpenAIClient({})
    service = SummaryService(openai_client=openai_client, article_repository=repository)

    results = service.summarize_articles(1, [article])

    assert results == []
    assert openai_client.calls == []
    assert repository.updates == []


def test_summarize_articles_marks_failed_when_summary_is_blank() -> None:
    article = build_article(1)
    repository = DummyArticleRepository({1: article})
    openai_client = DummyOpenAIClient({1: "   "})
    service = SummaryService(openai_client=openai_client, article_repository=repository)

    results = service.summarize_articles(1, [article])

    assert results == []
    assert openai_client.calls == [("記事タイトル", "説明文")]
    assert repository.updates == [(1, None, "failed")]


def test_summarize_articles_logs_reason_when_summary_generation_fails(caplog) -> None:
    article = build_article(1)
    repository = DummyArticleRepository({1: article})
    openai_client = DummyOpenAIClient({1: ExternalApiError("OpenAI failed")})
    service = SummaryService(openai_client=openai_client, article_repository=repository)

    with caplog.at_level(logging.WARNING, logger="focusdigest.summary"):
        results = service.summarize_articles(99, [article])

    assert results == []
    assert "記事要約に失敗しました" in caplog.text
    assert "article_id=1" in caplog.text
    assert "OpenAI failed" in caplog.text
