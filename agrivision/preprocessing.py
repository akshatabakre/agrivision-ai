"""OpenCV image pipeline: validation, quality enhancement, leaf detection and
colour-based lesion / chlorosis maps.

All functions take and return RGB uint8 numpy arrays unless stated otherwise.
"""
from __future__ import annotations

import io
from dataclasses import dataclass, field

import cv2
import numpy as np
from PIL import Image, ImageOps

from . import config


@dataclass
class QualityReport:
    width: int
    height: int
    blur_score: float
    brightness: float
    leaf_fraction: float
    enhanced: bool = False
    issues: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.issues


def load_image(data: bytes | str | Image.Image) -> np.ndarray:
    """Decode bytes / path / PIL image into an RGB array, honouring EXIF rotation."""
    if isinstance(data, Image.Image):
        img = data
    elif isinstance(data, (bytes, bytearray)):
        img = Image.open(io.BytesIO(data))
    else:
        img = Image.open(data)
    img = ImageOps.exif_transpose(img).convert("RGB")
    return np.array(img)


def limit_size(rgb: np.ndarray, max_side: int = 1024) -> np.ndarray:
    """Downscale very large photos so the OpenCV analysis stays fast."""
    h, w = rgb.shape[:2]
    scale = max_side / max(h, w)
    if scale >= 1:
        return rgb
    return cv2.resize(rgb, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)


def enhance(rgb: np.ndarray) -> np.ndarray:
    """CLAHE on the lightness channel - lifts dark / low-contrast field photos."""
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)
    l, a, b = cv2.split(lab)
    l = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(l)
    return cv2.cvtColor(cv2.merge((l, a, b)), cv2.COLOR_LAB2RGB)


def _background_like(rgb: np.ndarray) -> np.ndarray | None:
    """Pixels whose chroma matches a plain background, estimated from the image
    border. Compares only Lab a/b, so the background's own shadows match too.
    Returns None when the border is not uniform (e.g. a cluttered field photo)."""
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB).astype(np.float32)
    ab = lab[..., 1:]
    h, w = rgb.shape[:2]
    bw = max(2, int(min(h, w) * 0.04))
    border = np.concatenate([ab[:bw].reshape(-1, 2), ab[-bw:].reshape(-1, 2),
                             ab[:, :bw].reshape(-1, 2), ab[:, -bw:].reshape(-1, 2)])
    ref = np.median(border, axis=0)
    if np.percentile(np.linalg.norm(border - ref, axis=1), 70) > 6:
        return None
    return np.linalg.norm(ab - ref, axis=2) < 7


def _plant_pixels(rgb: np.ndarray) -> np.ndarray:
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    h, s, v = (hsv[..., i].astype(np.int16) for i in range(3))
    r, g, b = (rgb[..., i].astype(np.int16) for i in range(3))
    exg = 2 * g - r - b
    # Plant tissue is red / brown / yellow / green; blue-purple casts are background
    plant_hue = (h < 95) | (h > 165)
    return ((s > 45) & (v > 50) & plant_hue) | (exg > 25)


def _largest_filled(mask: np.ndarray, prefer_centre: bool = False) -> np.ndarray:
    """Keep the main component (largest, or largest-and-central) with holes filled."""
    mask = mask.astype(np.uint8) * 255
    k = max(3, int(min(mask.shape) * 0.01) | 1)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return np.zeros(mask.shape, dtype=bool)
    if prefer_centre:
        hh, ww = mask.shape
        diag = np.hypot(hh, ww)

        def score(c):
            m = cv2.moments(c)
            if m["m00"] == 0:
                return 0.0
            dist = np.hypot(m["m10"] / m["m00"] - ww / 2, m["m01"] / m["m00"] - hh / 2) / diag
            return cv2.contourArea(c) * (1.0 - dist)
        best = max(contours, key=score)
    else:
        best = max(contours, key=cv2.contourArea)
    filled = np.zeros_like(mask)
    cv2.drawContours(filled, [best], -1, 255, thickness=cv2.FILLED)
    return filled > 0


def _segment_field(rgb: np.ndarray) -> np.ndarray:
    """Leaf segmentation for cluttered field photos (green foliage / soil behind).

    Colour alone cannot separate a leaf from the leaves behind it, so GrabCut is
    seeded with two cues: plant-coloured pixels that are *in focus* are probable
    leaf (phone cameras focus on the subject), strongly blurred pixels are
    background.
    """
    h0, w0 = rgb.shape[:2]
    scale = min(1.0, 400 / max(h0, w0))
    small = cv2.resize(rgb, (int(w0 * scale), int(h0 * scale)), interpolation=cv2.INTER_AREA)
    hs, ws = small.shape[:2]

    gray = cv2.cvtColor(small, cv2.COLOR_RGB2GRAY).astype(np.float32)
    lap = np.abs(cv2.Laplacian(gray, cv2.CV_32F))
    focus = cv2.GaussianBlur(lap, (0, 0), sigmaX=max(2.0, min(hs, ws) * 0.03))
    focus /= max(float(np.percentile(focus, 99)), 1e-6)
    plant = _plant_pixels(small)

    gc = np.full((hs, ws), cv2.GC_PR_BGD, np.uint8)
    gc[focus < 0.12] = cv2.GC_BGD
    gc[plant & (focus > 0.35)] = cv2.GC_PR_FGD
    if not (gc == cv2.GC_PR_FGD).any() or not np.isin(gc, (cv2.GC_BGD, cv2.GC_PR_BGD)).any():
        return _largest_filled(cv2.resize(plant.astype(np.uint8), (w0, h0)) > 0, prefer_centre=True)

    bgd, fgd = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
    try:
        cv2.grabCut(cv2.cvtColor(small, cv2.COLOR_RGB2BGR), gc, None, bgd, fgd, 5, cv2.GC_INIT_WITH_MASK)
    except cv2.error:
        return _largest_filled(cv2.resize(plant.astype(np.uint8), (w0, h0)) > 0, prefer_centre=True)
    fg = ((gc == cv2.GC_FGD) | (gc == cv2.GC_PR_FGD)).astype(np.uint8)
    fg = cv2.resize(fg, (w0, h0), interpolation=cv2.INTER_NEAREST) > 0
    return _largest_filled(fg, prefer_centre=True)


