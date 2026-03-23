from uuid import uuid4

from app.config import get_settings
from app.coordination import CoordinationWorkspace
from app.graph import build_graph
from app.persistence import CheckpointRecord, RunSummary, SQLiteCheckpointStore, SQLiteMemoryStore
from app.schemas import RunTaskResponse


def _ensure_data_dir() -> None:
    settings = get_settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)


class MultiAgentService:
    def __init__(self) -> None:
        _ensure_data_dir()
        self.graph = build_graph()
        settings = get_settings()
        self.checkpoints = SQLiteCheckpointStore(settings.sqlite_path)
        self.memory = SQLiteMemoryStore(settings.sqlite_path)
        self.workspace = CoordinationWorkspace()

    def run_task(self, task: str, thread_id: str | None = None) -> RunTaskResponse:
        resolved_thread_id = thread_id or uuid4().hex
        self.workspace.initialize_thread(resolved_thread_id, task)
        self.workspace.append_log(resolved_thread_id, "planner", "Planner started.")
        try:
            result = self.graph.invoke({"task": task, "thread_id": resolved_thread_id, "messages": []})
        except Exception as exc:
            self.workspace.append_log(resolved_thread_id, "planner", f"Planner failed: {exc}")
            self.workspace.update_worker(
                resolved_thread_id,
                "planner",
                status="failed",
                context={"task": task, "error": str(exc)},
                output=f"Planner failed before the workflow completed.\n\nError: {exc}",
            )
            raise
        self.workspace.append_log(
            resolved_thread_id,
            "planner",
            f"Planner finished with mode={result.get('mode', 'unknown')}.",
        )

        planner_payload = {"mode": result.get("mode", ""), "plan": result.get("plan", "")}
        self.checkpoints.save(
            CheckpointRecord(
                thread_id=resolved_thread_id,
                step_name="planner",
                payload=planner_payload,
            )
        )
        self.workspace.update_worker(
            resolved_thread_id,
            "planner",
            status="completed",
            context={
                "task": task,
                "mode": result.get("mode", ""),
                "file_plan": result.get("file_plan", {}),
                "command_plan": result.get("command_plan", {}),
                "research_plan": result.get("research_plan", {}),
            },
            output=result.get("plan", ""),
        )

        if result.get("research_notes"):
            self.workspace.append_log(resolved_thread_id, "researcher", "Researcher produced research notes.")
            self.checkpoints.save(
                CheckpointRecord(
                    thread_id=resolved_thread_id,
                    step_name="researcher",
                    payload={"research_notes": result["research_notes"]},
                )
            )
            self.workspace.update_worker(
                resolved_thread_id,
                "researcher",
                status="completed",
                context={
                    "task": task,
                    "plan": result.get("plan", ""),
                    "research_plan": result.get("research_plan", {}),
                },
                output=result["research_notes"],
            )
        else:
            self.workspace.append_log(resolved_thread_id, "researcher", "Research step skipped.")
            self.workspace.update_worker(
                resolved_thread_id,
                "researcher",
                status="skipped",
                context={"task": task, "mode": result.get("mode", "")},
                output="Research step was skipped for this run.",
            )

        if result.get("execution_notes"):
            self.workspace.append_log(resolved_thread_id, "executor", "Executor produced implementation notes.")
            self.checkpoints.save(
                CheckpointRecord(
                    thread_id=resolved_thread_id,
                    step_name="executor",
                    payload={"execution_notes": result["execution_notes"]},
                )
            )
            self.workspace.update_worker(
                resolved_thread_id,
                "executor",
                status="completed",
                context={
                    "task": task,
                    "plan": result.get("plan", ""),
                    "file_plan": result.get("file_plan", {}),
                    "command_plan": result.get("command_plan", {}),
                },
                output=result["execution_notes"],
            )
        else:
            self.workspace.append_log(resolved_thread_id, "executor", "Execution step skipped.")
            self.workspace.update_worker(
                resolved_thread_id,
                "executor",
                status="skipped",
                context={"task": task, "mode": result.get("mode", "")},
                output="Execution step was skipped for this run.",
            )

        self.checkpoints.save(
            CheckpointRecord(
                thread_id=resolved_thread_id,
                step_name="synthesizer",
                payload={"final_response": result.get("final_response", "")},
            )
        )
        self.workspace.append_log(resolved_thread_id, "synthesizer", "Synthesizer merged the final response.")
        self.workspace.update_worker(
            resolved_thread_id,
            "synthesizer",
            status="completed",
            context={
                "task": task,
                "mode": result.get("mode", ""),
                "plan": result.get("plan", ""),
            },
            output=result.get("final_response", ""),
        )

        self.memory.save(
            RunSummary(
                thread_id=resolved_thread_id,
                task=task,
                summary=result.get("final_response", ""),
                metadata={"mode": result.get("mode", "research_then_execute")},
            )
        )
        self.workspace.finalize_thread(resolved_thread_id, result.get("final_response", ""))

        return RunTaskResponse(
            thread_id=resolved_thread_id,
            task=task,
            mode=result.get("mode", "research_then_execute"),
            plan=result.get("plan", ""),
            research_notes=result.get("research_notes", ""),
            execution_notes=result.get("execution_notes", ""),
            final_response=result.get("final_response", ""),
        )
