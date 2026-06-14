"""LangGraph orchestration for the browser automation multi-agent pipeline."""

from __future__ import annotations

import logging
from typing import Literal

from langgraph.graph import END, START, StateGraph

from agents.adaptive_repair import repair_script
from agents.error_diagnosis import diagnose_error
from agents.executor import execute_scripts
from agents.flow_discovery import discover_flows
from agents.regression_monitor import monitor_regression
from agents.report_generator import escalate_human, generate_report
from agents.script_generator import generate_scripts, regenerate_current_flow
from config import get_settings
from state.schema import AgentState

logger = logging.getLogger(__name__)


def _current_flow(state: AgentState) -> str:
    flows = state.get("discovered_flows", ["flow"])
    index = state.get("current_script_index", 0)
    return flows[min(index, len(flows) - 1)]


def _route_after_execute(
    state: AgentState,
) -> Literal["executor", "regression_monitor", "error_diagnosis", "regenerate_flow", "escalate"]:
    status = state.get("status", "")
    settings = get_settings()
    override = state.get("settings_override") or {}

    max_retries = int(override["max_retries"]) if "max_retries" in override else settings.max_retries
    max_repair = (
        int(override["max_repair_before_regenerate"])
        if "max_repair_before_regenerate" in override
        else settings.max_repair_before_regenerate
    )

    if status == "executing":
        return "executor"
    if status == "execution_success":
        return "regression_monitor"
    if status == "execution_failed":
        if state.get("retry_count", 0) >= max_retries:
            return "escalate"
        flow = _current_flow(state)
        repair_attempts = state.get("flow_repair_counts", {}).get(flow, 0)
        if repair_attempts >= max_repair:
            logger.info(
                "Flow %s exceeded repair threshold (%d); regenerating script",
                flow,
                max_repair,
            )
            return "regenerate_flow"
        return "error_diagnosis"
    logger.warning("Unexpected status after execute: %s", status)
    return "regression_monitor"


def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("flow_discovery", discover_flows)
    graph.add_node("script_generator", generate_scripts)
    graph.add_node("executor", execute_scripts)
    graph.add_node("error_diagnosis", diagnose_error)
    graph.add_node("adaptive_repair", repair_script)
    graph.add_node("regenerate_flow", regenerate_current_flow)
    graph.add_node("regression_monitor", monitor_regression)
    graph.add_node("report_generator", generate_report)
    graph.add_node("escalate", escalate_human)

    graph.add_edge(START, "flow_discovery")
    graph.add_edge("flow_discovery", "script_generator")
    graph.add_edge("script_generator", "executor")

    graph.add_conditional_edges(
        "executor",
        _route_after_execute,
        {
            "executor": "executor",
            "regression_monitor": "regression_monitor",
            "error_diagnosis": "error_diagnosis",
            "regenerate_flow": "regenerate_flow",
            "escalate": "escalate",
        },
    )

    graph.add_edge("error_diagnosis", "adaptive_repair")
    graph.add_edge("adaptive_repair", "executor")
    graph.add_edge("regenerate_flow", "executor")
    graph.add_edge("regression_monitor", "report_generator")
    graph.add_edge("report_generator", END)
    graph.add_edge("escalate", END)

    return graph


def compile_graph():
    return build_graph().compile()


def run_pipeline(
    url: str, intent: str, run_id: str, settings_override: dict | None = None
) -> AgentState:
    logger.info("Starting pipeline run_id=%s url=%s", run_id, url)
    app = compile_graph()
    initial_state: AgentState = {
        "url": url,
        "intent": intent,
        "run_id": run_id,
        "settings_override": settings_override,
        "discovered_flows": [],
        "generated_scripts": [],
        "execution_results": [],
        "diagnosis": None,
        "repaired_script": None,
        "retry_count": 0,
        "auto_repairs": 0,
        "screenshots": [],
        "regression_diff": None,
        "final_report": None,
        "status": "starting",
        "current_script_index": 0,
        "human_escalation": False,
        "flow_repair_counts": {},
        "script_sources": {},
        "flows_reused": [],
        "flows_generated": [],
        "flows_regenerated": [],
    }
    result = app.invoke(initial_state)
    logger.info("Pipeline complete run_id=%s status=%s", run_id, result.get("status"))
    return result
