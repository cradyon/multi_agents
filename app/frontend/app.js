import { createApp, computed, reactive } from "https://unpkg.com/vue@3/dist/vue.esm-browser.prod.js";

const STEP_ORDER = ["queued", "planner", "researcher", "executor", "synthesizer"];
const AUTH_TOKEN_KEY = "multi_agent_auth_token";
const CROWD = [
  { id: 1, delay: "0s", scale: 0.92, left: "8%" },
  { id: 2, delay: ".3s", scale: 0.82, left: "23%" },
  { id: 3, delay: ".6s", scale: 1.0, left: "40%" },
  { id: 4, delay: ".9s", scale: 0.86, left: "58%" },
  { id: 5, delay: "1.2s", scale: 0.96, left: "76%" },
];

createApp({
  setup() {
    const state = reactive({
      authMode: "login",
      isAuthenticated: false,
      authToken: localStorage.getItem(AUTH_TOKEN_KEY) || "",
      currentUser: "",
      loginUsername: "",
      loginPassword: "",
      registerUsername: "",
      registerPassword: "",
      authError: "",
      authInfo: "",
      passwordFocused: false,
      mouseInsideStage: false,
      mouseX: 0.5,
      mouseY: 0.5,
      taskInput: "请基于当前温哥华天气给我做一个出行 plan，目标是今天在温哥华去哪玩比较合适。要求输出中文，实用一点。",
      threadIdInput: "",
      activeTaskId: null,
      activeThreadId: null,
      runStatus: "Idle",
      progressTitle: "Waiting to start",
      progressPercent: 0,
      progressDetail: "Click Launch Workflow and the UI will keep refreshing automatically.",
      resultMeta: "No run yet.",
      resultBox: "Final result will appear here.",
      detailMeta: "Select a thread to inspect logs and outputs.",
      threadDetailFinal: "No thread selected.",
      threads: [],
      agents: [],
      heroStatus: "Idle",
      heroStage: "Waiting",
      heroProgress: "0%",
      currentStep: "queued",
      failed: false,
      taskPollTimer: null,
      threadPollTimer: null,
      listPollTimer: null,
    });

    const stepState = computed(() =>
      STEP_ORDER.map((step, index) => {
        const resolved = state.runStatus === "Completed" ? "synthesizer" : state.currentStep;
        const activeIndex = STEP_ORDER.indexOf(resolved);
        return {
          key: step,
          label: step === "queued" ? "Queue" : step.charAt(0).toUpperCase() + step.slice(1),
          active: state.runStatus !== "Completed" && (index === activeIndex || (activeIndex === -1 && index === 0)),
          complete: state.runStatus === "Completed" || index < activeIndex,
        };
      })
    );

    const characterMode = computed(() => {
      if (state.passwordFocused) return "watching";
      if (!state.mouseInsideStage) return "idle";
      if (state.mouseY < 0.28) return "thinking";
      if (state.mouseY > 0.76) return "crouch";
      if (state.mouseX < 0.28) return "wave-left";
      if (state.mouseX > 0.72) return "wave-right";
      return "follow";
    });

    const characterStyle = computed(() => {
      const lookX = (state.mouseX - 0.5) * 18;
      const lookY = (state.mouseY - 0.5) * 12;
      const bodyX = (state.mouseX - 0.5) * 26;
      const bodyY = (state.mouseY - 0.5) * 10;
      return {
        "--look-x": `${lookX}px`,
        "--look-y": `${lookY}px`,
        "--body-x": `${bodyX}px`,
        "--body-y": `${bodyY}px`,
      };
    });

    function formatMeta(parts) {
      return parts.filter(Boolean).join(" · ");
    }

    function readErrorMessage(error, fallback) {
      if (error && error.detail) return error.detail;
      if (error && error.message) return error.message;
      return fallback;
    }

    async function fetchJson(url, options = {}) {
      const headers = new Headers(options.headers || {});
      if (state.authToken) {
        headers.set("Authorization", `Bearer ${state.authToken}`);
      }
      const response = await fetch(url, { ...options, headers });
      if (!response.ok) {
        let detail = "";
        try {
          const payload = await response.json();
          detail = payload.detail || "";
        } catch {
          detail = await response.text();
        }
        const requestError = new Error(detail || response.statusText || "Request failed");
        requestError.detail = detail;
        requestError.status = response.status;
        throw requestError;
      }
      return response.json();
    }

    function syncHero(status, step, progress) {
      state.heroStatus = status || "Idle";
      state.heroStage = step || "Waiting";
      state.heroProgress = `${progress || 0}%`;
    }

    function updateProgress(payload) {
      const progress = Math.max(0, Math.min(Number(payload.progress || 0), 100));
      const titleMap = {
        queued: "Task queued",
        planner: "Planner running",
        researcher: "Researcher running",
        executor: "Executor running",
        synthesizer: "Synthesizer running",
        completed: "Workflow completed",
        failed: "Workflow failed",
      };

      state.currentStep = payload.current_step || "queued";
      state.progressTitle = titleMap[state.currentStep] || "Workflow running";
      state.progressPercent = progress;
      state.progressDetail = payload.detail || "Workflow is running.";
      state.failed = payload.status === "failed";
      syncHero(payload.status || "Idle", state.currentStep, progress);
    }

    function stopTaskPolling() {
      if (state.taskPollTimer) {
        window.clearInterval(state.taskPollTimer);
        state.taskPollTimer = null;
      }
    }

    function stopAutoRefresh() {
      if (state.listPollTimer) {
        window.clearInterval(state.listPollTimer);
        state.listPollTimer = null;
      }
      if (state.threadPollTimer) {
        window.clearInterval(state.threadPollTimer);
        state.threadPollTimer = null;
      }
    }

    function startAutoRefresh() {
      stopAutoRefresh();
      state.listPollTimer = window.setInterval(loadThreads, 4000);
      state.threadPollTimer = window.setInterval(() => {
        if (state.activeThreadId) {
          loadThread(state.activeThreadId);
        }
      }, 3000);
    }

    async function loadThreads() {
      try {
        state.threads = await fetchJson("/api/threads");
      } catch (error) {
        state.threads = [];
        state.resultMeta = readErrorMessage(error, "Unable to load threads.");
      }
    }

    async function loadThread(threadId) {
      state.activeThreadId = threadId;
      state.detailMeta = `Loading ${threadId}...`;

      try {
        const detail = await fetchJson(`/api/threads/${encodeURIComponent(threadId)}`);
        state.detailMeta = formatMeta([detail.thread_id, detail.status || "unknown", detail.path || ""]);
        state.threadDetailFinal = detail.final || "No final output yet.";
        state.agents = detail.agents || [];
      } catch (error) {
        state.detailMeta = "Failed to load thread detail";
        state.threadDetailFinal = readErrorMessage(error, "Unable to load thread detail.");
        state.agents = [];
      }
    }

    function pollTaskStatus(taskId) {
      stopTaskPolling();
      state.taskPollTimer = window.setInterval(async () => {
        try {
          const statusPayload = await fetchJson(`/api/tasks/${encodeURIComponent(taskId)}`);
          updateProgress(statusPayload);
          state.resultMeta = formatMeta([
            statusPayload.task_id,
            statusPayload.status,
            statusPayload.current_step || "",
            statusPayload.thread_path || "",
          ]);

          if (statusPayload.thread_id) {
            state.activeThreadId = statusPayload.thread_id;
            loadThread(state.activeThreadId);
          }

          if (statusPayload.result) {
            state.resultBox = statusPayload.result;
          }

          if (statusPayload.status === "completed") {
            state.runStatus = "Completed";
            stopTaskPolling();
            loadThreads();
          } else if (statusPayload.status === "failed") {
            state.runStatus = "Failed";
            state.resultBox = statusPayload.detail || "Workflow failed.";
            stopTaskPolling();
            loadThreads();
          }
        } catch (error) {
          if (error.status === 401) {
            logout();
          } else {
            state.progressDetail = "Status polling failed. Retrying automatically...";
          }
        }
      }, 1500);
    }

    async function runTask() {
      const taskValue = state.taskInput.trim();
      if (!taskValue) {
        state.resultMeta = "Task is required";
        state.resultBox = "Please enter a task before running the workflow.";
        return;
      }

      state.runStatus = "Submitting...";
      state.resultMeta = "Submitting task...";
      state.resultBox = "The request has been sent. Progress and thread details will refresh automatically.";
      updateProgress({
        status: "accepted",
        current_step: "queued",
        progress: 4,
        detail: "Click received. Preparing the background worker...",
      });
      startAutoRefresh();

      try {
        const data = await fetchJson("/api/tasks/start", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            task: taskValue,
            thread_id: state.threadIdInput || null,
            metadata: {},
          }),
        });

        state.activeTaskId = data.task_id;
        state.activeThreadId = data.thread_id || data.task_id;
        state.runStatus = "Running...";
        state.resultMeta = formatMeta([state.activeTaskId, data.status, data.detail || "", data.thread_path || ""]);
        state.resultBox = "Task accepted. The page is now polling backend status automatically.";
        updateProgress({
          status: data.status,
          current_step: "planner",
          progress: 8,
          detail: data.detail || "Background workflow started.",
        });
        await loadThreads();
        if (state.activeThreadId) {
          await loadThread(state.activeThreadId);
        }
        pollTaskStatus(state.activeTaskId);
      } catch (error) {
        state.runStatus = "Failed";
        state.resultMeta = "Request failed";
        state.resultBox = readErrorMessage(error, "Unknown request error.");
        updateProgress({
          status: "failed",
          current_step: "failed",
          progress: 100,
          detail: readErrorMessage(error, "Unknown request error."),
        });
      }
    }

    async function register() {
      state.authError = "";
      state.authInfo = "";
      try {
        const data = await fetchJson("/api/auth/register", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            username: state.registerUsername,
            password: state.registerPassword,
          }),
        });
        state.authInfo = `注册成功，欢迎 ${data.username}。现在可以登录了。`;
        state.authMode = "login";
        state.loginUsername = state.registerUsername;
        state.registerPassword = "";
      } catch (error) {
        state.authError = readErrorMessage(error, "注册失败。");
      }
    }

    async function login() {
      state.authError = "";
      state.authInfo = "";
      try {
        const data = await fetchJson("/api/auth/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            username: state.loginUsername,
            password: state.loginPassword,
          }),
        });
        state.authToken = data.token;
        localStorage.setItem(AUTH_TOKEN_KEY, data.token);
        state.currentUser = data.user.username;
        state.isAuthenticated = true;
        state.loginPassword = "";
        await loadThreads();
        startAutoRefresh();
      } catch (error) {
        state.authError = readErrorMessage(error, "登录失败。");
      }
    }

    async function restoreSession() {
      if (!state.authToken) return;
      try {
        const data = await fetchJson("/api/auth/me");
        state.currentUser = data.username;
        state.isAuthenticated = true;
        await loadThreads();
        startAutoRefresh();
      } catch {
        logout();
      }
    }

    function logout() {
      stopTaskPolling();
      stopAutoRefresh();
      state.authToken = "";
      state.isAuthenticated = false;
      state.currentUser = "";
      state.activeTaskId = null;
      state.activeThreadId = null;
      state.threads = [];
      state.agents = [];
      localStorage.removeItem(AUTH_TOKEN_KEY);
    }

    function refreshThreads() {
      loadThreads();
    }

    function onPasswordFocus() {
      state.passwordFocused = true;
    }

    function onPasswordBlur() {
      state.passwordFocused = false;
    }

    function onStageMove(event) {
      const rect = event.currentTarget.getBoundingClientRect();
      const x = (event.clientX - rect.left) / rect.width;
      const y = (event.clientY - rect.top) / rect.height;
      state.mouseInsideStage = true;
      state.mouseX = Math.max(0, Math.min(1, x));
      state.mouseY = Math.max(0, Math.min(1, y));
    }

    function onStageLeave() {
      state.mouseInsideStage = false;
      state.mouseX = 0.5;
      state.mouseY = 0.5;
    }

    restoreSession();

    return {
      state,
      stepState,
      characterMode,
      characterStyle,
      crowd: CROWD,
      runTask,
      refreshThreads,
      loadThread,
      register,
      login,
      logout,
      onPasswordFocus,
      onPasswordBlur,
      onStageMove,
      onStageLeave,
    };
  },
  template: `
    <div class="grid-overlay"></div>

    <section v-if="!state.isAuthenticated" class="login-page">
      <div class="login-shell">
        <div class="login-card">
          <div class="eyebrow">Access Portal</div>
          <h1 class="login-title">登录你的控制台</h1>
          <p class="login-copy">现在这里已经是 SQLite 真注册和真登录。用户名和密码会写进数据库，登录后拿到 token，再进入控制台。</p>

          <div class="auth-toggle">
            <button class="auth-tab" :class="{ active: state.authMode === 'login' }" @click="state.authMode = 'login'">登录</button>
            <button class="auth-tab" :class="{ active: state.authMode === 'register' }" @click="state.authMode = 'register'">注册</button>
          </div>

          <div v-if="state.authMode === 'login'" class="form-stack">
            <div>
              <label class="field-label" for="login-username">Username</label>
              <input id="login-username" v-model="state.loginUsername" class="input" type="text" placeholder="输入用户名" @keyup.enter="login" />
            </div>
            <div>
              <label class="field-label" for="login-password">Password</label>
              <input id="login-password" v-model="state.loginPassword" class="input" type="password" placeholder="输入密码" @focus="onPasswordFocus" @blur="onPasswordBlur" @keyup.enter="login" />
            </div>
            <div class="login-actions">
              <button class="btn btn-primary" @click="login">Login</button>
            </div>
          </div>

          <div v-else class="form-stack">
            <div>
              <label class="field-label" for="register-username">Username</label>
              <input id="register-username" v-model="state.registerUsername" class="input" type="text" placeholder="注册用户名" @keyup.enter="register" />
            </div>
            <div>
              <label class="field-label" for="register-password">Password</label>
              <input id="register-password" v-model="state.registerPassword" class="input" type="password" placeholder="注册密码" @keyup.enter="register" />
            </div>
            <div class="login-actions">
              <button class="btn btn-primary" @click="register">Create Account</button>
            </div>
          </div>

          <div class="login-error" v-if="state.authError">{{ state.authError }}</div>
          <div class="login-info" v-if="state.authInfo">{{ state.authInfo }}</div>
        </div>

        <div class="login-stage" @mousemove="onStageMove" @mouseleave="onStageLeave">
          <div class="stage-halo"></div>
          <div class="crowd-strip">
            <div v-for="item in crowd" :key="item.id" class="mini-person" :style="{ '--crowd-left': item.left, '--crowd-scale': item.scale, '--crowd-delay': item.delay }">
              <div class="mini-head"></div>
              <div class="mini-body"></div>
            </div>
          </div>
          <div class="stage-screen">
            <div class="stage-window">
              <div class="window-line short"></div>
              <div class="window-line"></div>
              <div class="window-line short alt"></div>
            </div>
            <div class="character" :class="characterMode" :style="characterStyle">
              <div class="character-head">
                <span class="eye left"></span>
                <span class="eye right"></span>
              </div>
              <div class="character-body"></div>
              <div class="character-arm left"></div>
              <div class="character-arm right"></div>
              <div class="character-leg left"></div>
              <div class="character-leg right"></div>
            </div>
            <div class="stage-caption">
              <strong>{{ state.authMode === 'register' ? '注册模式' : '登录模式' }}</strong>
              <span>{{ characterMode === 'watching' ? '你在输密码，小人会进入警戒动作。' : '舞台里的小人群会轻微摆动，主角会跟着你的鼠标方向做不同动作。' }}</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <div v-else class="app-shell">
      <section class="hero">
        <div class="hero-main">
          <div class="eyebrow">Vue 3 Frontend</div>
          <h1 class="hero-title">Multi-Agent Control Room</h1>
          <p class="hero-copy">你好，{{ state.currentUser }}。现在前台已经接上真实用户认证，任务接口也会带着 token 去请求后端。</p>
          <div class="hero-stats">
            <div class="stat">
              <span class="stat-label">Loop Status</span>
              <span class="stat-value">{{ state.heroStatus }}</span>
            </div>
            <div class="stat">
              <span class="stat-label">Current Stage</span>
              <span class="stat-value">{{ state.heroStage }}</span>
            </div>
            <div class="stat">
              <span class="stat-label">Progress</span>
              <span class="stat-value">{{ state.heroProgress }}</span>
            </div>
          </div>
        </div>
        <div class="hero-side">
          <div class="signal-card">
            <h3>Auth Status</h3>
            <p>当前会话已完成数据库登录。注册和登录都走 FastAPI 接口，用户信息保存在 SQLite 里。</p>
            <div class="signal-meter">
              <span></span><span></span><span></span><span></span>
            </div>
          </div>
          <div class="signal-card">
            <h3>Session</h3>
            <p>当前用户：{{ state.currentUser }}</p>
            <div class="login-actions">
              <button class="btn btn-secondary" @click="logout">Logout</button>
            </div>
          </div>
        </div>
      </section>

      <div class="content-grid">
        <section class="panel">
          <div class="panel-head">
            <h2>Mission Launch</h2>
            <span class="status-badge">{{ state.runStatus }}</span>
          </div>
          <div class="panel-body">
            <div class="form-stack">
              <div>
                <label class="field-label" for="thread-id">Thread ID</label>
                <input id="thread-id" v-model="state.threadIdInput" class="input" type="text" placeholder="Optional custom thread id" />
              </div>
              <div>
                <label class="field-label" for="task-input">Task</label>
                <textarea id="task-input" v-model="state.taskInput" class="textarea"></textarea>
              </div>
            </div>

            <div class="controls">
              <button class="btn btn-primary" @click="runTask" :disabled="state.runStatus === 'Submitting...' || state.runStatus === 'Running...'">
                {{ state.runStatus === 'Running...' ? 'Running...' : state.runStatus === 'Submitting...' ? 'Starting...' : 'Launch Workflow' }}
              </button>
              <button class="btn btn-secondary" @click="refreshThreads">Refresh Threads</button>
            </div>

            <div class="progress-shell" :class="{ failed: state.failed }">
              <div class="progress-row">
                <strong>{{ state.progressTitle }}</strong>
                <span>{{ state.progressPercent }}%</span>
              </div>
              <div class="progress-track">
                <div class="progress-bar" :style="{ width: state.progressPercent + '%' }"></div>
              </div>
              <div class="step-strip">
                <div v-for="step in stepState" :key="step.key" class="step-pill" :class="{ active: step.active, complete: step.complete }">{{ step.label }}</div>
              </div>
              <div class="progress-detail">{{ state.progressDetail }}</div>
            </div>

            <div class="output-meta">
              <span>Live Response</span>
              <span>{{ state.resultMeta }}</span>
            </div>
            <div class="result-box">{{ state.resultBox }}</div>
          </div>
        </section>

        <section class="panel">
          <div class="panel-head">
            <h2>Recent Threads</h2>
            <span class="detail-meta">APP_DEMO/threads</span>
          </div>
          <div class="panel-body">
            <div class="thread-list" v-if="state.threads.length">
              <button v-for="thread in state.threads" :key="thread.thread_id" class="thread-item" :class="{ active: state.activeThreadId === thread.thread_id }" @click="loadThread(thread.thread_id)">
                <div class="thread-id">{{ thread.thread_id }}</div>
                <div class="thread-meta">{{ [thread.status || 'unknown', thread.task || ''].filter(Boolean).join(' · ') }}</div>
                <div class="thread-meta">{{ thread.path || '' }}</div>
              </button>
            </div>
            <div v-else class="result-box">No threads yet.</div>
          </div>
        </section>
      </div>

      <section class="panel section-gap">
        <div class="panel-head">
          <h2>Thread Detail</h2>
          <span class="detail-meta">{{ state.detailMeta }}</span>
        </div>
        <div class="panel-body">
          <div class="thread-detail">
            <div class="result-box">{{ state.threadDetailFinal }}</div>
            <div class="agent-grid" v-if="state.agents.length">
              <article v-for="agent in state.agents" :key="agent.agent_id" class="agent-card">
                <div class="agent-top">
                  <h3>{{ agent.agent_id }}</h3>
                  <span class="chip">{{ agent.context?.status || 'unknown' }}</span>
                </div>
                <div class="agent-meta">{{ agent.path || '' }}</div>
                <div class="agent-meta">Log</div>
                <pre class="code-block">{{ agent.log || '' }}</pre>
                <div class="agent-meta">Output</div>
                <pre class="code-block">{{ agent.output || '' }}</pre>
              </article>
            </div>
            <div v-else class="result-box">No agent records found.</div>
          </div>
        </div>
      </section>
    </div>
  `,
}).mount("#app");
