"""Tests for LangGraph orchestration."""

from __future__ import annotations

import os

os.environ.setdefault("USE_MOCK_LLM", "true")

from orchestrator.graph import build_graph, compile_graph


def test_graph_compiles() -> None:
    graph = build_graph()
    app = compile_graph()
    assert graph is not None
    assert app is not None


def test_graph_has_expected_nodes() -> None:
    graph = build_graph()
    node_names = set(graph.nodes.keys())
    expected = {
        "flow_discovery",
        "script_generator",
        "executor",
        "error_diagnosis",
        "adaptive_repair",
        "regenerate_flow",
        "regression_monitor",
        "report_generator",
        "escalate",
    }
    assert expected.issubset(node_names)
