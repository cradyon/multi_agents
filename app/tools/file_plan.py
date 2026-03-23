from __future__ import annotations

from pathlib import PurePosixPath

from app.tools.types import ToolResult


def plan_file_structure(
    goal: str,
    *,
    project_root: str = "app",
    include_tests: bool = True,
    include_docs: bool = True,
) -> ToolResult:
    """Return a file plan for a feature without creating anything on disk."""
    root = PurePosixPath(project_root)

    layout = [
        str(root / "graph.py"),
        str(root / "state.py"),
        str(root / "config.py"),
        str(root / "llm.py"),
        str(root / "main.py"),
        str(root / "agents" / "planner.py"),
        str(root / "agents" / "researcher.py"),
        str(root / "agents" / "executor.py"),
        str(root / "agents" / "synthesizer.py"),
        str(root / "tools" / "research.py"),
        str(root / "tools" / "file_plan.py"),
        str(root / "tools" / "command_plan.py"),
    ]

    if include_tests:
        layout.append("tests/test_graph.py")
    if include_docs:
        layout.append("README.md")

    return ToolResult(
        tool_name="file_plan",
        input={
            "goal": goal,
            "project_root": project_root,
            "include_tests": include_tests,
            "include_docs": include_docs,
        },
        summary="Generated a safe file-structure plan without touching the filesystem.",
        safe=True,
        recommended_actions=[
            "Create only the files that are still missing.",
            "Keep agent responsibilities separated.",
            "Add tests after the first runnable slice is stable.",
        ],
        metadata={
            "proposed_files": layout,
            "suggested_module_order": [
                "state",
                "llm",
                "agents",
                "tools",
                "graph",
                "main",
            ],
        },
    )
