from typing import TypedDict


class ToolResult(TypedDict, total=False):
    tool_name: str
    input: dict
    summary: str
    safe: bool
    recommended_actions: list[str]
    warnings: list[str]
    metadata: dict
