"""Generate every figure and data table used in the project report.

All numbers are computed from the trained model, the cached embeddings and the
real pipeline, so the report always matches the system.

    python report/make_figures.py
"""
from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import torch  # noqa: E402
import torch.nn as nn  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402
from PIL import Image  # noqa: E402
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support  # noqa: E402

from agrivision import config, preprocessing as pp, severity  # noqa: E402
from agrivision.model import build_head  # noqa: E402
from agrivision.pipeline import get_engine  # noqa: E402
from agrivision.recommender import class_info  # noqa: E402

FIG = Path(__file__).resolve().parent / "figures"
FIG.mkdir(exist_ok=True)
DATA_OUT = Path(__file__).resolve().parent / "report_data.json"

GREEN, ORANGE, RED, BLUE, INK, MUTED = "#3a6b35", "#d9822b", "#c0392b", "#2b6c9e", "#221c16", "#8a7d6e"
plt.rcParams.update({
    "font.family": "serif", "font.serif": ["Times New Roman", "DejaVu Serif"],
    "font.size": 10, "axes.titlesize": 11, "axes.labelsize": 10,
    "axes.spines.top": False, "axes.spines.right": False, "savefig.dpi": 220,
    "savefig.bbox": "tight", "mathtext.fontset": "stix",
})


def short_name(c):
    i = class_info(c)
    return i["name"] if i["crop"] == "-" else f"{i['crop'].replace(' (Corn)', '').replace('Citrus (Orange)', 'Citrus')} - {i['name']}"


# ---------------------------------------------------------------- model + features
ckpt = torch.load(config.MODEL_PATH, map_location="cpu", weights_only=False)
classes = ckpt["classes"]
T = ckpt["temperature"]


def load_head(c):
    h = build_head(len(c["classes"]), c.get("head", "linear"))
    h.load_state_dict({k.removeprefix("head."): v for k, v in c["state_dict"].items() if k.startswith("head.")})
    return h.eval()


head = load_head(ckpt)
base = load_head(torch.load(config.MODELS_DIR / "lab_only_model_backup.pt", map_location="cpu", weights_only=False))
lab = np.load(config.FEATURE_CACHE)
fld = np.load(config.DATA_DIR / "field_features.npz")


def probs(h, x, t=1.0):
    with torch.no_grad():
        return torch.softmax(h(torch.from_numpy(x)) / t, 1).numpy()


p_lab, p_fld = probs(head, lab["x_test"], T), probs(head, fld["x_test"], T)
b_lab, b_fld = probs(base, lab["x_test"]), probs(base, fld["x_test"])
y_lab, y_fld = lab["y_test"], fld["y_test"]
metrics = json.loads(config.METRICS_PATH.read_text())

# ---------------------------------------------------------------- 1. architecture diagram


def box(ax, x, y, w, h, text, fc, ec=None, tc="white", fs=9.5, bold=True):
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
                                fc=fc, ec=ec or fc, lw=1.2))
    ax.text(x, y, text, ha="center", va="center", color=tc, fontsize=fs,
            fontweight="bold" if bold else "normal", linespacing=1.25)


def arrow(ax, a, b, color=INK, style="-|>", rad=0.0, ls="-"):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle=style, mutation_scale=12, color=color, lw=1.2,
                                 connectionstyle=f"arc3,rad={rad}", linestyle=ls))


fig, ax = plt.subplots(figsize=(8.6, 10.2))
ax.set_xlim(0, 10)
ax.set_ylim(0, 12.4)
ax.axis("off")
layers = [(11.55, "CLIENT LAYER"), (9.95, "SERVICE LAYER"), (8.35, "VISION LAYER"),
          (5.6, "DECISION LAYER"), (3.05, "KNOWLEDGE LAYER"), (1.15, "OUTPUT & STORAGE")]
for y, t in layers:
    ax.text(0.05, y, t, fontsize=7.5, color=MUTED, rotation=90, va="center", ha="left", family="monospace")
