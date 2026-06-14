"""FastAPI entrypoint for the Browser Automation AI Agent."""

from __future__ import annotations

import logging
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import BackgroundTasks, FastAPI, HTTPException
from pydantic import BaseModel, Field, HttpUrl

from config import get_settings
from orchestrator.graph import run_pipeline
from storage.redis_store import RunStore

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

run_store = RunStore()


class RunRequest(BaseModel):
    url: HttpUrl
    intent: str = Field(min_length=1, examples=["Test checkout flow"])


class RunResponse(BaseModel):
    run_id: str
    status: str


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
    ):
        path.mkdir(parents=True, exist_ok=True)


def _execute_run(run_id: str, url: str, intent: str) -> None:
    run_store.set_status(run_id, "running", progress=10)
    try:
        result = run_pipeline(url=url, intent=intent, run_id=run_id)
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


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/run", response_model=RunResponse)
def start_run(request: RunRequest, background_tasks: BackgroundTasks) -> RunResponse:
    run_id = str(uuid.uuid4())
    run_store.set_status(run_id, "running", progress=0)
    background_tasks.add_task(
        _execute_run,
        run_id,
        str(request.url),
        request.intent,
    )
    return RunResponse(run_id=run_id, status="running")


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
        status = run_store.get_status(run_id)
        if not status:
            raise HTTPException(status_code=404, detail="Run not found")
        return {"run_id": run_id, "status": status["status"], "progress": status.get("progress", 0)}
    return report


if __name__ == "__main__":
    settings = get_settings()
    logging.getLogger().setLevel(settings.log_level)
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
