from __future__ import annotations

from app.schemas.api import (
    ApiErrorResponse,
    ApiSuccessResponse,
    DigestRunData,
    EmptyData,
    HealthCheckData,
)
from app.schemas.digest_run import DigestRun


def build_digest_run() -> DigestRun:
    return DigestRun(
        run_id=12,
        triggered_by="manual",
        started_at="2026-04-18T08:00:00+09:00",
        finished_at="2026-04-18T08:01:42+09:00",
        fetched_count=20,
        selected_count=5,
        summarized_count=4,
        email_status="success",
        error_message=None,
        created_at="2026-04-18T08:00:00+09:00",
        updated_at="2026-04-18T08:01:42+09:00",
    )


def test_success_response_wraps_health_check_payload() -> None:
    response = ApiSuccessResponse[HealthCheckData](
        data=HealthCheckData(
            status="ok",
            app_name="FocusDigest",
            timestamp="2026-04-18T08:00:00+09:00",
        ),
        message="成功",
    )

    assert response.model_dump() == {
        "success": True,
        "data": {
            "status": "ok",
            "app_name": "FocusDigest",
            "timestamp": "2026-04-18T08:00:00+09:00",
        },
        "message": "成功",
    }


def test_success_response_allows_empty_object_payload() -> None:
    response = ApiSuccessResponse[EmptyData](
        data=EmptyData(),
        message="成功",
    )

    assert response.model_dump() == {
        "success": True,
        "data": {},
        "message": "成功",
    }


def test_error_response_matches_api_spec() -> None:
    response = ApiErrorResponse(
        error_code="JOB_ALREADY_RUNNING",
        message="既にジョブ実行中です",
    )

    assert response.model_dump() == {
        "success": False,
        "error_code": "JOB_ALREADY_RUNNING",
        "message": "既にジョブ実行中です",
    }


def test_digest_run_data_maps_from_domain_schema() -> None:
    data = DigestRunData.from_digest_run(build_digest_run())

    assert data.model_dump() == {
        "run_id": 12,
        "triggered_by": "manual",
        "started_at": "2026-04-18T08:00:00+09:00",
        "finished_at": "2026-04-18T08:01:42+09:00",
        "fetched_count": 20,
        "selected_count": 5,
        "summarized_count": 4,
        "email_status": "success",
        "error_message": None,
    }
