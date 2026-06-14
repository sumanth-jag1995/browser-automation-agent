"""Script Generator Agent — hybrid local storage with incremental generation."""

from __future__ import annotations

import logging
from typing import Any

from llm.client import LLMClient
from state.schema import AgentState
from storage.script_store import ScriptStore, compute_flow_hash
from test_data import credentials_file_path, get_login_credentials

logger = logging.getLogger(__name__)

_RUN_SIGNATURE = "async def run(page, url: str, screenshot_dir: str)"


def _indent_block(block: str, spaces: int) -> str:
    prefix = " " * spaces
    return "\n".join(prefix + line if line.strip() else line for line in block.strip().splitlines())


def _flow_needs_credentials(flow: str) -> bool:
    flow_lower = flow.lower()
    return any(keyword in flow_lower for keyword in ("login", "signin", "sign_in", "auth", "password"))


def _credentials_context(flow: str) -> str:
    if not _flow_needs_credentials(flow):
        return ""
    creds = get_login_credentials()
    path = credentials_file_path()
    return (
        f"\nTest credentials file: {path}\n"
        f"Default username: {creds['username']}\n"
        f"Default password: {creds['password']}\n"
        "Load credentials from the JSON file under the 'login' key when filling auth forms.\n"
    )


def _fallback_flow_actions(flow: str) -> str:
    """Lightweight heuristic actions when LLM is unavailable."""
    flow_lower = flow.lower()

    if _flow_needs_credentials(flow):
        creds = get_login_credentials()
        creds_path = str(credentials_file_path()).replace("\\", "\\\\")
        default_creds = (
            '{"username": "' + creds["username"] + '", "password": "' + creds["password"] + '"}'
        )
        return f'''
import json
from pathlib import Path

creds_path = Path("{creds_path}")
creds = {default_creds}
if creds_path.exists():
    creds = json.loads(creds_path.read_text(encoding="utf-8")).get("login", creds)

username = page.locator(
    'input[name="username"], input[type="email"], input[name="email"]'
).first
password = page.locator(
    'input[name="password"], input[type="password"]'
).first
submit = page.get_by_role("button", name="Login").or_(
    page.get_by_role("button", name="Sign in")
).or_(page.locator('button[type="submit"]')).first

if await username.count() > 0:
    await username.fill(creds["username"])
if await password.count() > 0:
    await password.fill(creds["password"])
if await submit.count() > 0:
    await submit.click(timeout=10000)

await page.wait_for_load_state("networkidle", timeout=30000)
'''

    if "checkout" in flow_lower:
        return '''
checkout = page.get_by_role("button", name="Checkout").or_(
    page.get_by_test_id("checkout-cta")
).or_(page.locator("#checkout-btn"))
if await checkout.count() > 0:
    await checkout.click(timeout=5000)
await page.wait_for_load_state("networkidle", timeout=30000)
'''

    if "search" in flow_lower:
        return '''
search = page.get_by_role("searchbox").or_(
    page.locator('input[type="search"], input[name="q"], input[name="search"]')
).first
if await search.count() > 0:
    await search.fill("test")
    await search.press("Enter")
await page.wait_for_load_state("networkidle", timeout=30000)
'''

    if "cart" in flow_lower or "add" in flow_lower:
        return '''
add_btn = page.get_by_role("button", name="Add to cart").or_(
    page.get_by_role("button", name="Add to Cart")
).first
if await add_btn.count() > 0:
    await add_btn.click(timeout=5000)
await page.wait_for_load_state("networkidle", timeout=30000)
'''

    return ""


def _build_fallback_script(flow: str, url: str) -> str:
    """Build a deterministic Playwright script when LLM generation is unavailable."""
    safe_flow = flow.replace('"', '\\"')
    flow_actions = _indent_block(_fallback_flow_actions(flow), 8)

    return f'''async def run(page, url: str, screenshot_dir: str) -> dict:
    """Automate flow: {safe_flow}"""
    import os

    result = {{"status": "success", "screenshots": [], "flow": "{safe_flow}"}}
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_load_state("networkidle", timeout=30000)
{flow_actions}
        os.makedirs(screenshot_dir, exist_ok=True)
        screenshot_path = os.path.join(screenshot_dir, "{safe_flow}.png")
        await page.screenshot(path=screenshot_path, full_page=True)
        result["screenshots"].append(screenshot_path)
    except Exception as exc:
        result = {{
            "status": "fail",
            "error": type(exc).__name__ + ": " + str(exc),
            "flow": "{safe_flow}",
            "screenshots": result.get("screenshots", []),
        }}
    return result
'''


def _extract_script_from_response(raw: dict[str, Any]) -> str | None:
    for key in ("script", "repaired_script", "generated_script"):
        value = raw.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    scripts = raw.get("scripts")
    if isinstance(scripts, list) and scripts:
        first = scripts[0]
        if isinstance(first, str) and first.strip():
            return first.strip()
    return None


def _is_valid_script(script: str) -> bool:
    if _RUN_SIGNATURE not in script:
        return False
    if "return" not in script:
        return False
    if "screenshot" not in script.lower():
        return False
    return True


