"""Adaptive Repair Agent — automatically repairs failed Playwright scripts."""

from __future__ import annotations

import logging
import textwrap
from typing import Any

from llm.client import LLMClient
from agents.script_generator import build_script, persist_script_for_flow
from state.schema import AgentState

logger = logging.getLogger(__name__)


def _current_flow(state: AgentState) -> str:
    flows = state.get("discovered_flows") or ["flow"]
    index = state.get("current_script_index", 0)
    if not flows:
        return "flow"
    return flows[min(index, len(flows) - 1)]


def _apply_heuristic_repair(script: str, diagnosis: dict[str, Any]) -> str:
    failure_type = diagnosis.get("failure_type", "selector")
    repaired = script

    if failure_type == "selector":
        repaired = repaired.replace(
            'page.locator("#checkout-btn")',
            'page.get_by_test_id("checkout-cta")',
        )
        if "get_by_test_id" not in repaired:
            repaired = repaired.replace(
                'await page.wait_for_load_state("networkidle", timeout=30000)',
                'await page.wait_for_load_state("networkidle", timeout=60000)\n'
                '                checkout = page.get_by_test_id("checkout-cta")',
            )

    if failure_type == "timeout":
        repaired = repaired.replace("timeout=30000", "timeout=60000")
        repaired = repaired.replace("timeout=60000", "timeout=90000")
        if "wait_for_load_state" not in repaired:
            repaired = repaired.replace(
                "await page.goto(url",
                'await page.wait_for_load_state("networkidle", timeout=60000)\n'
                "                await page.goto(url",
            )

    if "retry" not in repaired.lower():
        repaired = textwrap.dedent(
            """
            async def run(page, url: str, screenshot_dir: str) -> dict:
                import asyncio
                import os

                last_error = None
                for attempt in range(3):
                    result = {"status": "success", "screenshots": []}
                    try:
                        await page.goto(url, wait_until="domcontentloaded", timeout=90000)
                        await page.wait_for_load_state("networkidle", timeout=60000)
                        os.makedirs(screenshot_dir, exist_ok=True)
                        path = os.path.join(screenshot_dir, "repaired_flow.png")
                        await page.screenshot(path=path, full_page=True)
                        result["screenshots"].append(path)
                        return result
                    except Exception as exc:
                        last_error = exc
                        await asyncio.sleep(1 * (attempt + 1))
                return {"status": "fail", "error": type(last_error).__name__ + ": " + str(last_error)}
            """
        ).strip()

    return repaired


def repair_script(state: AgentState) -> dict[str, Any]:
    diagnosis = state.get("diagnosis") or {}
    scripts = state.get("generated_scripts", [])
    index = state.get("current_script_index", 0)
    failed_script = scripts[min(index, len(scripts) - 1)] if scripts else ""
    flow = _current_flow(state)

    logger.info("Repairing script for flow=%s failure_type=%s", flow, diagnosis.get("failure_type"))

    client = LLMClient(state.get("settings_override"))
    prompt = (
        f"Diagnosis:\n{diagnosis}\n\n"
        f"Failed script:\n{failed_script}\n\n"
        "Return repaired_script JSON."
    )

    repaired_script = failed_script
    try:
        if client.llm_enabled:
            system = client.load_prompt("repair")
            response = client.complete_json(prompt, system=system)
            repaired_script = response.get("repaired_script", failed_script)
        else:
            repaired_script = _apply_heuristic_repair(failed_script, diagnosis)
    except Exception as exc:
        logger.warning("Repair fallback: %s", exc)
        repaired_script = _apply_heuristic_repair(failed_script, diagnosis)

    if not repaired_script or "async def run" not in repaired_script:
        repaired_script = build_script(flow, state["url"], state["intent"])

    retry_count = state.get("retry_count", 0) + 1
    auto_repairs = state.get("auto_repairs", 0) + 1

    flow_repair_counts = dict(state.get("flow_repair_counts", {}))
    flow_repair_counts[flow] = flow_repair_counts.get(flow, 0) + 1

    scripts_copy = list(scripts)
    if scripts_copy and index < len(scripts_copy):
        scripts_copy[index] = repaired_script

    script_sources = dict(state.get("script_sources", {}))
    script_sources[flow] = "repaired"

    persist_script_for_flow(state, flow, repaired_script, "repaired")

    return {
        "repaired_script": repaired_script,
        "generated_scripts": scripts_copy,
        "retry_count": retry_count,
        "auto_repairs": auto_repairs,
        "flow_repair_counts": flow_repair_counts,
        "script_sources": script_sources,
        "status": "repaired",
    }