box(ax, 3.3, 11.55, 3.2, 0.8, "Web application\n(Streamlit)", GREEN)
box(ax, 7.2, 11.55, 3.2, 0.8, "Android application\n(Kotlin, Jetpack Compose)", GREEN)
box(ax, 5.25, 9.95, 5.2, 0.75, "REST API (FastAPI)  -  /analyze  /history  /report", INK)
arrow(ax, (3.3, 11.13), (4.4, 10.35))
arrow(ax, (7.2, 11.13), (6.1, 10.35))
box(ax, 2.9, 8.35, 3.4, 1.05, "Image validation &\npreprocessing\n(resolution, blur, exposure, CLAHE)", BLUE, fs=8.8)
box(ax, 7.4, 8.35, 3.6, 1.05, "Leaf segmentation\n(colour thresholds / focus-seeded\nGrabCut) + lesion colour maps", BLUE, fs=8.8)
arrow(ax, (5.25, 9.55), (2.9, 8.9))
arrow(ax, (4.6, 8.35), (5.55, 8.35))
box(ax, 2.9, 6.75, 3.4, 0.95, "MobileNetV3-Large backbone\n+ MLP head (39 classes)\ntemperature-calibrated", ORANGE, fs=8.8)
arrow(ax, (2.9, 7.8), (2.9, 7.25))
box(ax, 2.9, 5.35, 3.0, 0.75, "Confidence >= threshold?", "#f6e7d3", ec=ORANGE, tc=INK, fs=9)
arrow(ax, (2.9, 6.27), (2.9, 5.75))
box(ax, 1.45, 4.1, 1.5, 0.7, "Abstain:\nre-capture", RED, fs=8.3)
arrow(ax, (2.2, 4.98), (1.65, 4.47), color=RED)
ax.text(1.55, 4.8, "no", fontsize=8, color=RED)
box(ax, 3.9, 4.1, 2.6, 0.7, "Disease / Pest / Healthy\nrouting", ORANGE, fs=8.6)
arrow(ax, (3.3, 4.98), (3.7, 4.47))
ax.text(3.6, 4.85, "yes", fontsize=8, color=GREEN)
box(ax, 7.4, 6.6, 3.6, 0.85, "Severity estimation\n(damaged area → health score 0–100)", "#6b5b95", fs=8.8)
box(ax, 7.4, 5.2, 3.6, 0.85, "Nutrient screening\n(N / K / Fe-Mg colour patterns)", "#6b5b95", fs=8.8)
arrow(ax, (7.4, 7.82), (7.4, 7.05))
arrow(ax, (7.4, 6.17), (7.4, 5.65))
box(ax, 5.25, 3.05, 5.6, 0.85, "Recommendation engine  +  knowledge base\n(crop, severity, growth stage, weather, soil, region, history)",
    "#7a4f2a", fs=8.8)
arrow(ax, (3.9, 3.74), (4.4, 3.48))
arrow(ax, (7.4, 4.77), (6.9, 3.48))
box(ax, 2.9, 1.15, 3.0, 0.8, "Crop health report\n(screen + PDF)", GREEN)
box(ax, 7.6, 1.15, 3.0, 0.8, "SQLite diagnosis\nhistory", INK)
arrow(ax, (4.3, 2.62), (3.2, 1.56))
arrow(ax, (6.2, 2.62), (7.3, 1.56))
arrow(ax, (8.9, 1.56), (8.0, 2.62), color=MUTED, rad=-0.35, ls="--")
ax.text(9.25, 2.05, "recurrence\ncheck", fontsize=7.5, color=MUTED, ha="center")
fig.savefig(FIG / "fig_architecture.png")
plt.close(fig)

# ---------------------------------------------------------------- 2. qualitative pipeline grids
engine = get_engine()
field_rows = {Path(r["path"]).name: r for r in csv.DictReader(open(config.DATA_DIR / "field_manifest.csv", encoding="utf-8"))}


def field_path(name):
    return ROOT / field_rows[name]["path"]


