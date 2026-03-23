from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WorkflowNode:
    node_id: str
    label: str
    kind: str = "step"


@dataclass(frozen=True)
class WorkflowEdge:
    source: str
    target: str
    label: str | None = None


WORKFLOW_NODES: tuple[WorkflowNode, ...] = (
    WorkflowNode("start", "START", kind="terminal"),
    WorkflowNode("planner", "Planner"),
    WorkflowNode("researcher", "Researcher"),
    WorkflowNode("executor", "Executor"),
    WorkflowNode("synthesizer", "Synthesizer"),
    WorkflowNode("end", "END", kind="terminal"),
)

WORKFLOW_EDGES: tuple[WorkflowEdge, ...] = (
    WorkflowEdge("start", "planner"),
    WorkflowEdge("planner", "researcher", "mode = research_only"),
    WorkflowEdge("planner", "executor", "mode = execute_only"),
    WorkflowEdge("planner", "researcher", "mode = research_then_execute"),
    WorkflowEdge("researcher", "synthesizer", "mode = research_only"),
    WorkflowEdge("researcher", "executor", "mode = research_then_execute"),
    WorkflowEdge("executor", "synthesizer"),
    WorkflowEdge("synthesizer", "end"),
)


def build_workflow_mermaid() -> str:
    lines = ["flowchart TD"]

    for node in WORKFLOW_NODES:
        if node.kind == "terminal":
            lines.append(f'    {node.node_id}(["{node.label}"])')
        else:
            lines.append(f'    {node.node_id}["{node.label}"]')

    for edge in WORKFLOW_EDGES:
        if edge.label:
            lines.append(f"    {edge.source} -->|{edge.label}| {edge.target}")
        else:
            lines.append(f"    {edge.source} --> {edge.target}")

    return "\n".join(lines) + "\n"


def build_workflow_markdown() -> str:
    mermaid = build_workflow_mermaid().rstrip()
    return (
        "# Workflow Diagram\n\n"
        "This diagram reflects the current LangGraph workflow in the starter project.\n\n"
        "```mermaid\n"
        f"{mermaid}\n"
        "```\n"
    )
