"""Step 2 - transfer learning (fastest CPU route).

1. Run the frozen ImageNet MobileNetV3-Large backbone once over every image
   and cache the 1280-d embeddings (data/features.npz, data/field_features.npz).
2. Train only a linear classification head on those embeddings (seconds).
   Lab images (PlantVillage) and field photos (PlantDoc, if prepared with
   scripts/add_field_data.py) are trained together; the field photos are
   oversampled and mirrored so the model learns real backgrounds.
3. Calibrate confidence with temperature scaling on the validation set.
4. Save backbone + head as one offline checkpoint and run the evaluation.

    python scripts/train.py              # extract features (cached) + train
    python scripts/train.py --augment    # also add flipped copies of lab images
    python scripts/train.py --reuse      # reuse all cached features
    python scripts/train.py --no-field   # lab images only
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("TORCH_HOME", str(ROOT / "models" / ".torch"))

import numpy as np  # noqa: E402
import torch  # noqa: E402
import torch.nn as nn  # noqa: E402
from PIL import Image  # noqa: E402
from torch.utils.data import DataLoader, Dataset  # noqa: E402

from agrivision import config  # noqa: E402
from agrivision.model import TRANSFORM, AgriVisionNet, build_backbone, build_head  # noqa: E402

FIELD_MANIFEST = config.DATA_DIR / "field_manifest.csv"
FIELD_CACHE = config.DATA_DIR / "field_features.npz"
FIELD_REPEAT = 4     # field photos count this many times (x2 again with mirroring)
HEAD_KIND = "mlp"


class ImageList(Dataset):
    def __init__(self, paths, flip=False):
        self.paths, self.flip = paths, flip

    def __len__(self):
        return len(self.paths)

    def __getitem__(self, i):
        img = Image.open(config.ROOT / self.paths[i]).convert("RGB")
        img.thumbnail((640, 640))   # some field photos are 4000px; decode cost only
        if self.flip:
            img = img.transpose(Image.FLIP_LEFT_RIGHT)
        return TRANSFORM(img)


@torch.inference_mode()
def extract(backbone, paths, flip=False, tag=""):
    loader = DataLoader(ImageList(paths, flip), batch_size=32, num_workers=2)
    feats, start = [], time.time()
    for i, x in enumerate(loader, 1):
        feats.append(backbone(x).numpy())
        done = min(i * 32, len(paths))
        if i % 20 == 0 or done == len(paths):
            rate = done / (time.time() - start)
            print(f"  [{tag}] {done}/{len(paths)} images  {rate:.0f} img/s  "
                  f"ETA {(len(paths) - done) / rate / 60:.1f} min", flush=True)
    return np.concatenate(feats).astype(np.float32)


def read_manifest(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def lab_features(backbone, classes, augment, reuse):
    """PlantVillage embeddings - reused from cache when the class list matches."""
    if config.FEATURE_CACHE.exists() and (reuse or not augment):
        npz = np.load(config.FEATURE_CACHE)
        if [str(c) for c in npz["classes"]] == classes:
            print("Using cached lab features", config.FEATURE_CACHE.name)
            return {k: npz[k] for k in npz.files if k != "classes"}
    rows = read_manifest(config.MANIFEST_PATH)
    idx = {c: i for i, c in enumerate(classes)}
    data = {}
    for split in ("train", "val", "test"):
        part = [r for r in rows if r["split"] == split]
        paths = [r["path"] for r in part]
        y = np.array([idx[r["label"]] for r in part])
        print(f"Extracting lab {split} features ({len(paths)} images)")
        x = extract(backbone, paths, tag=split)
        if augment and split == "train":
            x = np.concatenate([x, extract(backbone, paths, flip=True, tag="train-flip")])
            y = np.concatenate([y, y])
        data[f"x_{split}"], data[f"y_{split}"] = x, y
    np.savez_compressed(config.FEATURE_CACHE, classes=np.array(classes), **data)
    return data


def field_features(backbone, classes, reuse):
    """PlantDoc embeddings: train + mirrored train, val, test + mirrored test (for TTA)."""
    if reuse and FIELD_CACHE.exists():
        npz = np.load(FIELD_CACHE)
        if [str(c) for c in npz["classes"]] == classes:
            print("Using cached field features", FIELD_CACHE.name)
            return {k: npz[k] for k in npz.files if k != "classes"}
    rows = read_manifest(FIELD_MANIFEST)
    idx = {c: i for i, c in enumerate(classes)}
    data = {}
    for split in ("train", "val", "test"):
        part = [r for r in rows if r["split"] == split]
        paths = [r["path"] for r in part]
        data[f"y_{split}"] = np.array([idx[r["label"]] for r in part])
        print(f"Extracting field {split} features ({len(paths)} images)")
        data[f"x_{split}"] = extract(backbone, paths, tag=f"field-{split}")
        if split in ("train", "test"):
            data[f"x_{split}_flip"] = extract(backbone, paths, flip=True, tag=f"field-{split}-flip")
    np.savez_compressed(FIELD_CACHE, classes=np.array(classes), **data)
    return data


def train_head(x_train, y_train, vals, n_classes, epochs=80, seed=0):
    """vals: list of (x, y) validation sets; model selection uses their mean accuracy."""
    torch.manual_seed(seed)
    head = build_head(n_classes, HEAD_KIND)
    xt, yt = torch.from_numpy(x_train), torch.from_numpy(y_train).long()
    vals = [(torch.from_numpy(x), torch.from_numpy(y).long()) for x, y in vals]
    opt = torch.optim.AdamW(head.parameters(), lr=1e-3, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, epochs)
    loss_fn = nn.CrossEntropyLoss(label_smoothing=0.05)

    best_acc, best_state, patience = 0.0, None, 0
    for epoch in range(1, epochs + 1):
        head.train()
        perm = torch.randperm(len(xt))
        for i in range(0, len(xt), 128):
            b = perm[i:i + 128]
            opt.zero_grad()
            loss = loss_fn(head(xt[b]), yt[b])
            loss.backward()
            opt.step()
        sched.step()
        head.eval()
        with torch.no_grad():
            accs = [(head(xv).argmax(1) == yv).float().mean().item() for xv, yv in vals]
        acc = float(np.mean(accs))
        if acc > best_acc:
            best_acc, best_state, patience = acc, {k: v.clone() for k, v in head.state_dict().items()}, 0
        else:
            patience += 1
        if epoch % 10 == 0:
            print(f"  epoch {epoch:3d}  loss {loss.item():.3f}  val_acc " +
                  " / ".join(f"{a:.4f}" for a in accs) + f"  best(mean) {best_acc:.4f}")
        if patience >= 15:
            print(f"  early stop at epoch {epoch}")
            break
    head.load_state_dict(best_state)
    return head.eval(), best_acc


def fit_temperature(head, x_val, y_val) -> float:
    """Temperature scaling so that '94%' means roughly 94% (slide 11: confidence is always visible)."""
    with torch.no_grad():
        logits = head(torch.from_numpy(x_val))
    y = torch.from_numpy(y_val).long()
    log_t = torch.zeros(1, requires_grad=True)
    opt = torch.optim.LBFGS([log_t], lr=0.1, max_iter=100)

    def closure():
        opt.zero_grad()
        loss = nn.functional.cross_entropy(logits / log_t.exp(), y)
        loss.backward()
        return loss

    opt.step(closure)
    return float(log_t.exp().item())


def pick_field_threshold(head, temperature, x_val, y_val) -> float:
    """Lowest confidence threshold at which answered field photos are misdiagnosed
    at most FIELD_TARGET_FDR of the time (never below the lab threshold)."""
    with torch.no_grad():
        probs = torch.softmax(head(torch.from_numpy(x_val)) / temperature, 1).numpy()
    pred, conf = probs.argmax(1), probs.max(1)
    for t in np.arange(config.CONFIDENCE_THRESHOLD, 0.96, 0.01):
        answered = conf >= t
        if answered.sum() >= 20 and (pred[answered] != y_val[answered]).mean() <= config.FIELD_TARGET_FDR:
            return round(float(t), 2)
    return 0.95


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--augment", action="store_true", help="add flipped copies of lab training images")
    ap.add_argument("--reuse", action="store_true", help="reuse all cached features")
    ap.add_argument("--no-field", action="store_true", help="ignore PlantDoc field photos")
    args = ap.parse_args()

    t0 = time.time()
    classes = sorted({r["label"] for r in read_manifest(config.MANIFEST_PATH)})
    backbone = build_backbone(pretrained=True).eval()
    lab = lab_features(backbone, classes, args.augment, args.reuse)
    use_field = FIELD_MANIFEST.exists() and not args.no_field
    field = field_features(backbone, classes, args.reuse) if use_field else None
    t_feat = time.time() - t0

    x_train, y_train = lab["x_train"], lab["y_train"]
    vals = [(lab["x_val"], lab["y_val"])]
    if field:
        fx = np.concatenate([field["x_train"], field["x_train_flip"]] * FIELD_REPEAT)
        fy = np.concatenate([field["y_train"], field["y_train"]] * FIELD_REPEAT)
        x_train, y_train = np.concatenate([x_train, fx]), np.concatenate([y_train, fy])
        vals.append((field["x_val"], field["y_val"]))
    print(f"Training {HEAD_KIND} head on {len(x_train)} embeddings, {len(classes)} classes "
          f"({'lab + field' if field else 'lab only'})")
    head, val_acc = train_head(x_train, y_train, vals, len(classes))
    temperature = fit_temperature(head, np.concatenate([v[0] for v in vals]),
                                  np.concatenate([v[1] for v in vals]))
    print(f"Best mean val accuracy {val_acc:.4f}; temperature {temperature:.3f}")

    field_threshold = config.CONFIDENCE_THRESHOLD
    if field:
        field_threshold = pick_field_threshold(head, temperature, field["x_val"], field["y_val"])
        print(f"Field-photo confidence threshold {field_threshold:.2f} "
              f"(target false diagnosis rate <= {config.FIELD_TARGET_FDR:.0%})")

    net = AgriVisionNet(len(classes), head_kind=HEAD_KIND)
    net.backbone.load_state_dict(backbone.state_dict())
    net.head.load_state_dict(head.state_dict())
    torch.save({
        "state_dict": net.state_dict(),
        "classes": classes,
        "temperature": temperature,
        "head": HEAD_KIND,
        "field_threshold": field_threshold,
        "backbone": "mobilenet_v3_large (IMAGENET1K_V2)",
        "metrics": {"val_accuracy": val_acc},
        "train_size": int(len(x_train)),
        "datasets": ["PlantVillage"] + (["PlantDoc"] if field else []),
        "feature_seconds": round(t_feat, 1),
    }, config.MODEL_PATH)
    print(f"Saved {config.MODEL_PATH}  ({config.MODEL_PATH.stat().st_size / 1e6:.1f} MB)")
    print(f"Total time {(time.time() - t0) / 60:.1f} min\n")

    from evaluate import evaluate
    evaluate()


if __name__ == "__main__":
    main()