examples = [
    ("Laboratory image", ROOT / "samples" / "tomato_early_blight.jpg", {}),
    ("Laboratory image", ROOT / "samples" / "potato_early_blight.jpg", {}),
    ("Field photograph", field_path("185161-004-EAF28842.jpg"), {}),
    ("Field photograph", field_path("Black%20rot%20on%20foliage.jpg"), {}),
]
quals = []
fig, axes = plt.subplots(len(examples), 4, figsize=(8.4, 2.25 * len(examples)))
for r, (kind, path, ctx) in enumerate(examples):
    res, imgs = engine.analyze(path.read_bytes(), ctx, save=False)
    rgb = imgs["original"]
    leaf = pp.segment_leaf(rgb)
    mask_vis = np.where(leaf[..., None], np.array([58, 107, 53], np.uint8), np.array([235, 228, 214], np.uint8))
    panels = [rgb, mask_vis, imgs["overlay"], None]
    for c, im in enumerate(panels):
        a = axes[r, c]
        a.axis("off")
        if im is not None:
            a.imshow(im)
    a = axes[r, 3]
    col = {"Healthy": GREEN, "Mild": "#b8961a", "Moderate": ORANGE, "Severe": RED}.get(res["severity"], MUTED)
    lines = [(kind, 8, MUTED, "normal"), (f"{res['crop']}", 9, INK, "normal"),
             (res["display_name"], 10.5, col, "bold"),
             (f"Confidence {res['confidence']:.0%}", 9, INK, "normal"),
             (f"Severity {res['severity']}", 9, col, "normal"),
             (f"Health score {res['health_score']}/100", 9, INK, "normal"),
             (f"Damaged tissue {res['damage']['affected']:.0%}", 9, INK, "normal")]
    for k, (t, fs, cl, w) in enumerate(lines):
        a.text(0.02, 0.92 - k * 0.135, t, fontsize=fs, color=cl, fontweight=w, transform=a.transAxes, va="top")
    quals.append({"kind": kind, "file": path.name, "crop": res["crop"], "diagnosis": res["display_name"],
                  "confidence": res["confidence"], "severity": res["severity"], "score": res["health_score"],
                  "affected": res["damage"]["affected"], "photo_type": res["photo_type"]})
for c, t in enumerate(["(a) Input", "(b) Leaf segmentation", "(c) Damage map", "(d) System output"]):
    axes[0, c].set_title(t, fontsize=10)
fig.tight_layout()
fig.savefig(FIG / "fig_qualitative.png")
plt.close(fig)

# Field challenges: abstention, misclassification, severity underestimation
hard = [("(a) Correct abstention", field_path("1234080-Early-Blight.jpg"), "Tomato - Early Blight", "original"),
        ("(b) Misclassification", field_path("55830b60a7cf2.image.jpg"), "Tomato - Septoria Leaf Spot", "original"),
        ("(c) Severity underestimated", field_path("2540_600.jpg"), "Potato - Late Blight", "overlay")]
fig, axes = plt.subplots(1, 3, figsize=(8.4, 3.9))
for a, (title, path, truth, view) in zip(axes, hard):
    res, imgs = engine.analyze(path.read_bytes(), {}, save=False)
    a.imshow(imgs[view])
    a.set_xticks([])
    a.set_yticks([])
    a.set_title(title, fontsize=10)
    out = res["display_name"] if res["status"] == "ok" else "Re-capture requested"
    extra = (f"top class {res['top_k'][0]['name']} ({res['top_k'][0]['probability']:.0%})"
             if res["status"] != "ok" else
             f"confidence {res['confidence']:.0%}, damage {res['damage']['affected']:.0%}")
    a.set_xlabel(f"Truth: {truth}\nOutput: {out}\n{extra}", fontsize=8.5, labelpad=6)
fig.tight_layout()
fig.savefig(FIG / "fig_field_cases.png")
plt.close(fig)

# ---------------------------------------------------------------- 3. segmentation comparison on a field photo
fpath = field_path("Powdery-Mildew-on-squash.jpg")
rgb = pp.limit_size(pp.load_image(str(fpath)))
naive = pp._largest_filled(pp._plant_pixels(rgb))
grab = pp.segment_leaf(rgb)
fig, axes = plt.subplots(1, 3, figsize=(8.4, 2.6))
for a, im, t in zip(axes, [rgb, pp.overlay(rgb, naive, pp.colour_maps(rgb, naive)),
                           pp.overlay(rgb, grab, pp.colour_maps(rgb, grab))],
                    ["(a) Field photograph", f"(b) Colour threshold only ({naive.mean():.0%} of frame)",
                     f"(c) Focus-seeded GrabCut ({grab.mean():.0%} of frame)"]):
    a.imshow(im)
    a.axis("off")
    a.set_title(t, fontsize=9.5)
fig.tight_layout()
fig.savefig(FIG / "fig_segmentation.png")
plt.close(fig)

