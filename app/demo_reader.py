from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.config import get_settings


def _threads_root() -> Path:
    return get_settings().coordination_dir / "threads"


def list_threads(limit: int = 10) -> list[dict[str, Any]]:
    root = _threads_root()
    if not root.exists():
        return []

    threads: list[dict[str, Any]] = []
    for thread_dir in sorted(root.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        if not thread_dir.is_dir():
            continue
        thread_file = thread_dir / "thread.json"
        if not thread_file.exists():
            continue
        try:
            payload = json.loads(thread_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        payload["path"] = str(thread_dir)
        threads.append(payload)
        if len(threads) >= limit:
            break
    return threads


def read_thread(thread_id: str) -> dict[str, Any]:
    thread_dir = _threads_root() / thread_id
    thread_file = thread_dir / "thread.json"
    if not thread_file.exists():
        raise FileNotFoundError(thread_id)

    payload = json.loads(thread_file.read_text(encoding="utf-8"))
    payload["path"] = str(thread_dir)
    payload["final"] = _read_text(thread_dir / "final.md")
    payload["agents"] = []

    agents_dir = thread_dir / "agents"
    if agents_dir.exists():
        for agent_dir in sorted(agents_dir.iterdir()):
            if not agent_dir.is_dir():
                continue
            payload["agents"].append(
                {
                    "agent_id": agent_dir.name,
                    "status": _read_text(agent_dir / "status.md"),
                    "context": _read_json(agent_dir / "context.json"),
                    "log": _read_text(agent_dir / "log.md"),
                    "output": _read_text(agent_dir / "output.md"),
                    "path": str(agent_dir),
                }
            )
    return payload


def read_thread_summary(thread_id: str) -> dict[str, Any] | None:
    thread_dir = _threads_root() / thread_id
    thread_file = thread_dir / "thread.json"
    if not thread_file.exists():
        return None

    payload = json.loads(thread_file.read_text(encoding="utf-8"))
    payload["path"] = str(thread_dir)
    payload["progress"] = _compute_progress(payload)
    return payload


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _compute_progress(payload: dict[str, Any]) -> int:
    status = payload.get("status", "unknown")
    if status in {"completed", "failed"}:
        return 100

    current_step = payload.get("current_step", "")
    step_progress = {
        "queued": 2,
        "planner": 15,
        "researcher": 45,
        "executor": 70,
        "synthesizer": 90,
        "completed": 100,
        "failed": 100,
    }
    return step_progress.get(current_step, 0)
