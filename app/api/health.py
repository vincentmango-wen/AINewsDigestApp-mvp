"""Health check API."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter

from app.schemas.api import ApiSuccessResponse, HealthCheckData

router = APIRouter(prefix="/api/v1", tags=["health"])


@router.get("/health", response_model=ApiSuccessResponse[HealthCheckData])
def get_health() -> ApiSuccessResponse[HealthCheckData]:
    return ApiSuccessResponse[HealthCheckData](
        data=HealthCheckData(
            status="ok",
            app_name="FocusDigest",
            timestamp=datetime.now().astimezone().isoformat(),
        ),
        message="成功",
    )
