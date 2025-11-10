import time
import traceback
from backend.storage.db import list_jobs, update_job_status
from backend.services.orchestrator import run_build

def enqueue(job_id: str):
    pass

def main_loop():
    while True:
        try:
            for j in list_jobs():
                if j["status"] == "queued":
                    update_job_status(j["id"], "running")
                    try:
                        run_build(j)
                    except Exception as e:
                        print(f"Error processing job {j['id']}: {e}")
                        traceback.print_exc()
                        update_job_status(j["id"], "failed", {"error": str(e)})
        except Exception as e:
            print(f"Error in worker loop: {e}")
            traceback.print_exc()
        time.sleep(1)

if __name__ == "__main__":
    main_loop()
