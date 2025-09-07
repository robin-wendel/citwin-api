import queue
import threading
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, JSONResponse

from pipeline import run_pipeline

# NETASCORE_DIR = Path("/Users/robinwendel/Developer/mobility-lab/netascore")
NETASCORE_FILE = Path("./data/netascore.gpkg")
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

def job_worker():
    while not STOP_EVENT.is_set():
        try:
            job_id = JOB_QUEUE.get(timeout=0.5)
        except queue.Empty:
            continue

        with JOBS_LOCK:
            job = JOBS.get(job_id)
            if not job:
                JOB_QUEUE.task_done()
                continue
            job["status"] = "running"
            job["started_at"] = datetime.now(timezone.utc).isoformat()

        try:
            outputs = run_pipeline(
                od_cluster_a=Path(job["od_cluster_a"]),
                od_cluster_b=Path(job["od_cluster_b"]),
                od_table=Path(job["od_table"]),
                stops=Path(job["stops"]),
                job_dir=Path(job["job_dir"]),
                target_srid=int(job["target_srid"]),
                # netascore_dir=NETASCORE_DIR,
                netascore_file=NETASCORE_FILE,
            )
            with JOBS_LOCK:
                job["status"] = "done"
                job["outputs"] = {k: str(v) for k, v in outputs.items()}
                job["finished_at"] = datetime.now(timezone.utc).isoformat()
        except Exception as e:
            with JOBS_LOCK:
                job["status"] = "failed"
                job["error"] = str(e)
                job["traceback"] = traceback.format_exc()
                job["finished_at"] = datetime.now(timezone.utc).isoformat()
        finally:
            JOB_QUEUE.task_done()

WORKER_THREAD = threading.Thread(target=job_worker, daemon=True)
WORKER_THREAD.start()

# ======================================================================================================================
# FastAPI
# ======================================================================================================================

app = FastAPI()
app.add_middleware(GZipMiddleware, minimum_size=1000)

@app.post("/jobs")
async def create_job(
    od_cluster_a: UploadFile = File(...),
    od_cluster_b: UploadFile = File(...),
    od_table: UploadFile = File(...),
    stops: UploadFile = File(...),
    target_srid: int = Form(...),
):
    job_id = str(uuid.uuid4())
    job_dir = (BASE_JOBS_DIR / job_id)
    job_dir.mkdir(parents=True, exist_ok=True)

    a_path = job_dir / f"a_{od_cluster_a.filename}"
    a_path.write_bytes(await od_cluster_a.read())

    b_path = job_dir / f"b_{od_cluster_b.filename}"
    b_path.write_bytes(await od_cluster_b.read())

    t_path = job_dir / f"t_{od_table.filename}"
    t_path.write_bytes(await od_table.read())

    s_path = job_dir / f"s_{stops.filename}"
    s_path.write_bytes(await stops.read())

    job = {
        "id": job_id,
        "status": "queued",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "job_dir": str(job_dir),
        "od_cluster_a": str(a_path),
        "od_cluster_b": str(b_path),
        "od_table": str(t_path),
        "stops": str(s_path),
        "target_srid": int(target_srid),
    }

    with JOBS_LOCK:
        JOBS[job_id] = job
    JOB_QUEUE.put(job_id)

    return {"job_id": job_id, "status": job["status"]}

@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    with JOBS_LOCK:
        job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return {k: v for k, v in job.items() if k != "traceback"}

@app.get("/jobs/{job_id}/downloads")
def list_downloads(job_id: str):
    with JOBS_LOCK:
        job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    if job.get("status") != "done":
        raise HTTPException(status_code=409, detail=f"job not finished (status={job.get('status')})")

    outputs: dict[str, str] = job.get("outputs") or {}
    result = []
    for key, path_str in outputs.items():
        p = Path(path_str)
        if p.exists():
            result.append({
                "key": key,
                "filename": p.name,
                "download_url": f"/jobs/{job_id}/download/{key}",
            })

    return JSONResponse(result)

@app.get("/jobs/{job_id}/download/{key}")
def download_output(job_id: str, key: str):
    with JOBS_LOCK:
        job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    if job.get("status") != "done":
        raise HTTPException(status_code=409, detail=f"job not finished (status={job.get('status')})")

    outputs: dict[str, str] = job.get("outputs") or {}
    path_str = outputs.get(key)
    if not path_str:
        raise HTTPException(status_code=404, detail=f"key not found")

    out_path = Path(path_str)
    if not out_path.exists():
        raise HTTPException(status_code=500, detail="file not found")

    return FileResponse(out_path, filename=out_path.name)
