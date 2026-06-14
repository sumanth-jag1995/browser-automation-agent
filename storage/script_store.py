"""Local filesystem storage for generated Playwright scripts."""

from __future__ import annotations

import hashlib
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from config import get_settings

logger = logging.getLogger(__name__)

MANIFEST_FILE = "manifest.json"


def site_key(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.netloc or parsed.path.strip("/") or "unknown"
    return re.sub(r"[^\w.-]", "_", host)


def compute_flow_hash(url: str, intent: str, flow: str) -> str:
    payload = f"{url}|{intent}|{flow}"
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


class ScriptStore:
    """Persist scripts and manifest on local disk per site."""

    def __init__(self, url: str) -> None:
        settings = get_settings()
        self.url = url
        self.site_dir = settings.scripts_dir / site_key(url)
        self.site_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_path = self.site_dir / MANIFEST_FILE

    def load_manifest(self) -> dict[str, Any]:
        if not self.manifest_path.exists():
            return {"url": self.url, "flows": {}}
        return json.loads(self.manifest_path.read_text(encoding="utf-8"))

    def save_manifest(self, manifest: dict[str, Any]) -> None:
        manifest["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    def script_path(self, flow: str) -> Path:
        safe_flow = re.sub(r"[^\w.-]", "_", flow)
        return self.site_dir / f"{safe_flow}.py"

    def read_script(self, flow: str) -> str | None:
        path = self.script_path(flow)
        if path.exists():
            return path.read_text(encoding="utf-8")
        return None

    def save_script(
        self,
        flow: str,
        script: str,
        *,
        flow_hash: str,
        intent: str,
        source: str,
        repair_count: int = 0,
        last_status: str = "pending",
    ) -> None:
        path = self.script_path(flow)
        path.write_text(script, encoding="utf-8")

        manifest = self.load_manifest()
        manifest["url"] = self.url
        manifest["intent"] = intent
        flows = manifest.setdefault("flows", {})
        flows[flow] = {
            "flow_hash": flow_hash,
            "script_path": path.name,
            "source": source,
            "repair_count": repair_count,
            "last_status": last_status,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        self.save_manifest(manifest)
        logger.info("Saved script for flow=%s source=%s path=%s", flow, source, path)

    def get_flow_entry(self, flow: str) -> dict[str, Any] | None:
        return self.load_manifest().get("flows", {}).get(flow)

    def should_reuse(self, flow: str, flow_hash: str) -> bool:
        entry = self.get_flow_entry(flow)
        if not entry or entry.get("flow_hash") != flow_hash:
            return False
        return self.script_path(flow).exists()

    def update_flow_status(self, flow: str, last_status: str, repair_count: int | None = None) -> None:
        manifest = self.load_manifest()
        flows = manifest.get("flows", {})
        if flow not in flows:
            return
        flows[flow]["last_status"] = last_status
        flows[flow]["updated_at"] = datetime.now(timezone.utc).isoformat()
        if repair_count is not None:
            flows[flow]["repair_count"] = repair_count
        self.save_manifest(manifest)

    def archive_removed_flows(self, active_flows: list[str]) -> list[str]:
        manifest = self.load_manifest()
        flows = manifest.get("flows", {})
        removed = [name for name in flows if name not in active_flows]
        for name in removed:
            flows[name]["archived"] = True
            flows[name]["archived_at"] = datetime.now(timezone.utc).isoformat()
        if removed:
            self.save_manifest(manifest)
        return removed
