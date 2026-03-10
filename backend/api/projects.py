import os
import json
import shutil
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.agent.auditor import scan
from backend.utils.logger import log_action, log_error

router = APIRouter()

# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------
_CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "config",
    "forge.config.json",
)


def _projects_root() -> str:
    try:
        with open(_CONFIG_PATH, "r") as f:
            cfg = json.load(f)
        return cfg.get("projects_path", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "projects"))
    except Exception:
        return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "projects")


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class CreateProjectRequest(BaseModel):
    name: str
    description: str = ""


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.get("")
async def list_projects():
    """List all projects in the projects directory."""
    root = _projects_root()
    os.makedirs(root, exist_ok=True)

    projects = []
    for entry in sorted(os.listdir(root)):
        project_dir = os.path.join(root, entry)
        if not os.path.isdir(project_dir):
            continue
        # Read optional metadata file
        meta_path = os.path.join(project_dir, ".forge_meta.json")
        meta = {}
        if os.path.exists(meta_path):
            try:
                with open(meta_path, "r") as f:
                    meta = json.load(f)
            except Exception:
                pass

        projects.append({
            "name": entry,
            "path": project_dir,
            "description": meta.get("description", ""),
            "created": meta.get("created"),
            "status": meta.get("status", "idle"),
        })

    log_action("projects", f"Listed {len(projects)} project(s)")
    return {"projects": projects}


@router.post("")
async def create_project(req: CreateProjectRequest):
    """Create a new empty project directory."""
    root = _projects_root()
    os.makedirs(root, exist_ok=True)

    # Sanitize project name
    safe_name = req.name.strip().replace(" ", "_").replace("/", "_").replace("\\", "_")
    if not safe_name:
        raise HTTPException(status_code=400, detail="Project name cannot be empty")

    project_dir = os.path.join(root, safe_name)
    if os.path.exists(project_dir):
        raise HTTPException(status_code=409, detail=f"Project '{safe_name}' already exists")

    os.makedirs(project_dir)

    # Write metadata
    meta = {
        "name": safe_name,
        "description": req.description,
        "created": datetime.now(timezone.utc).isoformat(),
        "status": "idle",
    }
    with open(os.path.join(project_dir, ".forge_meta.json"), "w") as f:
        json.dump(meta, f, indent=2)

    log_action("projects", f"Created project '{safe_name}'")
    return {"name": safe_name, "path": project_dir, **meta}


@router.get("/{name}")
async def get_project(name: str):
    """Get details about a specific project."""
    root = _projects_root()
    project_dir = os.path.join(root, name)

    if not os.path.isdir(project_dir):
        raise HTTPException(status_code=404, detail=f"Project '{name}' not found")

    # Read metadata
    meta_path = os.path.join(project_dir, ".forge_meta.json")
    meta = {}
    if os.path.exists(meta_path):
        try:
            with open(meta_path, "r") as f:
                meta = json.load(f)
        except Exception:
            pass

    # Count files
    file_count = sum(1 for _, _, files in os.walk(project_dir) for f in files if not f.startswith("."))

    return {
        "name": name,
        "path": project_dir,
        "description": meta.get("description", ""),
        "created": meta.get("created"),
        "status": meta.get("status", "idle"),
        "file_count": file_count,
    }


@router.delete("/{name}")
async def delete_project(name: str):
    """Delete a project and all its files."""
    root = _projects_root()
    project_dir = os.path.join(root, name)

    if not os.path.isdir(project_dir):
        raise HTTPException(status_code=404, detail=f"Project '{name}' not found")

    # Security: ensure we're within the projects root
    abs_root = os.path.abspath(root)
    abs_project = os.path.abspath(project_dir)
    if not abs_project.startswith(abs_root):
        raise HTTPException(status_code=403, detail="Invalid project path")

    shutil.rmtree(project_dir)
    log_action("projects", f"Deleted project '{name}'")
    return {"deleted": name}


@router.get("/{name}/files")
async def list_project_files(name: str):
    """List all files in a project."""
    root = _projects_root()
    project_dir = os.path.join(root, name)

    if not os.path.isdir(project_dir):
        raise HTTPException(status_code=404, detail=f"Project '{name}' not found")

    files = []
    for dirpath, dirnames, filenames in os.walk(project_dir):
        # Skip hidden and cache dirs
        dirnames[:] = [d for d in dirnames if not d.startswith(".") and d != "__pycache__" and d != "node_modules"]

        for filename in filenames:
            if filename.startswith("."):
                continue
            filepath = os.path.join(dirpath, filename)
            rel_path = os.path.relpath(filepath, project_dir).replace("\\", "/")
            try:
                size = os.path.getsize(filepath)
                files.append({"path": rel_path, "size": size})
            except Exception:
                continue

    return {"files": sorted(files, key=lambda f: f["path"])}


@router.get("/{name}/files/{file_path:path}")
async def read_project_file(name: str, file_path: str):
    """Read a specific file from a project."""
    root = _projects_root()
    project_dir = os.path.join(root, name)

    if not os.path.isdir(project_dir):
        raise HTTPException(status_code=404, detail=f"Project '{name}' not found")

    target = os.path.normpath(os.path.join(project_dir, file_path))

    # Security: ensure within project dir
    if not target.startswith(os.path.normpath(project_dir)):
        raise HTTPException(status_code=403, detail="Access denied")

    if not os.path.isfile(target):
        raise HTTPException(status_code=404, detail=f"File '{file_path}' not found")

    try:
        with open(target, "r", encoding="utf-8") as f:
            content = f.read()
        return {"path": file_path, "content": content, "size": len(content)}
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File is not text-readable")


@router.post("/{name}/audit")
async def audit_project(name: str):
    """Run the auditor against a project and return the full file map."""
    root = _projects_root()
    project_dir = os.path.join(root, name)

    if not os.path.isdir(project_dir):
        raise HTTPException(status_code=404, detail=f"Project '{name}' not found")

    result = scan(project_dir)
    log_action("audit", f"Audited project '{name}'", {"files": result["file_count"], "type": result["project_type"]})
    return result
