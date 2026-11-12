"""Pick the web app's sample images from the held-out test split, verified against
the current model:

- one correctly diagnosed image per selected class
- hard_case_*: an image the model is unsure about (it asks for a re-capture) but
  diagnoses correctly once the crop is specified - demonstrates abstention and
  the crop selector

    python scripts/make_samples.py
"""
import csv
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from agrivision import config  # noqa: E402
from agrivision.pipeline import get_engine  # noqa: E402
from agrivision.recommender import class_info  # noqa: E402

WANT = {
    "Tomato___Early_blight": "tomato_early_blight",
    "Tomato___Late_blight": "tomato_late_blight",
    "Tomato___healthy": "tomato_healthy",
    "Tomato___Spider_mites Two-spotted_spider_mite": "tomato_spider_mites_pest",
    "Tomato___Tomato_Yellow_Leaf_Curl_Virus": "tomato_yellow_leaf_curl_virus",
    "Potato___Early_blight": "potato_early_blight",
    "Corn___Common_rust": "corn_common_rust",
    "Grape___Black_rot": "grape_black_rot",
    "Squash___Powdery_mildew": "squash_powdery_mildew",
    "Pepper,_bell___Bacterial_spot": "pepper_bacterial_spot",
    "Orange___Haunglongbing_(Citrus_greening)": "orange_citrus_greening",
    "Background_without_leaves": "not_a_leaf_background",
}
HARD = {"Potato___Late_blight": "hard_case_potato_late_blight", "Apple___Apple_scab": "hard_case_apple_scab"}


def main():
    engine = get_engine()
    rows = [r for r in csv.DictReader(open(config.MANIFEST_PATH, encoding="utf-8")) if r["split"] == "test"]
    out = ROOT / "samples"
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir()
    for label, name in WANT.items():
        for r in (r for r in rows if r["label"] == label):
            res, _ = engine.analyze((ROOT / r["path"]).read_bytes(), {}, save=False)
            expected = "invalid" if class_info(label)["category"] == "invalid" else "ok"
            if res["status"] == expected and res["label"] == label:
                shutil.copy(ROOT / r["path"], out / f"{name}.jpg")
                break
        else:
            print("no verified sample for", label)
    for label, name in HARD.items():
        crop = class_info(label)["crop"]
        for r in (r for r in rows if r["label"] == label):
            data = (ROOT / r["path"]).read_bytes()
            auto, _ = engine.analyze(data, {}, save=False)
            fixed, _ = engine.analyze(data, {"crop": crop}, save=False)
            if (auto["status"] == "uncertain" and auto["top_k"][0]["label"] == label
                    and fixed["status"] == "ok" and fixed["label"] == label):
                shutil.copy(ROOT / r["path"], out / f"{name}.jpg")
                break
        else:
            print("no hard case found for", label)
    print(sorted(p.name for p in out.iterdir()))


if __name__ == "__main__":
    main()
