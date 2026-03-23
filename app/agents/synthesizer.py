from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.agents.common import coerce_text, infer_task_profile
from app.llm import create_chat_model
from app.state import AgentState


def _fallback_final_response(task: str) -> str:
    return infer_task_profile(task).final_fallback


def synthesizer_node(state: AgentState) -> AgentState:
    task = state["task"]
    plan = state.get("plan", "")
    research_notes = state.get("research_notes", "")
    execution_notes = state.get("execution_notes", "")
    file_plan = state.get("file_plan", {})
    command_plan = state.get("command_plan", {})
    profile = infer_task_profile(task)
    model = create_chat_model(role="synthesizer")
    headings = ", ".join(profile.final_headings)

    prompt = [
        SystemMessage(
            content=(
                "You are the lead synthesizer. Merge the planner, researcher, and executor outputs into one final answer. "
                "Be concrete, structured, practical, and concise. "
                f"Use these headings: {headings}. "
                "If upstream outputs are incomplete, still produce the best possible answer from the available material."
            )
        ),
        HumanMessage(
            content=(
                f"Original task:\n{task}\n\n"
                f"Plan:\n{plan}\n\n"
                f"File plan:\n{file_plan}\n\n"
                f"Command plan:\n{command_plan}\n\n"
                f"Research:\n{research_notes}\n\n"
                f"Execution:\n{execution_notes}"
            )
        ),
    ]
    fallback = _fallback_final_response(task)
    try:
        response = model.invoke(prompt)
        final_response = coerce_text(response.content, fallback)
    except Exception:
        final_response = fallback

    return {
        "final_response": final_response,
        "messages": [AIMessage(content=final_response, name="synthesizer")],
    }