# ---------------------------------------------------------------- 4. confusion matrix (lab)
pred_lab = p_lab.argmax(1)
cm = confusion_matrix(y_lab, pred_lab, labels=range(len(classes)), normalize="true")
names = [short_name(c) for c in classes]
fig, ax = plt.subplots(figsize=(8.6, 8.2))
im = ax.imshow(cm, cmap="Greens", vmin=0, vmax=1)
ax.set_xticks(range(len(names)), names, rotation=90, fontsize=5.6)
ax.set_yticks(range(len(names)), names, fontsize=5.6)
ax.set_xlabel("Predicted class")
ax.set_ylabel("True class")
ax.spines[:].set_visible(True)
cb = fig.colorbar(im, fraction=0.035, pad=0.02)
cb.ax.tick_params(labelsize=7)
fig.savefig(FIG / "fig_confusion.png")
plt.close(fig)

# ---------------------------------------------------------------- 5. coverage / FDR trade-off (lab + field)


def sweep(p, y):
    pred, conf = p.argmax(1), p.max(1)
    ts = np.linspace(0, 0.97, 98)
    cov, fdr = [], []
    for t in ts:
        a = conf >= t
        cov.append(a.mean() * 100)
        fdr.append((pred[a] != y[a]).mean() * 100 if a.any() else 0)
    return ts, np.array(cov), np.array(fdr)


fig, axes = plt.subplots(1, 2, figsize=(8.4, 3.2), sharey=True)
for a, (p, y, t, title) in zip(axes, [(p_lab, y_lab, config.CONFIDENCE_THRESHOLD, "(a) Laboratory test set"),
                                      (p_fld, y_fld, ckpt["field_threshold"], "(b) Field test set")]):
    ts, cov, fdr = sweep(p, y)
    a.plot(ts, cov, color=GREEN, lw=2, label="Coverage (% answered)")
    a.plot(ts, fdr, color=RED, lw=2, label="False diagnosis rate (%)")
    a.axvline(t, color=MUTED, ls="--", lw=1)
    a.text(t + 0.015, 55, f"threshold {t:.2f}", fontsize=8, color=MUTED)
    a.set_title(title)
    a.set_xlabel("Confidence threshold")
    a.grid(alpha=0.25)
axes[0].set_ylabel("Percentage")
axes[0].legend(fontsize=8, loc="center left")
fig.tight_layout()
fig.savefig(FIG / "fig_threshold.png")
plt.close(fig)

# ---------------------------------------------------------------- 6. lab vs field, before / after
acc = lambda p, y: float((p.argmax(1) == y).mean())  # noqa: E731
domain = {"base_lab": acc(b_lab, y_lab), "base_field": acc(b_fld, y_fld),
          "final_lab": acc(p_lab, y_lab), "final_field": acc(p_fld, y_fld)}
fig, ax = plt.subplots(figsize=(6.4, 3.2))
xs = np.arange(2)
w = 0.34
b1 = ax.bar(xs - w / 2, [domain["base_lab"] * 100, domain["base_field"] * 100], w, color="#c9bfae",
            label="Trained on laboratory images only")
b2 = ax.bar(xs + w / 2, [domain["final_lab"] * 100, domain["final_field"] * 100], w, color=GREEN,
            label="Trained on laboratory + field images")
for bars in (b1, b2):
    for b in bars:
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 1.5, f"{b.get_height():.1f}%",
                ha="center", fontsize=9)
ax.set_xticks(xs, ["Laboratory test set\n(PlantVillage, 2,270 images)", "Field test set\n(PlantDoc, 236 images)"])
ax.set_ylabel("Top-1 accuracy (%)")
ax.set_ylim(0, 110)
ax.legend(fontsize=8.5, frameon=False, loc="upper right")
fig.tight_layout()
fig.savefig(FIG / "fig_domain_gap.png")
plt.close(fig)

# ---------------------------------------------------------------- 7. accuracy per crop
crop_of = np.array([class_info(c)["crop"] for c in classes])
crops = sorted({c for c in crop_of if c != "-"})
lab_crop, fld_crop = [], []
for c in crops:
    m1 = crop_of[y_lab] == c
    m2 = crop_of[y_fld] == c
    lab_crop.append(acc(p_lab[m1], y_lab[m1]) * 100 if m1.any() else np.nan)
    fld_crop.append(acc(p_fld[m2], y_fld[m2]) * 100 if m2.sum() >= 5 else np.nan)
