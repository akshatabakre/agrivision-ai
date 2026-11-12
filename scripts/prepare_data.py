"""Step 1 - dataset pipeline: raw images -> cleaning -> labelling -> train/val/test.

Samples up to N images per class straight from the PlantVillage zip (only the
sampled files are extracted), drops unreadable files and writes a stratified
70/15/15 split to data/manifest.csv.

    python scripts/prepare_data.py --per-class 400
"""
from __future__ import annotations

import argparse
import csv
import random
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PIL import Image  # noqa: E402

from agrivision import config  # noqa: E402
from agrivision.recommender import load_kb  # noqa: E402

IMG_EXT = {".jpg", ".jpeg", ".png", ".bmp"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", default=str(config.DATA_DIR / "plantvillage.zip"))
    ap.add_argument("--per-class", type=int, default=400, help="0 = use every image")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    by_class: dict[str, list[str]] = defaultdict(list)
    with zipfile.ZipFile(args.zip) as zf:
        for name in zf.namelist():
            p = Path(name)
            if p.suffix.lower() in IMG_EXT and len(p.parts) >= 2:
                by_class[p.parts[-2]].append(name)

        print(f"Found {len(by_class)} classes, {sum(map(len, by_class.values()))} images")
        kb = load_kb()["classes"]
        missing = [c for c in by_class if c not in kb]
        if missing:
            print("WARNING - no knowledge-base entry for:", missing)

        rows = []
        for cls in sorted(by_class):
            files = sorted(by_class[cls])
            rng.shuffle(files)
            if args.per_class:
                files = files[: args.per_class]
            n = len(files)
            n_val = n_test = max(1, round(n * 0.15))
            for i, name in enumerate(files):
                split = "test" if i < n_test else "val" if i < n_test + n_val else "train"
                rows.append((name, cls, split))

        print(f"Extracting {len(rows)} sampled images ...")
        config.RAW_DATASET_DIR.mkdir(parents=True, exist_ok=True)
        clean = []
        for i, (name, cls, split) in enumerate(rows, 1):
            out = config.RAW_DATASET_DIR / cls / Path(name).name
            if not out.exists():
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_bytes(zf.read(name))
            try:  # data cleaning: drop corrupt / unreadable images
                with Image.open(out) as im:
                    im.verify()
            except Exception:
                print("  skipping corrupt file", out)
                continue
            clean.append((str(out.relative_to(config.ROOT)), cls, split))
            if i % 2000 == 0:
                print(f"  {i}/{len(rows)}")

    with open(config.MANIFEST_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["path", "label", "split"])
        w.writerows(clean)

    counts = defaultdict(int)
    for _, _, s in clean:
        counts[s] += 1
    print(f"Wrote {config.MANIFEST_PATH} - {dict(counts)}")


if __name__ == "__main__":
    main()
