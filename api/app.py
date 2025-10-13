import asyncio
import hmac
import queue
import shutil
import threading
import time
import traceback
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, Depends, File, Form, Request, Security, UploadFile, WebSocket
from fastapi.exceptions import HTTPException
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel, Field, RootModel

from api.config import settings
from api.paths import JOBS_DIR
from pipeline.run import run_pipeline, setup_logging

# ----------------------------------------------------------------------------------------------------------------------
# security
# ----------------------------------------------------------------------------------------------------------------------

API_KEY = settings.api_key

api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)):
    if not api_key or not hmac.compare_digest(api_key, API_KEY):
        raise HTTPException(status_code=403, detail="Unauthorized: Invalid API key")

# ----------------------------------------------------------------------------------------------------------------------
# models
# ----------------------------------------------------------------------------------------------------------------------

class OutputFormat(str, Enum):
    geojson = "GeoJSON"
    gpkg = "GPKG"


class JobCreateOut(BaseModel):
    job_id: str = Field(..., description="Unique job ID", examples=["550e8400-e29b-41d4-a716-446655440000"])
    status: str = Field(..., description="Initial job status", examples=["queued"])
    websocket_url: str = Field(..., description="WebSocket URL to monitor job completion", examples=["wss://api.example.com/ws/550e8400-e29b-41d4-a716-446655440000"])


class JobStatusOut(BaseModel):
    job_id: str = Field(..., description="Unique job ID", examples=["550e8400-e29b-41d4-a716-446655440000"])
    status: str = Field(..., description="Job status", examples=["running", "done", "failed"])
    step: Optional[str] = Field(None, description="Current processing step", examples=["1/10"])
    created_at: Optional[str] = Field(None, description="ISO 8601 creation time", examples=["2025-10-13T12:46:57"])
    started_at: Optional[str] = Field(None, description="ISO 8601 start time", examples=["2025-10-13T12:46:57Z"])
    finished_at: Optional[str] = Field(None, description="ISO 8601 finish time", examples=["2025-10-13T12:47:58Z"])
    error: Optional[str] = Field(None, description="Error message if failed")


class JobDownloadItem(BaseModel):
    key: str = Field(..., example="result")
    filename: str = Field(..., example="result.geojson")
    download_url: str = Field(..., example="/jobs/550e8400-e29b-41d4-a716-446655440000/download/result")


class JobDownloadsOut(RootModel[list[JobDownloadItem]]):
    pass

# ----------------------------------------------------------------------------------------------------------------------
# utilities
# ----------------------------------------------------------------------------------------------------------------------

def check_extension(upload: UploadFile, expected: set[str]):
    suffix = Path(upload.filename).suffix.lower()
    if suffix not in expected:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {suffix or 'none'}, allowed: {', '.join(sorted(expected))}")
    return suffix

# ----------------------------------------------------------------------------------------------------------------------
# logging
# ----------------------------------------------------------------------------------------------------------------------

logger = setup_logging()

