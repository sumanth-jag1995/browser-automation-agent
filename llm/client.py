"""Anthropic LLM client with deterministic mock fallback for offline/CI runs."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

from config import get_settings

logger = logging.getLogger(__name__)


class LLMClient:
    """Wrapper around Anthropic API with mock responses when no API key is set."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._client: Any = None
        if self.settings.llm_enabled:
            from anthropic import Anthropic

            self._client = Anthropic(api_key=self.settings.anthropic_api_key)

    def complete(self, prompt: str, system: str = "") -> str:
        if not self.settings.llm_enabled:
            logger.info("Using mock LLM response (no API key or mock mode enabled)")
            return self._mock_response(prompt)

        assert self._client is not None
        message = self._client.messages.create(
            model=self.settings.anthropic_model,
            max_tokens=4096,
            system=system or "You are a browser automation expert. Respond concisely.",
            messages=[{"role": "user", "content": prompt}],
        )
        text_blocks = [block.text for block in message.content if block.type == "text"]
        return "\n".join(text_blocks)

    def complete_json(self, prompt: str, system: str = "") -> dict[str, Any]:
        raw = self.complete(prompt, system=system)
        return self._parse_json(raw)

    @staticmethod
    def load_prompt(name: str) -> str:
        path = Path(__file__).resolve().parent.parent / "prompts" / f"{name}.txt"
        return path.read_text(encoding="utf-8")

    @staticmethod
    def _parse_json(raw: str) -> dict[str, Any]:
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\n?", "", cleaned)
            cleaned = re.sub(r"\n?```$", "", cleaned)
        return json.loads(cleaned)

    @staticmethod
    def _mock_response(prompt: str) -> str:
        lower = prompt.lower()
        if "user journeys" in lower or "discover" in lower:
            return json.dumps(
                ["login", "browse_products", "add_to_cart", "checkout", "payment"]
            )
        if "diagnos" in lower or "failure" in lower or "root cause" in lower:
            return json.dumps(
                {
                    "failure_type": "selector",
                    "severity": "critical",
                    "root_cause": "checkout button selector changed",
                    "fix_strategy": "use data-testid locator",
                }
            )
        if "repair" in lower or "fix" in lower:
            return json.dumps(
                {
                    "repaired_script": (
                        'async def run(page, url: str, screenshot_dir: str) -> dict:\n'
                        '    import os\n'
                        '    result = {"status": "success", "screenshots": []}\n'
                        '    try:\n'
                        '        await page.goto(url, wait_until="domcontentloaded", timeout=60000)\n'
                        '        await page.wait_for_load_state("networkidle", timeout=30000)\n'
                        '        os.makedirs(screenshot_dir, exist_ok=True)\n'
                        '        path = os.path.join(screenshot_dir, "repaired_flow.png")\n'
                        '        await page.screenshot(path=path, full_page=True)\n'
                        '        result["screenshots"].append(path)\n'
                        '    except Exception as exc:\n'
                        '        result = {"status": "fail", "error": type(exc).__name__ + ": " + str(exc)}\n'
                        '    return result\n'
                    )
                }
            )
        if "playwright" in lower or "script" in lower:
            return json.dumps({"scripts": []})
        return json.dumps({"status": "ok"})
