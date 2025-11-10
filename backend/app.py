import threading
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import health, jobs, settings, workspace, projects, upload, export
from backend.worker.queue_worker import main_loop

worker_thread = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global worker_thread
    worker_thread = threading.Thread(target=main_loop, daemon=True)
    worker_thread.start()
    yield
    
app = FastAPI(title="FORGE", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware, 
    allow_origins=["*"], 
    allow_methods=["*"], 
    allow_headers=["*"]
)
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
app.include_router(settings.router, prefix="/settings", tags=["settings"])
app.include_router(workspace.router, prefix="/workspace", tags=["workspace"])
app.include_router(projects.router, prefix="/projects", tags=["projects"])
app.include_router(upload.router, prefix="/upload", tags=["upload"])
app.include_router(export.router, prefix="/export", tags=["export"])
