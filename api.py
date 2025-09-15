import queue
import threading
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, JSONResponse

from pipeline.run import run_pipeline

BASE_JOBS_DIR = Path(__file__).parent / "jobs"
BASE_JOBS_DIR.mkdir(parents=True, exist_ok=True)

# ======================================================================================================================
# Jobs + Worker
# ======================================================================================================================

Job = Dict[str, Any]
JOBS: Dict[str, Job] = {}
JOB_QUEUE: "queue.Queue[str]" = queue.Queue()
JOBS_LOCK = threading.Lock()


def job_worker():
    while True:
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
                od_clusters_a=Path(job.get("od_clusters_a")),
                od_clusters_b=Path(job.get("od_clusters_b")),
                od_table=Path(job.get("od_table")),
                stops=Path(job.get("stops")),

                od_clusters_a_id_field=job.get("od_clusters_a_id_field"),
                od_clusters_a_count_field=job.get("od_clusters_a_count_field"),
                od_clusters_b_id_field=job.get("od_clusters_b_id_field"),
                od_clusters_b_count_field=job.get("od_clusters_b_count_field"),
                od_table_a_id_field=job.get("od_table_a_id_field"),
                od_table_b_id_field=job.get("od_table_b_id_field"),
                od_table_trips_field=job.get("od_table_trips_field"),

                netascore_gpkg=Path(job.get("netascore_gpkg")) if job.get("netascore_gpkg") else None,
                seed=job.get("seed"),

                job_dir=Path(job.get("job_dir")),
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
        od_clusters_a: UploadFile = File(...),
        od_clusters_b: UploadFile = File(...),
        od_table: UploadFile = File(...),
        stops: UploadFile = File(...),

        od_clusters_a_id_field: str = Form(...),
        od_clusters_a_count_field: str = Form(...),
        od_clusters_b_id_field: str = Form(...),
        od_clusters_b_count_field: str = Form(...),
        od_table_a_id_field: str = Form(...),
        od_table_b_id_field: str = Form(...),
        od_table_trips_field: str = Form(...),

        netascore_gpkg: Optional[UploadFile] = File(None),
        seed: Optional[int] = Form(None),
):
    job_id = str(uuid.uuid4())
    job_dir = (BASE_JOBS_DIR / job_id)
    job_dir.mkdir(parents=True, exist_ok=True)

    od_clusters_a_path = job_dir / f"od_clusters_a{Path(od_clusters_a.filename).suffix}"
    od_clusters_a_path.write_bytes(await od_clusters_a.read())

    od_clusters_b_path = job_dir / f"od_clusters_b{Path(od_clusters_b.filename).suffix}"
    od_clusters_b_path.write_bytes(await od_clusters_b.read())

    od_table_path = job_dir / f"od_table{Path(od_table.filename).suffix}"
    od_table_path.write_bytes(await od_table.read())

    stops_path = job_dir / f"stops{Path(stops.filename).suffix}"
    stops_path.write_bytes(await stops.read())

    netascore_gpkg_path = None
    if netascore_gpkg:
        netascore_gpkg_path = job_dir / f"netascore{Path(netascore_gpkg.filename).suffix}"
        netascore_gpkg_path.write_bytes(await netascore_gpkg.read())

    job = {
        "id": job_id,
        "status": "queued",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "job_dir": str(job_dir),

        "od_clusters_a": str(od_clusters_a_path),
        "od_clusters_b": str(od_clusters_b_path),
        "od_table": str(od_table_path),
        "stops": str(stops_path),

        "od_clusters_a_id_field": od_clusters_a_id_field,
        "od_clusters_a_count_field": od_clusters_a_count_field,
        "od_clusters_b_id_field": od_clusters_b_id_field,
        "od_clusters_b_count_field": od_clusters_b_count_field,
        "od_table_a_id_field": od_table_a_id_field,
        "od_table_b_id_field": od_table_b_id_field,
        "od_table_trips_field": od_table_trips_field,

        "netascore_gpkg": str(netascore_gpkg_path) if netascore_gpkg_path else None,
        "seed": seed,
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
