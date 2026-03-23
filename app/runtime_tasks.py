from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from threading import Lock, Thread

from app.api.schemas import RunTaskRequest, RunTaskResponse, TaskStatusResponse
from app.demo_reader import read_thread_summary
from app.service import MultiAgentService


@dataclass
class TaskRecord:
    task_id: str
    task: str
    status: str
    detail: str
    current_step: str
    progress: int
    thread_path: str
    result: str | None = None
    error: str | None = None
    started_at: str | None = None
    finished_at: str | None = None


class BackgroundTaskManager:
    def __init__(self, service: MultiAgentService) -> None:
        self.service = service
        self._records: dict[str, TaskRecord] = {}
        self._lock = Lock()

    def start_task(self, payload: RunTaskRequest) -> RunTaskResponse:
        task_id = payload.thread_id or self.service.create_thread_id()
        thread_path = f"APP_DEMO/threads/{task_id}"

        with self._lock:
            existing = self._records.get(task_id)
            if existing and existing.status in {"accepted", "running"}:
                return RunTaskResponse(
                    task_id=task_id,
                    thread_id=task_id,
                    status=existing.status,
                    task=existing.task,
                    result=existing.result,
                    final_response=existing.result,
                    detail="A task with this thread id is already running.",
                    thread_path=existing.thread_path,
                )

            self._records[task_id] = TaskRecord(
                task_id=task_id,
                task=payload.task,
                status="accepted",
                detail="Task accepted. Waiting to start.",
                current_step="queued",
                progress=2,
                thread_path=thread_path,
                started_at=datetime.now(UTC).isoformat(),
            )

        worker = Thread(target=self._run_task, args=(task_id, payload.task), daemon=True)
        worker.start()

        return RunTaskResponse(
            task_id=task_id,
            thread_id=task_id,
            status="accepted",
            task=payload.task,
            detail="Task accepted. The worker has started.",
            thread_path=thread_path,
        )

    def get_status(self, task_id: str) -> TaskStatusResponse:
        with self._lock:
            record = self._records.get(task_id)
            if record is not None:
                return TaskStatusResponse(
                    task_id=record.task_id,
                    thread_id=record.task_id,
                    status=record.status,
                    task=record.task,
                    detail=record.error or record.detail,
                    current_step=record.current_step,
                    progress=record.progress,
                    result=record.result,
                    thread_path=record.thread_path,
                )

        summary = read_thread_summary(task_id)
        if summary is None:
            raise FileNotFoundError(task_id)

        return TaskStatusResponse(
            task_id=task_id,
            thread_id=task_id,
            status=summary.get("status", "unknown"),
            task=summary.get("task"),
            detail=summary.get("detail"),
            current_step=summary.get("current_step"),
            progress=summary.get("progress", 0),
            result=summary.get("final_response_preview"),
            thread_path=summary.get("path"),
        )

    def _run_task(self, task_id: str, task: str) -> None:
        def report(status: str, current_step: str, detail: str, progress: int) -> None:
            with self._lock:
                record = self._records[task_id]
                record.status = status
                record.current_step = current_step
                record.detail = detail
                record.progress = progress

        report("running", "planner", "Planner is preparing the workflow.", 8)

        try:
            result = self.service.run_task(task=task, thread_id=task_id, progress_callback=report)
        except Exception as exc:
            with self._lock:
                record = self._records[task_id]
                record.status = "failed"
                record.current_step = "failed"
                record.progress = 100
                record.error = str(exc)
                record.detail = "The workflow failed before completion."
                record.finished_at = datetime.now(UTC).isoformat()
            return

        with self._lock:
            record = self._records[task_id]
            record.status = "completed"
            record.current_step = "completed"
            record.progress = 100
            record.result = result.final_response
            record.detail = f"Workflow completed in mode={result.mode}."
            record.finished_at = datetime.now(UTC).isoformat()
