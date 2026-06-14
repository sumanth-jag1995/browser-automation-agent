"""Flow Discovery Agent — identifies critical user journeys from URL and intent."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from llm.client import LLMClient
from state.schema import AgentState

logger = logging.getLogger(__name__)


def _default_flows(intent: str) -> list[str]:
    intent_lower = intent.lower()
    if "checkout" in intent_lower or "cart" in intent_lower:
        return ["login", "browse_products", "add_to_cart", "checkout", "payment"]
    if "login" in intent_lower or "auth" in intent_lower:
        return ["login", "logout", "password_reset"]
    return ["homepage", "navigation", "search", "content_view"]


def _parse_flows(raw: str) -> list[str]:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\n?", "", cleaned)
        cleaned = re.sub(r"\n?```$", "", cleaned)
    data = json.loads(cleaned)
    if isinstance(data, list):
        return [str(item) for item in data[:10]]
    if isinstance(data, dict) and "flows" in data:
        return [str(item) for item in data["flows"][:10]]
    raise ValueError("Unexpected flow discovery response format")


def discover_flows(state: AgentState) -> dict[str, Any]:
    url = state["url"]
    intent = state["intent"]
    logger.info("Discovering flows for url=%s intent=%s", url, intent)

    client = LLMClient(state.get("settings_override"))
    system = client.load_prompt("flow_discovery")
    prompt = f"URL: {url}\nIntent: {intent}\n\nReturn 3-5 critical user journeys as a JSON array."

    try:
        if client.llm_enabled:
            raw = client.complete(prompt, system=system)
            flows = _parse_flows(raw)
            logger.info('===============================================')
            logger.info(f"Flows: {flows}")
            logger.info('===============================================')
        else:
            logger.info('===============================================')
            logger.info(f"Prompt: {prompt}")
            logger.info('===============================================')
            flows = _default_flows(intent)
    except Exception as exc:
        logger.info("Flow discovery fallback due to error: %s", exc)
        flows = _default_flows(intent)

    logger.info("Discovered flows: %s", flows)
    return {
        "discovered_flows": flows,
        "status": "flows_discovered",
        "current_script_index": 0,
        "retry_count": state.get("retry_count", 0),
        "auto_repairs": state.get("auto_repairs", 0),
        "screenshots": state.get("screenshots", []),
        "execution_results": state.get("execution_results", []),
        "generated_scripts": state.get("generated_scripts", []),
    }