fig, ax = plt.subplots(figsize=(8.4, 3.3))
xs = np.arange(len(crops))
ax.bar(xs - 0.2, lab_crop, 0.4, color=GREEN, label="Laboratory")
ax.bar(xs + 0.2, np.nan_to_num(fld_crop), 0.4, color=ORANGE, label="Field")
for i, v in enumerate(fld_crop):
    if np.isnan(v):
        ax.text(i + 0.2, 2, "n/a", ha="center", fontsize=6.5, color=MUTED, rotation=90)
ax.set_xticks(xs, [c.replace(" (Corn)", "").replace("Citrus (Orange)", "Citrus") for c in crops], rotation=35,
              ha="right")
ax.set_ylabel("Accuracy (%)")
ax.set_ylim(0, 105)
ax.legend(fontsize=8.5, frameon=False, ncol=2, loc="lower center", bbox_to_anchor=(0.5, 1.0))
ax.grid(axis="y", alpha=0.25)
fig.tight_layout()
fig.savefig(FIG / "fig_per_crop.png")
plt.close(fig)

# ---------------------------------------------------------------- 8. severity curve
a = np.linspace(0, 1, 300)
s = 100 * (1 - a) ** 1.6
fig, ax = plt.subplots(figsize=(6.4, 3.0))
for lo, hi, name, col in [(90, 100, "Healthy", GREEN), (70, 90, "Mild", "#b8961a"),
                          (40, 70, "Moderate", ORANGE), (0, 40, "Severe", RED)]:
    ax.axhspan(lo, hi, color=col, alpha=0.12)
    ax.text(0.985, (lo + hi) / 2, name, ha="right", va="center", fontsize=8.5, color=col)
ax.plot(a * 100, s, color=INK, lw=2)
for pt in (0.05, 0.15, 0.30, 0.45):
    v = 100 * (1 - pt) ** 1.6
    ax.plot(pt * 100, v, "o", color=INK, ms=4)
    ax.annotate(f"{v:.0f}", (pt * 100, v), textcoords="offset points", xytext=(6, 4), fontsize=8)
ax.set_xlabel("Damaged leaf area, a (%)")
ax.set_ylabel("Health score")
ax.set_xlim(0, 100)
ax.set_ylim(0, 102)
fig.tight_layout()
fig.savefig(FIG / "fig_severity.png")
plt.close(fig)

# ---------------------------------------------------------------- 9. training curve (re-run of head training with logging)
torch.manual_seed(0)
FIELD_REPEAT = 4
fx = np.concatenate([fld["x_train"], fld["x_train_flip"]] * FIELD_REPEAT)
fy = np.concatenate([fld["y_train"], fld["y_train"]] * FIELD_REPEAT)
xt = torch.from_numpy(np.concatenate([lab["x_train"], fx]))
yt = torch.from_numpy(np.concatenate([lab["y_train"], fy])).long()
vals = [(torch.from_numpy(lab["x_val"]), torch.from_numpy(lab["y_val"]).long()),
        (torch.from_numpy(fld["x_val"]), torch.from_numpy(fld["y_val"]).long())]
h = build_head(len(classes), "mlp")
opt = torch.optim.AdamW(h.parameters(), lr=1e-3, weight_decay=1e-4)
sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, 80)
lossf = nn.CrossEntropyLoss(label_smoothing=0.05)
hist = {"loss": [], "lab": [], "field": []}
best, patience = 0, 0
for ep in range(80):
    h.train()
    perm = torch.randperm(len(xt))
    tot, n = 0.0, 0
    for i in range(0, len(xt), 128):
        b = perm[i:i + 128]
        opt.zero_grad()
        loss = lossf(h(xt[b]), yt[b])
        loss.backward()
        opt.step()
        tot += loss.item() * len(b)
        n += len(b)
    sched.step()
    h.eval()
    with torch.no_grad():
        accs = [(h(x).argmax(1) == y).float().mean().item() for x, y in vals]
    hist["loss"].append(tot / n)
    hist["lab"].append(accs[0])
    hist["field"].append(accs[1])
    if np.mean(accs) > best:
        best, patience, best_ep = np.mean(accs), 0, ep + 1
    else:
        patience += 1
    if patience >= 15:
        break
