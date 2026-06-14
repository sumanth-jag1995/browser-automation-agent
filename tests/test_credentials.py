"""Tests for login credentials test data."""

from __future__ import annotations

import json

from test_data import credentials_file_path, get_login_credentials


def test_credentials_file_exists() -> None:
    assert credentials_file_path().exists()


def test_login_credentials_values() -> None:
    creds = get_login_credentials()
    assert creds["username"] == "Admin"
    assert creds["password"] == "admin123"


def test_login_script_uses_credentials() -> None:
    from agents.script_generator import build_script

    script = build_script("login", "https://example.com")
    assert "Admin" in script
    assert "admin123" in script
    assert 'input[name="password"]' in script
    assert "credentials.json" in script
