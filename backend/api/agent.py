"""
REST + WebSocket endpoints for the build agent.
"""
import asyncio
import json
import os
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from backend.agent.loop import run_build
from backend.utils.logger import log_action, log_error

router = APIRouter()

# ---------------------------------------------------------------------------
# Config helper
# ---------------------------------------------------------------------------
_CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "config",
    "forge.config.json",
)


def _load_config() -> dict:
    try:
        with open(_CONFIG_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return {
            "lm_studio_url": "http://localhost:1234/v1",
            "projects_path": os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "projects"),
            "max_fix_iterations": 10,
            "circular_error_threshold": 3,
        }


# ---------------------------------------------------------------------------
# In-memory build state
# ---------------------------------------------------------------------------
_active_builds: dict[str, dict] = {}


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class BuildRequest(BaseModel):
    project: str
    task: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.post("/build")
async def start_build(req: BuildRequest):
    """
    Start an autonomous build for a project.
    The build runs asynchronously — connect to the WebSocket to stream events.
    """
    config = _load_config()
    projects_root = config.get("projects_path", "")
    project_path = os.path.join(projects_root, req.project)

    # Create project dir if it doesn't exist
    os.makedirs(project_path, exist_ok=True)

    if req.project in _active_builds and _active_builds[req.project].get("running"):
        raise HTTPException(status_code=409, detail=f"Build already running for '{req.project}'")

    # Store active model from startup info
    from backend.main import _startup_info
    config["_active_model"] = _startup_info.get("model")

    # Get the broadcast function from the connection manager
    from backend.main import manager

    async def broadcast(event: dict):
        await manager.broadcast(req.project, event)

    _active_builds[req.project] = {"running": True, "started": datetime.now(timezone.utc).isoformat()}

    # Run build in background task
    async def _run():
        try:
            result = await run_build(
                project_path=project_path,
                task_description=req.task,
                config=config,
                broadcast=broadcast,
            )
            _active_builds[req.project] = {"running": False, "result": result}
        except Exception as e:
            log_error("agent_api", f"Build failed: {e}")
            _active_builds[req.project] = {"running": False, "result": {"success": False, "detail": str(e)}}
            await broadcast({
                "event": "BUILD_FAILED",
                "reason": str(e),
                "iterations": 0,
            })

    asyncio.create_task(_run())

    log_action("agent_api", f"Build started for project '{req.project}'")
    return {
        "status": "started",
        "project": req.project,
        "message": f"Build started. Connect to WebSocket /agent/events/{req.project} for live events.",
    }


@router.get("/build/{project}/status")
async def build_status(project: str):
    """Get the current build status for a project."""
    info = _active_builds.get(project)
    if not info:
        return {"project": project, "status": "idle"}

    if info.get("running"):
        return {"project": project, "status": "running", "started": info.get("started")}

    return {
        "project": project,
        "status": "completed" if info.get("result", {}).get("success") else "failed",
        "result": info.get("result"),
    }
