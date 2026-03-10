# FORGE — Claude Code CLI Instructions
**Project Root:** `C:\Programs\forge`
**Projects Directory:** `C:\Programs\forge\projects`
**Spec Document:** `Forge_Architecture_Spec.docx` (full architecture reference)

---

## IDENTITY & PURPOSE

You are the build agent for **Forge** — a local AI-powered development environment that combines Replit's visual interface with Claude Code's autonomous agent loop, running entirely against a local LLM via LM Studio. No external APIs. No cloud dependencies.

Forge does two things:
1. **Build** new software projects from a plain-English prompt
2. **Fix** existing projects by auditing every file, diagnosing issues, and patching until clean

---

## GROUND RULES

- **Read every file in the project before writing anything.** No exceptions.
- **Never overwrite working code without understanding it first.**
- **Always apply targeted patches** — edit only the lines that need changing. Avoid full-file rewrites unless the file is broken beyond repair.
- **Run the build/tests after every set of changes.** Verify before moving on.
- **If something breaks, fix it before proceeding.** Do not leave broken states and move to the next task.
- **Log every action** to `C:\Programs\forge\logs\build.log` with timestamps.
- **Do not modify anything outside** `C:\Programs\forge\`.

---

## STARTUP PROTOCOL

On every Claude Code session, execute this sequence before doing anything else:

```
1. Read this file (CLAUDE.md) completely
2. Read forge\config\forge.config.json (create with defaults if missing)
3. List all files in C:\Programs\forge\ recursively
4. Identify what currently exists vs what is missing per the sprint plan below
5. Pick up at the earliest incomplete sprint
6. Report current state before beginning any edits
```

---

## PROJECT STRUCTURE (Build to This)

```
C:\Programs\forge\
├── CLAUDE.md                        ← This file
├── README.md                        ← Auto-generated after Sprint 1
├── forge.config.json                ← Root config (copy of config\forge.config.json)
│
├── backend\                         ← FastAPI Python server
│   ├── main.py                      ← Entry point: uvicorn server + WebSocket hub
│   ├── requirements.txt
│   ├── api\
│   │   ├── projects.py              ← REST endpoints: list, create, open, delete projects
│   │   ├── agent.py                 ← REST + WS endpoints: start build, stream events
│   │   └── github.py                ← GitHub push endpoint
│   ├── agent\
│   │   ├── auditor.py               ← Full project directory reader + file mapper
│   │   ├── builder.py               ← LLM call pipeline, file generator
│   │   ├── patcher.py               ← Targeted file edit applier
│   │   ├── runner.py                ← subprocess build/test executor, error capture
│   │   ├── tester.py                ← Test framework auto-detector + runner
│   │   └── loop.py                  ← The core build loop (audit → build → test → fix → repeat)
│   ├── llm\
│   │   ├── client.py                ← httpx async client for LM Studio OpenAI API
│   │   ├── vram.py                  ← nvidia-smi VRAM detector + model selector
│   │   └── prompts.py               ← All LLM prompt templates
│   └── utils\
│       ├── logger.py                ← Structured logger → logs\build.log
│       └── git.py                   ← git subprocess wrapper for GitHub integration
│
├── frontend\                        ← React + Vite UI
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src\
│       ├── main.jsx
│       ├── App.jsx                  ← Root layout: sidebar + editor + preview panel
│       ├── components\
│       │   ├── FileExplorer.jsx     ← Left sidebar: project file tree
│       │   ├── Editor.jsx           ← Monaco Editor wrapper
│       │   ├── PreviewPanel.jsx     ← Right panel with three tabs
│       │   ├── AppPreview.jsx       ← Tab 1: iframe to running app
│       │   ├── FileDiffs.jsx        ← Tab 2: real-time file change viewer
│       │   ├── Terminal.jsx         ← Tab 3: xterm.js terminal
│       │   ├── ProjectDashboard.jsx ← Home screen: project list + status
│       │   ├── NewProjectModal.jsx  ← Prompt input to start new build
│       │   └── StatusBar.jsx        ← Bottom bar: model loaded, build status, VRAM
│       ├── hooks\
│       │   ├── useWebSocket.js      ← WS connection to backend event stream
│       │   └── useProject.js        ← Project state management
│       └── styles\
│           └── globals.css          ← Tailwind base
│
├── config\
│   └── forge.config.json            ← See config schema below
│
├── logs\
│   └── build.log                    ← Rotating build log
│
└── projects\                        ← All built projects live here
    └── [project-name]\              ← Self-contained project directory
