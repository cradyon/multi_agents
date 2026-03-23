from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class CheckpointRecord:
    thread_id: str
    step_name: str
    payload: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)
    checkpoint_id: str | None = None
    created_at: datetime = field(default_factory=utc_now)


@dataclass(slots=True)
class RunSummary:
    thread_id: str
    task: str
    summary: str
    status: str = "completed"
    metadata: dict[str, Any] = field(default_factory=dict)
    summary_id: str | None = None
    created_at: datetime = field(default_factory=utc_now)
