from __future__ import annotations

from app.tools.types import ToolResult


def plan_command(
    task: str,
    *,
    cwd: str | None = None,
    allow_network: bool = False,
    allow_write: bool = False,
) -> ToolResult:
    """Return a safe command plan, never executing anything."""
    task_text = task.strip()

    recommended_commands: list[str] = []
    if "test" in task_text.lower():
        recommended_commands.append("python -m pytest")
    if "format" in task_text.lower() or "lint" in task_text.lower():
        recommended_commands.append("python -m ruff check .")
    if "run" in task_text.lower() or "start" in task_text.lower():
        recommended_commands.append("python -m app.main \"<task>\"")

    if not recommended_commands:
        recommended_commands.append("echo \"Review the task and choose a safe follow-up command manually.\"")

    safety_notes = [
        "This helper does not execute commands.",
        "Treat the output as a planning artifact only.",
    ]
    if not allow_network:
        safety_notes.append("Avoid commands that depend on network access unless explicitly approved.")
    if not allow_write:
        safety_notes.append("Avoid commands that modify files unless the user asked for edits.")

    return ToolResult(
        tool_name="command_plan",
        input={
            "task": task,
            "cwd": cwd,
            "allow_network": allow_network,
            "allow_write": allow_write,
        },
        summary="Prepared a safe command plan without running any shell process.",
        safe=False,
        recommended_actions=recommended_commands,
        warnings=safety_notes,
        metadata={
            "cwd": cwd,
            "policy": {
                "network": allow_network,
                "write": allow_write,
                "execution": "manual_review_required",
            },
        },
    )
