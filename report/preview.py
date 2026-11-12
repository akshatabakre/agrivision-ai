"""Render report pages to PNG for visual checking: python report/preview.py [first] [last] [scale]"""
import sys
from pathlib import Path

import pypdfium2 as pdfium
from PIL import Image

HERE = Path(__file__).resolve().parent
pdf = pdfium.PdfDocument(str(HERE / "AgriVision_AI_Project_Report.pdf"))
n = len(pdf)
first = int(sys.argv[1]) if len(sys.argv) > 1 else 1
last = min(int(sys.argv[2]) if len(sys.argv) > 2 else n, n)
scale = float(sys.argv[3]) if len(sys.argv) > 3 else 0.5
out = Path(sys.argv[4]) if len(sys.argv) > 4 else HERE / "preview"
out.mkdir(exist_ok=True)
pages = [pdf[i].render(scale=scale).to_pil() for i in range(first - 1, last)]
if scale <= 0.5:   # contact sheet, 4 per row
    w, h = pages[0].size
    rows = (len(pages) + 3) // 4
    sheet = Image.new("RGB", (w * 4 + 30, h * rows + 10 * rows), "white")
    for i, p in enumerate(pages):
        sheet.paste(p, ((i % 4) * (w + 10), (i // 4) * (h + 10)))
    sheet.save(out / f"sheet_{first}_{last}.png")
else:
    for i, p in enumerate(pages, first):
        p.save(out / f"page_{i:02d}.png")
print(f"{n} pages; rendered {first}-{last} to {out}")
pdf.close()