```

---

## CONFIG SCHEMA

`forge\config\forge.config.json` — create this in Sprint 1 if missing:

```json
{
  "lm_studio_url": "http://localhost:1234/v1",
  "forge_host": "localhost",
  "forge_port": 8000,
  "frontend_port": 3000,
  "projects_path": "C:\\Programs\\forge\\projects",
  "logs_path": "C:\\Programs\\forge\\logs",
  "model_selection": "auto",
  "model_override": null,
  "max_fix_iterations": 10,
  "circular_error_threshold": 3,
  "context_strategy": "full_dump",
  "github_enabled": false
}
```

---

## LM STUDIO — VRAM AUTO-DETECT LOGIC

Implement in `backend\llm\vram.py`:

```python
# Priority tiers based on free VRAM (nvidia-smi)
VRAM_MODEL_PRIORITY = [
    {"min_vram_gb": 56, "preferred_contains": ["32b", "70b"], "reason": "Large reasoning model"},
    {"min_vram_gb": 20, "preferred_contains": ["14b", "13b"], "reason": "Mid-range coder"},
    {"min_vram_gb": 8,  "preferred_contains": ["7b", "8b"],   "reason": "Efficient coder"},
]

# Steps:
# 1. Run: nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits
# 2. Parse free VRAM in MB → convert to GB
# 3. GET http://localhost:1234/v1/models → get list of loaded model IDs
# 4. Match loaded models against priority tiers (case-insensitive contains check)
# 5. Return best match — log the selection and reason
# 6. If no match: return first loaded model, log warning
```

---

## THE BUILD LOOP

Implement in `backend\agent\loop.py`. This is the heart of Forge.

```
FUNCTION run_build(project_path, task_description):

  PHASE 1 — AUDIT
    auditor.scan(project_path)
      → Read every file recursively
      → Build file_map: {filename: {purpose, imports, exports, language}}
      → Detect project type (Python/JS/mixed/unknown)
      → Identify missing dependencies, broken imports, syntax errors
      → Generate build_plan: ordered list of actions

  PHASE 2 — BUILD
    FOR each action in build_plan:
      builder.execute(action, file_map, task_description)
        → Call LLM with: full project dump + action instruction
        → LLM returns: file path + new content OR patch instructions
        → patcher.apply(file_path, patch)
        → Emit FILE_CHANGED event → WebSocket → FileDiffs tab
      Install any new dependencies detected

  PHASE 3 — RUN & FIX LOOP
    iteration = 0
    error_history = {}

    WHILE iteration < max_fix_iterations:
      result = runner.run(project_path)

      IF result.success:
        BREAK to PHASE 4

      error_signature = hash(result.error_type + result.error_location)

      IF error_history[error_signature] >= circular_error_threshold:
        # Try alternate strategy
        builder.alternate_fix(result, file_map)
        error_history = {}  # Reset after strategy change
      ELSE:
        error_history[error_signature] += 1
        patch = builder.diagnose_and_fix(result, file_map)
        patcher.apply(patch)

      Emit BUILD_ERROR + FIX_APPLIED events → WebSocket → Terminal tab
      iteration += 1

    IF iteration >= max_fix_iterations:
      Emit BUILD_FAILED event with full error context
      RETURN failure

  PHASE 4 — TEST
    tests = tester.detect(project_path)  # Find pytest/jest/vitest files
    IF tests found:
      test_result = tester.run(project_path)
      IF test_result.failures:
        # Feed failures back into PHASE 3 loop
        GOTO PHASE 3 with test failures as errors

  Emit BUILD_COMPLETE event
  RETURN success
```

---

## LLM PROMPT TEMPLATES

All prompts in `backend\llm\prompts.py`. Key templates:

**AUDIT PROMPT:**
```
You are Forge, an autonomous build agent. Analyze this project completely.

Project files:
{full_file_dump}

Task: {task_description}

