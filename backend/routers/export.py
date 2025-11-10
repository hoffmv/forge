import shutil
import zipfile
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from backend.config import settings
import tempfile
import os

router = APIRouter()

@router.get("/{job_id}/zip")
async def export_workspace_zip(job_id: str):
    """
    Export a workspace as a downloadable ZIP file.
    This allows users to download their generated code for deployment elsewhere.
    """
    # Find workspace directory
    workspace_root = Path(settings.WORKSPACE_ROOT)
    workspace_dirs = list(workspace_root.glob(f"*_{job_id[:8]}"))
    
    if not workspace_dirs:
        raise HTTPException(
            status_code=404,
            detail=f"Workspace not found for job {job_id}"
        )
    
    workspace_path = workspace_dirs[0]
    project_name = workspace_path.name.rsplit('_', 1)[0]
    
    # Create temporary ZIP file
    temp_dir = tempfile.gettempdir()
    zip_filename = f"{project_name}.zip"
    zip_path = os.path.join(temp_dir, zip_filename)
    
    # Create ZIP archive
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(workspace_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, workspace_path)
                    zipf.write(file_path, arcname)
        
        return FileResponse(
            path=zip_path,
            media_type='application/zip',
            filename=zip_filename,
            headers={
                "Content-Disposition": f"attachment; filename={zip_filename}"
            }
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create ZIP archive: {str(e)}"
        )

@router.post("/{job_id}/copy")
async def copy_workspace(job_id: str, destination: str):
    """
    Copy workspace to a user-specified directory on the local filesystem.
    Note: This works for desktop app, not web deployment.
    """
    # Find workspace directory
    workspace_root = Path(settings.WORKSPACE_ROOT)
    workspace_dirs = list(workspace_root.glob(f"*_{job_id[:8]}"))
    
    if not workspace_dirs:
        raise HTTPException(
            status_code=404,
            detail=f"Workspace not found for job {job_id}"
        )
    
    workspace_path = workspace_dirs[0]
    dest_path = Path(destination)
    
    try:
        # Validate destination
        if not dest_path.parent.exists():
            raise HTTPException(
                status_code=400,
                detail=f"Destination parent directory does not exist: {dest_path.parent}"
            )
        
        # Copy workspace
        if dest_path.exists():
            shutil.rmtree(dest_path)
        
        shutil.copytree(workspace_path, dest_path)
        
        return {
            "status": "success",
            "source": str(workspace_path),
            "destination": str(dest_path),
            "message": f"Workspace copied to {dest_path}"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to copy workspace: {str(e)}"
        )

@router.get("/{job_id}/path")
async def get_workspace_path(job_id: str):
    """
    Get the filesystem path where a workspace is stored.
    Useful for users to locate their generated code on disk.
    """
    workspace_root = Path(settings.WORKSPACE_ROOT)
    workspace_dirs = list(workspace_root.glob(f"*_{job_id[:8]}"))
    
    if not workspace_dirs:
        raise HTTPException(
            status_code=404,
            detail=f"Workspace not found for job {job_id}"
        )
    
    workspace_path = workspace_dirs[0]
    
    return {
        "job_id": job_id,
        "workspace_path": str(workspace_path.absolute()),
        "workspace_root": str(workspace_root.absolute()),
        "project_name": workspace_path.name.rsplit('_', 1)[0]
    }