def is_plain_background(rgb: np.ndarray) -> bool:
    return _background_like(rgb) is not None


def segment_leaf(rgb: np.ndarray) -> np.ndarray:
    """Return a boolean mask of the dominant plant/leaf region.

    Lab-style photos (plain background): plant tissue is saturated while the
    background is not, so we threshold on saturation plus an excess-green
    index and remove anything matching the border colour. Field photos
    (cluttered border) use focus-seeded GrabCut instead. Either way the main
    component is kept and its holes filled so lesions inside the leaf count.
    """
    bg = _background_like(rgb)
    if bg is None:
        return _segment_field(rgb)
    return _largest_filled(_plant_pixels(rgb) & ~bg)


def leaf_crop(rgb: np.ndarray, leaf: np.ndarray, fill: int = 160) -> np.ndarray:
    """Square crop around the leaf with the background replaced by neutral grey -
    makes a field photo look like the lab-style images the model learned from."""
    ys, xs = np.nonzero(leaf)
    if len(ys) == 0:
        return rgb
    out = rgb.copy()
    out[~leaf] = fill
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    side = int(max(y1 - y0, x1 - x0) * 1.08)
    cy, cx = (y0 + y1) // 2, (x0 + x1) // 2
    canvas = np.full((side, side, 3), fill, np.uint8)
    sy0, sx0 = max(0, cy - side // 2), max(0, cx - side // 2)
    sy1, sx1 = min(rgb.shape[0], sy0 + side), min(rgb.shape[1], sx0 + side)
    patch = out[sy0:sy1, sx0:sx1]
    oy, ox = (side - patch.shape[0]) // 2, (side - patch.shape[1]) // 2
    canvas[oy:oy + patch.shape[0], ox:ox + patch.shape[1]] = patch
    return canvas


def colour_maps(rgb: np.ndarray, leaf: np.ndarray) -> dict[str, np.ndarray]:
    """Classify leaf pixels into healthy green, chlorotic yellow, necrotic brown
    and powdery white. Hue uses OpenCV's 0-179 scale. Pixels matching none of
    these (glare, deep shadow, background slivers) are left unclassified and
    excluded from the damage percentages."""
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    h, s, v = (hsv[..., i].astype(np.int16) for i in range(3))

    # Powdery growth: much paler and greyer than this leaf's typical tissue
    if leaf.any():
        med_s, med_v = float(np.median(s[leaf])), float(np.median(v[leaf]))
    else:
        med_s, med_v = 80.0, 120.0
    white = leaf & (s < max(15.0, 0.35 * med_s)) & (v > max(170.0, min(245.0, med_v + 60)))
    # Shaded or waxy green tissue is still green-hued even when dull
    green = leaf & ~white & (h >= 28) & (h <= 95) & (s > 20) & (v > 25)
    yellow = leaf & (h >= 15) & (h < 28) & (s > 60) & (v > 90)
    brown = leaf & ~green & ~yellow & ~white & ((s > 35) | (v < 70)) & (v > 15)
    return {"green": green, "yellow": yellow, "brown": brown, "white": white}


def assess_quality(rgb: np.ndarray, leaf: np.ndarray) -> QualityReport:
    h, w = rgb.shape[:2]
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    # Normalise blur measure to a fixed size so it is comparable across resolutions
    blur = float(cv2.Laplacian(cv2.resize(gray, (512, 512)), cv2.CV_64F).var())
    brightness = float(gray.mean())
    leaf_fraction = float(leaf.mean())

    q = QualityReport(w, h, blur, brightness, leaf_fraction)
    if min(h, w) < config.MIN_RESOLUTION:
        q.issues.append(f"Image is too small ({w}x{h}). Use at least {config.MIN_RESOLUTION}px.")
    if blur < config.BLUR_THRESHOLD:
        q.issues.append("Image looks blurry. Hold the camera steady and focus on the leaf.")
    if brightness < config.DARK_THRESHOLD:
        q.issues.append("Image is too dark. Photograph in daylight.")
    if brightness > config.BRIGHT_THRESHOLD:
        q.issues.append("Image is over-exposed. Avoid direct glare on the leaf.")
    if leaf_fraction < config.MIN_LEAF_FRACTION:
        q.issues.append("No clear leaf / plant region found. Fill the frame with the affected leaf.")
    return q


def overlay(rgb: np.ndarray, leaf: np.ndarray, maps: dict[str, np.ndarray]) -> np.ndarray:
    """Visualise the analysis: leaf outline plus highlighted abnormal tissue."""
    out = rgb.copy()
    tint = out.astype(np.float32)
    colours = {"brown": (230, 60, 40), "yellow": (255, 200, 0), "white": (80, 160, 255)}
    for name, col in colours.items():
        m = maps[name]
        tint[m] = tint[m] * 0.35 + np.array(col, np.float32) * 0.65
    out = tint.astype(np.uint8)
    contours, _ = cv2.findContours(leaf.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(out, contours, -1, (40, 220, 90), max(2, min(rgb.shape[:2]) // 200))
    return out


def background_removed(rgb: np.ndarray, leaf: np.ndarray) -> np.ndarray:
    out = rgb.copy()
    out[~leaf] = (out[~leaf] * 0.15).astype(np.uint8)
    return out
