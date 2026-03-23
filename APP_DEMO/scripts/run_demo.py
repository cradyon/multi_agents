#!/usr/bin/env python3

from __future__ import annotations

import json
import sys
import time
from pathlib import Path


THREAD_ID = "live-demo-thread"
TASK = "Show four visible agent threads working on the multi-agent starter inside the main project workspace."

WORKERS = [
    {
        "worker_id": "agent-a-planner",
        "label": "Agent A",
        "role": "planner",
        "focus": "runtime plan",
        "output": """# Agent A Runtime Plan

1. Keep visible worker artifacts in `APP_DEMO/threads/<thread_id>/agents/...`.
2. Upgrade the graph to let research and execution branches run in parallel.
3. Use the synthesizer as the join point for branch outputs.
""",
    },
    {
        "worker_id": "agent-b-researcher",
        "label": "Agent B",
        "role": "researcher",
        "focus": "DeerFlow gap analysis",
        "output": """# Agent B Gap Analysis

- Current repo has starter graph, API, persistence, and coordination workspace.
- Missing pieces versus DeerFlow are sandbox, real tool execution, subagent runtime, and frontend orchestration.
""",
    },
    {
        "worker_id": "agent-c-executor",
        "label": "Agent C",
        "role": "executor",
        "focus": "implementation queue",
        "output": """# Agent C Implementation Queue

1. Add parallel routing in `app/graph.py`.
2. Add live worker-state updates in `app/service.py`.
3. Expose thread status from the API.
""",
    },
    {
        "worker_id": "agent-d-synthesizer",
        "label": "Agent D",
        "role": "synthesizer",
        "focus": "integration summary",
        "output": """# Agent D Integration Summary

The project already shows visible multi-worker coordination in the main repo.
The next milestone is true runtime concurrency rather than post-run artifact writing.
""",
    },
]


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_md(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def set_worker_state(base: Path, worker: dict, status: str, output: str) -> None:
    worker_dir = base / "agents" / worker["worker_id"]
    write_md(
        worker_dir / "status.md",
        f"""# {worker["label"]}

- Worker ID: `{worker["worker_id"]}`
- Role: `{worker["role"]}`
- Status: `{status}`
""",
    )
    write_json(
        worker_dir / "context.json",
        {
            "worker_id": worker["worker_id"],
            "label": worker["label"],
            "role": worker["role"],
            "status": status,
            "context": {
                "focus": worker["focus"],
                "thread_id": THREAD_ID,
                "task": TASK,
            },
        },
    )
    write_md(worker_dir / "output.md", output)


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    thread_dir = root / "APP_DEMO" / "threads" / THREAD_ID
    agents_dir = thread_dir / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)

    write_json(
        thread_dir / "thread.json",
        {
            "thread_id": THREAD_ID,
            "task": TASK,
            "status": "running",
            "workers": [worker["worker_id"] for worker in WORKERS],
        },
    )
    write_md(
        thread_dir / "README.md",
        "# Live Demo Thread\n\n"
        f"- Task: {TASK}\n"
        "- Status: running\n\n"
        "## Workers\n\n"
        + "\n".join(f"- {worker['label']} (`{worker['worker_id']}`): {worker['focus']}" for worker in WORKERS),
    )

    for worker in WORKERS:
        set_worker_state(thread_dir, worker, "running", "_Working..._")
        print(f"{worker['label']} started")
        sys.stdout.flush()
        time.sleep(0.3)

    for worker in WORKERS:
        set_worker_state(thread_dir, worker, "completed", worker["output"])
        print(f"{worker['label']} completed")
        sys.stdout.flush()
        time.sleep(0.3)

    write_json(
        thread_dir / "thread.json",
        {
            "thread_id": THREAD_ID,
            "task": TASK,
            "status": "completed",
            "workers": [worker["worker_id"] for worker in WORKERS],
            "final_response_preview": "Four visible agents completed a demo run inside the main project workspace.",
        },
    )
    write_md(
        thread_dir / "final.md",
        """# Live Demo Final

This demo wrote a visible four-agent run into the main project workspace.

- Agent A planned the runtime evolution.
- Agent B summarized the main DeerFlow gaps.
- Agent C produced a concrete implementation queue.
- Agent D synthesized the current state and next step.
""",
    )

    print(f"Demo finished: {thread_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
