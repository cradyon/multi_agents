from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(default="ok")
    service: str = Field(default="multi-agent-api")


class RunTaskRequest(BaseModel):
    task: str = Field(..., min_length=1, description="The task to run through the agent graph.")
    thread_id: str | None = Field(default=None, description="Optional thread identifier for later state wiring.")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Optional request metadata.")


class RunTaskResponse(BaseModel):
    task_id: str
    status: str
    task: str
    result: str | None = None
    detail: str | None = None
    thread_path: str | None = None


class ThreadSummaryResponse(BaseModel):
    thread_id: str
    task: str | None = None
    status: str | None = None
    path: str | None = None


class ThreadDetailResponse(BaseModel):
    thread_id: str
    task: str | None = None
    status: str | None = None
    path: str | None = None
    final: str | None = None
    agents: list[dict[str, Any]] = Field(default_factory=list)