# ----------------------------------------------------------------------------------------------------------------------
# jobs (worker / queue)
# ----------------------------------------------------------------------------------------------------------------------

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
            job["started_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        def progress_callback(step_message: str):
            with JOBS_LOCK:
                job["step"] = step_message

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
                stops_id_field=job.get("stops_id_field"),

                netascore_gpkg=Path(job.get("netascore_gpkg")) if job.get("netascore_gpkg") else None,
                output_format=job.get("output_format"),
                seed=job.get("seed"),

                job_dir=Path(job.get("job_dir")),

                progress_callback=progress_callback
            )
            with JOBS_LOCK:
                job["status"] = "done"
                job["step"] = None
                job["outputs"] = {k: str(v) for k, v in outputs.items()}
                job["finished_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        except Exception as e:
            with JOBS_LOCK:
                job["status"] = "failed"
                job["error"] = str(e)
                job["traceback"] = traceback.format_exc()
                job["finished_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        finally:
            JOB_QUEUE.task_done()

# ----------------------------------------------------------------------------------------------------------------------
# cleaner
# ----------------------------------------------------------------------------------------------------------------------

def delete_old_jobs():
    now = datetime.now(timezone.utc)
    for job_dir in JOBS_DIR.iterdir():
        if job_dir.is_dir():
            created_at = datetime.fromtimestamp(job_dir.stat().st_ctime, tz=timezone.utc)
            if (now - created_at).total_seconds() > 24 * 3600:
                shutil.rmtree(job_dir, ignore_errors=True)


def delete_old_jobs_periodically():
    delete_old_jobs()
    while not STOP_EVENT.is_set():
        time.sleep(3600)
        now = datetime.now(timezone.utc)
        with JOBS_LOCK:
            for job_id, job in list(JOBS.items()):
                created_at = datetime.fromisoformat(job["created_at"])
                if (now - created_at).total_seconds() > 24 * 3600:
                    shutil.rmtree(Path(job["job_dir"]), ignore_errors=True)
                    JOBS.pop(job_id, None)

# ----------------------------------------------------------------------------------------------------------------------
# worker + cleaner startup
# ----------------------------------------------------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(_app: FastAPI):
    worker_thread = threading.Thread(target=job_worker, daemon=True)
    cleaner_thread = threading.Thread(target=delete_old_jobs_periodically, daemon=True)

    worker_thread.start()
    cleaner_thread.start()

    yield

    STOP_EVENT.set()

    worker_thread.join(timeout=5)
    cleaner_thread.join(timeout=5)

# ----------------------------------------------------------------------------------------------------------------------
# fastapi
# ----------------------------------------------------------------------------------------------------------------------

app = FastAPI(
    title="CITWIN API",
    version="0.2.0",
    root_path=settings.api_root_path,
    lifespan=lifespan,
    redoc_url=None,
    swagger_ui_parameters={
        "defaultModelsExpandDepth": -1,
        "tryItOutEnabled": True,
    }
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# ----------------------------------------------------------------------------------------------------------------------

@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/jobs", response_model=JobCreateOut, dependencies=[Depends(verify_api_key)])
async def create_job(
        request: Request,

        od_clusters_a: UploadFile = File(..., description="Origin clusters file", examples=["b_klynger.gpkg"]),
        od_clusters_b: UploadFile = File(..., description="Destination clusters file", examples=["a_klynger.gpkg"]),
        od_table: UploadFile = File(..., description="Origin-destination table file", examples=["Data_2023_0099_Tabel_1.csv"]),
        stops: UploadFile = File(..., description="Public transport stops file", examples=["dynlayer.gpkg"]),

        od_clusters_a_id_field: str = Form(..., description="ID field for origin clusters", examples=["klynge_id"]),
        od_clusters_a_count_field: str = Form(..., description="Count field for origin clusters", examples=["Beboere"]),
        od_clusters_b_id_field: str = Form(..., description="ID field for destination clusters", examples=["klynge_id"]),
        od_clusters_b_count_field: str = Form(..., description="Count field for destination clusters", examples=["Arbejdere"]),
        od_table_a_id_field: str = Form(..., description="ID field for origin clusters in origin-destination table", examples=["Bopael_klynge_id"]),
        od_table_b_id_field: str = Form(..., description="ID field for destination clusters in origin-destination table", examples=["Arbejssted_klynge_id"]),
        od_table_trips_field: str = Form(..., description="Trips field in origin-destination table", examples=["Antal"]),
        stops_id_field: str = Form(..., description="ID field for public transport stops", examples=["stopnummer"]),

        netascore_gpkg: Optional[UploadFile] = File(None, description="Pre-generated netascore file"),
        output_format: Optional[OutputFormat] = Form(OutputFormat.geojson, description="Output format"),
        seed: Optional[int] = Form(None, description="Random seed for reproducibility of results"),
) -> JobCreateOut:
    job_id = str(uuid.uuid4())
    job_dir = (JOBS_DIR / job_id)
    job_dir.mkdir(parents=True, exist_ok=True)

    check_extension(od_clusters_a, {".geojson", ".gpkg"})
    check_extension(od_clusters_b, {".geojson", ".gpkg"})
    check_extension(od_table, {".csv"})
    check_extension(stops, {".geojson", ".gpkg"})
    if netascore_gpkg:
        check_extension(netascore_gpkg, {".gpkg"})

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
        "job_id": job_id,
        "status": "queued",
        "step": None,
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
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
        "stops_id_field": stops_id_field,

        "netascore_gpkg": str(netascore_gpkg_path) if netascore_gpkg_path else None,
        "output_format": output_format,
        "seed": seed,
    }

    with JOBS_LOCK:
        JOBS[job_id] = job
    JOB_QUEUE.put(job_id)

    base_url = str(request.base_url).rstrip("/")
    root_path = request.scope.get("root_path", "").rstrip("/")
    websocket_url = f"{base_url}{root_path}/ws/{job_id}".replace("http", "ws")

    return JobCreateOut(job_id=job_id, status=job["status"], websocket_url=websocket_url)


@app.get("/jobs/{job_id}", response_model=JobStatusOut, response_model_exclude_none=True, dependencies=[Depends(verify_api_key)])
def get_job_status(job_id: str) -> JobStatusOut:
    with JOBS_LOCK:
        job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatusOut(**job)


@app.get("/jobs/{job_id}/downloads", response_model=JobDownloadsOut, dependencies=[Depends(verify_api_key)])
def get_job_downloads(job_id: str) -> JobDownloadsOut:
    with JOBS_LOCK:
        job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.get("status") != "done":
        raise HTTPException(status_code=409, detail=f"Job not finished (status={job.get('status')})")

    outputs = job.get("outputs") or {}
    downloads = [
        JobDownloadItem(
            key=key,
            filename=Path(path).name,
            download_url=f"/jobs/{job_id}/download/{key}",
        )
        for key, path in outputs.items()
        if Path(path).exists()
    ]

    return JobDownloadsOut(root=downloads)


@app.get("/jobs/{job_id}/download/{key}", dependencies=[Depends(verify_api_key)])
def download_output(job_id: str, key: str) -> FileResponse:
    with JOBS_LOCK:
        job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.get("status") != "done":
        raise HTTPException(status_code=409, detail=f"Job not finished (status={job.get('status')})")

    outputs: dict[str, str] = job.get("outputs") or {}
    path_str = outputs.get(key)
    if not path_str:
        raise HTTPException(status_code=404, detail=f"Key not found")

    out_path = Path(path_str)
    if not out_path.exists():
        raise HTTPException(status_code=500, detail="File not found")

    return FileResponse(out_path, filename=out_path.name)


@app.websocket("/ws/{job_id}")
async def ws_job_done(websocket: WebSocket, job_id: str):
    await websocket.accept()
    try:
        while True:
            with JOBS_LOCK:
                job = JOBS.get(job_id)
                if job and job["status"] in {"done", "failed"}:
                    break
            await asyncio.sleep(1)

        await websocket.send_json(JobStatusOut(**job).model_dump(exclude_none=True))
    finally:
        await websocket.close()
