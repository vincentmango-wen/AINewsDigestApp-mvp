from __future__ import annotations

from app.schemas.article import Article
from app.services.article_selector import ArticleSelector


def build_article(article_id: int, published_at: str, *, category: str = "AI") -> Article:
    return Article(
        article_id=article_id,
        url=f"https://example.com/articles/{article_id}",
        title=f"記事{article_id}",
        description=f"説明{article_id}",
        source_name="Example News",
        published_at=published_at,
        category=category,
        summary=None,
        summary_status="pending",
        fetched_at="2026-04-25T00:00:00Z",
        last_sent_run_id=None,
        created_at="2026-04-25T00:00:00Z",
        updated_at="2026-04-25T00:00:00Z",
    )


def test_select_top_articles_returns_latest_five_articles() -> None:
    selector = ArticleSelector()
    articles = [
        build_article(1, "2026-04-25T01:00:00Z"),
        build_article(2, "2026-04-25T02:00:00Z"),
        build_article(3, "2026-04-25T03:00:00Z"),
        build_article(4, "2026-04-25T04:00:00Z"),
        build_article(5, "2026-04-25T05:00:00Z"),
        build_article(6, "2026-04-25T06:00:00Z"),
    ]

    results = selector.select_top_articles(articles, limit=5)

    assert [article.article_id for article in results] == [6, 5, 4, 3, 2]


def test_select_top_articles_skips_articles_with_blank_published_at() -> None:
    selector = ArticleSelector()
    articles = [
        build_article(1, "2026-04-25T01:00:00Z"),
        build_article(2, " "),
        build_article(3, "2026-04-25T03:00:00Z"),
    ]

    results = selector.select_top_articles(articles, limit=5)

    assert [article.article_id for article in results] == [3, 1]


def test_select_top_articles_returns_empty_when_limit_is_zero() -> None:
    selector = ArticleSelector()
    articles = [build_article(1, "2026-04-25T01:00:00Z")]

    results = selector.select_top_articles(articles, limit=0)

    assert results == []
