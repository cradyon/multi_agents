from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.agents.common import coerce_text, infer_task_profile
from app.llm import create_chat_model
from app.state import AgentState


def researcher_node(state: AgentState) -> AgentState:
    task = state["task"]
    plan = state.get("plan", "")
    research_plan = state.get("research_plan", {})
    profile = infer_task_profile(task)
    model = create_chat_model(role="worker")
    headings = ", ".join(profile.research_headings)

    prompt = [
        SystemMessage(
            content=(
                "You are the researcher agent in a multi-agent system. "
                f"Produce concise research notes with these headings: {headings}. "
                "If you lack external tools, be explicit about which parts are inferred, but still provide a useful answer."
            )
        ),
        HumanMessage(
            content=(
                f"Task:\n{task}\n\n"
                f"Planner notes:\n{plan}\n\n"
                f"Research planning artifact:\n{research_plan}"
            )
        ),
    ]
    fallback = profile.research_fallback
    try:
        response = model.invoke(prompt)
        notes = coerce_text(response.content, fallback)
    except Exception:
        notes = fallback

    return {
        "research_notes": notes,
        "messages": [AIMessage(content=notes, name="researcher")],
    }
