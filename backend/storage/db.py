import sqlite3
import os
import json
import time
import uuid
from backend.config import settings

os.makedirs(os.path.dirname(settings.DB_PATH) or ".", exist_ok=True)
conn = sqlite3.connect(settings.DB_PATH, check_same_thread=False)
cur = conn.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, data TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS kv (k TEXT PRIMARY KEY, v TEXT)")
conn.commit()

def create_job(payload: dict):
    j = {
        "id": uuid.uuid4().hex,
        "project_name": payload["project_name"],
        "stack": payload.get("stack", "python"),
        "spec": payload["spec"],
        "max_iters": payload.get("max_iters") or 3,
        "status": "queued",
        "created": time.time(),
        "report": None,
        "logs": [],  # Real-time build process logs
    }
    cur.execute("INSERT INTO jobs (id, data) VALUES (?, ?)", (j["id"], json.dumps(j)))
    conn.commit()
    return j

def update_job_status(job_id: str, status: str, report: dict | None = None):
    j = get_job(job_id)
    if j is None:
        raise ValueError(f"Job {job_id} not found")
    j["status"] = status
    if report is not None:
        j["report"] = report
    cur.execute("UPDATE jobs SET data=? WHERE id=?", (json.dumps(j), job_id))
    conn.commit()

def get_job(job_id: str):
    row = cur.execute("SELECT data FROM jobs WHERE id=?", (job_id,)).fetchone()
    return json.loads(row[0]) if row else None

def list_jobs():
    rows = cur.execute("SELECT data FROM jobs ORDER BY json_extract(data,'$.created') DESC").fetchall()
    return [json.loads(r[0]) for r in rows]

def set_runtime_provider(provider: str):
    cur.execute("INSERT INTO kv (k,v) VALUES ('provider',?) ON CONFLICT(k) DO UPDATE SET v=excluded.v", (provider,))
    conn.commit()

def get_runtime_provider():
    row = cur.execute("SELECT v FROM kv WHERE k='provider'").fetchone()
    return row[0] if row else None

def append_job_log(job_id: str, log_type: str, content: str | dict):
    """Append a log entry to the job's logs array for real-time visibility"""
    j = get_job(job_id)
    if j is None:
        raise ValueError(f"Job {job_id} not found")
    
    if "logs" not in j:
        j["logs"] = []
    
    log_entry = {
        "timestamp": time.time(),
        "type": log_type,  # 'plan', 'file', 'test', 'output', 'error'
        "content": content
    }
    j["logs"].append(log_entry)
    
    cur.execute("UPDATE jobs SET data=? WHERE id=?", (json.dumps(j), job_id))
    conn.commit()
