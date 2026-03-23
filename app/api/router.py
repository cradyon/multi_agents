from __future__ import annotations

from collections.abc import Callable

from fastapi import APIRouter, Depends, Header, HTTPException

from app.auth import AuthService, AuthUser
from app.api.schemas import (
    AuthLoginRequest,
    AuthLoginResponse,
    AuthRegisterRequest,
    AuthUserResponse,
    HealthResponse,
    RunTaskRequest,
    RunTaskResponse,
    TaskStatusResponse,
    ThreadDetailResponse,
    ThreadSummaryResponse,
)
from app.demo_reader import list_threads, read_thread

TaskRunner = Callable[[RunTaskRequest], RunTaskResponse]
TaskStatusReader = Callable[[str], TaskStatusResponse]
AuthServiceFactory = Callable[[], AuthService]


def get_task_runner() -> TaskRunner:
    """Default task runner placeholder.

    The main app can replace this dependency later with a LangGraph-backed runner.
    """

    def _runner(payload: RunTaskRequest) -> RunTaskResponse:
        return RunTaskResponse(
            task_id="placeholder-task-id",
            thread_id="placeholder-task-id",
            status="accepted",
            task=payload.task,
            result=f"Task received: {payload.task}",
            final_response=f"Task received: {payload.task}",
            detail="Executed through the configured task runner placeholder.",
            thread_path=None,
        )

    return _runner


def get_task_status_reader() -> TaskStatusReader:
    def _reader(task_id: str) -> TaskStatusResponse:
        return TaskStatusResponse(
            task_id=task_id,
            thread_id=task_id,
            status="unknown",
            detail="No task status reader is configured.",
            current_step="unknown",
            progress=0,
            result=None,
            thread_path=None,
        )

    return _reader


def get_auth_service() -> AuthService:
    raise RuntimeError("Auth service dependency is not configured.")


def get_current_user(
    authorization: str | None = Header(default=None),
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthUser:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token.")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        return auth_service.authenticate_token(token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse()


@router.post("/auth/register", response_model=AuthUserResponse)
def register(
    payload: AuthRegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthUserResponse:
    try:
        user = auth_service.register_user(payload.username, payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return AuthUserResponse(username=user.username)


@router.post("/auth/login", response_model=AuthLoginResponse)
def login(
    payload: AuthLoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthLoginResponse:
    try:
        user, token = auth_service.login_user(payload.username, payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    return AuthLoginResponse(token=token, user=AuthUserResponse(username=user.username))


@router.get("/auth/me", response_model=AuthUserResponse)
def me(current_user: AuthUser = Depends(get_current_user)) -> AuthUserResponse:
    return AuthUserResponse(username=current_user.username)


@router.post("/tasks/run", response_model=RunTaskResponse)
def run_task(
    payload: RunTaskRequest,
    task_runner: TaskRunner = Depends(get_task_runner),
    current_user: AuthUser = Depends(get_current_user),
) -> RunTaskResponse:
    return task_runner(payload)


@router.post("/tasks/start", response_model=RunTaskResponse)
def start_task(
    payload: RunTaskRequest,
    task_runner: TaskRunner = Depends(get_task_runner),
    current_user: AuthUser = Depends(get_current_user),
) -> RunTaskResponse:
    return task_runner(payload)


@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
def get_task_status(
    task_id: str,
    task_status_reader: TaskStatusReader = Depends(get_task_status_reader),
    current_user: AuthUser = Depends(get_current_user),
) -> TaskStatusResponse:
    return task_status_reader(task_id)


@router.get("/threads", response_model=list[ThreadSummaryResponse])
def get_threads(current_user: AuthUser = Depends(get_current_user)) -> list[ThreadSummaryResponse]:
    return [ThreadSummaryResponse(**item) for item in list_threads()]


@router.get("/threads/{thread_id}", response_model=ThreadDetailResponse)
def get_thread(thread_id: str, current_user: AuthUser = Depends(get_current_user)) -> ThreadDetailResponse:
    try:
        payload = read_thread(thread_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Thread not found: {thread_id}") from exc
    return ThreadDetailResponse(**payload)
