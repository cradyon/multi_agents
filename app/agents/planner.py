import json

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.agents.common import extract_json_object, infer_task_profile
from app.llm import create_chat_model
from app.state import AgentState
from app.tools import plan_command, plan_file_structure, plan_web_research


def planner_node(state: AgentState) -> AgentState:
    task = state["task"]
    profile = infer_task_profile(task)
    file_plan = plan_file_structure(task)
    command_plan = plan_command(task, cwd=".", allow_network=False, allow_write=False)
    research_plan = plan_web_research(task, context="langgraph multi-agent architecture")

    prompt = [
        SystemMessage(
            content=(
                "You are the planner in a multi-agent system. "
                "Decide whether the task needs research, execution, or both. "
                "Use the provided planning artifacts when they help you shape the workflow. "
                "Return ONLY valid JSON with keys: mode, plan, rationale. "
                "Valid mode values are research_only, execute_only, research_then_execute. "
                f"This task appears to fit the profile '{profile.name}'."
            )
        ),
        HumanMessage(
            content=(
                f"Task:\n{task}\n\n"
                f"Preferred fallback mode: {profile.planner_mode}\n"
                f"Preferred fallback plan: {profile.planner_plan}\n"
                f"Preferred fallback rationale: {profile.planner_rationale}\n\n"
                f"File plan:\n{json.dumps(file_plan, ensure_ascii=False, indent=2)}\n\n"
                f"Command plan:\n{json.dumps(command_plan, ensure_ascii=False, indent=2)}\n\n"
                f"Research plan:\n{json.dumps(research_plan, ensure_ascii=False, indent=2)}"
            )
        ),
    ]
    try:
        model = create_chat_model(role="planner")
        response = model.invoke(prompt)
        parsed = extract_json_object(response.content if isinstance(response.content, str) else str(response.content))
    except Exception:
        parsed = {}

    mode = parsed.get("mode", profile.planner_mode)
    if mode not in {"research_only", "execute_only", "research_then_execute"}:
        mode = profile.planner_mode

    default_plan = profile.planner_plan
    plan = str(parsed.get("plan") or default_plan).strip() or default_plan
    rationale = str(parsed.get("rationale") or profile.planner_rationale).strip()
    planner_summary = f"Planner mode: {mode}\nPlan: {plan}\nRationale: {rationale}"

    return {
        "mode": mode,
        "plan": plan,
        "file_plan": file_plan,
        "command_plan": command_plan,
        "research_plan": research_plan,
        "messages": [AIMessage(content=planner_summary, name="planner")],
    }
