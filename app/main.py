"""Application entrypoint for FocusDigest."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.health import router as health_router
from app.core.logging import configure_logging
from app.db.connection import initialize_database


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger = configure_logging()
    initialize_database()
    logger.info("データベースを初期化しました", extra={"run_id": "-"})
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(health_router)