Return a JSON build plan:
{
  "project_type": "...",
  "detected_issues": [...],
  "build_plan": [
    {"action": "create|edit|delete", "file": "path", "instruction": "what to do"}
  ]
}
Return JSON only. No explanation.
```

**FIX PROMPT:**
```
You are Forge. A build error occurred. Fix it.

Error:
{error_output}

Relevant files:
{relevant_file_contents}

Return a JSON patch:
{
  "file": "relative/path/to/file",
  "patch_type": "replace_lines|full_rewrite|insert_after",
  "target": "exact string to find (for replace) or line number",
  "replacement": "new content"
}
Return JSON only. No explanation.
```

---

## WEBSOCKET EVENT SCHEMA

Backend emits these events to frontend via WebSocket:

```json
{"event": "BUILD_STARTED",   "project": "name", "timestamp": "..."}
{"event": "FILE_CHANGED",    "file": "path", "diff": "before/after", "timestamp": "..."}
{"event": "BUILD_ERROR",     "error": "...", "iteration": 3, "timestamp": "..."}
{"event": "FIX_APPLIED",     "file": "path", "summary": "...", "timestamp": "..."}
{"event": "TESTS_RUNNING",   "framework": "pytest", "timestamp": "..."}
{"event": "TEST_FAILED",     "test": "name", "error": "...", "timestamp": "..."}
{"event": "BUILD_COMPLETE",  "project": "name", "duration_seconds": 42, "timestamp": "..."}
{"event": "BUILD_FAILED",    "reason": "...", "iterations": 10, "timestamp": "..."}
{"event": "MODEL_SELECTED",  "model": "...", "vram_free_gb": 31, "timestamp": "..."}
```

---

## SPRINT EXECUTION ORDER

Work through these in sequence. Complete each sprint fully before starting the next. Run tests at the end of every sprint.

### Sprint 1 — Backend Foundation
**Goal:** FastAPI server running, LM Studio connected, VRAM detection working

Tasks:
- [ ] Create `backend\requirements.txt` (fastapi, uvicorn, httpx, watchdog, python-dotenv)
- [ ] Create `backend\main.py` — uvicorn server, CORS, WebSocket hub, startup event
- [ ] Create `backend\llm\client.py` — async httpx wrapper for LM Studio `/v1/chat/completions`
- [ ] Create `backend\llm\vram.py` — nvidia-smi VRAM detection + model selector
- [ ] Create `config\forge.config.json` with defaults
- [ ] Create `utils\logger.py` — rotating file logger to `logs\build.log`
- [ ] **Test:** `curl http://localhost:8000/health` returns `{"status":"ok","model":"[selected]","vram_free_gb":[N]}`

### Sprint 2 — Project Auditor
**Goal:** Forge can read any project directory and produce a complete file map

Tasks:
- [ ] Create `agent\auditor.py` — recursive file scanner, language detector, import extractor
- [ ] Create `agent\prompts.py` — AUDIT_PROMPT template
- [ ] Create `api\projects.py` — GET /projects, POST /projects, GET /projects/{name}
- [ ] **Test:** POST /projects/audit with a sample project path → returns complete file_map JSON

### Sprint 3 — Build Loop Core
**Goal:** Full autonomous build loop working end-to-end in the backend

Tasks:
- [ ] Create `agent\builder.py` — LLM call for file generation + fix diagnosis
- [ ] Create `agent\patcher.py` — targeted file patch applier (replace_lines, full_rewrite, insert_after)
- [ ] Create `agent\runner.py` — subprocess executor, exit code + stderr capture
- [ ] Create `agent\loop.py` — full 4-phase build loop per the spec above
- [ ] Create `api\agent.py` — POST /agent/build, WebSocket /agent/events/{project}
- [ ] **Test:** POST /agent/build with a simple "hello world Flask app" prompt → loop runs to clean pass

### Sprint 4 — Test Runner
**Goal:** Forge auto-detects and runs tests, failures feed the fix loop

Tasks:
- [ ] Create `agent\tester.py` — pytest/jest/vitest auto-detector, runner, failure parser
- [ ] Integrate tester into Phase 4 of `loop.py`
- [ ] **Test:** Build a project with intentional test failures → Forge fixes until tests pass

### Sprint 5 — Frontend Shell
**Goal:** React UI running with editor and file explorer

