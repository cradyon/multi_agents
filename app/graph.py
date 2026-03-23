from langgraph.graph import END, START, StateGraph

from app.agents.executor import executor_node
from app.agents.planner import planner_node
from app.agents.researcher import researcher_node
from app.agents.synthesizer import synthesizer_node
from app.state import AgentState
from app.workflow_spec import build_workflow_mermaid


def route_from_planner(state: AgentState) -> str:
    mode = state.get("mode", "research_then_execute")
    if mode == "research_only":
        return "researcher"
    if mode == "execute_only":
        return "executor"
    return "researcher"


def route_after_research(state: AgentState) -> str:
    mode = state.get("mode", "research_then_execute")
    if mode == "research_only":
        return "synthesizer"
    return "executor"


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("planner", planner_node)
    graph.add_node("researcher", researcher_node)
    graph.add_node("executor", executor_node)
    graph.add_node("synthesizer", synthesizer_node)

    graph.add_edge(START, "planner")
    graph.add_conditional_edges(
        "planner",
        route_from_planner,
        {
            "researcher": "researcher",
            "executor": "executor",
        },
    )
    graph.add_conditional_edges(
        "researcher",
        route_after_research,
        {
            "executor": "executor",
            "synthesizer": "synthesizer",
        },
    )
    graph.add_edge("executor", "synthesizer")
    graph.add_edge("synthesizer", END)

    return graph.compile()


__all__ = ["build_graph", "build_workflow_mermaid"]
