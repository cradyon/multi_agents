from __future__ import annotations

from collections.abc import Callable

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from app.api import router
from app.api.schemas import RunTaskRequest, RunTaskResponse
from app.api.router import get_task_runner
from app.service import MultiAgentService


def create_app(task_runner: Callable[[RunTaskRequest], RunTaskResponse] | None = None) -> FastAPI:
    app = FastAPI(title="Multi-Agent API", version="0.1.0")

    if task_runner is not None:
        # Late binding hook for the future LangGraph runner.
        # The API contract stays stable when the implementation is wired in.
        app.dependency_overrides[get_task_runner] = lambda: task_runner

    app.include_router(router, prefix="/api")

    @app.get("/", response_class=HTMLResponse)
    def index() -> str:
        return """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Multi-Agent Console</title>
  <style>
    :root {
      --bg: #f4f2ed;
      --panel: #ffffff;
      --ink: #1f2937;
      --muted: #6b7280;
      --line: #d9d4ca;
      --accent: #0f766e;
      --accent-2: #f59e0b;
      --shadow: 0 16px 40px rgba(17, 24, 39, 0.08);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      background:
        radial-gradient(circle at top right, rgba(245, 158, 11, 0.12), transparent 30%),
        radial-gradient(circle at top left, rgba(15, 118, 110, 0.10), transparent 35%),
        var(--bg);
      color: var(--ink);
    }
    .shell {
      max-width: 1400px;
      margin: 0 auto;
      padding: 32px 24px 48px;
    }
    .hero {
      display: grid;
      gap: 16px;
      margin-bottom: 24px;
    }
    h1 {
      margin: 0;
      font-size: 42px;
      line-height: 1;
      letter-spacing: -0.04em;
    }
    .hero p { margin: 0; color: var(--muted); max-width: 760px; font-size: 18px; }
    .grid {
      display: grid;
      grid-template-columns: 1.05fr 0.95fr;
      gap: 20px;
      align-items: start;
    }
    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 24px;
      box-shadow: var(--shadow);
      overflow: hidden;
    }
    .panel-head {
      padding: 18px 20px;
      border-bottom: 1px solid var(--line);
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
    }
    .panel-head h2 { margin: 0; font-size: 20px; }
    .panel-body { padding: 20px; }
    textarea {
      width: 100%;
      min-height: 220px;
      resize: vertical;
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 16px;
      font: inherit;
      font-size: 16px;
      background: #fcfbf8;
    }
    input[type="text"] {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 12px 14px;
      font: inherit;
      background: #fcfbf8;
    }
    .controls {
      display: grid;
      gap: 12px;
      margin-top: 14px;
    }
    button {
      border: 0;
      border-radius: 999px;
      padding: 12px 18px;
      font: inherit;
      font-weight: 700;
      cursor: pointer;
      background: var(--accent);
      color: #fff;
    }
    button.secondary {
      background: transparent;
      color: var(--accent);
      border: 1px solid rgba(15, 118, 110, 0.25);
    }
    .meta, .status {
      color: var(--muted);
      font-size: 14px;
    }
    .result {
      white-space: pre-wrap;
      line-height: 1.6;
      font-size: 16px;
      background: #fcfbf8;
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 16px;
      min-height: 180px;
    }
    .thread-list {
      display: grid;
      gap: 10px;
    }
    .thread-item {
      padding: 14px 16px;
      border-radius: 16px;
      border: 1px solid var(--line);
      background: #fcfbf8;
      cursor: pointer;
    }
    .thread-item strong { display: block; margin-bottom: 6px; }
    .thread-detail {
      display: grid;
      gap: 16px;
    }
    .agent-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 14px;
    }
    .agent-card {
      border: 1px solid var(--line);
      border-radius: 18px;
      background: #fcfbf8;
      padding: 16px;
      display: grid;
      gap: 10px;
    }
    .agent-card h3 { margin: 0; font-size: 16px; }
    .chip {
      display: inline-block;
      padding: 4px 10px;
      border-radius: 999px;
      background: rgba(245, 158, 11, 0.16);
      color: #9a6700;
      font-size: 12px;
      font-weight: 700;
    }
    pre {
      white-space: pre-wrap;
      word-break: break-word;
      margin: 0;
      background: #fff;
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 12px;
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
      font-size: 12px;
      line-height: 1.5;
    }
    @media (max-width: 1100px) {
      .grid { grid-template-columns: 1fr; }
      .agent-grid { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <div class="shell">
    <section class="hero">
      <h1>Multi-Agent Console</h1>
      <p>Enter a task, run the LangGraph workflow, and inspect the final output together with the visible worker logs written into APP_DEMO.</p>
    </section>

    <div class="grid">
      <section class="panel">
        <div class="panel-head">
          <h2>Run Task</h2>
          <span class="status" id="run-status">Idle</span>
        </div>
        <div class="panel-body">
          <label class="meta" for="thread-id">Thread ID</label>
          <input id="thread-id" type="text" placeholder="Optional custom thread id" />
          <div style="height:12px"></div>
          <label class="meta" for="task-input">Task</label>
          <textarea id="task-input">请基于当前温哥华天气给我做一个出行 plan，目标是今天在温哥华去哪玩比较合适。要求输出中文，实用一点。</textarea>
          <div class="controls">
            <button id="run-btn">Run Workflow</button>
            <button id="refresh-btn" class="secondary" type="button">Refresh Recent Threads</button>
          </div>
          <div style="height:16px"></div>
          <div class="meta" id="result-meta">No run yet.</div>
          <div style="height:10px"></div>
          <div class="result" id="result-box">Final result will appear here.</div>
        </div>
      </section>

      <section class="panel">
        <div class="panel-head">
          <h2>Recent Threads</h2>
          <span class="meta">APP_DEMO/threads</span>
        </div>
        <div class="panel-body">
          <div class="thread-list" id="thread-list"></div>
        </div>
      </section>
    </div>

    <section class="panel" style="margin-top:20px;">
      <div class="panel-head">
        <h2>Thread Detail</h2>
        <span class="meta" id="detail-meta">Select a thread to inspect logs and outputs.</span>
      </div>
      <div class="panel-body">
        <div class="thread-detail" id="thread-detail">
          <div class="result">No thread selected.</div>
        </div>
      </div>
    </section>
  </div>

  <script>
    const taskInput = document.getElementById('task-input');
    const threadIdInput = document.getElementById('thread-id');
    const runBtn = document.getElementById('run-btn');
    const refreshBtn = document.getElementById('refresh-btn');
    const runStatus = document.getElementById('run-status');
    const resultMeta = document.getElementById('result-meta');
    const resultBox = document.getElementById('result-box');
    const threadList = document.getElementById('thread-list');
    const threadDetail = document.getElementById('thread-detail');
    const detailMeta = document.getElementById('detail-meta');

    async function loadThreads() {
      const res = await fetch('/api/threads');
      const threads = await res.json();
      threadList.innerHTML = '';

      if (!threads.length) {
        threadList.innerHTML = '<div class="result">No threads yet.</div>';
        return;
      }

      for (const thread of threads) {
        const item = document.createElement('div');
        item.className = 'thread-item';
        item.innerHTML = `
          <strong>${thread.thread_id}</strong>
          <div class="meta">${thread.status || 'unknown'} · ${thread.task || ''}</div>
          <div class="meta">${thread.path || ''}</div>
        `;
        item.addEventListener('click', () => loadThread(thread.thread_id));
        threadList.appendChild(item);
      }
    }

    async function loadThread(threadId) {
      detailMeta.textContent = `Loading ${threadId}...`;
      const res = await fetch(`/api/threads/${threadId}`);
      const detail = await res.json();
      detailMeta.textContent = `${detail.thread_id} · ${detail.status || 'unknown'} · ${detail.path || ''}`;

      const agentsHtml = (detail.agents || []).map(agent => `
        <article class="agent-card">
          <div>
            <h3>${agent.agent_id}</h3>
            <span class="chip">${agent.context?.status || 'unknown'}</span>
          </div>
          <div class="meta">${agent.path || ''}</div>
          <div class="meta">Log</div>
          <pre>${escapeHtml(agent.log || '')}</pre>
          <div class="meta">Output</div>
          <pre>${escapeHtml(agent.output || '')}</pre>
        </article>
      `).join('');

      threadDetail.innerHTML = `
        <div class="result">${escapeHtml(detail.final || 'No final output yet.')}</div>
        <div class="agent-grid">${agentsHtml || '<div class="result">No agent records found.</div>'}</div>
      `;
    }

    async function runTask() {
      runStatus.textContent = 'Running...';
      resultMeta.textContent = 'Sending request...';
      resultBox.textContent = 'Working...';
      runBtn.disabled = true;

      try {
        const payload = {
          task: taskInput.value,
          thread_id: threadIdInput.value || null,
          metadata: {},
        };
        const res = await fetch('/api/tasks/run', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        const data = await res.json();
        resultMeta.textContent = `${data.task_id} · ${data.status} · ${data.detail || ''} · ${data.thread_path || ''}`;
        resultBox.textContent = data.result || 'No result returned.';
        runStatus.textContent = 'Completed';
        await loadThreads();
        if (data.task_id) {
          await loadThread(data.task_id);
        }
      } catch (error) {
        runStatus.textContent = 'Failed';
        resultMeta.textContent = 'Request failed';
        resultBox.textContent = String(error);
      } finally {
        runBtn.disabled = false;
      }
    }

    function escapeHtml(value) {
      return String(value)
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;');
    }

    runBtn.addEventListener('click', runTask);
    refreshBtn.addEventListener('click', loadThreads);
    loadThreads();
  </script>
</body>
</html>
        """

    return app


service = MultiAgentService()


def _run_with_service(payload: RunTaskRequest) -> RunTaskResponse:
    result = service.run_task(task=payload.task, thread_id=payload.thread_id)
    return RunTaskResponse(
        task_id=result.thread_id,
        status="completed",
        task=result.task,
        result=result.final_response,
        detail=f"mode={result.mode}",
        thread_path=f"APP_DEMO/threads/{result.thread_id}",
    )


app = create_app(task_runner=_run_with_service)