def _generate_script_with_llm(
    flow: str, url: str, intent: str, settings_override: dict | None = None
) -> str | None:
    client = LLMClient(settings_override)
    if not client.llm_enabled:
        return None

    system = client.load_prompt("script_generation")
    prompt = (
        f"URL: {url}\n"
        f"Intent: {intent}\n"
        f"Flow: {flow}\n"
        f"{_credentials_context(flow)}\n"
        "Generate a Playwright automation script for this flow."
    )

    try:
        response = client.complete_json(prompt, system=system)
        script = _extract_script_from_response(response)
        if script and _is_valid_script(script):
            return script
        logger.warning("LLM returned invalid script for flow=%s, using fallback", flow)
    except Exception as exc:
        logger.warning("LLM script generation failed for flow=%s: %s", flow, exc)

    return None


def build_script(flow: str, url: str, intent: str = "", settings_override: dict | None = None) -> str:
    """Build a Playwright script string for a single flow."""
    script = _generate_script_with_llm(flow, url, intent, settings_override)
    if script:
        return script
    return _build_fallback_script(flow, url)


def _is_valid_cached_script(script: str) -> bool:
    return _is_valid_script(script)


def _resolve_scripts_for_flows(
    url: str,
    intent: str,
    flows: list[str],
    *,
    force_flows: set[str] | None = None,
    settings_override: dict | None = None,
) -> tuple[list[str], dict[str, str], list[str], list[str], list[str]]:
    store = ScriptStore(url)
    store.archive_removed_flows(flows)

    scripts: list[str] = []
    script_sources: dict[str, str] = {}
    flows_reused: list[str] = []
    flows_generated: list[str] = []
    flows_regenerated: list[str] = []
    force = force_flows or set()

    for flow in flows:
        flow_hash = compute_flow_hash(url, intent, flow)
        must_regenerate = flow in force

        if not must_regenerate and store.should_reuse(flow, flow_hash):
            script = store.read_script(flow)
            if script and not _is_valid_cached_script(script):
                script = None
            if script:
                scripts.append(script)
                script_sources[flow] = "cached"
                flows_reused.append(flow)
                logger.info("Reusing cached script for flow=%s", flow)
                continue

        script = build_script(flow, url, intent, settings_override)
        scripts.append(script)
        source = "regenerated" if must_regenerate else "generated"
        if source == "regenerated":
            flows_regenerated.append(flow)
        else:
            flows_generated.append(flow)
        script_sources[flow] = source
        store.save_script(
            flow,
            script,
            flow_hash=flow_hash,
            intent=intent,
            source=source,
            repair_count=0,
            last_status="pending",
        )
        logger.info("%s script for flow=%s", source.capitalize(), flow)

    return scripts, script_sources, flows_reused, flows_generated, flows_regenerated


def generate_scripts(state: AgentState) -> dict[str, Any]:
    """Resolve scripts using hybrid strategy: reuse cached, generate only new/changed flows."""
    flows = state.get("discovered_flows", [])
    url = state["url"]
    intent = state["intent"]
    logger.info("Resolving scripts for %d flows (hybrid/local storage)", len(flows))

    scripts, script_sources, flows_reused, flows_generated, flows_regenerated = _resolve_scripts_for_flows(
        url, intent, flows, settings_override=state.get("settings_override")
    )

    return {
        "generated_scripts": scripts,
        "script_sources": script_sources,
        "flows_reused": flows_reused,
        "flows_generated": flows_generated,
        "flows_regenerated": flows_regenerated,
        "flow_repair_counts": state.get("flow_repair_counts", {}),
        "status": "scripts_generated",
        "current_script_index": 0,
    }


def regenerate_current_flow(state: AgentState) -> dict[str, Any]:
    """Regenerate script from scratch after repeated repair failures."""
    url = state["url"]
    intent = state["intent"]
    flows = state.get("discovered_flows", [])
    index = state.get("current_script_index", 0)
    scripts = list(state.get("generated_scripts", []))

    if not flows or index >= len(flows):
        return {"status": "execution_failed"}

    flow = flows[index]
    logger.info("Regenerating script from scratch for flow=%s after repair exhaustion", flow)

    new_script = build_script(flow, url, intent, settings_override=state.get("settings_override"))
    flow_hash = compute_flow_hash(url, intent, flow)
    store = ScriptStore(url)
    store.save_script(
        flow,
        new_script,
        flow_hash=flow_hash,
        intent=intent,
        source="regenerated",
        repair_count=0,
        last_status="pending",
    )

    if index < len(scripts):
        scripts[index] = new_script
    else:
        scripts.append(new_script)

    script_sources = dict(state.get("script_sources", {}))
    script_sources[flow] = "regenerated"

    flows_regenerated = list(state.get("flows_regenerated", []))
    if flow not in flows_regenerated:
        flows_regenerated.append(flow)

    flow_repair_counts = dict(state.get("flow_repair_counts", {}))
    flow_repair_counts[flow] = 0

    return {
        "generated_scripts": scripts,
        "repaired_script": new_script,
        "script_sources": script_sources,
        "flows_regenerated": flows_regenerated,
        "flow_repair_counts": flow_repair_counts,
        "status": "regenerated",
    }


def persist_script_for_flow(state: AgentState, flow: str, script: str, source: str) -> None:
    """Save a script to local storage after successful execution or repair."""
    if not _is_valid_cached_script(script):
        logger.warning("Skipping persist for flow=%s: script failed validation", flow)
        return

    url = state["url"]
    intent = state["intent"]
    flow_hash = compute_flow_hash(url, intent, flow)
    store = ScriptStore(url)
    entry = store.get_flow_entry(flow) or {}
    store.save_script(
        flow,
        script,
        flow_hash=flow_hash,
        intent=intent,
        source=source,
        repair_count=entry.get("repair_count", 0),
        last_status="success",
    )
