from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.agents.common import coerce_text, infer_task_profile
from app.llm import create_chat_model
from app.state import AgentState


def executor_node(state: AgentState) -> AgentState:
    task = state["task"]
    plan = state.get("plan", "")
    research_notes = state.get("research_notes", "")
    file_plan = state.get("file_plan", {})
    command_plan = state.get("command_plan", {})
    profile = infer_task_profile(task)
    model = create_chat_model(role="worker")
    headings = ", ".join(profile.execution_headings)

    prompt = [
        SystemMessage(
            content=(
                "You are the executor agent in a multi-agent system. "
                "Turn the task, plan, and research into an actionable answer. "
                f"Use these headings: {headings}."
            )
        ),
        HumanMessage(
            content=(
                f"Task:\n{task}\n\n"
                f"Planner notes:\n{plan}\n\n"
                f"Research notes:\n{research_notes}\n\n"
                f"File plan:\n{file_plan}\n\n"
                f"Command plan:\n{command_plan}"
            )
        ),
    ]
    fallback = profile.execution_fallback
    try:
        response = model.invoke(prompt)
        notes = coerce_text(response.content, fallback)
    except Exception:
        notes = fallback

    return {
        "execution_notes": notes,
        "messages": [AIMessage(content=notes, name="executor")],
    }
