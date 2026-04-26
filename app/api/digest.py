"""Digest job APIs."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, Depends
from fastapi.responses import JSONResponse

from app.clients.news_api_client import NewsApiClient
from app.clients.openai_client import OpenAiClient
from app.core.config import Settings, get_settings
from app.core.exceptions import AppError
from app.repositories.article_repository import ArticleRepository
from app.repositories.digest_run_repository import DigestRunRepository
from app.schemas.api import ApiErrorResponse, ApiSuccessResponse, DigestRunData
from app.services.article_selector import ArticleSelector
from app.services.digest_service import DigestService
from app.services.mail_service import MailService
from app.services.news_service import NewsService
from app.services.run_history_service import RunHistoryService
from app.services.summary_service import SummaryService

router = APIRouter(prefix="/api/v1", tags=["digest"])


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


def _error_response(error: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=error.status_code,
        content=ApiErrorResponse(
            error_code=error.error_code,
            message=error.message,
        ).model_dump(),
    )


@router.post("/jobs/digest/run", response_model=ApiSuccessResponse[DigestRunData])
def run_digest_job(
    payload: dict[str, Any] | None = Body(default=None),
    digest_service: DigestService = Depends(get_digest_service),
) -> ApiSuccessResponse[DigestRunData] | JSONResponse:
    if payload not in (None, {}):
        return JSONResponse(
            status_code=400,
            content=ApiErrorResponse(
                error_code="VALIDATION_ERROR",
                message="リクエストボディは空または空JSONのみ許可されています",
            ).model_dump(),
        )

    try:
        result = digest_service.run("manual")
    except AppError as error:
        return _error_response(error)

    return ApiSuccessResponse[DigestRunData](
        data=DigestRunData.from_digest_run(result.run),
        message="ダイジェスト処理が完了しました",
    )
