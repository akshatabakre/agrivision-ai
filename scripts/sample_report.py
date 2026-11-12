"""Generate an example PDF report (storage/reports/sample_report.pdf) for the demo / project report.

    python scripts/sample_report.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from agrivision import config, report  # noqa: E402
from agrivision.pipeline import get_engine  # noqa: E402

ctx = {"crop": "Tomato", "field_id": "Demo plot", "region": "Maharashtra", "growth_stage": "Fruiting",
       "temperature": 27.0, "humidity": 85.0}
result, images = get_engine().analyze((ROOT / "samples" / "tomato_early_blight.jpg").read_bytes(), ctx, save=False)
out = config.REPORT_DIR / "sample_report.pdf"
out.write_bytes(report.build_pdf(result, images))
print(out)
