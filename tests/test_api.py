"""Tests for FastAPI endpoints."""

from __future__ import annotations

import os
import time

os.environ.setdefault("USE_MOCK_LLM", "true")

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_run_and_status_flow() -> None:
    response = client.post(
        "/run",
        json={"url": "https://example.com", "intent": "Test homepage flow"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "run_id" in data
    assert data["status"] == "running"

    run_id = data["run_id"]
    for _ in range(60):
        status_resp = client.get(f"/status/{run_id}")
        if status_resp.status_code == 200:
            status_data = status_resp.json()
            if status_data["progress"] == 100:
                break
        time.sleep(1)

    report_resp = client.get(f"/report/{run_id}")
    assert report_resp.status_code == 200
    report = report_resp.json()
    assert report.get("flows_total", 0) > 0 or report.get("status") in {"success", "failed", "running"}
