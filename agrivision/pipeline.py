"""End-to-end workflow (slide 5):

image -> validation & preprocessing -> CV model -> disease / pest / nutrient
      -> severity assessment -> recommendation engine -> crop health report
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import numpy as np
from PIL import Image

from . import config, database, nutrient, preprocessing as pp, severity
from .model import Classifier
from .recommender import class_info, load_kb, recommend

CATEGORY_LABELS = {"disease": "Disease", "pest": "Pest", "nutrient": "Nutrient deficiency",
                   "healthy": "Healthy", "invalid": "Not a leaf"}


class AgriVision:
    def __init__(self, model_path=config.MODEL_PATH):
        self.clf = Classifier(model_path)
        self.classes = self.clf.classes
        self.info = [class_info(c) for c in self.classes]
        self.categories = np.array([i["category"] for i in self.info])

    @property
    def crops(self) -> list[str]:
        return sorted({i["crop"] for i in self.info if i["category"] != "invalid"})

    def _restrict_to_crop(self, probs: np.ndarray, crop: str | None) -> np.ndarray:
        """If the farmer tells us the crop, only that crop's classes (and 'no leaf') compete."""
        if not crop or crop not in self.crops:
            return probs
        keep = np.array([i["crop"] == crop or i["category"] == "invalid" for i in self.info])
        out = np.where(keep, probs, 0.0)
        return out / out.sum() if out.sum() > 0 else probs

    def analyze(self, data, context: dict | None = None, save: bool = True,
                filename: str | None = None) -> tuple[dict, dict[str, np.ndarray]]:
        ctx = {k: v for k, v in (context or {}).items() if v not in (None, "", "Not specified")}
        messages: list[str] = []

        # 1. Validation & preprocessing
        rgb = pp.limit_size(pp.load_image(data))
        leaf = pp.segment_leaf(rgb)
        quality = pp.assess_quality(rgb, leaf)
        if quality.brightness < 70:
            rgb = pp.enhance(rgb)
            leaf = pp.segment_leaf(rgb)
            quality.enhanced = True
            quality.leaf_fraction = float(leaf.mean())
        if not leaf.any():
            leaf = np.ones(rgb.shape[:2], dtype=bool)

        # 2. AI classification
        raw_probs = self.clf.predict(rgb)
        probs = self._restrict_to_crop(raw_probs, ctx.get("crop"))
        order = np.argsort(probs)[::-1]
        top = int(order[0])
        label, conf = self.classes[top], float(probs[top])
        info = self.info[top]
        category = info["category"]

        if ctx.get("crop") and probs is not raw_probs:
            auto_top = int(np.argmax(raw_probs))
            if self.info[auto_top]["crop"] != ctx["crop"] and raw_probs[auto_top] > 0.6:
                messages.append(f"Note: the image looks more like a {self.info[auto_top]['crop']} leaf "
                                f"than {ctx['crop']}. Check the selected crop.")

        # 3. Lesion & nutrient analysis
        maps = pp.colour_maps(rgb, leaf)
        dmg = severity.damage_stats(leaf, maps)
        nut = nutrient.screen(leaf, maps)

        cat_p = {c: float(probs[self.categories == c].sum()) for c in ("disease", "pest", "healthy", "invalid")}
        # Nutrient stress is only separable among leaves the model sees as disease-free
        nut_share = cat_p["healthy"] * nut["index"] if nut["pattern"] else 0.0
        category_probs = {
            "Disease": cat_p["disease"], "Pest": cat_p["pest"],
            "Nutrient deficiency": nut_share, "Healthy": cat_p["healthy"] - nut_share,
            "Not a leaf": cat_p["invalid"],
        }

        # 4. Decide: abstain, or diagnose. Field photos (cluttered background) are
        #    harder, so they must clear a stricter, separately calibrated threshold.
        field_photo = not pp.is_plain_background(rgb)
        threshold = self.clf.field_threshold if field_photo else config.CONFIDENCE_THRESHOLD
        status = "ok"
        if category == "invalid":
            status = "invalid"
            messages.insert(0, "No crop leaf was recognised in this image. Photograph a single leaf "
                               "filling most of the frame.")
        elif conf < threshold:
            status = "uncertain"
            messages.insert(0, f"Low confidence ({conf:.0%}). The model is not sure enough to recommend "
                               "a treatment - please re-capture: one leaf, daylight, plain background, in focus.")
        messages.extend(quality.issues)

        display_name, cause = info["name"], info.get("cause", "")
        symptoms = list(info.get("symptoms", []))
        if status == "ok" and category == "healthy" and nut["pattern"] and nut["index"] >= 0.25:
            category = "nutrient"
            n_info = load_kb()["nutrients"][nut["pattern"]]
            display_name = f"Probable {n_info['name']}"
            cause = "Nutrient deficiency pattern detected by leaf colour analysis"
            symptoms = n_info["signature"] + nut["evidence"]
        elif category == "healthy":
            display_name = f"Healthy {info['crop']}"
            cause = "No visible abnormality"

        if status == "ok":
            score = severity.health_score(category, dmg["affected"], conf, info.get("severity_floor"))
            sev = severity.band(score)
            recurrence = database.recurrence_count(ctx.get("field_id"), label) if category != "healthy" else 0
            rec = recommend(label, category, sev, ctx, recurrence, nut["pattern"]).__dict__
        else:
            score, sev, recurrence = None, "Unknown", 0
            rec = {"urgency": "Re-capture", "actions": [], "notes": [], "prevention": []}
            if status == "uncertain":
                display_name = "Uncertain - re-capture needed"
                cause = "Possible: " + ", ".join(
                    f"{self.info[i]['crop']} {self.info[i]['name']} ({probs[i]:.0%})" for i in order[:3])

        result = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "status": status,
            "messages": messages,
            "label": label,
            "display_name": display_name,
            "crop": info["crop"] if category != "invalid" else (ctx.get("crop") or "-"),
            "category": category,
            "category_label": CATEGORY_LABELS[category],
            "cause": cause,
            "symptoms": symptoms,
            "confidence": conf,
            "confidence_threshold": threshold,
            "photo_type": "field" if field_photo else "plain background",
            "severity": sev,
            "health_score": score,
            "recurrence": recurrence,
            "top_k": [{"label": self.classes[i], "crop": self.info[i]["crop"], "name": self.info[i]["name"],
                       "probability": float(probs[i])} for i in order[:5]],
            "category_probs": category_probs,
            "damage": {k: round(v, 4) for k, v in dmg.items()},
            "nutrient": nut,
            "quality": {"width": quality.width, "height": quality.height,
                        "blur_score": round(quality.blur_score, 1),
                        "brightness": round(quality.brightness, 1),
                        "leaf_fraction": round(quality.leaf_fraction, 3), "enhanced": quality.enhanced},
            "recommendation": rec,
            "context": ctx,
            "model": "MobileNetV3-Large (transfer learning)",
        }
        images = {
            "original": rgb,
            "leaf": pp.background_removed(rgb, leaf),
            "overlay": pp.overlay(rgb, leaf, maps),
        }

        if save:
            stem = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            path = config.UPLOAD_DIR / f"{stem}.jpg"
            Image.fromarray(rgb).save(path, quality=90)
            result["image_file"] = filename or path.name
            result["id"] = database.save(result, str(path.relative_to(config.ROOT)))
        return result, images


_instance: AgriVision | None = None


def get_engine() -> AgriVision:
    global _instance
    if _instance is None:
        _instance = AgriVision()
    return _instance


def images_for(record: dict) -> dict[str, np.ndarray]:
    """Rebuild report images for a stored diagnosis."""
    path = record.get("image_path")
    if not path or not (config.ROOT / path).exists():
        return {}
    rgb = np.array(Image.open(config.ROOT / Path(path)).convert("RGB"))
    leaf = pp.segment_leaf(rgb)
    return {"original": rgb, "overlay": pp.overlay(rgb, leaf, pp.colour_maps(rgb, leaf))}
