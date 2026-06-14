"""Execution Agent — runs generated Playwright scripts."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, Coroutine

from playwright.async_api import async_playwright

from agents.script_generator import persist_script_for_flow
from config import get_settings
from state.schema import AgentState
from storage.script_store import ScriptStore

logger = logging.getLogger(__name__)


async def _run_script(
    script_source: str,
    url: str,
    screenshot_dir: str,
    *,
    headless: bool,
) -> dict[str, Any]:
    namespace: dict[str, Any] = {}
    exec(script_source, namespace)  # noqa: S102
    run_fn: Callable[..., Coroutine[Any, Any, dict[str, Any]]] = namespace["run"]

    async with async_playwright() as playwright:
        logger.info("Launching Chromium (headless=%s)", headless)
        browser = await playwright.chromium.launch(headless=headless)
        context = await browser.new_context(viewport={"width": 1280, "height": 720})
        page = await context.new_page()
        try:
            result = await run_fn(page, url, screenshot_dir)
        finally:
            await context.close()
            await browser.close()
    return result


def _current_flow(state: AgentState) -> str:
    flows = state.get("discovered_flows", ["flow"])
    index = state.get("current_script_index", 0)
    return flows[min(index, len(flows) - 1)]


def execute_scripts(state: AgentState) -> dict[str, Any]:
    settings = get_settings()
    scripts = state.get("generated_scripts", [])
    repaired = state.get("repaired_script")
    index = state.get("current_script_index", 0)
    url = state["url"]
    screenshot_dir = str(settings.screenshot_dir)
    flow_name = _current_flow(state)

    if not scripts and not repaired:
        return {
            "status": "failed",
            "execution_results": [{"status": "fail", "error": "No scripts to execute"}],
        }

    script = repaired if repaired else scripts[min(index, len(scripts) - 1)]

    logger.info("Executing script for flow=%s (index=%d)", flow_name, index)

    try:
        result = asyncio.run(
            _run_script(
                script,
                url,
                screenshot_dir,
                headless=settings.playwright_headless,
            )
        )
    except Exception as exc:
        logger.exception("Script execution crashed")
        result = {"status": "fail", "error": f"{type(exc).__name__}: {exc}", "flow": flow_name}

    results = list(state.get("execution_results", []))
    results.append(result)

    all_screenshots = list(state.get("screenshots", []))
    all_screenshots.extend(result.get("screenshots", []))

    flow_repair_counts = dict(state.get("flow_repair_counts", {}))
    script_sources = dict(state.get("script_sources", {}))
    store = ScriptStore(url)

    update: dict[str, Any] = {
        "execution_results": results,
        "screenshots": all_screenshots,
        "repaired_script": None,
        "flow_repair_counts": flow_repair_counts,
        "script_sources": script_sources,
    }

    if result.get("status") == "success":
        source = script_sources.get(flow_name, "generated")
        if source == "cached":
            source = "cached"
        persist_script_for_flow(state, flow_name, script, source)
        store.update_flow_status(flow_name, "success", repair_count=0)
        flow_repair_counts[flow_name] = 0

        next_index = index + 1
        if next_index < len(scripts):
            update["current_script_index"] = next_index
            update["status"] = "executing"
        else:
            update["status"] = "execution_success"
            update["current_script_index"] = next_index
    else:
        store.update_flow_status(
            flow_name,
            "failed",
            repair_count=flow_repair_counts.get(flow_name, 0),
        )
        update["status"] = "execution_failed"

    update["flow_repair_counts"] = flow_repair_counts
    return update
