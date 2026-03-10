"""
GitHub push endpoint.
POST /projects/{name}/push — push project to a GitHub repo.
"""
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.utils.git import full_push
from backend.utils.logger import log_action, log_error

router = APIRouter(tags=["github"])


class PushRequest(BaseModel):
    repo_url: str
    token: str | None = None
    commit_message: str = "Forge build"


@router.post("/projects/{name}/push")
async def push_to_github(name: str, body: PushRequest):
    """Push a project to a GitHub repository."""
    from backend.main import load_config
    config = load_config()
    projects_path = config.get("projects_path", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "projects"))

    project_path = os.path.join(projects_path, name)
    if not os.path.isdir(project_path):
        raise HTTPException(status_code=404, detail=f"Project '{name}' not found")

    log_action("github", f"Pushing {name} to {body.repo_url}")

    result = full_push(
        project_path=project_path,
        repo_url=body.repo_url,
        message=body.commit_message,
        token=body.token,
    )

    if not result["success"]:
        log_error("github", "Push failed", result)
        raise HTTPException(status_code=500, detail=result.get("detail", "Push failed"))

    log_action("github", f"Push complete for {name}")
    return {"status": "pushed", "detail": result["detail"]}
