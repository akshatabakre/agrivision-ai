"""Nutrient-deficiency screening from leaf colour patterns (slide 7).

PlantVillage has no deficiency labels, so this module uses explainable OpenCV
rules over the leaf's colour maps instead of a learned classifier:

  N      uniform yellowing across the leaf
  K      yellow / brown damage concentrated at the leaf margins
  Fe/Mg  interveinal chlorosis - yellow lamina with thin green veins

The output is a *probable* pattern; soil or tissue testing must confirm it.
"""
from __future__ import annotations

import cv2
import numpy as np

YELLOW_MIN = 0.12        # share of leaf that must be chlorotic to raise a flag
UNIFORM_YELLOW = 0.25
MARGIN_EXCESS = 0.20     # margin damage must exceed interior damage by this much
VEIN_RATIO = 0.35        # share of green pixels that sit in thin vein-like lines


def screen(leaf: np.ndarray, maps: dict[str, np.ndarray]) -> dict:
    area = int(leaf.sum())
    result = {"pattern": None, "index": 0.0, "evidence": [], "measures": {}}
    if area < 500:
        return result

    yellow, brown, green = maps["yellow"], maps["brown"], maps["green"]
    yellow_frac = float(yellow.sum()) / area

    # Margin band ~ 6% of the leaf's equivalent diameter
    diameter = np.sqrt(4 * area / np.pi)
    k = max(3, int(diameter * 0.06) | 1)
    interior = cv2.erode(leaf.astype(np.uint8), np.ones((k, k), np.uint8)) > 0
    margin = leaf & ~interior
    damaged = yellow | brown
    margin_dmg = float(damaged[margin].mean()) if margin.any() else 0.0
    interior_dmg = float(damaged[interior].mean()) if interior.any() else 0.0

    # Veins: green structures that vanish under a morphological opening are thin
    g = green.astype(np.uint8)
    vk = max(3, int(diameter * 0.015) | 1)
    opened = cv2.morphologyEx(g, cv2.MORPH_OPEN, np.ones((vk, vk), np.uint8)) > 0
    vein_ratio = float((green & ~opened).sum()) / max(int(green.sum()), 1)

    result["measures"] = {
        "yellow_fraction": round(yellow_frac, 3),
        "margin_damage": round(margin_dmg, 3),
        "interior_damage": round(interior_dmg, 3),
        "vein_ratio": round(vein_ratio, 3),
    }
    margin_excess = margin_dmg - interior_dmg
    result["index"] = round(float(np.clip(max(yellow_frac * 2, margin_excess * 2), 0, 1)), 3)

    if margin_excess > MARGIN_EXCESS and margin_dmg > 0.30:
        result["pattern"] = "K"
        result["evidence"].append(
            f"Damage concentrated at the leaf margin ({margin_dmg:.0%} vs {interior_dmg:.0%} inside)")
    elif yellow_frac >= YELLOW_MIN and vein_ratio > VEIN_RATIO:
        result["pattern"] = "Fe/Mg"
        result["evidence"].append(
            f"{yellow_frac:.0%} of the leaf is yellow while thin green vein lines remain")
    elif yellow_frac >= UNIFORM_YELLOW:
        result["pattern"] = "N"
        result["evidence"].append(f"Broad, uniform yellowing over {yellow_frac:.0%} of the leaf")
    return result
