"""Agent state schema for LangGraph orchestration."""

from typing import Any, Optional, TypedDict


class AgentState(TypedDict, total=False):
    """Shared state passed between agents in the orchestration graph."""

    url: str
    intent: str
    discovered_flows: list[str]
    generated_scripts: list[str]
    execution_results: list[dict[str, Any]]
    diagnosis: Optional[dict[str, Any]]
    repaired_script: Optional[str]
    retry_count: int
    screenshots: list[str]
    regression_diff: Optional[dict[str, Any]]
    final_report: Optional[dict[str, Any]]
    status: str
    run_id: str
    current_script_index: int
    auto_repairs: int
    human_escalation: bool
    flow_repair_counts: dict[str, int]
    script_sources: dict[str, str]
    flows_reused: list[str]
    flows_generated: list[str]
    flows_regenerated: list[str]
    settings_override: Optional[dict[str, Any]]
