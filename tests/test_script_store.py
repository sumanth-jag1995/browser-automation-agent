"""Tests for local script storage and hybrid script resolution."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("USE_MOCK_LLM", "true")

from agents.script_generator import build_script, generate_scripts, regenerate_current_flow
from config import get_settings
from state.schema import AgentState
from storage.script_store import ScriptStore, compute_flow_hash, site_key


@pytest.fixture
def script_env(tmp_path, monkeypatch):
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()
    settings = get_settings()
    monkeypatch.setattr(settings, "scripts_dir", scripts_dir)
    return scripts_dir


@pytest.fixture
def base_state() -> AgentState:
    return {
        "url": "https://example.com",
        "intent": "Test checkout flow",
        "run_id": "test-run",
        "discovered_flows": ["login", "checkout"],
        "generated_scripts": [],
        "execution_results": [],
        "retry_count": 0,
        "auto_repairs": 0,
        "screenshots": [],
        "status": "starting",
        "current_script_index": 0,
        "flow_repair_counts": {},
        "script_sources": {},
        "flows_reused": [],
        "flows_generated": [],
        "flows_regenerated": [],
    }


def test_site_key_and_flow_hash() -> None:
    assert site_key("https://shop.example.com/path") == "shop.example.com"
    h1 = compute_flow_hash("https://example.com", "Test checkout", "login")
    h2 = compute_flow_hash("https://example.com", "Test checkout", "login")
    h3 = compute_flow_hash("https://example.com", "Test admin", "login")
    assert h1 == h2
    assert h1 != h3


def test_script_store_save_and_load(script_env, base_state) -> None:
    store = ScriptStore(base_state["url"])
    script = build_script("login", base_state["url"])
    flow_hash = compute_flow_hash(base_state["url"], base_state["intent"], "login")

    store.save_script(
        "login",
        script,
        flow_hash=flow_hash,
        intent=base_state["intent"],
        source="generated",
    )

    assert store.read_script("login") == script
    assert store.should_reuse("login", flow_hash) is True
    assert store.should_reuse("login", "different-hash") is False
    assert (script_env / "example.com" / "login.py").exists()
    assert (script_env / "example.com" / "manifest.json").exists()


def test_hybrid_reuses_cached_scripts(script_env, base_state) -> None:
    first = generate_scripts(base_state)
    assert len(first["generated_scripts"]) == 2
    assert first["flows_generated"] == ["login", "checkout"]
    assert first["flows_reused"] == []

    second = generate_scripts(base_state)
    assert len(second["generated_scripts"]) == 2
    assert second["flows_reused"] == ["login", "checkout"]
    assert second["flows_generated"] == []


def test_hybrid_regenerates_on_intent_change(script_env, base_state) -> None:
    generate_scripts(base_state)

    base_state["intent"] = "Test admin panel"
    result = generate_scripts(base_state)
    assert result["flows_generated"] == ["login", "checkout"]
    assert result["flows_reused"] == []


def test_regenerate_current_flow(script_env, base_state) -> None:
    initial = generate_scripts(base_state)
    base_state.update(initial)
    base_state["flow_repair_counts"] = {"login": 2}
    base_state["current_script_index"] = 0

    result = regenerate_current_flow(base_state)
    assert result["status"] == "regenerated"
    assert "login" in result["flows_regenerated"]
    assert result["flow_repair_counts"]["login"] == 0
    assert result["repaired_script"] is not None

    store = ScriptStore(base_state["url"])
    entry = store.get_flow_entry("login")
    assert entry is not None
    assert entry["source"] == "regenerated"
