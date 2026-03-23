# APP Demo Workspace

这个目录统一放置 demo、可视化产物和历史线程记录。

主要分成三类：

- `scripts/`: demo 和可视化辅助脚本
- `threads/`: 每次 demo / 调查运行生成的多 agent 日志与结果
- `workflows/`: workflow 图、Mermaid 文件、JPG 图片

真实运行后的线程目录形态：

```text
APP_DEMO/threads/<thread_id>/
```

每个 thread 下面会包含：

- `thread.json`: thread 元信息
- `README.md`: thread 概览
- `final.md`: 最终结果
- `agents/agent-a-planner/`
- `agents/agent-b-researcher/`
- `agents/agent-c-executor/`
- `agents/agent-d-synthesizer/`

每个 agent 目录里会有：

- `status.md`
- `context.json`
- `log.md`
- `output.md`
