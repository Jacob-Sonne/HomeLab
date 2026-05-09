import asyncio
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

import yt_dlp
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

# ── Config ────────────────────────────────────────────────────────────────────

DOWNLOAD_DIR = Path("/music")

# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(title="yt/pull", description="Homelab YouTube downloader")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def index():
    return FileResponse("/app/app/templates/index.html")


# ── In-memory job store ───────────────────────────────────────────────────────

jobs: dict[str, dict] = {}


# ── Schemas ───────────────────────────────────────────────────────────────────

class DownloadRequest(BaseModel):
    url: str
    title: Optional[str] = None
    start: Optional[str] = None   # e.g. "00:01:30"
    end: Optional[str] = None     # e.g. "00:05:00"
    format: str = "mp4"           # mp4 | mp3 | webm | m4a
    quality: str = "best"         # best | 1080p | 720p | 480p | 360p


# ── Helpers ───────────────────────────────────────────────────────────────────

def hms_to_seconds(hms: str) -> float:
    """Convert HH:MM:SS, MM:SS, or raw seconds string to float seconds."""
    if not hms:
        return 0.0
    parts = [float(p) for p in hms.strip().split(":")]
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    return parts[0]


def build_ydl_opts(job: dict) -> dict:
    fmt = job["format"]
    quality = job["quality"]

    # Format selector
    if fmt in ("mp3", "m4a"):
        ydl_format = "bestaudio/best"
    elif quality == "best":
        ydl_format = "bestvideo+bestaudio/best"
    else:
        height = quality.replace("p", "")
        ydl_format = f"bestvideo[height<={height}]+bestaudio/best[height<={height}]"

    # Output path
    if job.get("title"):
        outtmpl = str(DOWNLOAD_DIR / f"{job['title']}.%(ext)s")
    else:
        outtmpl = str(DOWNLOAD_DIR / "%(title)s.%(ext)s")

    # Post-processors for format conversion
    postprocessors = []
    if fmt == "mp3":
        postprocessors.append({
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        })
    elif fmt == "m4a":
        postprocessors.append({
            "key": "FFmpegExtractAudio",
            "preferredcodec": "m4a",
        })
    elif fmt in ("mp4", "webm"):
        postprocessors.append({
            "key": "FFmpegVideoConvertor",
            "preferedformat": fmt,
        })

    opts: dict = {
        "format": ydl_format,
        "outtmpl": outtmpl,
        "postprocessors": postprocessors,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "writethumbnail": False,
        "progress_hooks": [],  # injected in run_download
    }

    # Native time clipping — requires yt-dlp 2023+ and ffmpeg
    if job.get("start") or job.get("end"):
        from yt_dlp.utils import download_range_func
        start_s = hms_to_seconds(job["start"]) if job.get("start") else None
        end_s   = hms_to_seconds(job["end"])   if job.get("end")   else None
        opts["download_ranges"] = download_range_func(None, [(start_s, end_s)])
        opts["force_keyframes_at_cuts"] = True

    return opts


# ── Background worker ─────────────────────────────────────────────────────────

async def run_download(job_id: str):
    job = jobs[job_id]
    job["status"] = "fetching"

    def progress_hook(d):
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes", 0)
            job["progress"] = round(downloaded / total * 100, 1) if total else 0
            job["status"] = "downloading"
        elif d["status"] == "finished":
            job["progress"] = 100
            job["filepath"] = d.get("filename")

    opts = build_ydl_opts(job)
    opts["progress_hooks"] = [progress_hook]

    loop = asyncio.get_event_loop()

    def _download():
        with yt_dlp.YoutubeDL(opts) as ydl:
            # Fetch metadata first so title/thumbnail populate quickly in the UI
            info = ydl.extract_info(job["url"], download=False)
            if not job["title"]:
                job["title"] = info.get("title", job["url"])
            job["thumbnail"] = info.get("thumbnail")
            ydl.download([job["url"]])

    try:
        await loop.run_in_executor(None, _download)
        job["status"] = "done"
    except Exception as exc:
        job["status"] = "error"
        job["error"] = str(exc)


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "jobs": len(jobs)}


@app.post("/download", status_code=202)
async def create_download(req: DownloadRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    job = {
        "id": job_id,
        "url": req.url,
        "title": req.title,
        "thumbnail": None,
        "status": "waiting",
        "progress": 0.0,
        "format": req.format,
        "quality": req.quality,
        "start": req.start,
        "end": req.end,
        "created_at": datetime.utcnow().isoformat(),
        "filepath": None,
        "error": None,
    }
    jobs[job_id] = job
    background_tasks.add_task(run_download, job_id)
    return job


@app.get("/queue")
def list_queue():
    return sorted(jobs.values(), key=lambda j: j["created_at"], reverse=True)


@app.get("/status/{job_id}")
def get_status(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.delete("/cancel/{job_id}")
def cancel_job(job_id: str):
    job = jobs.pop(job_id, None)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.get("filepath"):
        try:
            Path(job["filepath"]).unlink(missing_ok=True)
        except OSError:
            pass
    return {"cancelled": job_id}


@app.get("/files/{job_id}")
def download_file(job_id: str):
    """Serve the finished file back through the browser."""
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["status"] != "done" or not job.get("filepath"):
        raise HTTPException(status_code=409, detail="File not ready")
    path = Path(job["filepath"])
    if not path.exists():
        raise HTTPException(status_code=410, detail="File no longer on disk")
    return FileResponse(path, filename=path.name)