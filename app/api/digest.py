"""Digest job APIs."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, Depends

from app.clients.news_api_client import NewsApiClient
from app.clients.openai_client import OpenAiClient
from app.core.config import Settings, get_settings
from app.core.exceptions import NotFoundError, ValidationError
from app.repositories.article_repository import ArticleRepository
from app.repositories.digest_run_repository import DigestRunRepository
from app.schemas.api import ApiSuccessResponse, DigestRunData
from app.services.article_selector import ArticleSelector
from app.services.digest_service import DigestService
from app.services.mail_service import MailService
from app.services.news_service import NewsService
from app.services.run_history_service import RunHistoryService
from app.services.summary_service import SummaryService

router = APIRouter(prefix="/api/v1", tags=["digest"])


def get_run_history_service() -> RunHistoryService:
    return RunHistoryService(DigestRunRepository())


def get_digest_service(settings: Settings = Depends(get_settings)) -> DigestService:
    article_repository = ArticleRepository()

    return DigestService(
        settings=settings,
        news_service=NewsService(NewsApiClient(api_key=settings.THE_NEWS_API_TOKEN)),
        article_repository=article_repository,
        article_selector=ArticleSelector(),
        summary_service=SummaryService(
            openai_client=OpenAiClient(api_key=settings.openai_api_key),
            article_repository=article_repository,
        ),
        mail_service=MailService(settings=settings),
        run_history_service=RunHistoryService(DigestRunRepository()),
    )
@router.post("/jobs/digest/run", response_model=ApiSuccessResponse[DigestRunData])
def run_digest_job(
    payload: dict[str, Any] | None = Body(default=None),
    digest_service: DigestService = Depends(get_digest_service),
) -> ApiSuccessResponse[DigestRunData]:
    if payload not in (None, {}):
        raise ValidationError("リクエストボディは空または空JSONのみ許可されています")

    result = digest_service.run("manual")

    return ApiSuccessResponse[DigestRunData](
        data=DigestRunData.from_digest_run(result.run),
        message="ダイジェスト処理が完了しました",
    )


@router.get("/jobs/digest/runs/latest", response_model=ApiSuccessResponse[DigestRunData])
def get_latest_digest_run(
    run_history_service: RunHistoryService = Depends(get_run_history_service),
) -> ApiSuccessResponse[DigestRunData]:
    latest_run = run_history_service.get_latest_run()
    if latest_run is None:
        raise NotFoundError("直近の実行履歴が存在しません")

    return ApiSuccessResponse[DigestRunData](
        data=DigestRunData.from_digest_run(latest_run),
        message="成功",
    )
