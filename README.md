# FORGE

Local AI-powered development environment. Combines a visual workbench UI with an autonomous build agent that generates, runs, and fixes code using a local LLM via LM Studio.

No external APIs. No cloud dependencies. Everything runs on your machine.

## Quick Start (Windows PowerShell)

```powershell
# 1. Start LM Studio and load a model (e.g. qwen2.5-32b-instruct)

# 2. Start the backend
cd C:\Programs\forge
pip install -r backend\requirements.txt
python -m uvicorn backend.main:app --host localhost --port 8000

# 3. Start the frontend (separate terminal)
cd C:\Programs\forge\frontend
npm install
npm run dev

# 4. Open Forge
start http://localhost:3000
```

## How It Works

Forge runs a 4-phase build loop against your local LLM:

1. **Audit** -- Scans every file in the project, detects languages, imports, and issues
2. **Build** -- Sends the project + task description to the LLM, generates or edits files
3. **Run & Fix** -- Executes the project, captures errors, sends them back to the LLM for patches. Repeats until clean or max iterations reached. Detects circular errors and switches strategy automatically.
4. **Test** -- Auto-detects pytest/jest/vitest, runs tests, feeds failures back into the fix loop

All events stream to the UI in real time via WebSocket.

## Configuration

All settings live in `config\forge.config.json`:

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

### Key Settings

| Setting | Description |
|---------|-------------|
| `lm_studio_url` | LM Studio API endpoint. Change this when deploying to a server. |
| `model_selection` | `"auto"` uses VRAM-based tier matching. Set to `"manual"` and use `model_override` to pin a specific model. |
| `model_override` | Exact model ID string when `model_selection` is `"manual"`. |
| `max_fix_iterations` | How many times the fix loop retries before giving up. Default: 10. |
| `circular_error_threshold` | After seeing the same error N times, switch to an alternate fix strategy. Default: 3. |
| `projects_path` | Where built projects are stored. |

## Server Deployment

To run Forge against an LM Studio instance on a different machine, change only the config:

```json
{
  "lm_studio_url": "http://192.168.1.100:1234/v1",
  "forge_host": "0.0.0.0"
}
```

No code changes required.

## VRAM Auto-Detection

Forge queries `nvidia-smi` for total GPU VRAM and selects the best loaded model:

| Total VRAM | Preferred Models | Tier |
|------------|-----------------|------|
| 48+ GB | 70B | Large reasoning model |
| 24+ GB | 32B, 30B | Full-size coder |
| 16+ GB | 14B, 13B, 20B | Mid-range coder |
| 8+ GB | 7B, 8B | Efficient coder |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Server status, model, VRAM info |
| GET | `/projects` | List all projects |
| POST | `/projects` | Create a new project |
| DELETE | `/projects/{name}` | Delete a project |
| GET | `/projects/{name}/files` | List project files |
| GET | `/projects/{name}/files/{path}` | Read a file |
| POST | `/projects/{name}/audit` | Run the auditor |
| POST | `/agent/build` | Start an autonomous build |
| GET | `/agent/build/{project}/status` | Check build status |
| POST | `/projects/{name}/push` | Push to GitHub |
| WS | `/agent/events/{project}` | Live build event stream |

## Project Structure

```
forge/
├── backend/          FastAPI server + build agent
│   ├── main.py       Entry point, WebSocket hub
│   ├── api/          REST endpoints
│   ├── agent/        Build loop, auditor, builder, patcher, runner, tester
│   ├── llm/          LM Studio client, VRAM detection, prompt templates
│   └── utils/        Logger, git wrapper
├── frontend/         React + Vite UI
│   └── src/
│       ├── components/   FileExplorer, Editor, PreviewPanel, Dashboard
│       └── hooks/        useWebSocket, useProject
├── config/           forge.config.json
├── logs/             build.log (rotating)
└── projects/         Built projects live here
```
