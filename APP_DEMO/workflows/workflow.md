# Workflow Diagram

This diagram reflects the current LangGraph workflow in the starter project.

```mermaid
flowchart TD
    start(["START"])
    planner["Planner"]
    researcher["Researcher"]
    executor["Executor"]
    synthesizer["Synthesizer"]
    end(["END"])
    start --> planner
    planner -->|mode = research_only| researcher
    planner -->|mode = execute_only| executor
    planner -->|mode = research_then_execute| researcher
    researcher -->|mode = research_only| synthesizer
    researcher -->|mode = research_then_execute| executor
    executor --> synthesizer
    synthesizer --> end
```
