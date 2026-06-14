"""Shared test data for automation flows."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

CREDENTIALS_FILE = Path(__file__).resolve().parent / "credentials.json"

DEFAULT_LOGIN = {
    "username": "Admin",
    "password": "admin123",
}


@lru_cache
def _load_credentials_file() -> dict[str, Any]:
    if not CREDENTIALS_FILE.exists():
        return {"login": DEFAULT_LOGIN}
    return json.loads(CREDENTIALS_FILE.read_text(encoding="utf-8"))


def get_login_credentials() -> dict[str, str]:
    """Return login username and password from test data."""
    data = _load_credentials_file()
    login = data.get("login", DEFAULT_LOGIN)
    return {
        "username": str(login.get("username", DEFAULT_LOGIN["username"])),
        "password": str(login.get("password", DEFAULT_LOGIN["password"])),
}


def credentials_file_path() -> Path:
    return CREDENTIALS_FILE
