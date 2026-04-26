"""Common API schemas."""

from __future__ import annotations

from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict

from app.schemas.digest_run import DigestRun, EmailStatus, TriggeredBy

ResponseDataT = TypeVar("ResponseDataT", bound=BaseModel)


class EmptyData(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ApiSuccessResponse(BaseModel, Generic[ResponseDataT]):
    model_config = ConfigDict(extra="forbid")

    success: Literal[True] = True
    data: ResponseDataT
    message: str


class ApiErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: Literal[False] = False
    error_code: str
    message: str


class HealthCheckData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    app_name: str
    timestamp: str


class DigestRunData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: int
    triggered_by: TriggeredBy
    started_at: str
    finished_at: str | None
    fetched_count: int
    selected_count: int
    summarized_count: int
    email_status: EmailStatus
    error_message: str | None

    @classmethod
    def from_digest_run(cls, digest_run: DigestRun) -> "DigestRunData":
        return cls(
            run_id=digest_run.run_id,
            triggered_by=digest_run.triggered_by,
            started_at=digest_run.started_at,
            finished_at=digest_run.finished_at,
            fetched_count=digest_run.fetched_count,
            selected_count=digest_run.selected_count,
            summarized_count=digest_run.summarized_count,
            email_status=digest_run.email_status,
            error_message=digest_run.error_message,
        )
