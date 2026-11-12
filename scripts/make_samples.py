"""Copy one held-out test image per selected class into samples/ for the demo."""
import csv
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from agrivision import config  # noqa: E402

WANT = {
    "Tomato___Early_blight": "tomato_early_blight",
    "Tomato___Late_blight": "tomato_late_blight",
    "Tomato___healthy": "tomato_healthy",
    "Tomato___Spider_mites Two-spotted_spider_mite": "tomato_spider_mites_pest",
    "Tomato___Tomato_Yellow_Leaf_Curl_Virus": "tomato_yellow_leaf_curl_virus",
    "Potato___Early_blight": "potato_early_blight",
    "Potato___Late_blight": "potato_late_blight",
    "Corn___Common_rust": "corn_common_rust",
    "Apple___Apple_scab": "apple_scab",
    "Grape___Black_rot": "grape_black_rot",
    "Squash___Powdery_mildew": "squash_powdery_mildew",
    "Pepper,_bell___Bacterial_spot": "pepper_bacterial_spot",
    "Orange___Haunglongbing_(Citrus_greening)": "orange_citrus_greening",
    "Background_without_leaves": "not_a_leaf_background",
}

out = ROOT / "samples"
out.mkdir(exist_ok=True)
done = set()
with open(config.MANIFEST_PATH, encoding="utf-8") as f:
    for r in csv.DictReader(f):
        if r["split"] == "test" and r["label"] in WANT and r["label"] not in done:
            shutil.copy(ROOT / r["path"], out / f"{WANT[r['label']]}.jpg")
            done.add(r["label"])
print(sorted(p.name for p in out.iterdir()))
