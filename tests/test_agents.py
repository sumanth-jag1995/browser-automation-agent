"""Unit tests for browser automation agents."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("USE_MOCK_LLM", "true")

from agents.adaptive_repair import repair_script
from agents.error_diagnosis import diagnose_error
from agents.flow_discovery import discover_flows
from agents.regression_monitor import monitor_regression
from agents.report_generator import generate_report
from config import get_settings
from agents.script_generator import generate_scripts
from state.schema import AgentState


@pytest.fixture
def base_state() -> AgentState:
    return {
        "url": "https://example.com",
        "intent": "Test checkout flow",
        "run_id": "test-run",
        "discovered_flows": [],
        "generated_scripts": [],
        "execution_results": [],
        "retry_count": 0,
        "auto_repairs": 0,
        "screenshots": [],
        "status": "starting",
        "current_script_index": 0,
    }


def test_flow_discovery_returns_flows(base_state: AgentState) -> None:
    result = discover_flows(base_state)
    flows = result["discovered_flows"]
    assert 3 <= len(flows) <= 5
    assert "checkout" in flows or "login" in flows


def test_script_generator_creates_scripts(base_state: AgentState, tmp_path, monkeypatch) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "scripts_dir", tmp_path / "scripts")
    base_state["discovered_flows"] = ["homepage", "login", "checkout"]
    result = generate_scripts(base_state)
    scripts = result["generated_scripts"]
    assert len(scripts) == 3
    assert "async def run" in scripts[0]
    assert "screenshot" in scripts[0].lower()
    assert result["flows_generated"] == ["homepage", "login", "checkout"]


def test_error_diagnosis_heuristic(base_state: AgentState) -> None:
    base_state["execution_results"] = [{"status": "fail", "error": "TimeoutError: waiting for selector"}]
    base_state["generated_scripts"] = ['async def run(page, url, screenshot_dir): return {}']
    result = diagnose_error(base_state)
    diagnosis = result["diagnosis"]
    assert diagnosis["failure_type"] == "timeout"
    assert "fix_strategy" in diagnosis


def test_adaptive_repair_increments_retry(base_state: AgentState) -> None:
    base_state["diagnosis"] = {
        "failure_type": "timeout",
        "severity": "major",
        "root_cause": "slow page",
        "fix_strategy": "increase timeout",
    }
    base_state["generated_scripts"] = [
        'async def run(page, url, screenshot_dir):\n    await page.goto(url)\n    return {"status": "success"}'
    ]
    result = repair_script(base_state)
    assert result["retry_count"] == 1
    assert result["auto_repairs"] == 1
    assert "repaired_script" in result or result.get("generated_scripts")


def test_regression_monitor_creates_baseline(tmp_path, base_state: AgentState) -> None:
    from PIL import Image

    current_dir = tmp_path / "current"
    baseline_dir = tmp_path / "baseline"
    current_dir.mkdir()
    baseline_dir.mkdir()

    img_path = current_dir / "test.png"
    Image.new("RGB", (100, 100), color=(255, 0, 0)).save(img_path)

    from config import get_settings

    settings = get_settings()
    settings.screenshot_dir = current_dir
    settings.baseline_dir = baseline_dir

    base_state["screenshots"] = [str(img_path)]
    result = monitor_regression(base_state)
    diff = result["regression_diff"]
    assert diff["regression_detected"] is False
    assert (baseline_dir / "test.png").exists()


def test_report_generator(base_state: AgentState) -> None:
    base_state["discovered_flows"] = ["a", "b"]
    base_state["execution_results"] = [{"status": "success"}, {"status": "success"}]
    base_state["regression_diff"] = {"regressions": 0, "regression_detected": False}
    result = generate_report(base_state)
    report = result["final_report"]
    assert report["flows_total"] == 2
    assert report["flows_passed"] == 2
    assert report["status"] == "success"