Tasks:
- [ ] Scaffold `frontend\` with Vite + React
- [ ] Install: @monaco-editor/react, xterm, xterm-addon-fit, tailwindcss
- [ ] Create `App.jsx` — three-panel layout (sidebar + editor + preview)
- [ ] Create `FileExplorer.jsx` — file tree from backend /projects/{name}/files
- [ ] Create `Editor.jsx` — Monaco editor, read-only during builds
- [ ] Create `StatusBar.jsx` — model name, VRAM, build status
- [ ] **Test:** `npm run dev` → UI loads, file explorer shows project files, editor renders file content

### Sprint 6 — Live Preview Tabs
**Goal:** All three preview tabs functional

Tasks:
- [ ] Create `PreviewPanel.jsx` with tab switcher
- [ ] Create `AppPreview.jsx` — iframe pointing to running app port, auto-refresh on BUILD_COMPLETE
- [ ] Create `FileDiffs.jsx` — displays FILE_CHANGED events as before/after diffs
- [ ] Create `Terminal.jsx` — xterm.js instance streaming terminal output
- [ ] **Test:** Run a build → all three tabs update in real time

### Sprint 7 — WebSocket Bridge
**Goal:** Backend events stream live to all frontend tabs

Tasks:
- [ ] Create `hooks\useWebSocket.js` — WS connection manager with reconnect
- [ ] Wire FILE_CHANGED → FileDiffs, BUILD_ERROR/FIX_APPLIED → Terminal, BUILD_COMPLETE → AppPreview refresh
- [ ] Backend: emit all events from build loop through WS hub
- [ ] **Test:** Full build from UI → events appear in correct tabs with no lag

### Sprint 8 — Project Dashboard
**Goal:** Full project management screen

Tasks:
- [ ] Create `ProjectDashboard.jsx` — grid of project cards with status badges
- [ ] Create `NewProjectModal.jsx` — prompt input, optional project name, start build button
- [ ] Status colors: Building (yellow), Error (red), Clean (green), Idle (gray)
- [ ] **Test:** Create 3 projects via UI, verify dashboard shows correct status for each

### Sprint 9 — GitHub Integration
**Goal:** Optional per-project GitHub push

Tasks:
- [ ] Create `utils\git.py` — git init, add, commit, push via subprocess
- [ ] Create `api\github.py` — POST /projects/{name}/push (body: repo_url, token)
- [ ] Add GitHub toggle + push button to project settings panel in UI
- [ ] **Test:** Enable GitHub on a clean project → push → verify repo updated

### Sprint 10 — End-to-End Validation
**Goal:** Forge builds a real, non-trivial project flawlessly from a single prompt

Test Project: "Build a Python FastAPI backend with a React frontend. The app tracks labor hours — users can log hours against projects, view totals by project, and export a CSV report."

Success criteria:
- [ ] Backend runs without errors
- [ ] Frontend loads in browser
- [ ] All core features functional
- [ ] Tests pass (if generated)
- [ ] GitHub push works (optional)
- [ ] Full build log captured in `logs\build.log`

---

## WHEN YOU HIT AN ERROR IN YOUR OWN BUILD

If Claude Code itself encounters an error while building Forge:

1. **Do not skip it.** Fix it before moving to the next file.
2. Read the error carefully — identify the exact file and line.
3. Check if a dependency is missing (`pip install X` or `npm install X`).
4. Apply the minimal targeted fix.
5. Re-run the affected test before continuing.
6. Log what was fixed and why in `logs\build.log`.

---

## STARTUP COMMANDS (Windows PowerShell)

```powershell
# Start backend
cd C:\Programs\forge\backend
pip install -r requirements.txt
uvicorn main:app --host localhost --port 8000 --reload

# Start frontend (separate terminal)
cd C:\Programs\forge\frontend
npm install
npm run dev

# Open Forge
start http://localhost:3000
```

---

## CONFIG — SERVER MIGRATION

When Forge moves to a work server, change only `forge.config.json`:

```json
{
  "lm_studio_url": "http://[SERVER_IP]:1234/v1",
  "forge_host": "0.0.0.0",
  "projects_path": "/opt/forge/projects"
}
```

No code changes required.

---

*FORGE — Trendovista Empire Operations*
*Claude Code: read this file first. Follow sprints in order. Do not skip steps.*
