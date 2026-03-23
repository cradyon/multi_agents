from typing import Annotated, Literal, TypedDict

from langgraph.graph.message import add_messages


class AgentState(TypedDict, total=False):
    messages: Annotated[list, add_messages]
    thread_id: str
    task: str
    mode: Literal["research_only", "execute_only", "research_then_execute"]
    plan: str
    file_plan: dict
    command_plan: dict
    research_plan: dict
    research_notes: str
    execution_notes: str
    final_response: str
