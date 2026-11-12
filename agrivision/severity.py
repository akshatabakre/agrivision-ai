"""Severity estimation: turns the share of visibly damaged leaf tissue into a
0-100 crop health score and a Healthy / Mild / Moderate / Severe band."""
from __future__ import annotations

import numpy as np

from . import config

BAND_ORDER = ["Healthy", "Mild", "Moderate", "Severe"]
# Highest score allowed for each band - used to enforce severity floors
BAND_MAX = {"Healthy": 100, "Mild": 89, "Moderate": 69, "Severe": 39}


def damage_stats(leaf: np.ndarray, maps: dict[str, np.ndarray]) -> dict[str, float]:
    # Denominator = classified tissue only, so glare / shadow don't dilute or inflate damage
    area = max(int(sum(m.sum() for m in maps.values())), 1)
    stats = {k: float(m.sum()) / area for k, m in maps.items()}
    stats["affected"] = min(1.0, stats["yellow"] + stats["brown"] + stats["white"])
    return stats


def band(score: float) -> str:
    for lower, name in config.SEVERITY_BANDS:
        if score >= lower:
            return name
    return "Severe"


def leaf_damage_score(affected: float) -> float:
    """Non-linear: the first lesions cost less than the last healthy tissue.
    5% damage -> 92, 15% -> 77, 30% -> 56, 45% -> 38."""
    return 100.0 * (1.0 - affected) ** 1.6


def health_score(category: str, affected: float, confidence: float,
                 severity_floor: str | None = None) -> int:
    if category == "healthy":
        # A confident healthy verdict on clean tissue scores 90-100
        score = 90 + 10 * confidence * (1 - min(affected, 0.5) * 2)
    elif category == "nutrient":
        score = min(max(leaf_damage_score(affected), 40), BAND_MAX["Mild"])
    else:
        # Disease / pest confirmed by the model: at least "Mild" whatever the pixel count
        score = min(leaf_damage_score(affected), BAND_MAX["Mild"])
        if severity_floor:
            score = min(score, BAND_MAX[severity_floor])
    return int(round(max(0.0, min(100.0, score))))
