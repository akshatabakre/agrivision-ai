"""Image assets for the presentation: phone-screenshot placeholders, a rendered
sample PDF report, and square crops of the example leaf images.

    python presentation/make_assets.py
"""
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
A = HERE / "assets"
A.mkdir(exist_ok=True)
FONTS = Path("C:/Windows/Fonts")

PLACEHOLDERS = {
    "ph_diagnose": "Diagnose screen",
    "ph_result": "Result screen",
    "ph_actions": "Recommended actions",
    "ph_history": "History screen",
    "ph_report": "PDF report opened\non the phone",
    "ph_context": "Field context &\nsensor readings",
    "ph_damage": "\u201cHow the AI saw it\u201d\n(damage map)",
}


def placeholder(name, label, w=540, h=1200):
    """Phone-shaped (9:20) placeholder; in PowerPoint: right-click > Change Picture."""
    img = Image.new("RGB", (w, h), (250, 245, 236))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([6, 6, w - 7, h - 7], radius=46, outline=(34, 28, 22), width=8)
    # dashed inner frame
    x0, y0, x1, y1 = 34, 70, w - 35, h - 70
    dash, gap = 18, 12
    for x in range(x0, x1, dash + gap):
        d.line([(x, y0), (min(x + dash, x1), y0)], fill=(138, 125, 110), width=3)
        d.line([(x, y1), (min(x + dash, x1), y1)], fill=(138, 125, 110), width=3)
    for y in range(y0, y1, dash + gap):
        d.line([(x0, y), (x0, min(y + dash, y1))], fill=(138, 125, 110), width=3)
        d.line([(x1, y), (x1, min(y + dash, y1))], fill=(138, 125, 110), width=3)
    d.rounded_rectangle([w // 2 - 60, 26, w // 2 + 60, 40], radius=7, fill=(34, 28, 22))   # speaker slot
    mono = ImageFont.truetype(str(FONTS / "consola.ttf"), 26)
    size = 44   # shrink long labels so they stay inside the phone frame
    while size > 24 and max(ImageFont.truetype(str(FONTS / "georgiab.ttf"), size).getlength(line)
                            for line in label.split("\n")) > w - 110:
        size -= 2
    serif = ImageFont.truetype(str(FONTS / "georgiab.ttf"), size)
    small = ImageFont.truetype(str(FONTS / "calibri.ttf"), 28)
    # camera glyph
    cx, cy = w // 2, h // 2 - 190
    d.rounded_rectangle([cx - 70, cy - 45, cx + 70, cy + 50], radius=16, outline=(58, 107, 53), width=7)
    d.ellipse([cx - 30, cy - 22, cx + 30, cy + 38], outline=(58, 107, 53), width=7)
    d.rectangle([cx - 30, cy - 60, cx + 10, cy - 45], fill=(58, 107, 53))
    d.text((cx, h // 2 - 70), "APP SCREENSHOT", font=mono, fill=(138, 125, 110), anchor="mm")
    d.multiline_text((cx, h // 2 + 20), label, font=serif, fill=(34, 28, 22), anchor="mm", align="center", spacing=10)
    d.multiline_text((cx, h - 190), "Right-click \u2192 Change Picture\nto insert the screenshot", font=small,
                     fill=(138, 125, 110), anchor="mm", align="center", spacing=8)
    img.save(A / f"{name}.png")


for n, l in PLACEHOLDERS.items():
    placeholder(n, l)

# Sample PDF report (current model) rendered to an image
subprocess.run([sys.executable, "-W", "ignore", str(ROOT / "scripts" / "sample_report.py")], check=True,
               capture_output=True)
import pypdfium2 as pdfium  # noqa: E402

pdf = pdfium.PdfDocument(str(ROOT / "storage" / "reports" / "sample_report.pdf"))
pdf[0].render(scale=2.0).to_pil().save(A / "pdf_report_page.png")
pdf.close()

# Square crops of the example images (centre crop)
for p in A.glob("ex_*_*.png"):
    if p.stem.endswith("_sq"):
        continue
    im = Image.open(p)
    s = min(im.size)
    l, t = (im.width - s) // 2, (im.height - s) // 2
    im.crop((l, t, l + s, t + s)).resize((600, 600)).save(A / f"{p.stem}_sq.png")
print(sorted(x.name for x in A.iterdir()))
