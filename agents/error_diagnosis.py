"""Error Diagnosis Agent — identifies root cause of script failures."""

from __future__ import annotations

import json
import logging
from typing import Any

from llm.client import LLMClient
from state.schema import AgentState

logger = logging.getLogger(__name__)

FAILURE_TYPES = {
    "timeout",
    "selector",
    "missing_element",
    "network_error",
    "authentication",
    "visual_regression",
}


def _heuristic_diagnosis(error: str) -> dict[str, Any]:
    lower = error.lower()
    if "timeout" in lower:
        return {
            "failure_type": "timeout",
            "severity": "major",
            "root_cause": "Page or element did not load within timeout",
            "fix_strategy": "increase timeout and wait for networkidle",
        }
    if "selector" in lower or "locator" in lower:
        return {
            "failure_type": "selector",
            "severity": "critical",
            "root_cause": "Element selector no longer matches DOM",
            "fix_strategy": "use data-testid locator",
        }
    if "net::" in lower or "network" in lower:
        return {
            "failure_type": "network_error",
            "severity": "major",
            "root_cause": "Network request failed during navigation",
            "fix_strategy": "add retry wrapper and increase navigation timeout",
        }
    return {
        "failure_type": "missing_element",
        "severity": "critical",
        "root_cause": error[:200],
        "fix_strategy": "use resilient locators with fallback selectors",
    }


def diagnose_error(state: AgentState) -> dict[str, Any]:
    results = state.get("execution_results", [])
    last = results[-1] if results else {}
    error = last.get("error", "Unknown error")
    scripts = state.get("generated_scripts", [])
    index = state.get("current_script_index", 0)
    failed_script = scripts[min(index, len(scripts) - 1)] if scripts else ""

    logger.info("Diagnosing failure: %s", error[:120])

    client = LLMClient(state.get("settings_override"))
    prompt = (
        f"Failed script:\n{failed_script}\n\n"
        f"Execution error:\n{error}\n\n"
        "Return diagnosis JSON."
    )

    try:
        if client.llm_enabled:
            system = client.load_prompt("diagnosis")
            diagnosis = client.complete_json(prompt, system=system)
        else:
            diagnosis = _heuristic_diagnosis(error)
    except (json.JSONDecodeError, Exception) as exc:
        logger.warning("Diagnosis fallback: %s", exc)
        diagnosis = _heuristic_diagnosis(error)

    if diagnosis.get("failure_type") not in FAILURE_TYPES:
        diagnosis["failure_type"] = "selector"

    return {"diagnosis": diagnosis, "status": "diagnosed"}
