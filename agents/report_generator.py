"""Report Generator Agent — produces final execution report."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config import get_settings
from state.schema import AgentState

logger = logging.getLogger(__name__)


def generate_report(state: AgentState) -> dict[str, Any]:
    settings = get_settings()
    settings.reports_dir.mkdir(parents=True, exist_ok=True)

    flows = state.get("discovered_flows", [])
    results = state.get("execution_results", [])
    passed = sum(1 for r in results if r.get("status") == "success")
    regression = state.get("regression_diff") or {}
    regressions = regression.get("regressions", 0)

    overall_status = "success"
    if state.get("human_escalation"):
        overall_status = "escalated"
    elif any(r.get("status") == "fail" for r in results):
        overall_status = "failed"
    elif regression.get("regression_detected"):
        overall_status = "regression"

    report = {
        "run_id": state.get("run_id", ""),
        "url": state.get("url", ""),
        "intent": state.get("intent", ""),
        "flows_total": len(flows),
        "flows_passed": passed,
        "auto_repairs": state.get("auto_repairs", 0),
        "retries_used": state.get("retry_count", 0),
        "regressions": regressions,
        "status": overall_status,
        "screenshots": state.get("screenshots", []),
        "execution_results": results,
        "script_sources": state.get("script_sources", {}),
        "flows_reused": state.get("flows_reused", []),
        "flows_generated": state.get("flows_generated", []),
        "flows_regenerated": state.get("flows_regenerated", []),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    run_id = state.get("run_id", "unknown")
    report_path = settings.reports_dir / f"{run_id}.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    logger.info("Report written to %s", report_path)

    return {"final_report": report, "status": overall_status}


def escalate_human(state: AgentState) -> dict[str, Any]:
    logger.warning("Max retries exceeded; escalating to human review")
    report = generate_report(state)
    report["human_escalation"] = True
    report["status"] = "escalated"
    if report.get("final_report"):
        report["final_report"]["status"] = "escalated"
        report["final_report"]["human_escalation"] = True
    return report
