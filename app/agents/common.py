from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


def extract_json_object(text: str) -> dict[str, Any]:
    if not text:
        return {}

    stripped = text.strip()
    if stripped.startswith("```"):
        parts = stripped.split("```")
        for part in parts:
            candidate = part.strip()
            if candidate.startswith("json"):
                candidate = candidate[4:].strip()
            parsed = _try_parse_json(candidate)
            if parsed:
                return parsed

    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return {}
    return _try_parse_json(stripped[start : end + 1])


def _try_parse_json(text: str) -> dict[str, Any]:
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def coerce_text(content: Any, fallback: str) -> str:
    if isinstance(content, str):
        cleaned = content.strip()
        return cleaned or fallback
    cleaned = str(content).strip()
    return cleaned or fallback


@dataclass(frozen=True)
class TaskProfile:
    name: str
    planner_mode: str
    planner_plan: str
    planner_rationale: str
    research_headings: list[str]
    research_fallback: str
    execution_headings: list[str]
    execution_fallback: str
    final_headings: list[str]
    final_fallback: str


def infer_task_profile(task: str) -> TaskProfile:
    lowered = task.lower()

    if "温哥华" in task and ("天气" in task or "去哪玩" in task or "plan" in lowered):
        return TaskProfile(
            name="vancouver_weather_trip",
            planner_mode="research_then_execute",
            planner_plan=(
                "1. 先判断天气更适合室内、室外还是混合路线。 "
                "2. 再按上午、下午、晚上给出 1 到 2 个可执行去处。 "
                "3. 最后补充怕冷或下小雨时的替代方案和一条最省心路线。"
            ),
            planner_rationale="天气出行类任务需要先归纳条件，再转成按时间段可执行的建议。",
            research_headings=["天气判断", "适合的区域", "风险提醒", "替代方案"],
            research_fallback=(
                "天气判断: 当前偏凉且多云，更适合混合路线。\n"
                "适合的区域: Stanley Park、Canada Place、Granville Island、Yaletown 一带更容易组合出行。\n"
                "风险提醒: 纯户外停留时间不宜过长，需准备保暖与防小雨方案。\n"
                "替代方案: Vancouver Aquarium、美术馆、商场区、咖啡馆串联路线。"
            ),
            execution_headings=["当前判断", "上午", "下午", "晚上", "替代方案", "最省心路线"],
            execution_fallback=(
                "当前判断: 今天更适合混合路线。\n"
                "上午: Stanley Park 或 Canada Place 简单走走，怕冷就改去 Vancouver Aquarium。\n"
                "下午: Granville Island 逛市场和吃热食。\n"
                "晚上: Yaletown 或 Robson Street 吃饭散步。\n"
                "替代方案: 如果下小雨，改成美术馆、商场区、咖啡馆串联路线。\n"
                "最省心路线: 上午海边短走，中午去 Granville Island，晚上回市区吃饭。"
            ),
            final_headings=["当前判断", "最容易执行的玩法", "替代方案", "最省心的一日路线"],
            final_fallback=(
                "当前判断\n"
                "今天温哥华大约 7°C 左右、偏凉且多云，更适合“混合路线”：白天安排短时室外 + 室内停留，晚上尽量选市区轻松活动。\n\n"
                "最容易执行的玩法\n"
                "上午可以去 Stanley Park 海边或 Canada Place 一带散步 1 到 1.5 小时；如果怕冷，就改去 Vancouver Aquarium 或美术馆。\n"
                "下午适合去 Granville Island 逛市场、喝咖啡、吃点热食；如果天气转差，可以换成 Gastown + 室内餐厅。\n"
                "晚上建议去 Robson Street / Yaletown 吃饭散步，或者选一间有景观的餐厅，不建议排太长时间的纯户外路线。\n\n"
                "替代方案\n"
                "如果下小雨或怕冷，优先选 Vancouver Aquarium、温哥华美术馆、商场区、咖啡馆串联路线。\n\n"
                "最省心的一日路线\n"
                "上午 Stanley Park 或 Canada Place 简单走走，中午去 Granville Island 吃饭，下午继续逛市场和室内小店，晚上回到 Yaletown/Robson Street 吃饭收尾。"
            ),
        )

    if "bc省政府" in task or "bc 省政府" in lowered or "british columbia" in lowered or "政府支持" in task:
        return TaskProfile(
            name="bc_government_programs",
            planner_mode="research_only",
            planner_plan=(
                "1. 明确用户要的是 BC 省政府当前支持的项目类型。 "
                "2. 先按主题整理常见支持方向，例如创业、就业、培训、住房、清洁能源和中小企业。 "
                "3. 对每类说明适合人群、申请入口和需要进一步核实的点。"
            ),
            planner_rationale="政府项目查询类任务以信息整理为主，优先研究，再给出分类说明与后续核实建议。",
            research_headings=["可能的项目类别", "适合对象", "申请入口", "需要核实的点"],
            research_fallback=(
                "可能的项目类别: 常见会覆盖就业培训、企业补助、住房支持、清洁能源和社区服务等方向。\n"
                "适合对象: 取决于你是个人、学生、求职者、创业者、中小企业还是非营利机构。\n"
                "申请入口: 一般会分布在 BC Government、WorkBC、BC Housing、CleanBC 等官方项目页面。\n"
                "需要核实的点: 项目开放时间、地区限制、收入或行业门槛、所需材料。"
            ),
            execution_headings=["当前判断", "你应该优先看的支持方向", "下一步怎么查", "提醒"],
            execution_fallback=(
                "当前判断: 这类问题更适合先按项目方向分类，再去核实各自的官方申请页面。\n"
                "你应该优先看的支持方向: 就业与培训、创业与中小企业、住房支持、能源补贴、社区与家庭支持。\n"
                "下一步怎么查: 先确定你属于个人还是企业，再按场景去对应官方入口。\n"
                "提醒: 政府项目变化快，最终资格和开放状态要以官网为准。"
            ),
            final_headings=["当前判断", "BC 省政府常见支持方向", "怎么快速定位适合你的项目", "提醒"],
            final_fallback=(
                "当前判断\n"
                "如果你现在只是想快速了解 BC 省政府支持的项目，最好的方式不是先找一个总名单，而是先按你的身份和目标分类看。\n\n"
                "BC 省政府常见支持方向\n"
                "常见会集中在这几类：就业与技能培训、创业与中小企业支持、住房补助与租住支持、清洁能源与家居改造补贴、社区与家庭支持项目。\n\n"
                "怎么快速定位适合你的项目\n"
                "如果你是求职者，先看 WorkBC 和技能培训类项目；如果你是创业者或中小企业，优先看省政府的 business grants、innovation、regional supports；如果你是居民家庭，优先看 BC Housing、能源补贴和家庭支持类项目。\n\n"
                "提醒\n"
                "政府项目会按时间、地区、收入、行业或身份变化，真正申请前一定要回到官方页面核实 eligibility、截止时间和材料要求。"
            ),
        )

    if "工作" in task or "职业" in task or "job" in lowered or "career" in lowered:
        return TaskProfile(
            name="jobs_and_careers",
            planner_mode="research_then_execute",
            planner_plan=(
                "1. Summarize the market signal from the available data. "
                "2. Extract which roles benefit most from the AI wave. "
                "3. Turn the findings into candidate-specific advice."
            ),
            planner_rationale="Career questions benefit from market framing plus pragmatic advice.",
            research_headings=["Market Signal", "Opportunity Areas", "Risks", "Candidate Takeaways"],
            research_fallback=(
                "Market Signal: The market is selective rather than frozen.\n"
                "Opportunity Areas: AI-adjacent implementation, platform, data, and automation roles.\n"
                "Risks: Entry-level competition and generic coding profiles are under pressure.\n"
                "Candidate Takeaways: Candidates need demonstrable project delivery and AI-assisted productivity."
            ),
            execution_headings=["Short-Term View", "Long-Term View", "Easiest Roles to Land", "Advice by Seniority", "Watchlist"],
            execution_fallback=(
                "Short-Term View: Hiring is cautious but active in targeted areas.\n"
                "Long-Term View: Software and AI-enabling roles still show durable demand.\n"
                "Easiest Roles to Land: AI application engineer, data/platform engineer, cloud operations, security, technical support with automation skills.\n"
                "Advice by Seniority: Junior candidates need strong projects; mid-level candidates need ownership; senior candidates need AI leverage and business impact.\n"
                "Watchlist: postings volume, AI-skill demand, layoffs vs hiring stabilization, and employer preference for hybrid execution skills."
            ),
            final_headings=["当前判断", "最容易找到工作的方向", "分层建议", "未来6到12个月观察点"],
            final_fallback=(
                "当前判断\n"
                "短期内 IT 招聘更谨慎，但并未冻结；长期看软件与 AI 相关岗位仍然增长。\n\n"
                "最容易找到工作的方向\n"
                "AI 应用工程、数据/平台工程、云运维与安全、自动化支持类岗位通常更容易与企业当前需求对齐。\n\n"
                "分层建议\n"
                "初级候选人要突出项目与交付；中级候选人要体现 ownership；高级候选人要展示 AI 落地与团队杠杆能力。\n\n"
                "未来6到12个月观察点\n"
                "关注 AI 技能岗位数量、企业是否恢复中级招聘、平台与安全预算、以及自动化是否继续压缩泛开发岗位。"
            ),
        )

    return TaskProfile(
        name="generic",
        planner_mode="research_then_execute",
        planner_plan=(
            "1. Clarify the user goal and key constraints. "
            "2. Gather the most relevant facts or options. "
            "3. Convert them into a concise, actionable answer."
        ),
        planner_rationale="Generic fallback used because the task did not match a more specific profile.",
        research_headings=["Goal", "Key Facts", "Risks", "Next Steps"],
        research_fallback=(
            "Goal: Clarify what the user is trying to accomplish.\n"
            "Key Facts: Extract the most relevant facts already available in the prompt or context.\n"
            "Risks: Call out uncertainty, missing data, or fast-changing details.\n"
            "Next Steps: Turn the result into a practical recommendation."
        ),
        execution_headings=["Current Assessment", "Recommended Approach", "Alternatives", "Next Step"],
        execution_fallback=(
            "Current Assessment: The task should be broken into a small number of practical steps.\n"
            "Recommended Approach: Start with the clearest option that can be executed quickly.\n"
            "Alternatives: Provide one or two backup paths if conditions change.\n"
            "Next Step: Make the first action obvious and low-friction."
        ),
        final_headings=["当前判断", "核心建议", "执行方式"],
        final_fallback=(
            "当前判断\n"
            "建议先明确目标和限制条件，再给出最省心的执行方案。\n\n"
            "核心建议\n"
            "优先输出最相关的信息和一条可立即执行的主路径，再补充 1 到 2 个备选方案。\n\n"
            "执行方式\n"
            "先给结论，再补充依据与提醒。"
        ),
    )
