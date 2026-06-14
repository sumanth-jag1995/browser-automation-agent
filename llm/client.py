"""LLM client (Anthropic or OpenRouter) with deterministic mock fallback for offline/CI runs."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

import httpx

from config import get_settings

logger = logging.getLogger(__name__)


class LLMClient:
    """Wrapper around Anthropic or OpenRouter APIs with mock responses when no API key is set."""

    def __init__(self, override: dict[str, Any] | None = None) -> None:
        self.settings = get_settings()
        self._override = override or {}
        self._anthropic_client: Any = None

        # Effective values — override takes precedence over env-based settings
        eff_api_key = self._override.get("openrouter_api_key") or self.settings.openrouter_api_key
        eff_model = self._override.get("openrouter_model") or self.settings.openrouter_model
        mock_forced = bool(self._override.get("use_mock_llm", False))

        self._effective_api_key: str = eff_api_key or ""
        self._effective_model: str = eff_model or ""
        # llm_enabled: False if mock is forced OR if we have no effective API key
        # This respects UI-provided credentials (override) not just env vars
        self.llm_enabled: bool = (not mock_forced) and bool(self._effective_api_key)

        if self.settings.resolved_llm_provider == "anthropic" and self.llm_enabled:
            from anthropic import Anthropic

            self._anthropic_client = Anthropic(api_key=self.settings.anthropic_api_key)

    def complete(self, prompt: str, system: str = "") -> str:
        if not self.llm_enabled:
            logger.info("Using mock LLM response (no API key or mock mode enabled)")
            return self._mock_response(prompt)

        # Determine provider: override takes precedence, then fall back to env-based setting
        if "openrouter_api_key" in self._override:
            provider = "openrouter"
        else:
            provider = self.settings.resolved_llm_provider
        
        if provider == "anthropic":
            return self._complete_anthropic(prompt, system)
        if provider == "openrouter":
            return self._complete_openrouter(prompt, system)
        raise RuntimeError(f"Unsupported LLM provider: {provider}")

    def _complete_anthropic(self, prompt: str, system: str) -> str:
        assert self._anthropic_client is not None
        message = self._anthropic_client.messages.create(
            model=self.settings.llm_model,
            max_tokens=4096,
            system=system or "You are a browser automation expert. Respond concisely.",
            messages=[{"role": "user", "content": prompt}],
        )
        text_blocks = [block.text for block in message.content if block.type == "text"]
        return "\n".join(text_blocks)

    def _complete_openrouter(self, prompt: str, system: str) -> str:
        url = f"{self.settings.openrouter_base_url.rstrip('/')}/chat/completions"
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        else:
            messages.append(
                {
                    "role": "system",
                    "content": "You are a browser automation expert. Respond concisely.",
                }
            )
        messages.append({"role": "user", "content": prompt})

        response = httpx.post(
            url,
            headers={
                "Authorization": f"Bearer {self._effective_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self._effective_model,
                "messages": messages,
                "max_tokens": 4096,
            },
            timeout=120.0,
        )
        if response.status_code != 200:
            raise RuntimeError(
                f"OpenRouter request failed ({response.status_code}): {response.text}"
            )

        data = response.json()
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(f"Unexpected OpenRouter response: {data}") from exc

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
        if "generate a playwright automation script" in lower:
            return json.dumps({"scripts": []})
        if "playwright" in lower or "script" in lower:
            return json.dumps({"scripts": []})
        return json.dumps({"status": "ok"})
