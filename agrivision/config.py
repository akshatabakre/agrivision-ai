"""Central configuration: paths, thresholds and model settings."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = ROOT / "data"
RAW_DATASET_DIR = DATA_DIR / "plantvillage"          # extracted class folders live here
MANIFEST_PATH = DATA_DIR / "manifest.csv"           # train/val/test split list
FEATURE_CACHE = DATA_DIR / "features.npz"

MODELS_DIR = ROOT / "models"
MODEL_PATH = MODELS_DIR / "agrivision_mobilenetv3.pt"
METRICS_PATH = MODELS_DIR / "metrics.json"
CONFUSION_PNG = MODELS_DIR / "confusion_matrix.png"
THRESHOLD_PNG = MODELS_DIR / "threshold_curve.png"

STORAGE_DIR = ROOT / "storage"
DB_PATH = STORAGE_DIR / "agrivision.db"
UPLOAD_DIR = STORAGE_DIR / "uploads"
REPORT_DIR = STORAGE_DIR / "reports"

KB_PATH = Path(__file__).resolve().parent / "knowledge_base.json"

# Model input
IMG_SIZE = 224
IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)

# Below this top-1 confidence the system abstains and asks for a re-capture
# instead of recommending a treatment (slide 12: False Diagnosis Rate).
CONFIDENCE_THRESHOLD = 0.60
# Field photos (cluttered background) get a stricter threshold, chosen during
# training so that at most this share of answered field photos is misdiagnosed.
FIELD_TARGET_FDR = 0.20

# Image validation
MIN_RESOLUTION = 64           # px, shortest side
BLUR_THRESHOLD = 40.0         # variance of Laplacian below this = blurry
DARK_THRESHOLD = 40           # mean brightness (0-255)
BRIGHT_THRESHOLD = 225
MIN_LEAF_FRACTION = 0.05      # leaf mask must cover at least 5% of the frame

# Health score bands (slide 8)
SEVERITY_BANDS = [
    (90, "Healthy"),
    (70, "Mild"),
    (40, "Moderate"),
    (0, "Severe"),
]

# A diagnosis of the same problem in the same field within this window
# is treated as a recurring outbreak and escalated.
RECURRENCE_WINDOW_DAYS = 30

for _d in (DATA_DIR, MODELS_DIR, STORAGE_DIR, UPLOAD_DIR, REPORT_DIR):
    _d.mkdir(parents=True, exist_ok=True)
