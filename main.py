"""FastAPI entrypoint for the Browser Automation AI Agent."""

from __future__ import annotations

import logging
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, HttpUrl

from config import get_settings
from orchestrator.graph import run_pipeline
from storage.redis_store import RunStore
from storage.report_index import list_reports, load_report

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

run_store = RunStore()


class RunRequest(BaseModel):
    url: HttpUrl
    intent: str = Field(min_length=1, examples=["Test checkout flow"])
    openrouter_api_key: str | None = None
    openrouter_model: str | None = None
    use_mock_llm: bool | None = None
    max_retries: int | None = None
    max_repair_before_regenerate: int | None = None


class RunResponse(BaseModel):
    run_id: str
    status: str
    dashboard_url: str


class StatusResponse(BaseModel):
    status: str
    progress: int


def _ensure_dirs() -> None:
    settings = get_settings()
    for path in (
        settings.screenshot_dir,
        settings.baseline_dir,
        settings.reports_dir,
        settings.scripts_dir,
        Path("screenshots"),
    ):
        path.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    _ensure_dirs()
    yield


app = FastAPI(
    title="Browser Automation AI Agent",
    version="1.0.0",
    description="Multi-agent browser automation with LangGraph orchestration",
    lifespan=lifespan,
)

# Enable CORS for cross-origin requests (e.g., Vercel frontend calling Railway backend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        # Add your production frontend URLs here:
        # "https://your-vercel-domain.vercel.app",
        # "https://yourdomain.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

screenshots_root = Path("screenshots")
if screenshots_root.exists():
    app.mount("/screenshots", StaticFiles(directory=str(screenshots_root)), name="screenshots")


@app.get("/")
def root() -> RedirectResponse:
    return RedirectResponse(url="/dashboard")


@app.get("/api/runs")
def api_list_runs(limit: int = 50) -> list[dict[str, Any]]:
    return list_reports(limit=limit)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/run", response_model=RunResponse)
def start_run(request: RunRequest, background_tasks: BackgroundTasks) -> RunResponse:
    run_id = str(uuid.uuid4())
    run_store.set_status(run_id, "running", progress=0)

    override: dict = {}
    if request.openrouter_api_key is not None:
        override["openrouter_api_key"] = request.openrouter_api_key
    if request.openrouter_model is not None:
        override["openrouter_model"] = request.openrouter_model
    if request.use_mock_llm is not None:
        override["use_mock_llm"] = request.use_mock_llm
    if request.max_retries is not None:
        override["max_retries"] = request.max_retries
    if request.max_repair_before_regenerate is not None:
        override["max_repair_before_regenerate"] = request.max_repair_before_regenerate

    background_tasks.add_task(
        _execute_run,
        run_id,
        str(request.url),
        request.intent,
        override or None,
    )
    return RunResponse(
        run_id=run_id,
        status="running",
        dashboard_url=f"/dashboard/{run_id}",
    )


@app.get("/run/{run_id}/dashboard")
def run_dashboard_redirect(run_id: str) -> RedirectResponse:
    return RedirectResponse(url=f"/dashboard/{run_id}")


@app.get("/status/{run_id}", response_model=StatusResponse)
def get_status(run_id: str) -> StatusResponse:
    status = run_store.get_status(run_id)
    if not status:
        raise HTTPException(status_code=404, detail="Run not found")
    return StatusResponse(status=status["status"], progress=status.get("progress", 0))


@app.get("/report/{run_id}")
def get_report(run_id: str) -> dict[str, Any]:
    report = run_store.get_report(run_id)
    if not report:
        report = load_report(run_id)
    if not report:
        status = run_store.get_status(run_id)
        if not status:
            raise HTTPException(status_code=404, detail="Run not found")
        return {"run_id": run_id, "status": status["status"], "progress": status.get("progress", 0)}
    return report


# Serve the built React frontend — must come AFTER all API routes
_FRONTEND_DIST = Path(__file__).resolve().parent / "frontend" / "dist"

if _FRONTEND_DIST.exists():
    app.mount(
        "/assets",
        StaticFiles(directory=str(_FRONTEND_DIST / "assets")),
        name="frontend-assets",
    )

    @app.get("/{full_path:path}", response_class=HTMLResponse)
    def serve_spa(full_path: str) -> HTMLResponse:
        index = _FRONTEND_DIST / "index.html"
        return HTMLResponse(index.read_text(encoding="utf-8"))


def _execute_run(run_id: str, url: str, intent: str, settings_override: dict | None = None) -> None:
    run_store.set_status(run_id, "running", progress=10)
    try:
        result = run_pipeline(url=url, intent=intent, run_id=run_id, settings_override=settings_override)
        report = result.get("final_report") or {}
        run_store.set_report(run_id, report)
        final_status = report.get("status", result.get("status", "success"))
        run_store.set_status(run_id, final_status, progress=100)
    except Exception as exc:
        logger.exception("Run failed run_id=%s", run_id)
        run_store.set_status(run_id, "failed", progress=100)
        run_store.set_report(
            run_id,
            {"run_id": run_id, "status": "failed", "error": str(exc)},
        )


if __name__ == "__main__":
    settings = get_settings()
    logging.getLogger().setLevel(settings.log_level)
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
