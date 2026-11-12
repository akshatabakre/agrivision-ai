"""Step 3 - evaluation on the held-out test split (slide 13).

Classification metrics: accuracy, precision, recall, F1, confusion matrix.
Plus the metric that actually matters: the False Diagnosis Rate at each
confidence threshold, i.e. how often a treatment would be recommended for the
wrong problem, against how often the system abstains.

    python scripts/evaluate.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import torch  # noqa: E402
from sklearn.metrics import (accuracy_score, classification_report,  # noqa: E402
                             confusion_matrix, precision_recall_fscore_support)

from agrivision import config  # noqa: E402
from agrivision.model import build_head  # noqa: E402
from agrivision.recommender import class_info  # noqa: E402


def evaluate():
    npz = np.load(config.FEATURE_CACHE)
    ckpt = torch.load(config.MODEL_PATH, map_location="cpu", weights_only=False)
    classes = ckpt["classes"]
    head = build_head(len(classes), ckpt.get("head", "linear"))
    head.load_state_dict({k.removeprefix("head."): v for k, v in ckpt["state_dict"].items()
                          if k.startswith("head.")})
    head.eval()

    x, y = torch.from_numpy(npz["x_test"]), npz["y_test"]
    with torch.no_grad():
        probs = torch.softmax(head(x) / ckpt["temperature"], 1).numpy()
    pred, conf = probs.argmax(1), probs.max(1)

    acc = accuracy_score(y, pred)
    p, r, f1, _ = precision_recall_fscore_support(y, pred, average="macro", zero_division=0)
    names = [f"{class_info(c)['crop']} - {class_info(c)['name']}" if class_info(c)["crop"] != "-"
             else class_info(c)["name"] for c in classes]
    report = classification_report(y, pred, target_names=names, output_dict=True, zero_division=0)

    cats = np.array([class_info(c)["category"] for c in classes])
    cat_acc = float((cats[pred] == cats[y]).mean())

    # Abstention sweep
    sweep = []
    for t in np.round(np.arange(0.0, 0.96, 0.05), 2):
        answered = conf >= t
        n = int(answered.sum())
        wrong = int((pred[answered] != y[answered]).sum())
        sweep.append({"threshold": float(t), "coverage": n / len(y),
                      "false_diagnosis_rate": wrong / n if n else 0.0,
                      "accuracy_answered": 1 - wrong / n if n else 1.0})
    at = next(s for s in sweep if abs(s["threshold"] - config.CONFIDENCE_THRESHOLD) < 1e-6)

    metrics = {
        "test_images": int(len(y)),
        "train_images": ckpt.get("train_size"),
        "num_classes": len(classes),
        "accuracy": acc, "precision_macro": p, "recall_macro": r, "f1_macro": f1,
        "category_accuracy": cat_acc,
        "val_accuracy": ckpt["metrics"].get("val_accuracy"),
        "temperature": ckpt["temperature"],
        "confidence_threshold": config.CONFIDENCE_THRESHOLD,
        "coverage_at_threshold": at["coverage"],
        "false_diagnosis_rate_at_threshold": at["false_diagnosis_rate"],
        "false_diagnosis_rate_no_abstention": sweep[0]["false_diagnosis_rate"],
        "threshold_sweep": sweep,
        "per_class": {k: v for k, v in report.items() if k in names},
    }

    # Field photographs (PlantDoc test split) - the "lab images are not field images" check
    field_cache = config.DATA_DIR / "field_features.npz"
    if field_cache.exists():
        f = np.load(field_cache)

        def field_probs(xf):
            with torch.no_grad():
                return torch.softmax(head(torch.from_numpy(xf)) / ckpt["temperature"], 1).numpy()

        fy = f["y_test"]
        plain = field_probs(f["x_test"])
        tta = (plain + field_probs(f["x_test_flip"])) / 2   # test-time mirror augmentation

        field_t = float(ckpt.get("field_threshold", config.CONFIDENCE_THRESHOLD))

        def summarise(pp):
            pr, cf = pp.argmax(1), pp.max(1)
            answered = cf >= field_t
            top3 = np.argsort(pp, 1)[:, -3:]
            return {
                "accuracy": float((pr == fy).mean()),
                "top3_accuracy": float(np.mean([fy[i] in top3[i] for i in range(len(fy))])),
                "f1_macro": float(precision_recall_fscore_support(
                    fy, pr, labels=np.unique(fy), average="macro", zero_division=0)[2]),
                "category_accuracy": float((cats[pr] == cats[fy]).mean()),
                "coverage_at_threshold": float(answered.mean()),
                "false_diagnosis_rate_at_threshold":
                    float((pr[answered] != fy[answered]).mean()) if answered.any() else 0.0,
            }

        metrics["field"] = {"dataset": "PlantDoc test split", "test_images": int(len(fy)),
                            "confidence_threshold": field_t,
                            **summarise(plain), "with_mirror_tta": summarise(tta)}

        # Same field test, scored by the earlier lab-only model (kept for comparison)
        baseline = config.MODELS_DIR / "lab_only_model_backup.pt"
        if baseline.exists():
            b = torch.load(baseline, map_location="cpu", weights_only=False)
            bh = build_head(len(b["classes"]), b.get("head", "linear"))
            bh.load_state_dict({k.removeprefix("head."): v for k, v in b["state_dict"].items()
                                if k.startswith("head.")})
            with torch.no_grad():
                bp = bh.eval()(torch.from_numpy(f["x_test"])).argmax(1).numpy()
            metrics["field_baseline_accuracy"] = float((bp == fy).mean())
    with open(config.METRICS_PATH, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    # Confusion matrix (row-normalised)
    cm = confusion_matrix(y, pred, labels=range(len(classes)), normalize="true")
    fig, ax = plt.subplots(figsize=(14, 12))
    im = ax.imshow(cm, cmap="Greens", vmin=0, vmax=1)
    ax.set_xticks(range(len(names)), names, rotation=90, fontsize=7)
    ax.set_yticks(range(len(names)), names, fontsize=7)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_title(f"AgriVision AI - confusion matrix (test accuracy {acc:.1%})")
    fig.colorbar(im, fraction=0.03)
    fig.tight_layout()
    fig.savefig(config.CONFUSION_PNG, dpi=110)
    plt.close(fig)

    # Coverage vs false diagnosis rate
    ts = [s["threshold"] for s in sweep]
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(ts, [s["coverage"] * 100 for s in sweep], label="Coverage (% images answered)", color="#2e7d32")
    ax.plot(ts, [s["false_diagnosis_rate"] * 100 for s in sweep], label="False diagnosis rate (%)",
            color="#c0392b")
    ax.axvline(config.CONFIDENCE_THRESHOLD, ls="--", color="#888")
    ax.text(config.CONFIDENCE_THRESHOLD + 0.01, 50, "chosen threshold", color="#666", fontsize=8)
    ax.set_xlabel("Confidence threshold")
    ax.set_ylabel("%")
    ax.set_title("Abstain vs. misdiagnose trade-off")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(config.THRESHOLD_PNG, dpi=110)
    plt.close(fig)

    print("=" * 60)
    print(f"Test images            {len(y)}")
    print(f"Accuracy               {acc:.4f}")
    print(f"Precision / Recall / F1 (macro)  {p:.4f} / {r:.4f} / {f1:.4f}")
    print(f"Category routing acc.  {cat_acc:.4f}  (disease / pest / healthy / not-a-leaf)")
    print(f"False diagnosis rate   {sweep[0]['false_diagnosis_rate']:.4f} without abstention")
    print(f"                       {at['false_diagnosis_rate']:.4f} at threshold "
          f"{config.CONFIDENCE_THRESHOLD} (answers {at['coverage']:.1%} of images)")
    if "field" in metrics:
        fm = metrics["field"]
        if "field_baseline_accuracy" in metrics:
            print(f"FIELD, lab-only model   acc {metrics['field_baseline_accuracy']:.4f}  (before PlantDoc)")
        for label, s in (("FIELD (PlantDoc)", fm), ("FIELD + mirror TTA", fm["with_mirror_tta"])):
            print(f"{label:22} acc {s['accuracy']:.4f}  top-3 {s['top3_accuracy']:.4f}  "
                  f"F1 {s['f1_macro']:.4f}  category {s['category_accuracy']:.4f}  "
                  f"FDR@{fm['confidence_threshold']} {s['false_diagnosis_rate_at_threshold']:.4f} "
                  f"(answers {s['coverage_at_threshold']:.1%})")
    print(f"Saved {config.METRICS_PATH.name}, {config.CONFUSION_PNG.name}, {config.THRESHOLD_PNG.name}")
    print("=" * 60)
    return metrics


if __name__ == "__main__":
    evaluate()
