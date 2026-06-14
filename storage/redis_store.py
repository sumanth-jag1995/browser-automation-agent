"""Run state persistence with Redis and in-memory fallback."""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

from config import get_settings

logger = logging.getLogger(__name__)


class RunStore:
    """Persist run status and reports; falls back to memory when Redis is unavailable."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._memory: dict[str, dict[str, Any]] = {}
        self._redis: Any = None
        try:
            import redis

            client = redis.from_url(self.settings.redis_url, decode_responses=True)
            client.ping()
            self._redis = client
            logger.info("Connected to Redis at %s", self.settings.redis_url)
        except Exception as exc:
            logger.warning("Redis unavailable (%s); using in-memory store", exc)

    def _key(self, run_id: str, suffix: str) -> str:
        return f"run:{run_id}:{suffix}"

    def set_status(self, run_id: str, status: str, progress: int = 0) -> None:
        payload = {"status": status, "progress": progress}
        self._write(run_id, "status", payload)

    def get_status(self, run_id: str) -> Optional[dict[str, Any]]:
        return self._read(run_id, "status")

    def set_report(self, run_id: str, report: dict[str, Any]) -> None:
        self._write(run_id, "report", report)

    def get_report(self, run_id: str) -> Optional[dict[str, Any]]:
        return self._read(run_id, "report")

    def _write(self, run_id: str, suffix: str, payload: dict[str, Any]) -> None:
        key = self._key(run_id, suffix)
        data = json.dumps(payload)
        if self._redis:
            self._redis.set(key, data)
        else:
            self._memory.setdefault(run_id, {})[suffix] = payload

    def _read(self, run_id: str, suffix: str) -> Optional[dict[str, Any]]:
        if self._redis:
            raw = self._redis.get(self._key(run_id, suffix))
            return json.loads(raw) if raw else None
        return self._memory.get(run_id, {}).get(suffix)
