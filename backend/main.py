import json
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from backend.llm.client import close_client
from backend.llm.vram import select_model
from backend.utils.logger import log, log_action, log_sprint
from backend.api.projects import router as projects_router
from backend.api.agent import router as agent_router
from backend.api.github import router as github_router

# ---------------------------------------------------------------------------
# Load forge config
# ---------------------------------------------------------------------------
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "forge.config.json")

def load_config() -> dict:
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    # Return defaults if config missing
    return {
        "lm_studio_url": "http://localhost:1234/v1",
        "forge_host": "localhost",
        "forge_port": 8000,
        "frontend_port": 3000,
        "projects_path": os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "projects"),
        "logs_path": os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs"),
        "model_selection": "auto",
        "model_override": None,
        "max_fix_iterations": 10,
        "circular_error_threshold": 3,
        "context_strategy": "full_dump",
        "github_enabled": False,
    }

forge_config = load_config()

# ---------------------------------------------------------------------------
# WebSocket connection manager
# ---------------------------------------------------------------------------
class ConnectionManager:
    """Manages WebSocket connections per project."""

    def __init__(self):
        self.active: dict[str, list[WebSocket]] = {}

    async def connect(self, project: str, ws: WebSocket):
        await ws.accept()
        self.active.setdefault(project, []).append(ws)
        log_action("ws_connect", f"Client connected to project '{project}'")

    def disconnect(self, project: str, ws: WebSocket):
        if project in self.active:
            self.active[project] = [c for c in self.active[project] if c is not ws]
            if not self.active[project]:
                del self.active[project]
        log_action("ws_disconnect", f"Client disconnected from project '{project}'")

    async def broadcast(self, project: str, event: dict):
        """Broadcast an event dict to all clients listening to a project."""
        event.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
        payload = json.dumps(event)
        dead: list[WebSocket] = []
        for ws in self.active.get(project, []):
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(project, ws)

manager = ConnectionManager()

# ---------------------------------------------------------------------------
# Startup state
# ---------------------------------------------------------------------------
_startup_info: dict = {}

# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    log_sprint(1, "Backend server starting")

    # Ensure projects directory exists
    os.makedirs(forge_config["projects_path"], exist_ok=True)

    # Select model on startup
    model_info = select_model(forge_config["lm_studio_url"])
    _startup_info.update(model_info)

    if model_info["model"]:
        await manager.broadcast("__system__", {
            "event": "MODEL_SELECTED",
            "model": model_info["model"],
            "total_vram_gb": model_info["total_vram_gb"],
            "vram_free_gb": model_info["vram_free_gb"],
        })

    log_action("startup", "Forge backend ready", {
        "host": forge_config["forge_host"],
        "port": forge_config["forge_port"],
        "model": model_info["model"],
        "total_vram_gb": model_info["total_vram_gb"],
        "vram_free_gb": model_info["vram_free_gb"],
    })

    yield

    # Shutdown
    await close_client()
    log_action("shutdown", "Forge backend stopped")

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(title="FORGE", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(projects_router, prefix="/projects", tags=["projects"])
app.include_router(agent_router, prefix="/agent", tags=["agent"])
app.include_router(github_router, tags=["github"])

# ---------------------------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------------------------
@app.get("/health")
async def health():
    return {
        "status": "ok",
        "model": _startup_info.get("model"),
        "total_vram_gb": _startup_info.get("total_vram_gb"),
        "vram_free_gb": _startup_info.get("vram_free_gb"),
    }

# ---------------------------------------------------------------------------
# WebSocket endpoint for build events
# ---------------------------------------------------------------------------
@app.websocket("/agent/events/{project}")
async def agent_events(ws: WebSocket, project: str):
    await manager.connect(project, ws)
    try:
        while True:
            # Keep connection alive; clients only receive broadcasts
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(project, ws)

# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host=forge_config["forge_host"],
        port=forge_config["forge_port"],
        reload=True,
    )
