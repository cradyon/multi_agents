# Multi-Agent Starter

这是一个从零起步的 `LangGraph multi-agent` MVP，方向参考了 DeerFlow，但刻意先收敛成一个更容易跑通的骨架。

当前版本包含 4 个角色：

- `planner`: 判断任务走研究、执行还是两者都走
- `researcher`: 产出背景分析、假设和风险
- `executor`: 把任务转成实现草案、接口设计或编码步骤
- `synthesizer`: 汇总前面三个角色，输出最终答案

现在已经不是单纯的 4 个角色 demo，而是把你说的几个 phase 合到了一起：

- `phase 1`: graph / state / model wiring
- `phase 2`: tools 规划层
- `phase 3`: SQLite checkpoint + memory
- `phase 4`: FastAPI service layer

## 目录

```text
app/
  agents/
    planner.py
    researcher.py
    executor.py
    synthesizer.py
  api/
  config.py
  graph.py
  llm.py
  main.py
  persistence/
  service.py
  state.py
  tools/
APP_DEMO/
  scripts/
  threads/
  workflows/
```

## 1. 安装依赖

推荐用 `uv`：

```bash
uv venv
source .venv/bin/activate
uv pip install -e .
```

也可以用 `pip`：

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## 2. 配置模型

复制环境变量模板：

```bash
cp .env.example .env
```

默认使用 `OpenRouter`：

```env
MODEL_VENDOR=openrouter
OPENROUTER_API_KEY=your_openrouter_api_key
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=anthropic/claude-sonnet-4.5
```

如果要切到 OpenAI：

```env
MODEL_VENDOR=openai
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4.1
```

如果要切到 Volcengine / 火山方舟：

```env
MODEL_VENDOR=volcengine
VOLCENGINE_API_KEY=your_volcengine_api_key
VOLCENGINE_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
VOLCENGINE_MODEL=doubao-seed-1-6-250615
```

## 3. 运行

```bash
python -m app.main "给我设计一个类似 DearFlow 的 multi-agent coding assistant MVP"
```

或：

```bash
multi-agent "给我设计一个类似 DearFlow 的 multi-agent coding assistant MVP"
```

启动 API：

```bash
uvicorn app.server:app --reload
```

测试接口：

```bash
curl http://127.0.0.1:8000/api/health
curl -X POST http://127.0.0.1:8000/api/tasks/run \
  -H "Content-Type: application/json" \
  -d '{"task":"设计一个 LangGraph multi-agent coding assistant","thread_id":"demo-thread"}'
```

## 4. 可见的多 Worker 目录

你刚刚提到，希望在项目目录里直接看到多个 agent/thread 的 stride。这版已经支持把每次运行写到可见目录里：

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
    agent-b-researcher/
      status.md
      context.json
      output.md
    agent-c-executor/
      status.md
      context.json
      output.md
    agent-d-synthesizer/
      status.md
      context.json
      output.md
```

这样你在项目里就能直接看到：

- 哪个 thread 正在跑
- Agent A/B/C/D 分别负责什么
- 每个 agent 当前状态
- 每个 agent 的输出内容
- 最终汇总结果

这个目录不是“外挂 sidecar”，而是主项目自己的运行产物层：

- 代码在 [app/coordination/workspace.py](/Users/kevin/AGIProj/multi-agent/app/coordination/workspace.py)
- 运行产物在 `APP_DEMO/threads/<thread_id>/...`
- 主服务在 [app/service.py](/Users/kevin/AGIProj/multi-agent/app/service.py) 里会直接写它

如果你想先看不依赖外部包的演示，可以直接跑：

```bash
python3 APP_DEMO/scripts/run_demo.py
```

它会在主项目下生成：

```text
APP_DEMO/threads/live-demo-thread/
```

这就是“合到主项目里”的版本，不是额外的独立项目。

## 5. 画出 Workflow 图

如果你想把当前 LangGraph workflow 导出成图，可以直接跑：

```bash
python3 APP_DEMO/scripts/render_workflow.py
```

它会生成：

- `APP_DEMO/workflows/workflow.mmd`
- `APP_DEMO/workflows/workflow.md`

其中 `workflow.md` 里是可直接渲染的 Mermaid 图。
## 6. 下一步建议

这版先解决“能跑”“能持久化”“能经由 API 调用”和“能继续扩 DearFlow 式能力”几个目标。下一轮建议继续加：

1. 把占位型 `tools` 换成真实 web / filesystem / shell tools
2. 把现在的 SQLite store 接到更细粒度的 LangGraph checkpoint
3. 加真正的 `subagent parallelism`
4. 加 `sandbox`
5. 加 `Web UI`
6. 加 `skills`

## 7. 和 DeerFlow 的关系

这个 starter 借鉴的是 DeerFlow 的几个核心思路：

- 用 `LangGraph` 管 agent workflow
- 把不同 agent 的职责拆开
- 把模型接入层独立出去
- 先做 lead agent orchestration，再往上叠加 memory、sandbox、skills

但它还不是 DeerFlow 那种完整的 super agent harness，目前只是一个适合启动项目的最小后端骨架。
