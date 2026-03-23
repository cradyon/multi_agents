from __future__ import annotations

from collections.abc import Callable

from fastapi import APIRouter, Depends, HTTPException

from app.api.schemas import (
    HealthResponse,
    RunTaskRequest,
    RunTaskResponse,
    ThreadDetailResponse,
    ThreadSummaryResponse,
)
from app.demo_reader import list_threads, read_thread

TaskRunner = Callable[[RunTaskRequest], RunTaskResponse]


def get_task_runner() -> TaskRunner:
    """Default task runner placeholder.

    The main app can replace this dependency later with a LangGraph-backed runner.
    """

    def _runner(payload: RunTaskRequest) -> RunTaskResponse:
        return RunTaskResponse(
            task_id="placeholder-task-id",
            status="accepted",
            task=payload.task,
            result=f"Task received: {payload.task}",
            detail="Executed through the configured task runner placeholder.",
            thread_path=None,
        )

    return _runner


router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse()


@router.post("/tasks/run", response_model=RunTaskResponse)
def run_task(
    payload: RunTaskRequest,
    task_runner: TaskRunner = Depends(get_task_runner),
) -> RunTaskResponse:
    return task_runner(payload)


@router.get("/threads", response_model=list[ThreadSummaryResponse])
def get_threads() -> list[ThreadSummaryResponse]:
    return [ThreadSummaryResponse(**item) for item in list_threads()]


@router.get("/threads/{thread_id}", response_model=ThreadDetailResponse)
def get_thread(thread_id: str) -> ThreadDetailResponse:
    try:
        payload = read_thread(thread_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Thread not found: {thread_id}") from exc
    return ThreadDetailResponse(**payload)
