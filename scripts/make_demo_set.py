"""Build a demo folder of test images that the current model diagnoses correctly.

Every candidate is processed the way the Android app sends it (EXIF-rotated,
longest side <= 1600 px, JPEG quality 92, crop = Auto-detect) and must also
survive heavy recompression (JPEG quality 70, as messaging apps do). Only
held-out test images are used, never training images.

    python scripts/make_demo_set.py
"""
from __future__ import annotations

import csv
import io
import random
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PIL import Image, ImageOps  # noqa: E402

from agrivision import config  # noqa: E402
from agrivision.pipeline import get_engine  # noqa: E402

OUT = ROOT / "demo_images"

# (label, source, preferred confidence range) - variety of crops, problem types and confidence
SLOTS = [
    ("Tomato___Early_blight", "field", (0.73, 1.00)),
    ("Corn___Common_rust", "field", (0.85, 1.00)),
    ("Apple___Cedar_apple_rust", "field", (0.73, 0.95)),
    ("Grape___Black_rot", "field", (0.73, 1.00)),
    ("Squash___Powdery_mildew", "field", (0.90, 1.00)),
    ("Potato___Late_blight", "lab", (0.95, 1.00)),
    ("Tomato___Spider_mites Two-spotted_spider_mite", "lab", (0.65, 0.85)),
    ("Pepper,_bell___Bacterial_spot", "lab", (0.75, 0.92)),
    ("Orange___Haunglongbing_(Citrus_greening)", "lab", (0.97, 1.00)),
    ("Strawberry___healthy", "lab", (0.85, 0.99)),
]
FALLBACK = {"Tomato___Early_blight": "Tomato___Late_blight"}


def app_bytes(path: Path, quality: int = 92) -> bytes:
    """Re-create what the Android app uploads."""
    img = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    img.thumbnail((1600, 1600))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality)
    return buf.getvalue()


def check(engine, path, label):
    res, _ = engine.analyze(app_bytes(path), {}, save=False)
    if res["status"] != "ok" or res["label"] != label:
        return None
    res2, _ = engine.analyze(app_bytes(path, quality=70), {}, save=False)
    if res2["status"] != "ok" or res2["label"] != label:
        return None
    return res


def main():
    engine = get_engine()
    rng = random.Random(7)
    pools = {"lab": [r for r in csv.DictReader(open(config.MANIFEST_PATH, encoding="utf-8")) if r["split"] == "test"],
             "field": [r for r in csv.DictReader(open(config.DATA_DIR / "field_manifest.csv", encoding="utf-8"))
                       if r["split"] == "test"]}
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "extra_safety_checks").mkdir(parents=True)

    chosen = []
    for label, source, (lo, hi) in SLOTS:
        for lab in (label, FALLBACK.get(label)):
            if lab is None:
                continue
            cands = [r for r in pools[source] if r["label"] == lab]
            rng.shuffle(cands)
            passing = []
            for r in cands[:60]:
                p = ROOT / r["path"]
                if min(Image.open(p).size) < 200:
                    continue
                res = check(engine, p, lab)
                if res:
                    passing.append((p, res))
                    if lo <= res["confidence"] <= hi:
                        break
            if passing:
                mid = (lo + hi) / 2
                in_range = [x for x in passing if lo <= x[1]["confidence"] <= hi]
                chosen.append((source, *(in_range or sorted(passing, key=lambda x: abs(x[1]["confidence"] - mid)))[0]))
                break
        else:
            print("no passing image for", label)

    rows = []
    for i, (source, p, res) in enumerate(chosen, 1):
        name = f"{i:02d}_{res['crop'].split(' (')[0].lower().replace(' ', '_')}_" \
               f"{res['display_name'].lower().replace(' ', '_').replace('(', '').replace(')', '')}.jpg"
        Image.open(p).convert("RGB").save(OUT / name, quality=95)
        rows.append((name, source, res))
        print(f"{name:60} {source:5} {res['confidence']:.0%} {res['severity']:8} {res['health_score']}")

    # Safety-feature demos: a non-leaf image, and a field photo the system declines to diagnose
    extras = []
    bg = [r for r in pools["lab"] if r["label"] == "Background_without_leaves"]
    rng.shuffle(bg)
    for r in bg[:20]:
        res, _ = engine.analyze(app_bytes(ROOT / r["path"]), {}, save=False)
        if res["status"] == "invalid":
            Image.open(ROOT / r["path"]).convert("RGB").save(OUT / "extra_safety_checks" / "A_not_a_leaf.jpg", quality=95)
            extras.append(("A_not_a_leaf.jpg", "Rejected: 'No crop leaf was recognised'"))
            break
    fld = pools["field"][:]
    rng.shuffle(fld)
    for r in fld:
        res, _ = engine.analyze(app_bytes(ROOT / r["path"]), {}, save=False)
        res2, _ = engine.analyze(app_bytes(ROOT / r["path"], 70), {}, save=False)
        if res["status"] == res2["status"] == "uncertain" and res["top_k"][0]["label"] == r["label"]:
            Image.open(ROOT / r["path"]).convert("RGB").save(OUT / "extra_safety_checks" / "B_uncertain_recapture.jpg",
                                                             quality=95)
            extras.append(("B_uncertain_recapture.jpg",
                           f"Abstains ({res['confidence']:.0%} confidence): asks for a re-capture; "
                           f"true class {res['top_k'][0]['crop']} - {res['top_k'][0]['name']} is its top guess"))
            break

    lines = ["# AgriVision AI - demo images", "",
             "All images are from the held-out **test sets** (never used in training) and were verified with the "
             "current model exactly as the Android app sends them, with **Crop = Auto-detect** and no field context.",
             "", "| File | Source dataset | Expected diagnosis | Confidence | Severity | Health score |",
             "|---|---|---|---|---|---|"]
    for name, source, res in rows:
        lines.append(f"| {name} | {'PlantDoc (field)' if source == 'field' else 'PlantVillage (lab)'} | {res['crop']} - "
                     f"{res['display_name']} ({res['category_label']}) | {res['confidence']:.0%} | {res['severity']} | "
                     f"{res['health_score']}/100 |")
    lines += ["", "## extra_safety_checks", ""]
    lines += [f"- **{n}** - {d}" for n, d in extras]
    lines += ["", "Confidence and health score can differ by a point or two from this table because the phone "
              "re-compresses the photo.", ""]
    (OUT / "DEMO_GUIDE.md").write_text("\n".join(lines), encoding="utf-8")
    print("extras:", extras)


if __name__ == "__main__":
    main()
