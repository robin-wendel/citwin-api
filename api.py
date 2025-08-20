import queue
import threading
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse

from pipeline import run_pipeline

NETASCORE_DIR = Path("/Users/robinwendel/Developer/mobility-lab/netascore")
BASE_JOBS_DIR = Path("./jobs")
BASE_JOBS_DIR.mkdir(parents=True, exist_ok=True)

# ======================================================================================================================
# worker + job queue
# ======================================================================================================================

Job = Dict[str, Any]
JOBS: Dict[str, Job] = {}
JOB_QUEUE: "queue.Queue[str]" = queue.Queue()
JOBS_LOCK = threading.Lock()
STOP_EVENT = threading.Event()

def worker_loop():
    while not STOP_EVENT.is_set():
        try:
            job_id = JOB_QUEUE.get(timeout=0.5)
        except queue.Empty:
            continue

        with JOBS_LOCK:
            job = JOBS.get(job_id)
            if not job:
                continue
            job["status"] = "running"
            job["started_at"] = datetime.now(timezone.utc).isoformat()

        try:
            out_path = run_pipeline(
                vector_path=Path(job["input_vector"]),
                netascore_dir=NETASCORE_DIR,
                job_dir=Path(job["job_dir"]),
                target_srid=int(job["target_srid"]),
            )
            with JOBS_LOCK:
                job["status"] = "done"
                job["output_file"] = str(out_path.resolve())
                job["finished_at"] = datetime.now(timezone.utc).isoformat()
        except Exception as e:
            with JOBS_LOCK:
                job["status"] = "failed"
                job["error"] = str(e)
                job["traceback"] = traceback.format_exc()
                job["finished_at"] = datetime.now(timezone.utc).isoformat()
        finally:
            JOB_QUEUE.task_done()

WORKER_THREAD = threading.Thread(target=worker_loop, daemon=True)
WORKER_THREAD.start()

# ======================================================================================================================
# FastAPI
# ======================================================================================================================

app = FastAPI()
app.add_middleware(GZipMiddleware, minimum_size=1000)

@app.post("/jobs")
def create_job(file: UploadFile = File(...), target_srid: int = Form(...)):
    job_id = str(uuid.uuid4())
    job_dir = BASE_JOBS_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    input_path = job_dir / (file.filename or "input.gpkg")
    with input_path.open("wb") as f:
        f.write(file.file.read())

    job: Job = {
        "id": job_id,
        "status": "queued",
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "job_dir": str(job_dir),
        "input_vector": str(input_path),
        "target_srid": target_srid,
    }

    with JOBS_LOCK:
        JOBS[job_id] = job
    JOB_QUEUE.put(job_id)

    return {"job_id": job_id, "status": "queued"}

@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    with JOBS_LOCK:
        job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return {k: v for k, v in job.items() if k != "traceback"}

@app.get("/jobs/{job_id}/download")
def download_result(job_id: str):
    with JOBS_LOCK:
        job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    if job.get("status") != "done":
        raise HTTPException(status_code=409, detail=f"job not finished (status={job.get('status')})")
    out_path = Path(job["output_file"])
    if not out_path.exists():
        raise HTTPException(status_code=500, detail="output file missing")
    return FileResponse(out_path, filename=out_path.name, media_type="application/geo+json")
