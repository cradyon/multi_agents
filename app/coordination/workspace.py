from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.config import get_settings


@dataclass(frozen=True)
class WorkerSpec:
    worker_id: str
    label: str
    role: str


WORKERS: tuple[WorkerSpec, ...] = (
    WorkerSpec("agent-a-planner", "Agent A", "planner"),
    WorkerSpec("agent-b-researcher", "Agent B", "researcher"),
    WorkerSpec("agent-c-executor", "Agent C", "executor"),
    WorkerSpec("agent-d-synthesizer", "Agent D", "synthesizer"),
)


class CoordinationWorkspace:
    def __init__(self, base_dir: Path | None = None) -> None:
        settings = get_settings()
        self.base_dir = base_dir or settings.coordination_dir

    def initialize_thread(self, thread_id: str, task: str) -> Path:
        thread_dir = self._thread_dir(thread_id)
        agents_dir = thread_dir / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)

        self._write_json(
            thread_dir / "thread.json",
            {
                "thread_id": thread_id,
                "task": task,
                "workers": [worker.worker_id for worker in WORKERS],
                "status": "running",
            },
        )
        self._write_markdown(
            thread_dir / "README.md",
            [
                f"# Thread {thread_id}",
                "",
                f"- Task: {task}",
                "- Status: running",
                "",
                "## Workers",
                "",
            ]
            + [f"- {worker.label} (`{worker.worker_id}`): {worker.role}" for worker in WORKERS],
        )

        for worker in WORKERS:
            self._initialize_worker(thread_dir, task, worker)

        return thread_dir

    def update_worker(
        self,
        thread_id: str,
        worker_role: str,
        *,
        status: str,
        context: dict[str, Any],
        output: str,
    ) -> None:
        worker = self._find_worker(worker_role)
        worker_dir = self._thread_dir(thread_id) / "agents" / worker.worker_id
        worker_dir.mkdir(parents=True, exist_ok=True)

        self._write_json(
            worker_dir / "context.json",
            {
                "worker_id": worker.worker_id,
                "label": worker.label,
                "role": worker.role,
                "status": status,
                "context": context,
            },
        )
        self._write_markdown(
            worker_dir / "status.md",
            [
                f"# {worker.label}",
                "",
                f"- Worker ID: `{worker.worker_id}`",
                f"- Role: `{worker.role}`",
                f"- Status: `{status}`",
            ],
        )
        self._write_markdown(worker_dir / "output.md", [output.strip() or "_No output yet._"])

    def append_log(self, thread_id: str, worker_role: str, message: str) -> None:
        worker = self._find_worker(worker_role)
        worker_dir = self._thread_dir(thread_id) / "agents" / worker.worker_id
        worker_dir.mkdir(parents=True, exist_ok=True)

        log_path = worker_dir / "log.md"
        existing = log_path.read_text(encoding="utf-8") if log_path.exists() else "# Log\n"
        if not existing.endswith("\n"):
            existing += "\n"
        existing += f"- {message}\n"
        log_path.write_text(existing, encoding="utf-8")

    def finalize_thread(self, thread_id: str, final_response: str) -> None:
        thread_dir = self._thread_dir(thread_id)
        thread_file = thread_dir / "thread.json"
        payload = self._read_json(thread_file)
        payload["status"] = "completed"
        payload["final_response_preview"] = final_response[:280]
        self._write_json(thread_file, payload)
        self._write_markdown(thread_dir / "final.md", [final_response.strip() or "_No final response._"])

    def _initialize_worker(self, thread_dir: Path, task: str, worker: WorkerSpec) -> None:
        worker_dir = thread_dir / "agents" / worker.worker_id
        worker_dir.mkdir(parents=True, exist_ok=True)
        self._write_markdown(
            worker_dir / "status.md",
            [
                f"# {worker.label}",
                "",
                f"- Worker ID: `{worker.worker_id}`",
                f"- Role: `{worker.role}`",
                "- Status: `pending`",
            ],
        )
        self._write_json(
            worker_dir / "context.json",
            {
                "worker_id": worker.worker_id,
                "label": worker.label,
                "role": worker.role,
                "status": "pending",
                "context": {"task": task},
            },
        )
        self._write_markdown(worker_dir / "output.md", ["_Pending work._"])
        self._write_markdown(worker_dir / "log.md", ["# Log", "- Worker created and waiting for execution."])

    def _thread_dir(self, thread_id: str) -> Path:
        return self.base_dir / "threads" / thread_id

    def _find_worker(self, worker_role: str) -> WorkerSpec:
        for worker in WORKERS:
            if worker.role == worker_role:
                return worker
        raise ValueError(f"Unknown worker role: {worker_role}")

    def _write_json(self, path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def _read_json(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    def _write_markdown(self, path: Path, lines: list[str]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
