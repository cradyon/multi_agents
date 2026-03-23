from __future__ import annotations

from app.tools.types import ToolResult


def plan_web_research(
    query: str,
    *,
    context: str | None = None,
    source_hints: list[str] | None = None,
    max_queries: int = 5,
) -> ToolResult:
    """Return a safe research plan instead of performing live browsing.

    This is intentionally a placeholder so the main graph can decide whether to
    route to a real browser/search tool later.
    """
    normalized_query = query.strip()
    hints = [hint.strip() for hint in (source_hints or []) if hint.strip()]

    search_queries = [normalized_query]
    if context:
        search_queries.append(f"{normalized_query} {context.strip()}")
    if hints:
        search_queries.extend(f"{normalized_query} {hint}" for hint in hints[: max(0, max_queries - len(search_queries))])

    search_queries = search_queries[:max_queries]

    return ToolResult(
        tool_name="web_research_plan",
        input={
            "query": query,
            "context": context,
            "source_hints": hints,
            "max_queries": max_queries,
        },
        summary="Prepared a safe research plan without making any network requests.",
        safe=False,
        recommended_actions=[
            "Validate the query intent.",
            "Run the queries through a real search provider later.",
            "Review and rank sources before synthesizing conclusions.",
        ],
        warnings=[
            "This helper does not browse the web.",
            "Treat the suggested queries as planning hints only.",
        ],
        metadata={
            "search_queries": search_queries,
            "next_step": "wire to a real search tool or browser node",
        },
    )
