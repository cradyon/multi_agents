# Multi-Agent Starter

A `LangGraph`-based multi-agent starter inspired by DeerFlow, scoped down into a practical repo you can run, inspect, and extend.

This project focuses on three things:

- a clear multi-agent backend skeleton
- visible thread and agent artifacts under the project directory
- a lightweight FastAPI web console for running tasks and inspecting outputs

## What It Includes

- `planner`: decides whether the task should research, execute, or do both
- `researcher`: produces background notes and structured findings
- `executor`: turns the task into an actionable plan or implementation draft
- `synthesizer`: merges the upstream outputs into the final response

The current starter already combines the first four build phases:

- `phase 1`: graph, state, and model wiring
- `phase 2`: tool planning layer
- `phase 3`: SQLite checkpoint and memory
- `phase 4`: FastAPI service and web UI

## Repo Layout

```text
app/
  agents/
  api/
  coordination/
  persistence/
  tools/
  config.py
  graph.py
  llm.py
  main.py
  server.py
  service.py
  state.py
APP_DEMO/
  scripts/
  workflows/
```

Notes:

- runtime artifacts are intentionally ignored from git
- generated threads are written to `APP_DEMO/threads/<thread_id>/`
- demo scripts and workflow assets are grouped under `APP_DEMO/`

## Quick Start

### 1. Create a virtual environment

Using `uv`:

```bash
uv venv
source .venv/bin/activate
uv pip install -e .
```

Using `pip`:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 2. Add environment variables

Create a local `.env` file in the repo root.

OpenRouter example:

```env
MODEL_VENDOR=openrouter
OPENROUTER_API_KEY=your_openrouter_api_key
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=openrouter/free
```

OpenAI example:

```env
MODEL_VENDOR=openai
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4.1
```

Volcengine example:

```env
MODEL_VENDOR=volcengine
VOLCENGINE_API_KEY=your_volcengine_api_key
VOLCENGINE_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
VOLCENGINE_MODEL=doubao-seed-2-0-mini-260215
```

### 3. Run a task from the CLI

```bash
python -m app.main "给我设计一个类似 DearFlow 的 multi-agent coding assistant MVP"
```

or:

```bash
multi-agent "给我设计一个类似 DearFlow 的 multi-agent coding assistant MVP"
```

### 4. Run the web server

```bash
uvicorn app.server:app --host 127.0.0.1 --port 8765
```

Then open:

- [http://127.0.0.1:8765](http://127.0.0.1:8765)

If `8765` is already in use, switch to another port such as `8766`.

## Offline / Fallback Behavior

This starter is runnable even when a model call fails or external network access is unavailable.

- the FastAPI app still starts
- the LangGraph workflow still completes
- each agent falls back to a deterministic local response
- thread artifacts are still written under `APP_DEMO/threads/`

That makes the repo usable as a local demo project first, and a live LLM-backed project second.

## Run Tests

With the existing virtual environment:

```bash
./.venv/bin/python -m unittest discover -s tests -v
```

### 5. Run the API directly

```bash
curl http://127.0.0.1:8765/api/health
curl -X POST http://127.0.0.1:8765/api/tasks/run \
  -H "Content-Type: application/json" \
  -d '{"task":"设计一个 LangGraph multi-agent coding assistant","thread_id":"demo-thread"}'
```

## Visible Thread Artifacts

Every run is written into a project-visible workspace:

```text
APP_DEMO/threads/<thread_id>/
  thread.json
  README.md
  final.md
  agents/
    agent-a-planner/
      status.md
      context.json
      output.md
      log.md
    agent-b-researcher/
      status.md
      context.json
      output.md
      log.md
    agent-c-executor/
      status.md
      context.json
      output.md
      log.md
    agent-d-synthesizer/
      status.md
      context.json
      output.md
      log.md
```

This makes it easy to inspect:

- which thread ran
- what each worker did
- whether a step completed, skipped, or failed
- the final synthesized answer

The coordination layer lives in [workspace.py](/Users/kevin/AGIProj/multi-agent/app/coordination/workspace.py), and the main workflow integration lives in [service.py](/Users/kevin/AGIProj/multi-agent/app/service.py).

## Demo Assets

### Demo scripts

- `python3 APP_DEMO/scripts/run_demo.py`
- `python3 APP_DEMO/scripts/render_workflow.py`
- `python3 APP_DEMO/scripts/render_workflow_jpg.py`

### Workflow previews

Current workflow:

![Current Workflow](/Users/kevin/AGIProj/multi-agent/APP_DEMO/workflows/workflow-current.jpg)

Future parallel workflow:

![Future Parallel Workflow](/Users/kevin/AGIProj/multi-agent/APP_DEMO/workflows/workflow-future-parallel.jpg)

## Current Status

This repo is a good starter for:

- LangGraph orchestration experiments
- visible agent-thread coordination
- model-vendor abstraction
- backend-first multi-agent product prototyping

It is not yet a full DeerFlow-style production harness. The current version still relies on fallback logic for some task classes and does not yet use live web retrieval as a first-class tool.

## Roadmap

- replace planning-only tools with real web, file, and shell tools
- add live source retrieval with citations
- add runtime parallel subagent execution
- harden checkpointing and resume behavior
- improve the web UI into a richer chat and trace console
- add skills, sandboxing, and evals

## Development Notes

- `.env` is intentionally ignored
- `.venv`, local data, and generated thread artifacts are intentionally ignored
- the project currently writes runtime data under `.multi_agent_data/`
- generated demo threads live under `APP_DEMO/threads/`

## Relationship to DeerFlow

This starter borrows the high-level ideas:

- graph-based agent orchestration
- explicit role separation
- model wiring as its own layer
- gradual layering of memory, tools, sandboxing, and skills

But it deliberately starts smaller so it is easier to run and evolve in a local workspace.

## License

This project is released under the MIT License. See [LICENSE](/Users/kevin/AGIProj/multi-agent/LICENSE).
