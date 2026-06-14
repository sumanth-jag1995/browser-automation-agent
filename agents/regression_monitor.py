"""Regression Monitor Agent — detects visual changes via pixel comparison."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from config import get_settings
from state.schema import AgentState

logger = logging.getLogger(__name__)


def _compare_images(current_path: Path, baseline_path: Path, threshold: float = 0.01) -> dict[str, Any]:
    if not baseline_path.exists():
        shutil.copy2(current_path, baseline_path)
        return {
            "changed_pixels": 0,
            "regression_detected": False,
            "baseline_created": True,
            "current": str(current_path),
            "baseline": str(baseline_path),
        }

    current = np.array(Image.open(current_path).convert("RGB"))
    baseline = np.array(Image.open(baseline_path).convert("RGB"))

    if current.shape != baseline.shape:
        baseline_img = Image.open(baseline_path).convert("RGB")
        baseline_img = baseline_img.resize((current.shape[1], current.shape[0]))
        baseline = np.array(baseline_img)

    diff = np.abs(current.astype(np.int16) - baseline.astype(np.int16))
    changed = int(np.sum(np.any(diff > 10, axis=2)))
    total_pixels = current.shape[0] * current.shape[1]
    ratio = changed / total_pixels if total_pixels else 0.0

    return {
        "changed_pixels": changed,
        "change_ratio": round(ratio, 4),
        "regression_detected": ratio > threshold,
        "current": str(current_path),
        "baseline": str(baseline_path),
    }


def monitor_regression(state: AgentState) -> dict[str, Any]:
    settings = get_settings()
    settings.baseline_dir.mkdir(parents=True, exist_ok=True)
    settings.screenshot_dir.mkdir(parents=True, exist_ok=True)

    screenshots = state.get("screenshots", [])
    logger.info("Checking regression for %d screenshots", len(screenshots))

    comparisons: list[dict[str, Any]] = []
    regressions = 0

    for shot in screenshots:
        current_path = Path(shot)
        if not current_path.exists():
            continue
        baseline_path = settings.baseline_dir / current_path.name
        result = _compare_images(current_path, baseline_path)
        comparisons.append(result)
        if result.get("regression_detected"):
            regressions += 1

    summary = {
        "comparisons": comparisons,
        "regressions": regressions,
        "changed_pixels": sum(c.get("changed_pixels", 0) for c in comparisons),
        "regression_detected": regressions > 0,
    }

    return {"regression_diff": summary, "status": "regression_checked"}
