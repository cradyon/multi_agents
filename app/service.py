from __future__ import annotations

from collections.abc import Callable
from uuid import uuid4

from app.agents.executor import executor_node
from app.agents.planner import planner_node
from app.agents.researcher import researcher_node
from app.agents.synthesizer import synthesizer_node
from app.config import get_settings
from app.coordination import CoordinationWorkspace
from app.persistence import CheckpointRecord, RunSummary, SQLiteCheckpointStore, SQLiteMemoryStore
from app.schemas import RunTaskResponse
from app.state import AgentState


def _ensure_data_dir() -> None:
    settings = get_settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)


class MultiAgentService:
    def __init__(self) -> None:
        _ensure_data_dir()
        settings = get_settings()
        self.checkpoints = SQLiteCheckpointStore(settings.sqlite_path)
        self.memory = SQLiteMemoryStore(settings.sqlite_path)
        self.workspace = CoordinationWorkspace()

    def create_thread_id(self) -> str:
        return uuid4().hex

    def run_task(
        self,
        task: str,
        thread_id: str | None = None,
        progress_callback: Callable[[str, str, str, int], None] | None = None,
    ) -> RunTaskResponse:
        resolved_thread_id = thread_id or self.create_thread_id()
        state: AgentState = {"task": task, "thread_id": resolved_thread_id, "messages": []}

        self.workspace.initialize_thread(resolved_thread_id, task)
        self.workspace.update_worker(
            resolved_thread_id,
            "planner",
            status="running",
            context={"task": task},
            output="Planner is building the workflow plan.",
        )
        self.workspace.append_log(resolved_thread_id, "planner", "Planner started.")
        self._report_progress(progress_callback, resolved_thread_id, "running", "planner", "Planner started.", 8)

        try:
            state.update(planner_node(state))
        except Exception as exc:
            self.workspace.append_log(resolved_thread_id, "planner", f"Planner failed: {exc}")
            self.workspace.update_worker(
                resolved_thread_id,
                "planner",
                status="failed",
                context={"task": task, "error": str(exc)},
                output=f"Planner failed before the workflow completed.\n\nError: {exc}",
            )
            self.workspace.fail_thread(resolved_thread_id, f"Planner failed: {exc}")
            raise

        self.workspace.append_log(
            resolved_thread_id,
            "planner",
            f"Planner finished with mode={state.get('mode', 'unknown')}.",
        )
        self.checkpoints.save(
            CheckpointRecord(
                thread_id=resolved_thread_id,
                step_name="planner",
                payload={"mode": state.get("mode", ""), "plan": state.get("plan", "")},
            )
        )
        self.workspace.update_worker(
            resolved_thread_id,
            "planner",
            status="completed",
            context={
                "task": task,
                "mode": state.get("mode", ""),
                "file_plan": state.get("file_plan", {}),
                "command_plan": state.get("command_plan", {}),
                "research_plan": state.get("research_plan", {}),
            },
            output=state.get("plan", ""),
        )
        self._report_progress(
            progress_callback,
            resolved_thread_id,
            "running",
            "planner",
            f"Planner completed with mode={state.get('mode', 'unknown')}.",
            25,
        )

        if state.get("mode") != "execute_only":
            self.workspace.update_worker(
                resolved_thread_id,
                "researcher",
                status="running",
                context={
                    "task": task,
                    "plan": state.get("plan", ""),
                    "research_plan": state.get("research_plan", {}),
                },
                output="Research is in progress.",
            )
            self.workspace.append_log(resolved_thread_id, "researcher", "Researcher started.")
            self._report_progress(
                progress_callback,
                resolved_thread_id,
                "running",
                "researcher",
                "Researcher is gathering notes.",
                45,
            )
            try:
                state.update(researcher_node(state))
            except Exception as exc:
                self.workspace.append_log(resolved_thread_id, "researcher", f"Researcher failed: {exc}")
                self.workspace.update_worker(
                    resolved_thread_id,
                    "researcher",
                    status="failed",
                    context={"task": task, "error": str(exc)},
                    output=f"Researcher failed before the workflow completed.\n\nError: {exc}",
                )
                self.workspace.fail_thread(resolved_thread_id, f"Researcher failed: {exc}")
                raise

        if state.get("research_notes"):
            self.workspace.append_log(resolved_thread_id, "researcher", "Researcher produced research notes.")
            self.checkpoints.save(
                CheckpointRecord(
                    thread_id=resolved_thread_id,
                    step_name="researcher",
                    payload={"research_notes": state["research_notes"]},
                )
            )
            self.workspace.update_worker(
                resolved_thread_id,
                "researcher",
                status="completed",
                context={
                    "task": task,
                    "plan": state.get("plan", ""),
                    "research_plan": state.get("research_plan", {}),
                },
                output=state["research_notes"],
            )
            self._report_progress(
                progress_callback,
                resolved_thread_id,
                "running",
                "researcher",
                "Research notes are ready.",
                55,
            )
        else:
            self.workspace.append_log(resolved_thread_id, "researcher", "Research step skipped.")
            self.workspace.update_worker(
                resolved_thread_id,
                "researcher",
                status="skipped",
                context={"task": task, "mode": state.get("mode", "")},
                output="Research step was skipped for this run.",
            )

        if state.get("mode") != "research_only":
            self.workspace.update_worker(
                resolved_thread_id,
                "executor",
                status="running",
                context={
                    "task": task,
                    "plan": state.get("plan", ""),
                    "file_plan": state.get("file_plan", {}),
                    "command_plan": state.get("command_plan", {}),
                },
                output="Execution is in progress.",
            )
            self.workspace.append_log(resolved_thread_id, "executor", "Executor started.")
            self._report_progress(
                progress_callback,
                resolved_thread_id,
                "running",
                "executor",
                "Executor is preparing the implementation notes.",
                70,
            )
            try:
                state.update(executor_node(state))
            except Exception as exc:
                self.workspace.append_log(resolved_thread_id, "executor", f"Executor failed: {exc}")
                self.workspace.update_worker(
                    resolved_thread_id,
                    "executor",
                    status="failed",
                    context={"task": task, "error": str(exc)},
                    output=f"Executor failed before the workflow completed.\n\nError: {exc}",
                )
                self.workspace.fail_thread(resolved_thread_id, f"Executor failed: {exc}")
                raise

        if state.get("execution_notes"):
            self.workspace.append_log(resolved_thread_id, "executor", "Executor produced implementation notes.")
            self.checkpoints.save(
                CheckpointRecord(
                    thread_id=resolved_thread_id,
                    step_name="executor",
                    payload={"execution_notes": state["execution_notes"]},
                )
            )
            self.workspace.update_worker(
                resolved_thread_id,
                "executor",
                status="completed",
                context={
                    "task": task,
                    "plan": state.get("plan", ""),
                    "file_plan": state.get("file_plan", {}),
                    "command_plan": state.get("command_plan", {}),
                },
                output=state["execution_notes"],
            )
            self._report_progress(
                progress_callback,
                resolved_thread_id,
                "running",
                "executor",
                "Execution notes are ready.",
                82,
            )
        else:
            self.workspace.append_log(resolved_thread_id, "executor", "Execution step skipped.")
            self.workspace.update_worker(
                resolved_thread_id,
                "executor",
                status="skipped",
                context={"task": task, "mode": state.get("mode", "")},
                output="Execution step was skipped for this run.",
            )

        self.workspace.update_worker(
            resolved_thread_id,
            "synthesizer",
            status="running",
            context={
                "task": task,
                "mode": state.get("mode", ""),
                "plan": state.get("plan", ""),
            },
            output="Synthesizer is building the final answer.",
        )
        self.workspace.append_log(resolved_thread_id, "synthesizer", "Synthesizer started.")
        self._report_progress(
            progress_callback,
            resolved_thread_id,
            "running",
            "synthesizer",
            "Synthesizer is merging the final response.",
            90,
        )
        try:
            state.update(synthesizer_node(state))
        except Exception as exc:
            self.workspace.append_log(resolved_thread_id, "synthesizer", f"Synthesizer failed: {exc}")
            self.workspace.update_worker(
                resolved_thread_id,
                "synthesizer",
                status="failed",
                context={"task": task, "error": str(exc)},
                output=f"Synthesizer failed before the workflow completed.\n\nError: {exc}",
            )
            self.workspace.fail_thread(resolved_thread_id, f"Synthesizer failed: {exc}")
            raise

        self.checkpoints.save(
            CheckpointRecord(
                thread_id=resolved_thread_id,
                step_name="synthesizer",
                payload={"final_response": state.get("final_response", "")},
            )
        )
        self.workspace.append_log(resolved_thread_id, "synthesizer", "Synthesizer merged the final response.")
        self.workspace.update_worker(
            resolved_thread_id,
            "synthesizer",
            status="completed",
            context={
                "task": task,
                "mode": state.get("mode", ""),
                "plan": state.get("plan", ""),
            },
            output=state.get("final_response", ""),
        )

        self.memory.save(
            RunSummary(
                thread_id=resolved_thread_id,
                task=task,
                summary=state.get("final_response", ""),
                metadata={"mode": state.get("mode", "research_then_execute")},
            )
        )
        self.workspace.finalize_thread(resolved_thread_id, state.get("final_response", ""))
        self._report_progress(progress_callback, resolved_thread_id, "completed", "completed", "Workflow completed.", 100)

        return RunTaskResponse(
            thread_id=resolved_thread_id,
            task=task,
            mode=state.get("mode", "research_then_execute"),
            plan=state.get("plan", ""),
            research_notes=state.get("research_notes", ""),
            execution_notes=state.get("execution_notes", ""),
            final_response=state.get("final_response", ""),
        )

    def _report_progress(
        self,
        callback: Callable[[str, str, str, int], None] | None,
        thread_id: str,
        status: str,
        current_step: str,
        detail: str,
        progress: int,
    ) -> None:
        self.workspace.update_thread(thread_id, status=status, detail=detail, current_step=current_step)
        if callback is not None:
            callback(status, current_step, detail, progress)
