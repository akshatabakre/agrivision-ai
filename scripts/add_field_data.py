"""Step 1b - add real field photographs (PlantDoc) to the dataset.

PlantVillage images are lab photos on plain backgrounds; PlantDoc (Singh et al.,
2020, CC-BY-4.0) has the same crops and diseases photographed in the field.
This maps PlantDoc's class names onto the PlantVillage labels, drops unreadable
files and writes data/field_manifest.csv:

    PlantDoc train -> 85% train / 15% val      PlantDoc test -> test (field accuracy)

    python scripts/add_field_data.py
"""
from __future__ import annotations

import csv
import random
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PIL import Image  # noqa: E402

from agrivision import config  # noqa: E402

FIELD_DIR = config.DATA_DIR / "plantdoc"
FIELD_MANIFEST = config.DATA_DIR / "field_manifest.csv"

# PlantDoc folder name (lower-case) -> PlantVillage label
LABEL_MAP = {
    "apple scab leaf": "Apple___Apple_scab",
    "apple leaf": "Apple___healthy",
    "apple rust leaf": "Apple___Cedar_apple_rust",
    "bell_pepper leaf": "Pepper,_bell___healthy",
    "bell_pepper leaf spot": "Pepper,_bell___Bacterial_spot",
    "blueberry leaf": "Blueberry___healthy",
    "cherry leaf": "Cherry___healthy",
    "corn gray leaf spot": "Corn___Cercospora_leaf_spot Gray_leaf_spot",
    "corn leaf blight": "Corn___Northern_Leaf_Blight",
    "corn rust leaf": "Corn___Common_rust",
    "peach leaf": "Peach___healthy",
    "potato leaf": "Potato___healthy",
    "potato leaf early blight": "Potato___Early_blight",
    "potato leaf late blight": "Potato___Late_blight",
    "raspberry leaf": "Raspberry___healthy",
    "soyabean leaf": "Soybean___healthy",
    "soybean leaf": "Soybean___healthy",
    "squash powdery mildew leaf": "Squash___Powdery_mildew",
    "strawberry leaf": "Strawberry___healthy",
    "tomato early blight leaf": "Tomato___Early_blight",
    "tomato septoria leaf spot": "Tomato___Septoria_leaf_spot",
    "tomato leaf": "Tomato___healthy",
    "tomato leaf bacterial spot": "Tomato___Bacterial_spot",
    "tomato leaf late blight": "Tomato___Late_blight",
    "tomato leaf mosaic virus": "Tomato___Tomato_mosaic_virus",
    "tomato leaf yellow virus": "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
    "tomato mold leaf": "Tomato___Leaf_Mold",
    "tomato two spotted spider mites leaf": "Tomato___Spider_mites Two-spotted_spider_mite",
    "grape leaf": "Grape___healthy",
    "grape leaf black rot": "Grape___Black_rot",
}
IMG_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def main():
    zip_path = config.DATA_DIR / "plantdoc.zip"
    rng = random.Random(42)
    rows, unmapped = [], Counter()
    with zipfile.ZipFile(zip_path) as zf:
        for name in zf.namelist():
            p = Path(name)
            if p.suffix.lower() not in IMG_EXT or len(p.parts) < 3:
                continue
            split_dir, cls_dir = p.parts[-3].lower(), p.parts[-2]
            if split_dir not in ("train", "test"):
                continue
            label = LABEL_MAP.get(cls_dir.strip().lower())
            if label is None:
                unmapped[cls_dir] += 1
                continue
            # Some PlantDoc file names contain '?' and other characters Windows forbids
            safe = re.sub(r'[<>:"/\\|?*]', "_", p.stem)[:100] + p.suffix.lower()
            out = FIELD_DIR / split_dir / cls_dir.replace(" ", "_") / safe
            if not out.exists():
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_bytes(zf.read(name))
            try:  # data cleaning: PlantDoc contains a few corrupt / non-image files
                with Image.open(out) as im:
                    im.convert("RGB").load()
            except Exception:
                out.unlink(missing_ok=True)
                continue
            split = "test" if split_dir == "test" else ("val" if rng.random() < 0.15 else "train")
            rows.append((str(out.relative_to(config.ROOT)), label, split))

    with open(FIELD_MANIFEST, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["path", "label", "split"])
        w.writerows(rows)

    if unmapped:
        print("Not mapped (no matching class):", dict(unmapped))
    print(f"Wrote {FIELD_MANIFEST}: {dict(Counter(r[2] for r in rows))}")
    print(f"{len({r[1] for r in rows})} classes covered")


if __name__ == "__main__":
    main()
