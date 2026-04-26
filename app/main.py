"""Application entrypoint for FocusDigest."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.digest import router as digest_router
from app.api.health import router as health_router
from app.core.exceptions import AppError
from app.core.logging import configure_logging
from app.db.connection import initialize_database
from app.schemas.api import ApiErrorResponse
from app.schedulers.digest_scheduler import DigestScheduler

APP_TITLE = "FocusDigest"
APP_VERSION = "v1"
APP_DESCRIPTION = (
    "FocusDigest MVP API. "
    "ローカル検証用途として、ヘルスチェック、ダイジェスト手動実行、"
    "最新実行結果取得を提供します。"
)


def build_digest_scheduler() -> DigestScheduler:
    return DigestScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger = configure_logging()
    initialize_database()
    logger.info("データベースを初期化しました", extra={"run_id": "-"})
    digest_scheduler = build_digest_scheduler()
    digest_scheduler.start()
    app.state.digest_scheduler = digest_scheduler

    try:
        yield
    finally:
        digest_scheduler.shutdown()


app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    description=APP_DESCRIPTION,
    lifespan=lifespan,
)
app.include_router(health_router)
app.include_router(digest_router)


@app.exception_handler(AppError)
async def handle_app_error(_: Request, error: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=error.status_code,
        content=ApiErrorResponse(
            error_code=error.error_code,
            message=error.message,
        ).model_dump(),
    )


@app.exception_handler(RequestValidationError)
async def handle_request_validation_error(_: Request, __: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content=ApiErrorResponse(
            error_code="VALIDATION_ERROR",
            message="入力値が不正です",
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def handle_unexpected_error(_: Request, __: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content=ApiErrorResponse(
            error_code="INTERNAL_SERVER_ERROR",
            message="サーバー内部エラーが発生しました",
        ).model_dump(),
    )
