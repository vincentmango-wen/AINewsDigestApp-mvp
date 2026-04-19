"""Digest run schemas."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Literal

TriggeredBy = Literal["manual", "scheduler"]
EmailStatus = Literal["success", "skipped", "failed"]


@dataclass(frozen=True, slots=True)
class DigestRun:
    run_id: int
    triggered_by: TriggeredBy
    started_at: str
    finished_at: str | None
    fetched_count: int
    selected_count: int
    summarized_count: int
    email_status: EmailStatus
    error_message: str | None
    created_at: str
    updated_at: str

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "DigestRun":
        return cls(
            run_id=row["id"],
            triggered_by=row["triggered_by"],
            started_at=row["started_at"],
            finished_at=row["finished_at"],
            fetched_count=row["fetched_count"],
            selected_count=row["selected_count"],
            summarized_count=row["summarized_count"],
            email_status=row["email_status"],
            error_message=row["error_message"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
