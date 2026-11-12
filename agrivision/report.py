"""PDF crop-health report (slide 11) built with fpdf2."""
from __future__ import annotations

import io
from datetime import datetime

import numpy as np
from fpdf import FPDF
from PIL import Image

BAND_COLOURS = {
    "Healthy": (46, 125, 50), "Mild": (192, 160, 20),
    "Moderate": (214, 120, 30), "Severe": (190, 50, 40),
}
INK = (34, 28, 22)
MUTED = (120, 110, 100)

_REPLACE = {"—": "-", "–": "-", "→": "->", "°": " deg", "’": "'",
            "‘": "'", "“": '"', "”": '"', "•": "-", "≥": ">=", "≤": "<="}


def _t(text) -> str:
    """Core PDF fonts are latin-1 only."""
    s = str(text)
    for a, b in _REPLACE.items():
        s = s.replace(a, b)
    return s.encode("latin-1", "replace").decode("latin-1")


def _png(arr: np.ndarray, max_side: int = 600) -> io.BytesIO:
    img = Image.fromarray(arr)
    img.thumbnail((max_side, max_side))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


class _Report(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*MUTED)
        self.cell(0, 6, "AGRIVISION AI  -  CROP HEALTH REPORT", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(200, 190, 175)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(3)

    def footer(self):
        self.set_y(-14)
        self.set_font("Helvetica", "I", 7.5)
        self.set_text_color(*MUTED)
        self.multi_cell(0, 3.5, _t(
            "AI diagnosis is an early-screening aid, not a definitive agricultural verdict. Confirm "
            "high-impact decisions with an expert or soil / tissue test."), align="C")


def _heading(pdf: FPDF, text: str):
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*MUTED)
    pdf.cell(0, 6, _t(text.upper()), new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(*INK)


def _bullets(pdf: FPDF, items, numbered=False):
    pdf.set_font("Helvetica", "", 10)
    for i, item in enumerate(items, 1):
        prefix = f"{i:02d}  " if numbered else "-  "
        pdf.multi_cell(0, 5.5, _t(prefix + item), new_x="LMARGIN", new_y="NEXT")


def build_pdf(result: dict, images: dict[str, np.ndarray] | None = None) -> bytes:
    pdf = _Report()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()
    ctx = result.get("context", {})

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*MUTED)
    meta = [f"CROP  {result['crop']}", f"DATE  {result['timestamp'][:16].replace('T', ' ')}"]
    if ctx.get("field_id"):
        meta.append(f"FIELD  {ctx['field_id']}")
    if result.get("id"):
        meta.append(f"REPORT #{result['id']}")
    pdf.cell(0, 6, _t("   |   ".join(meta)), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    # Verdict block
    colour = BAND_COLOURS.get(result["severity"], INK)
    pdf.set_font("Times", "B", 24)
    pdf.set_text_color(*(INK if result["status"] != "ok" else colour))
    pdf.multi_cell(0, 10, _t(result["display_name"]), new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(*INK)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 5.5, _t(f"Probable cause: {result['cause']}"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    score = result["health_score"]
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(45, 7, _t(f"Confidence: {result['confidence']:.0%}"))
    pdf.cell(50, 7, _t(f"Severity: {result['severity']}"))
    pdf.cell(0, 7, _t(f"Health score: {score if score is not None else '--'} / 100"),
             new_x="LMARGIN", new_y="NEXT")

    # Health bar
    y = pdf.get_y() + 1
    pdf.set_fill_color(225, 218, 205)
    pdf.rect(10, y, 190, 5, "F")
    if score:
        pdf.set_fill_color(*colour)
        pdf.rect(10, y, 190 * score / 100, 5, "F")
    pdf.set_y(y + 6)
    pdf.set_font("Helvetica", "", 7.5)
    pdf.set_text_color(*MUTED)
    pdf.cell(0, 4, "0-39 SEVERE    40-69 MODERATE    70-89 MILD    90-100 HEALTHY",
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(*INK)

    if result["status"] != "ok":
        _heading(pdf, "Re-capture needed")
        _bullets(pdf, result.get("messages", []))

    # Images
    if images:
        _heading(pdf, "Image analysis")
        y = pdf.get_y()
        keys = [k for k in ("original", "overlay") if k in images]
        for i, key in enumerate(keys):
            pdf.image(_png(images[key]), x=10 + i * 97, y=y, w=90)
        pdf.set_y(y + 92)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*MUTED)
        pdf.cell(0, 4, "Left: uploaded image.  Right: detected leaf (green outline), necrotic tissue (red), "
                       "chlorosis (yellow), powdery growth (blue).", new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(*INK)

    if result.get("symptoms"):
        _heading(pdf, "Observed symptoms (typical for this diagnosis)")
        _bullets(pdf, result["symptoms"])

    rec = result.get("recommendation") or {}
    if rec.get("actions"):
        _heading(pdf, f"Recommended actions  -  urgency: {rec.get('urgency', '')}")
        _bullets(pdf, rec["actions"], numbered=True)
    if rec.get("notes"):
        _heading(pdf, "Context notes")
        _bullets(pdf, rec["notes"])
    if rec.get("prevention"):
        _heading(pdf, "Prevention")
        _bullets(pdf, rec["prevention"])

    _heading(pdf, "Model output")
    pdf.set_font("Courier", "", 9)
    cats = result.get("category_probs", {})
    pdf.multi_cell(0, 4.5, _t("  ".join(f"{k}: {v:.0%}" for k, v in cats.items())),
                   new_x="LMARGIN", new_y="NEXT")
    for cand in result.get("top_k", []):
        pdf.cell(0, 4.5, _t(f"  {cand['probability']:6.1%}  {cand['crop']} - {cand['name']}"),
                 new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "I", 7.5)
    pdf.set_text_color(*MUTED)
    pdf.ln(2)
    pdf.cell(0, 4, _t(f"Generated {datetime.now():%Y-%m-%d %H:%M} by AgriVision AI "
                      f"({result.get('model', 'MobileNetV3')})"), new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())