ep = np.arange(1, len(hist["loss"]) + 1)
fig, ax1 = plt.subplots(figsize=(6.6, 3.1))
ax1.plot(ep, np.array(hist["lab"]) * 100, color=GREEN, lw=2, label="Validation accuracy - laboratory")
ax1.plot(ep, np.array(hist["field"]) * 100, color=ORANGE, lw=2, label="Validation accuracy - field")
ax1.axvline(best_ep, color=MUTED, ls="--", lw=1)
ax1.text(best_ep + 0.5, 70, f"selected epoch {best_ep}", fontsize=8, color=MUTED)
ax1.set_xlabel("Epoch")
ax1.set_ylabel("Accuracy (%)")
ax1.set_ylim(40, 100)
ax2 = ax1.twinx()
ax2.plot(ep, hist["loss"], color=INK, lw=1.2, ls=":", label="Training loss")
ax2.set_ylabel("Training loss")
ax2.spines["right"].set_visible(True)
l1, n1 = ax1.get_legend_handles_labels()
l2, n2 = ax2.get_legend_handles_labels()
ax1.legend(l1 + l2, n1 + n2, fontsize=8, frameon=False, loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=3)
fig.tight_layout()
fig.savefig(FIG / "fig_training.png")
plt.close(fig)

# ---------------------------------------------------------------- 10. PDF report page + screenshots
import pypdfium2 as pdfium  # noqa: E402
import subprocess  # noqa: E402

subprocess.run([sys.executable, "-W", "ignore", str(ROOT / "scripts" / "sample_report.py")], check=True,
               capture_output=True)
pdf = pdfium.PdfDocument(str(config.REPORT_DIR / "sample_report.pdf"))
pdf[0].render(scale=2.2).to_pil().save(FIG / "fig_pdf_report.png")


def crop(src, dst, box_):
    Image.open(FIG / src).crop(box_).save(FIG / dst)


if (FIG / "webapp_explain_full.png").exists():
    crop("webapp_explain_full.png", "fig_webapp_input.png", (60, 100, 1340, 850))
    crop("webapp_explain_full.png", "fig_webapp_result.png", (60, 905, 1340, 1420))
    crop("webapp_explain_full.png", "fig_webapp_explain.png", (60, 1425, 1340, 2460))
if (FIG / "webapp_model.png").exists():
    crop("webapp_model.png", "fig_webapp_model.png", (60, 255, 1340, 1300))

# ---------------------------------------------------------------- data for tables
lab_prf = precision_recall_fscore_support(y_lab, pred_lab, labels=range(len(classes)), zero_division=0)
pred_fld = p_fld.argmax(1)
per_class = []
for i, c in enumerate(classes):
    m = y_fld == i
    per_class.append({"class": short_name(c), "category": class_info(c)["category"],
                      "lab_p": float(lab_prf[0][i]), "lab_r": float(lab_prf[1][i]), "lab_f1": float(lab_prf[2][i]),
                      "lab_n": int(lab_prf[3][i]),
                      "field_acc": float((pred_fld[m] == i).mean()) if m.any() else None, "field_n": int(m.sum())})
counts = defaultdict(lambda: defaultdict(int))
for path, split in ((config.MANIFEST_PATH, "lab"), (config.DATA_DIR / "field_manifest.csv", "field")):
    for r in csv.DictReader(open(path, encoding="utf-8")):
        counts[f"{split}_{r['split']}"]["n"] += 1
DATA_OUT.write_text(json.dumps({
    "metrics": metrics, "domain": domain, "qualitative": quals, "per_class": per_class,
    "split_counts": {k: v["n"] for k, v in counts.items()},
    "temperature": T, "field_threshold": ckpt["field_threshold"], "train_size": ckpt["train_size"],
    "train_epochs": len(hist["loss"]), "best_epoch": best_ep,
    "head_params": int(sum(p.numel() for p in head.parameters())),
    "backbone_params": int(sum(v.numel() for k, v in ckpt["state_dict"].items() if k.startswith("backbone."))),
}, indent=2))
print("figures:", sorted(p.name for p in FIG.glob("fig_*.png")))
print("domain:", {k: round(v, 4) for k, v in domain.items()}, "best epoch", best_ep, "of", len(hist["loss"]))
