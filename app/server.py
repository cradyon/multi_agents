from __future__ import annotations

from collections.abc import Callable
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api import router
from app.api.router import get_auth_service, get_task_runner, get_task_status_reader
from app.api.schemas import RunTaskRequest, RunTaskResponse, TaskStatusResponse
from app.auth import AuthService
from app.config import get_settings
from app.persistence import SQLiteUserStore
from app.runtime_tasks import BackgroundTaskManager
from app.service import MultiAgentService


def create_app(
    task_runner: Callable[[RunTaskRequest], RunTaskResponse] | None = None,
    task_status_reader: Callable[[str], TaskStatusResponse] | None = None,
) -> FastAPI:
    app = FastAPI(title="Multi-Agent API", version="0.1.0")
    settings = get_settings()
    allowed_origins = _parse_cors_allow_origins(settings.cors_allow_origins)
    allow_any_origin = "*" in allowed_origins
    frontend_dir = _frontend_dir()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins or ["*"],
        allow_credentials=not allow_any_origin,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    if task_runner is not None:
        app.dependency_overrides[get_task_runner] = lambda: task_runner
    if task_status_reader is not None:
        app.dependency_overrides[get_task_status_reader] = lambda: task_status_reader
    app.dependency_overrides[get_auth_service] = _get_auth_service

    app.include_router(router, prefix="/api")
    app.mount("/assets", StaticFiles(directory=frontend_dir), name="assets")

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(frontend_dir / "index.html")

    return app


def _frontend_dir() -> Path:
    return Path(__file__).resolve().parent / "frontend"


def _parse_cors_allow_origins(raw_value: str) -> list[str]:
    return [origin.strip() for origin in raw_value.split(",") if origin.strip()]


@lru_cache(maxsize=1)
def _get_service() -> MultiAgentService:
    return MultiAgentService()


@lru_cache(maxsize=1)
def _get_task_manager() -> BackgroundTaskManager:
    return BackgroundTaskManager(_get_service())


@lru_cache(maxsize=1)
def _get_auth_service() -> AuthService:
    settings = get_settings()
    return AuthService(
        user_store=SQLiteUserStore(settings.sqlite_path),
        secret_key=settings.auth_secret_key,
    )


def _run_with_service(payload: RunTaskRequest) -> RunTaskResponse:
    return _get_task_manager().start_task(payload)


def _read_task_status(task_id: str) -> TaskStatusResponse:
    try:
        return _get_task_manager().get_status(task_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}") from exc


app = create_app(task_runner=_run_with_service, task_status_reader=_read_task_status)
