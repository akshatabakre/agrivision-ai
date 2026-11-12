"""Build the AgriVision AI project report (PDF).

    python report/make_figures.py      # figures + numbers (once)
    python report/build_report.py      # -> report/AgriVision_AI_Project_Report.pdf
"""
from __future__ import annotations

import io
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from PIL import Image as PILImage  # noqa: E402
from reportlab.lib import colors  # noqa: E402
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT  # noqa: E402
from reportlab.lib.pagesizes import A4  # noqa: E402
from reportlab.lib.styles import ParagraphStyle  # noqa: E402
from reportlab.lib.units import cm  # noqa: E402
from reportlab.pdfbase import pdfmetrics  # noqa: E402
from reportlab.pdfbase.ttfonts import TTFont  # noqa: E402
from reportlab.platypus import (BaseDocTemplate, CondPageBreak, Flowable, Frame, Image, KeepTogether,  # noqa: E402
                                NextPageTemplate, PageBreak, PageTemplate, Paragraph, Spacer, Table,
                                TableStyle)
from reportlab.platypus.tableofcontents import TableOfContents  # noqa: E402

from agrivision.recommender import load_kb  # noqa: E402

FIG = HERE / "figures"
OUT = HERE / "AgriVision_AI_Project_Report.pdf"
D = json.loads((HERE / "report_data.json").read_text())
M = D["metrics"]
FM = M["field"]

# ------------------------------------------------------------------ fonts & palette
FONTS = Path("C:/Windows/Fonts")
pdfmetrics.registerFont(TTFont("TNR", FONTS / "times.ttf"))
pdfmetrics.registerFont(TTFont("TNR-B", FONTS / "timesbd.ttf"))
pdfmetrics.registerFont(TTFont("TNR-I", FONTS / "timesi.ttf"))
pdfmetrics.registerFont(TTFont("TNR-BI", FONTS / "timesbi.ttf"))
pdfmetrics.registerFont(TTFont("Mono", FONTS / "consola.ttf"))
pdfmetrics.registerFontFamily("TNR", normal="TNR", bold="TNR-B", italic="TNR-I", boldItalic="TNR-BI")

INK = colors.HexColor("#1d1d1b")
ACCENT = colors.black                     # headings, rules and labels
ACCENT_LIGHT = colors.HexColor("#ececec")  # table header shading
MUTED = colors.HexColor("#5a5a5a")
RULE = colors.HexColor("#8a8a8a")
W, H = A4
TEXT_W = W - 2.75 * cm - 2.45 * cm

# ------------------------------------------------------------------ styles
body = ParagraphStyle("body", fontName="TNR", fontSize=11.5, leading=16.8, alignment=TA_JUSTIFY,
                      spaceAfter=7, textColor=INK)
body_first = ParagraphStyle("body_first", parent=body)
bullet = ParagraphStyle("bullet", parent=body, leftIndent=18, bulletIndent=5, spaceAfter=3.5)
small = ParagraphStyle("small", parent=body, fontSize=9.5, leading=12.5, alignment=TA_LEFT, spaceAfter=0)
cell = ParagraphStyle("cell", fontName="TNR", fontSize=9.8, leading=12.4, textColor=INK)
cell_b = ParagraphStyle("cell_b", parent=cell, fontName="TNR-B")
cell_c = ParagraphStyle("cell_c", parent=cell, alignment=TA_CENTER)
caption = ParagraphStyle("caption", fontName="TNR", fontSize=10, leading=13, alignment=TA_JUSTIFY,
                         textColor=INK, spaceBefore=4, spaceAfter=12, leftIndent=14, rightIndent=14)
caption_t = ParagraphStyle("caption_t", parent=caption, alignment=TA_CENTER, spaceBefore=6, spaceAfter=5)
chap_no = ParagraphStyle("chap_no", fontName="TNR", fontSize=12, leading=14, textColor=ACCENT, spaceAfter=2)
h1 = ParagraphStyle("h1", fontName="TNR-B", fontSize=21, leading=25, textColor=INK, spaceAfter=4)
h2 = ParagraphStyle("h2", fontName="TNR-B", fontSize=14, leading=18, textColor=ACCENT, spaceBefore=12,
                    spaceAfter=6)
h3 = ParagraphStyle("h3", fontName="TNR-BI", fontSize=12, leading=15, textColor=INK, spaceBefore=6,
                    spaceAfter=3)
front_h = ParagraphStyle("front_h", fontName="TNR-B", fontSize=20, leading=24, textColor=INK, spaceAfter=14)
ref_style = ParagraphStyle("ref", parent=body, fontSize=10.5, leading=14, leftIndent=26, firstLineIndent=-26,
                           alignment=TA_LEFT, spaceAfter=5)
code = ParagraphStyle("code", fontName="Mono", fontSize=8.6, leading=11, textColor=INK, alignment=TA_LEFT)

# ------------------------------------------------------------------ references (numbered by first citation)
REFS = {
    "savary": 'S. Savary, L. Willocquet, S. J. Pethybridge, P. Esker, N. McRoberts, and A. Nelson, "The global '
              'burden of pathogens and pests on major food crops," <i>Nature Ecology &amp; Evolution</i>, vol. 3, '
              'pp. 430&#8211;439, 2019.',
    "kamilaris": 'A. Kamilaris and F. X. Prenafeta-Bold&#250;, "Deep learning in agriculture: A survey," '
                 '<i>Computers and Electronics in Agriculture</i>, vol. 147, pp. 70&#8211;90, 2018.',
    "liakos": 'K. G. Liakos, P. Busato, D. Moshou, S. Pearson, and D. Bochtis, "Machine learning in agriculture: '
              'A review," <i>Sensors</i>, vol. 18, no. 8, Art. 2674, 2018.',
    "barbedo2013": 'J. G. A. Barbedo, "Digital image processing techniques for detecting, quantifying and '
                   'classifying plant diseases," <i>SpringerPlus</i>, vol. 2, Art. 660, 2013.',
    "arivazhagan": 'S. Arivazhagan, R. N. Shebiah, S. Ananthi, and S. V. Varthini, "Detection of unhealthy region '
                   'of plant leaves and classification of plant leaf diseases using texture features," '
                   '<i>Agricultural Engineering International: CIGR Journal</i>, vol. 15, no. 1, pp. 211&#8211;217, 2013.',
    "hughes": 'D. P. Hughes and M. Salath&#233;, "An open access repository of images on plant health to enable '
              'the development of mobile disease diagnostics," arXiv:1511.08060, 2015.',
    "mohanty": 'S. P. Mohanty, D. P. Hughes, and M. Salath&#233;, "Using deep learning for image-based plant '
               'disease detection," <i>Frontiers in Plant Science</i>, vol. 7, Art. 1419, 2016.',
    "ferentinos": 'K. P. Ferentinos, "Deep learning models for plant disease detection and diagnosis," '
                  '<i>Computers and Electronics in Agriculture</i>, vol. 145, pp. 311&#8211;318, 2018.',
    "too": 'E. C. Too, L. Yujian, S. Njuki, and L. Yingchun, "A comparative study of fine-tuning deep learning '
           'models for plant disease identification," <i>Computers and Electronics in Agriculture</i>, vol. 161, '
           'pp. 272&#8211;279, 2019.',
    "geetharamani": 'G. Geetharamani and J. Arun Pandian, "Identification of plant leaf diseases using a nine-layer '
                    'deep convolutional neural network," <i>Computers &amp; Electrical Engineering</i>, vol. 76, '
                    'pp. 323&#8211;338, 2019.',
    "barbedo2018a": 'J. G. A. Barbedo, "Factors influencing the use of deep learning for plant disease '
                    'recognition," <i>Biosystems Engineering</i>, vol. 172, pp. 84&#8211;91, 2018.',
    "barbedo2018b": 'J. G. A. Barbedo, "Impact of dataset size and variety on the effectiveness of deep learning '
                    'and transfer learning for plant disease classification," <i>Computers and Electronics in '
                    'Agriculture</i>, vol. 153, pp. 46&#8211;53, 2018.',
    "plantdoc": 'D. Singh, N. Jain, P. Jain, P. Kayal, S. Kumawat, and N. Batra, "PlantDoc: A dataset for visual '
                'plant disease detection," in <i>Proc. 7th ACM IKDD CoDS and 25th COMAD</i>, 2020, '
                'pp. 249&#8211;253.',
    "he": 'K. He, X. Zhang, S. Ren, and J. Sun, "Deep residual learning for image recognition," in <i>Proc. IEEE '
          'Conf. Computer Vision and Pattern Recognition (CVPR)</i>, 2016, pp. 770&#8211;778.',
    "sandler": 'M. Sandler, A. Howard, M. Zhu, A. Zhmoginov, and L.-C. Chen, "MobileNetV2: Inverted residuals and '
               'linear bottlenecks," in <i>Proc. IEEE/CVF Conf. Computer Vision and Pattern Recognition (CVPR)</i>, '
               '2018, pp. 4510&#8211;4520.',
    "howard": 'A. Howard <i>et al.</i>, "Searching for MobileNetV3," in <i>Proc. IEEE/CVF Int. Conf. Computer '
              'Vision (ICCV)</i>, 2019, pp. 1314&#8211;1324.',
    "tan": 'M. Tan and Q. V. Le, "EfficientNet: Rethinking model scaling for convolutional neural networks," in '
           '<i>Proc. 36th Int. Conf. Machine Learning (ICML)</i>, PMLR vol. 97, 2019, pp. 6105&#8211;6114.',
    "deng": 'J. Deng, W. Dong, R. Socher, L.-J. Li, K. Li, and L. Fei-Fei, "ImageNet: A large-scale hierarchical '
            'image database," in <i>Proc. IEEE Conf. Computer Vision and Pattern Recognition (CVPR)</i>, 2009, '
            'pp. 248&#8211;255.',
    "yosinski": 'J. Yosinski, J. Clune, Y. Bengio, and H. Lipson, "How transferable are features in deep neural '
                'networks?" in <i>Advances in Neural Information Processing Systems (NeurIPS)</i>, vol. 27, 2014, '
                'pp. 3320&#8211;3328.',
    "guo": 'C. Guo, G. Pleiss, Y. Sun, and K. Q. Weinberger, "On calibration of modern neural networks," in '
           '<i>Proc. 34th Int. Conf. Machine Learning (ICML)</i>, PMLR vol. 70, 2017, pp. 1321&#8211;1330.',
    "geifman": 'Y. Geifman and R. El-Yaniv, "Selective classification for deep neural networks," in <i>Advances '
               'in Neural Information Processing Systems (NeurIPS)</i>, vol. 30, 2017, pp. 4878&#8211;4887.',
    "pech": 'J. L. Pech-Pacheco, G. Crist&#243;bal, J. Chamorro-Mart&#237;nez, and J. Fern&#225;ndez-Valdivia, '
            '"Diatom autofocusing in brightfield microscopy: A comparative study," in <i>Proc. 15th Int. Conf. '
            'Pattern Recognition (ICPR)</i>, vol. 3, 2000, pp. 314&#8211;317.',
    "zuiderveld": 'K. Zuiderveld, "Contrast limited adaptive histogram equalization," in <i>Graphics Gems IV</i>, '
                  'P. S. Heckbert, Ed. San Diego, CA: Academic Press, 1994, pp. 474&#8211;485.',
    "woebbecke": 'D. M. Woebbecke, G. E. Meyer, K. Von Bargen, and D. A. Mortensen, "Color indices for weed '
                 'identification under various soil, residue, and lighting conditions," <i>Transactions of the '
                 'ASAE</i>, vol. 38, no. 1, pp. 259&#8211;269, 1995.',
    "grabcut": 'C. Rother, V. Kolmogorov, and A. Blake, "GrabCut: Interactive foreground extraction using iterated '
               'graph cuts," <i>ACM Transactions on Graphics</i>, vol. 23, no. 3, pp. 309&#8211;314, 2004.',
    "szegedy": 'C. Szegedy, V. Vanhoucke, S. Ioffe, J. Shlens, and Z. Wojna, "Rethinking the Inception architecture '
               'for computer vision," in <i>Proc. IEEE Conf. Computer Vision and Pattern Recognition (CVPR)</i>, '
               '2016, pp. 2818&#8211;2826.',
    "adamw": 'I. Loshchilov and F. Hutter, "Decoupled weight decay regularization," in <i>Proc. Int. Conf. '
             'Learning Representations (ICLR)</i>, 2019.',
    "sgdr": 'I. Loshchilov and F. Hutter, "SGDR: Stochastic gradient descent with warm restarts," in <i>Proc. Int. '
            'Conf. Learning Representations (ICLR)</i>, 2017.',
    "marschner": 'P. Marschner, Ed., <i>Marschner\'s Mineral Nutrition of Higher Plants</i>, 3rd ed. London, U.K.: '
                 'Academic Press, 2012.',
    "pytorch": 'A. Paszke <i>et al.</i>, "PyTorch: An imperative style, high-performance deep learning library," in '
               '<i>Advances in Neural Information Processing Systems (NeurIPS)</i>, vol. 32, 2019, '
               'pp. 8024&#8211;8035.',
    "opencv": 'G. Bradski, "The OpenCV library," <i>Dr. Dobb\'s Journal of Software Tools</i>, vol. 25, no. 11, '
              'pp. 120&#8211;125, 2000.',
    "sklearn": 'F. Pedregosa <i>et al.</i>, "Scikit-learn: Machine learning in Python," <i>Journal of Machine '
               'Learning Research</i>, vol. 12, pp. 2825&#8211;2830, 2011.',
    "yolo": 'J. Redmon, S. Divvala, R. Girshick, and A. Farhadi, "You only look once: Unified, real-time object '
            'detection," in <i>Proc. IEEE Conf. Computer Vision and Pattern Recognition (CVPR)</i>, 2016, '
            'pp. 779&#8211;788.',
}
ORDER: list[str] = []


def C(*keys: str) -> str:
    nums = []
    for k in keys:
        assert k in REFS, k
        if k not in ORDER:
            ORDER.append(k)
        nums.append(ORDER.index(k) + 1)
    return "[" + ", ".join(str(n) for n in nums) + "]"


# ------------------------------------------------------------------ flowables


def roman(n: int) -> str:
    vals = [(10, "x"), (9, "ix"), (5, "v"), (4, "iv"), (1, "i")]
    out = ""
    for v, s in vals:
        while n >= v:
            out += s
            n -= v
    return out


LABELS: dict[int, str] = {}   # physical page -> printed label; kept across multiBuild passes


def page_fmt(p: int) -> str:
    return LABELS.get(p, str(p))


class Numbering(Flowable):
    """Switches page numbering (none / roman / arabic) from the page it appears on."""

    def __init__(self, mode):
        super().__init__()
        self.mode = mode

    def wrap(self, aw, ah):
        return 0, 0

    def draw(self):
        pass


class Heading(Paragraph):
    def __init__(self, text, style, level, toc_text=None):
        super().__init__(text, style)
        self.toc_level, self.toc_text = level, toc_text or text


class Caption(Paragraph):
    def __init__(self, text, style, kind, entry):
        super().__init__(text, style)
        self.list_kind, self.list_entry = kind, entry


class ListOf(TableOfContents):
    def __init__(self, kind):
        super().__init__(formatter=page_fmt)
        self.kind = kind
        self.levelStyles = [ParagraphStyle("lof", fontName="TNR", fontSize=11, leading=15, leftIndent=62,
                                           firstLineIndent=-62, rightIndent=30, spaceAfter=3)]
        self.dotsMinLevel = 0

    def notify(self, kind, stuff):
        if kind == self.kind:
            self.addEntry(*stuff)


class Doc(BaseDocTemplate):
    def __init__(self, path):
        super().__init__(str(path), pagesize=A4, leftMargin=2.75 * cm, rightMargin=2.45 * cm,
                         topMargin=3.0 * cm, bottomMargin=2.7 * cm, title="AgriVision AI - Project Report",
                         author="Akshata Bakre, Himanshu Kashyap", subject="Minor Project Report",
                         keywords="crop disease, computer vision, MobileNetV3, deep learning")
        frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id="f", leftPadding=0,
                      rightPadding=0, topPadding=0, bottomPadding=0)
        cover_frame = Frame(2.6 * cm, 2.6 * cm, W - 5.2 * cm, H - 5.2 * cm, id="c")
        self.addPageTemplates([PageTemplate("cover", [cover_frame], onPage=self.draw_cover),
                               PageTemplate("body", [frame], onPageEnd=self.draw_page)])
        self.key = 0

    def beforeDocument(self):
        self.numbering, self.offset, self.key = "none", 0, 0

    def page_label(self):
        n = self.page - self.offset
        return roman(n) if self.numbering == "roman" else str(n)

    def afterFlowable(self, f):
        if isinstance(f, Numbering):
            self.numbering, self.offset = f.mode, self.page - 1
        elif isinstance(f, Heading):
            self.key += 1
            key = f"h{self.key}"
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(f.toc_text.replace("&amp;", "&"), key, level=f.toc_level,
                                      closed=f.toc_level > 0)
            LABELS[self.page] = self.page_label()
            self.notify("TOCEntry", (f.toc_level, f.toc_text, self.page, key))
        elif isinstance(f, Caption):
            self.key += 1
            key = f"c{self.key}"
            self.canv.bookmarkPage(key)
            LABELS[self.page] = self.page_label()
            self.notify(f.list_kind, (0, f.list_entry, self.page, key))

    # -------------------------------------------------------------- page decoration
    @staticmethod
    def border(c):
        c.saveState()
        c.setStrokeColor(colors.black)
        c.setLineWidth(1.0)
        m = 1.25 * cm
        c.rect(m, m, W - 2 * m, H - 2 * m)
        c.restoreState()

    def draw_cover(self, c, doc):
        self.border(c)

    def draw_page(self, c, doc):
        self.border(c)
        c.saveState()
        if self.numbering == "arabic":
            c.setFont("TNR-I", 9.5)
            c.setFillColor(MUTED)
            c.drawString(self.leftMargin, H - 2.05 * cm, "AgriVision AI: Crop Health Monitoring and Failure Diagnosis")
            c.drawRightString(W - self.rightMargin, H - 2.05 * cm, "Minor Project Report")
            c.setStrokeColor(RULE)
            c.setLineWidth(0.5)
            c.line(self.leftMargin, H - 2.2 * cm, W - self.rightMargin, H - 2.2 * cm)
        if self.numbering in ("roman", "arabic"):
            c.setFont("TNR", 10.5)
            c.setFillColor(INK)
            c.drawCentredString(W / 2, 1.85 * cm, self.page_label())
        c.restoreState()


# ------------------------------------------------------------------ content helpers
story: list = []
fig_no, tab_no, eq_no = [0], [0], [0]
sec = [0, 0]
REF_FIG: dict[str, int] = {}
PHOTOS = {"fig_segmentation", "fig_qualitative", "fig_field_cases", "fig_webapp_input", "fig_webapp_result",
          "fig_webapp_explain", "fig_pdf_report"}
REF_TAB: dict[str, int] = {}


def P(text, style=body):
    story.append(Paragraph(text, style))


def bullets(items, numbered=False):
    for i, t in enumerate(items, 1):
        story.append(Paragraph(t, bullet, bulletText=f"{i}." if numbered else "\u2022"))
    story.append(Spacer(1, 4))


def chapter(title, numbering=None):
    sec[0] += 1
    sec[1] = 0
    story.append(PageBreak())
    if numbering:
        story.append(Numbering(numbering))
    story.append(Paragraph(f"CHAPTER {sec[0]}", chap_no))
    story.append(Heading(title, h1, 0, f"{sec[0]}&nbsp;&nbsp;{title}"))
    story.append(HRule(ACCENT, 1.2, 14))


def section(title):
    sec[1] += 1
    story.append(CondPageBreak(3.2 * cm))
    story.append(Heading(f"{sec[0]}.{sec[1]}&nbsp;&nbsp;{title}", h2, 1, f"{sec[0]}.{sec[1]}&nbsp;&nbsp;{title}"))


def sub(title):
    story.append(Paragraph(title, h3))


class HRule(Flowable):
    def __init__(self, color, width, space):
        super().__init__()
        self.color, self.lw, self.space = color, width, space

    def wrap(self, aw, ah):
        self.aw = aw
        return aw, self.space

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.lw)
        self.canv.line(0, self.space - 4, self.aw, self.space - 4)


def figure(key, path, text, width=15.5 * cm, max_h=19 * cm):
    fig_no[0] += 1
    REF_FIG[key] = fig_no[0]
    img = PILImage.open(path)
    if Path(path).stem in PHOTOS:   # photographs / screenshots: high-quality JPEG keeps the PDF small
        jpg = FIG / "jpg" / (Path(path).stem + ".jpg")
        jpg.parent.mkdir(exist_ok=True)
        img.convert("RGB").save(jpg, quality=90, optimize=True)
        path = jpg
    w = width
    h = w * img.height / img.width
    if h > max_h:
        h, w = max_h, max_h * img.width / img.height
    im = Image(str(path), width=w, height=h)
    short = text.split(". ")[0].rstrip(".")
    cap = Caption(f"<b>Figure {fig_no[0]}:</b> {text}", caption, "LOF", f"Figure {fig_no[0]}:&nbsp;&nbsp;{short}")
    story.append(KeepTogether([Spacer(1, 4), im, cap]))


def F(key):
    return f"Figure {REF_FIG[key]}"


def T_(key):
    return f"Table {REF_TAB[key]}"


def table(key, rows, widths, text, header=True, align=None, font=9.8, keep=True, zebra=True):
    tab_no[0] += 1
    REF_TAB[key] = tab_no[0]
    data = []
    for r, row in enumerate(rows):
        out = []
        for ci, v in enumerate(row):
            st = cell_b if (header and r == 0) else cell
            if align and align[ci] == "C":
                st = ParagraphStyle("x", parent=st, alignment=TA_CENTER)
            if font != 9.8:
                st = ParagraphStyle("y", parent=st, fontSize=font, leading=font * 1.27)
            out.append(v if isinstance(v, Flowable) else Paragraph(str(v), st))
        data.append(out)
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    style = [("VALIGN", (0, 0), (-1, -1), "TOP"),
             ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
             ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
             ("LINEABOVE", (0, 0), (-1, 0), 1.3, INK), ("LINEBELOW", (0, -1), (-1, -1), 1.3, INK)]
    if header:
        style += [("LINEBELOW", (0, 0), (-1, 0), 0.7, INK), ("BACKGROUND", (0, 0), (-1, 0), ACCENT_LIGHT)]
        if zebra:
            style.append(("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7f8f5")]))
    t.setStyle(TableStyle(style))
    short = text.split(". ")[0].rstrip(".")
    cap = Caption(f"<b>Table {tab_no[0]}:</b> {text}", caption_t, "LOT", f"Table {tab_no[0]}:&nbsp;&nbsp;{short}")
    if keep:
        story.append(KeepTogether([cap, t, Spacer(1, 12)]))
    else:
        story.extend([cap, t, Spacer(1, 12)])


def equation(tex, fontsize=15):
    eq_no[0] += 1
    fig = plt.figure(figsize=(0.01, 0.01))
    tex = tex.replace(r"\frac", r"\dfrac")   # display-style fractions
    fig.text(0, 0, f"${tex}$", fontsize=fontsize, math_fontfamily="stix")
    buf = io.BytesIO()
    fig.savefig(buf, dpi=300, transparent=True, bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)
    buf.seek(0)
    pim = PILImage.open(buf)
    w = pim.width / 300 * 72 * 0.82
    h = pim.height / 300 * 72 * 0.82
    if w > 12.6 * cm:
        w, h = 12.6 * cm, h * 12.6 * cm / w
    buf.seek(0)
    img = Image(buf, width=w, height=h)
    t = Table([["", img, Paragraph(f"({eq_no[0]})", ParagraphStyle("eqn", parent=body, alignment=2))]],
              colWidths=[1.5 * cm, TEXT_W - 3.0 * cm, 1.5 * cm])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (1, 0), (1, 0), "CENTER"),
                           ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    story.append(t)
    return eq_no[0]


REPO_URL = "https://github.com/akshatabakre/agrivision-ai"
REPO_LINK = f'<a href="{REPO_URL}"><font color="#1f4e8c"><u>{REPO_URL}</u></font></a>'


def pct(x, d=1):
    return f"{x * 100:.{d}f}%"


# ------------------------------------------------------------------ measured inference time
from agrivision.pipeline import get_engine  # noqa: E402

eng = get_engine()
lab_img = (ROOT / "samples" / "tomato_early_blight.jpg").read_bytes()
fld_img = (ROOT / "data" / "plantdoc" / "test" / "Squash_Powdery_mildew_leaf" / "Powdery-Mildew-on-squash.jpg").read_bytes()
eng.analyze(lab_img, save=False)


def timeit(b, n=5):
    t0 = time.perf_counter()
    for _ in range(n):
        eng.analyze(b, save=False)
    return (time.perf_counter() - t0) / n


T_LAB, T_FLD = timeit(lab_img), timeit(fld_img)

# ================================================================== COVER
story.append(NextPageTemplate("body"))
cover_title = ParagraphStyle("ct", fontName="TNR-B", fontSize=22, leading=30, alignment=TA_CENTER, textColor=INK)
cover_inst = ParagraphStyle("ci", fontName="TNR-B", fontSize=21, leading=26, alignment=TA_CENTER, textColor=INK)
cover_dept = ParagraphStyle("cd", fontName="TNR", fontSize=15.5, leading=20, alignment=TA_CENTER, textColor=INK)
cover_mid = ParagraphStyle("cm", fontName="TNR", fontSize=17, leading=24, alignment=TA_CENTER, textColor=INK)
cover_lab = ParagraphStyle("cl", fontName="TNR-B", fontSize=12.5, leading=17, textColor=INK)
cover_val = ParagraphStyle("cv", fontName="TNR", fontSize=12.5, leading=19, textColor=INK)
cover_sub = ParagraphStyle("cs", fontName="TNR-I", fontSize=12.5, leading=17, alignment=TA_CENTER, textColor=ACCENT)

story += [Spacer(1, 0.6 * cm), Paragraph("National Institute of Technology Raipur", cover_inst), Spacer(1, 6),
          Paragraph("Department of Information Technology", cover_dept), Spacer(1, 0.75 * cm)]
logo = PILImage.open(FIG / "nitrr_logo_0.jpg")
lw = 4.3 * cm
story += [Image(str(FIG / "nitrr_logo_0.jpg"), width=lw, height=lw * logo.height / logo.width),
          Spacer(1, 0.85 * cm), Paragraph("Minor Project Report", cover_mid), Paragraph("on", cover_mid),
          Spacer(1, 0.45 * cm),
          Paragraph("AgriVision AI: AI-Powered Crop Health<br/>Monitoring and Failure Diagnosis", cover_title),
          Spacer(1, 0.35 * cm),
          Paragraph("Detection of crop diseases, pest damage and nutrient deficiencies<br/>from a single leaf "
                    "photograph using computer vision", cover_sub),
          Spacer(1, 1.6 * cm)]
who = Table([[Paragraph("Submitted by:", cover_lab), Paragraph("Guided by:", cover_lab)],
             [Paragraph("1. Akshata Bakre (23118007)", cover_val), Paragraph("Dr. Sanjay Kumar", cover_val)],
             [Paragraph("2. Himanshu Kashyap (23118043)", cover_val), ""]],
            colWidths=[9.2 * cm, 6.3 * cm])
who.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("ALIGN", (1, 0), (1, -1), "LEFT")]))
who.hAlign = "LEFT"
story += [who, Spacer(1, 0.9 * cm)]
for k, v in (("Branch", "Information Technology"), ("Course", "B. Tech."), ("Semester", "7")):
    story.append(Paragraph(f"<b>{k}:</b> {v}", cover_val))

# ================================================================== FRONT MATTER
story += [PageBreak(), Numbering("roman")]
story.append(Heading("Abstract", front_h, 0))
P("Crop diseases, pest attacks and nutrient deficiencies are usually recognised only after visible damage has "
  "become severe, and farmers often lack timely access to agricultural experts who can distinguish between "
  f"them. This project presents <b>AgriVision AI</b>, an end-to-end decision-support system that diagnoses crop "
  f"health problems from a single photograph of a leaf. The system validates and pre-processes the image, "
  f"isolates the leaf from its background using colour analysis for plain-background photographs and a "
  f"focus-seeded GrabCut algorithm for field photographs, and classifies it into 39 classes covering 14 crops "
  f"with a MobileNetV3-Large network adapted through transfer learning. Each result is routed into one of four "
  f"categories (disease, pest, nutrient deficiency or healthy), the proportion of damaged tissue is converted "
  f"into a 0&#8211;100 crop health score and a severity band, and a knowledge-based recommendation engine "
  f"produces treatment and prevention advice that accounts for severity, growth stage, weather, soil readings, "
  f"region and the diagnosis history of the field. Confidence is calibrated with temperature scaling, and the "
  f"system abstains and requests a new photograph whenever confidence is insufficient.")
P(f"The model was trained on {D['split_counts']['lab_train']:,} laboratory images from PlantVillage and "
  f"{D['split_counts']['field_train']:,} field photographs from PlantDoc. On a held-out laboratory test set of "
  f"{M['test_images']:,} images it achieves an accuracy of {pct(M['accuracy'])} and a macro F1-score of "
  f"{M['f1_macro']:.3f}; with abstention, the false diagnosis rate falls to {pct(M['false_diagnosis_rate_at_threshold'])}. "
  f"On an independent test set of {FM['test_images']} field photographs, accuracy rises from "
  f"{pct(D['domain']['base_field'])} for a model trained on laboratory images alone to "
  f"{pct(FM['accuracy'])} after field images are included in training, quantifying the gap between laboratory "
  f"and real-world conditions. The system is delivered as a Streamlit web application, a FastAPI REST service "
  f"and a native Android application, and generates downloadable PDF crop-health reports. Training requires "
  f"only a CPU, and a complete diagnosis takes under two seconds on a standard laptop.")
P("<b>Keywords:</b> plant disease detection, computer vision, transfer learning, MobileNetV3, image "
  "segmentation, confidence calibration, selective classification, precision agriculture.",
  ParagraphStyle("kw", parent=body, spaceBefore=6))
P(f"<b>Source code:</b> the complete project &#8212; code, trained model, Android application and "
  f"documentation &#8212; is available at {REPO_LINK}.", ParagraphStyle("repo", parent=body, spaceBefore=4))

story += [PageBreak(), Paragraph("Contents", front_h)]
toc = TableOfContents(formatter=page_fmt)
toc.levelStyles = [
    ParagraphStyle("t0", fontName="TNR-B", fontSize=12, leading=16, leftIndent=0, firstLineIndent=0,
                   spaceBefore=7, textColor=INK),
    ParagraphStyle("t1", fontName="TNR", fontSize=11, leading=14.5, leftIndent=24, firstLineIndent=0,
                   textColor=INK),
]
toc.dotsMinLevel = 1
story.append(toc)

story += [PageBreak(), Heading("List of Figures", front_h, 0), ListOf("LOF"), PageBreak(),
          Heading("List of Tables", front_h, 0), ListOf("LOT"), Spacer(1, 1 * cm),
          Heading("List of Abbreviations", ParagraphStyle("fh2", parent=front_h, fontSize=17, spaceBefore=6), 0)]
abbr = [("API", "Application Programming Interface"), ("CLAHE", "Contrast-Limited Adaptive Histogram Equalisation"),
        ("CNN", "Convolutional Neural Network"), ("CPU", "Central Processing Unit"), ("ExG", "Excess Green index"),
        ("FDR", "False Diagnosis Rate"), ("HSV", "Hue, Saturation, Value colour space"),
        ("KVK", "Krishi Vigyan Kendra (agricultural extension centre)"), ("MLP", "Multi-Layer Perceptron"),
        ("PDF", "Portable Document Format"), ("ReLU", "Rectified Linear Unit"),
        ("REST", "Representational State Transfer"), ("SQL", "Structured Query Language"),
        ("UI", "User Interface")]
t = Table([[Paragraph(f"<b>{a}</b>", cell), Paragraph(b, cell)] for a, b in abbr], colWidths=[2.8 * cm, 12 * cm])
t.setStyle(TableStyle([("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
                       ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
story.append(t)

# ================================================================== 1 INTRODUCTION
chapter("Introduction", numbering="arabic")
section("Background and Motivation")
P(f"Plant pathogens and pests remain one of the largest threats to food security. A global expert survey "
  f"estimated yield losses of 21.5% for wheat, 30.0% for rice, 22.5% for maize, 17.2% for potato and 21.4% "
  f"for soybean attributable to pathogens and pests {C('savary')}. A large share of these losses is avoidable: "
  f"most foliar diseases can be contained if they are recognised early and treated correctly. In practice, "
  f"however, farmers frequently identify problems only once the visible damage has become severe.")
P("Several factors contribute to this delay. Many diseases look alike in their early stages, nutrient "
  "deficiencies produce discolouration that closely resembles disease symptoms, pest damage spreads before it "
  "is noticed, and manual field inspection is slow and labour-intensive. Access to agricultural experts is "
  "limited, particularly for small farms. The consequences compound along a predictable chain: late detection "
  "leads to incorrect diagnosis, incorrect diagnosis to improper treatment, improper treatment to reduced yield, "
  "and reduced yield to financial loss. Intervention is most effective at the first link of this chain.")
P(f"Advances in computer vision and the availability of smartphones with good cameras make it feasible to move "
  f"the first diagnostic step to the farmer. Deep convolutional neural networks have reached very high accuracy "
  f"on curated plant disease datasets {C('mohanty', 'ferentinos', 'too')}, and lightweight architectures make "
  f"inference practical on modest hardware {C('howard')}. Turning a classifier into a useful tool, however, "
  f"requires more than a class label: the user needs to know how severe the problem is, how reliable the "
  f"diagnosis is, and what to do next {C('kamilaris', 'liakos')}.")

section("Problem Statement")
P("The objective is to design and implement a scalable computer-vision application that allows a farmer to "
  "photograph a crop leaf and receive, without waiting for an expert visit, (i) the probable problem and its "
  "cause, (ii) whether it is a disease, a pest attack, a nutrient deficiency or a healthy plant, (iii) an "
  "estimate of severity, (iv) actionable, context-aware recommendations and (v) a crop-health report, while "
  "ensuring that uncertain diagnoses are flagged rather than presented as fact.")

section("Objectives")
bullets([
    "To build an image pipeline that validates photographs, corrects poor exposure and separates the leaf from "
    "both plain and cluttered backgrounds.",
    "To train a lightweight deep-learning classifier for 38 crop conditions across 14 crops, together with a "
    "class for images that contain no leaf.",
    "To route every diagnosis into one of four categories &#8212; disease, pest, nutrient deficiency or healthy "
    "&#8212; and to screen for nitrogen, potassium and iron/magnesium deficiency patterns.",
    "To estimate severity as a 0&#8211;100 crop health score and a four-level band from the damaged leaf area.",
    "To generate recommendations that depend on crop, severity, growth stage, environmental conditions, region "
    "and the diagnosis history of the field.",
    "To make the system reliable through calibrated confidence and abstention, and to evaluate it on both "
    "laboratory and real field photographs.",
    "To deliver the system through a web application, a REST API and an Android application, with PDF reports "
    "and persistent history.",
], numbered=True)

section("Contributions")
P("The main contributions of this work are the following:")
bullets([
    "A complete, working diagnosis system that integrates validation, segmentation, classification, severity "
    "estimation, nutrient screening, recommendations, reporting and history in a single pipeline, deployed on "
    "three interfaces.",
    f"A quantitative measurement of the laboratory-to-field gap on this task: a model trained only on laboratory "
    f"images reaches {pct(D['domain']['base_lab'])} on laboratory test images but only "
    f"{pct(D['domain']['base_field'])} on field photographs; including field photographs in training raises "
    f"field accuracy to {pct(FM['accuracy'])} while keeping laboratory accuracy at {pct(M['accuracy'])}.",
    "A focus-seeded GrabCut segmentation method that isolates the photographed leaf from surrounding foliage "
    "by exploiting the camera's depth of field.",
    "Separate, data-driven abstention thresholds for laboratory-style and field photographs, so that the system "
    "trades coverage for reliability where the task is harder.",
])

section("Organisation of the Report")
P("Chapter 2 reviews related work and identifies the research gap. Chapter 3 presents the system architecture "
  "and technology stack. Chapter 4 describes the methodology: datasets, preprocessing, segmentation, the "
  "classification model, abstention, severity estimation, nutrient screening and the recommendation engine. "
  "Chapter 5 covers the implementation of the web application, REST API, Android application and reports. "
  "Chapter 6 reports experimental results, Chapter 7 discusses them, Chapter 8 lists limitations and future "
  "work, and Chapter 9 concludes the report.")

# ================================================================== 2 LITERATURE
chapter("Literature Review")
section("Image-Based Plant Disease Recognition")
P(f"Early approaches to automated disease recognition relied on hand-crafted features. Images were segmented "
  f"with colour thresholds, and colour, texture and shape descriptors such as colour co-occurrence matrices were "
  f"extracted and classified with support vector machines or neural networks {C('arivazhagan', 'barbedo2013')}. "
  f"Barbedo's survey of these techniques {C('barbedo2013')} notes that they work well under controlled "
  f"conditions but are sensitive to illumination, background and the variability of symptoms, and that "
  f"features must be engineered separately for each crop and disease.")
P(f"The release of the PlantVillage dataset {C('hughes')}, containing tens of thousands of labelled leaf images "
  f"photographed against uniform backgrounds, enabled end-to-end deep learning. Mohanty <i>et al.</i> "
  f"{C('mohanty')} trained AlexNet and GoogLeNet on 38 classes and reported 99.35% accuracy on a held-out split. "
  f"Ferentinos {C('ferentinos')} reported 99.53% accuracy with VGG on a larger dataset of 58 classes, and Too "
  f"<i>et al.</i> {C('too')} compared fine-tuned architectures and obtained 99.75% with DenseNet. "
  f"Geetharamani and Arun Pandian {C('geetharamani')} designed a nine-layer CNN trained on an augmented "
  f"version of PlantVillage; the non-augmented version of their dataset is used in this project.")

section("The Laboratory-to-Field Gap")
P(f"Near-perfect accuracy on PlantVillage does not transfer to photographs taken in the field. Mohanty <i>et "
  f"al.</i> {C('mohanty')} already observed that accuracy dropped to 31.4% when their model was tested on images "
  f"collected from other sources. Barbedo {C('barbedo2018a', 'barbedo2018b')} analysed the factors responsible: "
  f"limited dataset variety, complex backgrounds, varying illumination and capture conditions, symptom "
  f"variation between growth stages, and the co-occurrence of several disorders on the same leaf. To address "
  f"this, Singh <i>et al.</i> {C('plantdoc')} assembled PlantDoc, a dataset of field photographs covering 13 "
  f"crops and 27 classes largely aligned with PlantVillage, and showed that models trained on laboratory images "
  f"perform poorly on it while training on field images improves results considerably.")

section("Lightweight Architectures and Transfer Learning")
P(f"Residual networks {C('he')} made very deep models trainable, but deployment on phones and low-cost devices "
  f"favours efficient architectures. MobileNetV2 {C('sandler')} introduced inverted residual blocks with linear "
  f"bottlenecks; MobileNetV3 {C('howard')} combined them with squeeze-and-excitation modules, the hard-swish "
  f"activation and architecture search to improve the accuracy&#8211;latency trade-off further. EfficientNet "
  f"{C('tan')} scales depth, width and resolution jointly. All of these are usually initialised with weights "
  f"pre-trained on ImageNet {C('deng')}; Yosinski <i>et al.</i> {C('yosinski')} showed that features learned on "
  f"large generic datasets transfer well to new tasks, which makes it possible to obtain strong results with "
  f"comparatively little task-specific data and compute.")

section("Reliability: Calibration and Selective Prediction")
P(f"A diagnostic tool must indicate how much its output can be trusted. Guo <i>et al.</i> {C('guo')} showed that "
  f"modern neural networks are poorly calibrated &#8212; their softmax confidence does not match their empirical "
  f"accuracy &#8212; and that a single temperature parameter fitted on validation data largely corrects this. "
  f"Selective classification {C('geifman')} formalises the option to abstain: by rejecting inputs whose "
  f"confidence falls below a threshold, the error rate on accepted inputs can be reduced at the cost of "
  f"coverage. For crop diagnosis this trade-off is asymmetric, because recommending the wrong treatment is more "
  f"harmful than asking for another photograph.")

section("Comparison of Existing Approaches")
P(f"{'Table 1'} summarises the principal families of approaches together with their strengths and limitations.")
table("approaches", [
    ["Approach", "Representative work", "Strengths", "Limitations"],
    ["Hand-crafted features with classical classifiers", f"{C('arivazhagan', 'barbedo2013')}",
     "Interpretable; low compute; little training data", "Sensitive to background and lighting; features "
     "engineered per crop; limited accuracy"],
    ["Deep CNNs trained on laboratory images", f"{C('mohanty', 'ferentinos', 'too', 'geetharamani')}",
     "Very high accuracy on curated test sets; end-to-end learning", "Accuracy collapses on field photographs; "
     "single label only; no severity or advice"],
    ["Lightweight transfer-learning models", f"{C('sandler', 'howard', 'tan')}",
     "Fast inference; suitable for mobile and edge devices", "Same domain-shift problem when trained on "
     "laboratory data"],
    ["Field-image datasets", f"{C('plantdoc')}", "Realistic backgrounds and capture conditions",
     "Small and noisy; lower absolute accuracy"],
    ["<b>This work (AgriVision AI)</b>", "&#8212;", "Laboratory + field training; segmentation; severity; "
     "nutrient screening; context-aware advice; calibrated abstention; three interfaces",
     "Field accuracy still moderate; nutrient and severity estimation rule-based"],
], [3.6 * cm, 2.7 * cm, 4.3 * cm, 4.9 * cm], "Comparison of approaches to image-based plant disease recognition")

section("Research Gap")
P("Most published systems report a single class label and its accuracy on a held-out split of the same "
  "laboratory dataset. Few of them estimate severity, distinguish nutrient deficiencies from disease, produce "
  "actionable and context-dependent recommendations, communicate calibrated confidence, abstain when unsure, or "
  "measure how performance changes on field photographs. AgriVision AI is designed to close these gaps in one "
  "deployable system and to evaluate it rigorously on both laboratory and field images.")

# ================================================================== 3 SYSTEM DESIGN
chapter("System Design")
section("Requirements")
P("The functional and non-functional requirements derived from the problem statement are listed in "
  "Table 2.")
table("req", [
    ["ID", "Requirement", "Type"],
    ["R1", "Accept a leaf photograph by upload or camera capture", "Functional"],
    ["R2", "Reject unusable images (no leaf, blurred, too dark or too bright) with guidance", "Functional"],
    ["R3", "Identify crop and condition; route into disease, pest, nutrient deficiency or healthy", "Functional"],
    ["R4", "Estimate severity and a 0&#8211;100 health score", "Functional"],
    ["R5", "Provide treatment, prevention and context-aware recommendations", "Functional"],
    ["R6", "Generate a downloadable crop-health report and keep a per-field history", "Functional"],
    ["R7", "Always display confidence; abstain below a threshold", "Reliability"],
    ["R8", "Diagnose an image in under 2 seconds on a laptop CPU; train without a GPU", "Performance"],
    ["R9", "Expose the pipeline through an API so that new front ends need no model changes", "Extensibility"],
    ["R10", "Operate without internet access once installed", "Deployment"],
], [1.3 * cm, 11.3 * cm, 2.9 * cm], "System requirements", align=["C", "L", "L"])

section("System Architecture")
P(f"The system is organised in six layers, shown in {'Figure 1'}. Clients (the web application and the "
  f"Android application) communicate with a REST service. The vision layer validates and pre-processes the "
  f"photograph and segments the leaf. The decision layer classifies the image, applies the abstention rule, "
  f"routes the result into a category, estimates severity and screens for nutrient deficiencies. The knowledge "
  f"layer turns the diagnosis into recommendations, and the output layer produces the report and stores the "
  f"diagnosis, which in turn feeds back into the recommendation engine to detect recurring outbreaks.")
figure("arch", FIG / "fig_architecture.png",
       "Layered architecture of AgriVision AI. Arrows show the flow of a single diagnosis; the dashed arrow shows "
       "the history lookup used to escalate recurring outbreaks", width=13.2 * cm)

section("End-to-End Workflow")
P("A single diagnosis proceeds through the following steps:")
bullets([
    "The user captures or uploads a photograph and optionally supplies the crop, field name, region, growth "
    "stage and sensor readings (temperature, humidity, soil moisture, soil pH).",
    "The image is decoded with EXIF orientation applied, resized to at most 1024 pixels on its longer side and "
    "validated for resolution, blur, exposure and the presence of a leaf; dark images are enhanced.",
    "The leaf is segmented, and each leaf pixel is labelled as healthy, chlorotic, necrotic or powdery.",
    "The classifier produces calibrated probabilities over 39 classes; if the crop is supplied, probabilities "
    "are restricted to that crop.",
    "If the most probable class is the background class, or confidence is below the applicable threshold, the "
    "system abstains and asks for a new photograph.",
    "Otherwise the result is routed into a category, the health score and severity band are computed, and "
    "nutrient patterns are checked for leaves classified as healthy.",
    "The recommendation engine combines the knowledge base with severity, context and field history.",
    "The result is displayed, stored in the database and made available as a PDF report.",
], numbered=True)

section("Technology Stack")
table("stack", [
    ["Layer", "Technology", "Purpose"],
    ["Computer vision", f"OpenCV 5 {C('opencv')}, Pillow, NumPy", "Decoding, validation, CLAHE, segmentation, colour analysis"],
    ["Machine learning", f"PyTorch 2 {C('pytorch')}, torchvision, scikit-learn {C('sklearn')}",
     "MobileNetV3 backbone, head training, metrics"],
    ["Backend", "Python 3, FastAPI, Uvicorn", "REST API and model serving"],
    ["Web front end", "Streamlit", "Interactive web application"],
    ["Mobile front end", "Kotlin, Jetpack Compose, OkHttp", "Native Android application (Android 9+)"],
    ["Storage", "SQLite", "Diagnosis history and recurrence detection"],
    ["Reporting", "fpdf2, Matplotlib", "PDF crop-health reports and evaluation plots"],
], [3.2 * cm, 6.0 * cm, 6.3 * cm], "Technology stack")

# ================================================================== 4 METHODOLOGY
chapter("Methodology")
section("Datasets and Data Preparation")
P(f"Two public datasets are used (Table 4). PlantVillage {C('hughes', 'geetharamani')} provides laboratory "
  f"images of 38 crop conditions photographed on uniform backgrounds, together with a class of background "
  f"images without leaves, which the system uses to reject photographs that do not contain a leaf. To keep "
  f"training feasible on a CPU and to limit class imbalance, at most 1,500 images were sampled per class with a "
  f"fixed random seed, giving {sum(D['split_counts'][k] for k in ('lab_train', 'lab_val', 'lab_test')):,} images that were split 70/15/15 into training, validation and test sets "
  f"with stratification by class. Unreadable files were removed during preparation.")
P(f"PlantDoc {C('plantdoc')} contributes photographs taken in natural conditions, with foliage, soil, hands and "
  f"structures in the background. Its class names were mapped onto the PlantVillage labels (for example, "
  f"<i>Tomato Early blight leaf</i> to <i>Tomato &#8211; Early Blight</i>), which covers 28 of the 39 classes. "
  f"PlantDoc's official test split was kept aside as an independent field test set; its training split was "
  f"divided 85/15 into training and validation subsets.")
sc = D["split_counts"]
table("data", [
    ["Dataset", "Image type", "Classes", "Train", "Validation", "Test"],
    ["PlantVillage", "Laboratory, plain background", "39", f"{sc['lab_train']:,}", f"{sc['lab_val']:,}",
     f"{sc['lab_test']:,}"],
    ["PlantDoc", "Field, natural background", "28 (mapped)", f"{sc['field_train']:,}", f"{sc['field_val']:,}",
     f"{sc['field_test']:,}"],
    ["<b>Total</b>", "", "39", f"<b>{sc['lab_train'] + sc['field_train']:,}</b>",
     f"<b>{sc['lab_val'] + sc['field_val']:,}</b>", f"<b>{sc['lab_test'] + sc['field_test']:,}</b>"],
], [2.6 * cm, 4.3 * cm, 2.1 * cm, 2.1 * cm, 2.3 * cm, 2.1 * cm], "Datasets and splits used in this work",
    align=["L", "L", "C", "C", "C", "C"])

section("Image Validation and Preprocessing")
P(f"Photographs are first decoded with their EXIF orientation applied and downscaled so that the longer side is "
  f"at most 1024 pixels. Four quality checks follow. The resolution must be at least 64 pixels on the shorter "
  f"side. Sharpness is measured as the variance of the Laplacian of the grey-scale image resized to 512 &#215; "
  f"512 pixels {C('pech')}:")
equation(r"B = \mathrm{Var}\left(\nabla^{2} I\right)")
P("Images with <i>B</i> &lt; 40 are reported as blurred. Mean brightness must lie between 40 and 225, and the "
  "segmented leaf must cover at least 5% of the frame. Failed checks are shown to the user as specific "
  f"guidance, for example to photograph in daylight or to fill the frame with the leaf. Images with mean "
  f"brightness below 70 are enhanced with contrast-limited adaptive histogram equalisation (CLAHE) "
  f"{C('zuiderveld')} applied to the lightness channel of the Lab colour space (clip limit 2.0, 8 &#215; 8 tiles). "
  f"For classification, the image is resized to 224 &#215; 224 pixels and normalised channel-wise with the "
  f"ImageNet statistics:")
equation(r"\hat{x}_{c} = \frac{x_{c}/255 - \mu_{c}}{\sigma_{c}}, \quad \mu = (0.485, 0.456, 0.406), \; \sigma = (0.229, 0.224, 0.225)")

section("Leaf Segmentation")
P("Segmentation serves two purposes: it measures how much of the leaf is damaged, and it provides the visual "
  "explanation shown to the user. Two strategies are used, selected automatically from the image border.")
sub("Plain-background photographs")
P(f"Plant tissue is saturated in colour, while backgrounds such as paper, benches or walls are not. A pixel is "
  f"marked as plant if its saturation exceeds 45 and its value exceeds 50 with a hue in the red&#8211;yellow&#8211;green "
  f"range, or if its excess-green index {C('woebbecke')} exceeds 25:")
equation(r"\mathrm{ExG} = 2G - R - B")
P("Coloured backgrounds are removed by estimating the background chroma from a border band covering 4% of the "
  "image. If the border is uniform (70% of border pixels lie within 6 units of the median in the Lab a*b* "
  "plane), every pixel whose chroma is within 7 units of that median is treated as background:")
equation(r"d(p) = \left\| (a^{*}_{p}, b^{*}_{p}) - (\tilde{a}^{*}, \tilde{b}^{*}) \right\|_{2} < 7")
P("Because only chroma is compared, the background's own shadows are removed as well. The mask is cleaned with "
  "morphological opening and closing, the largest connected component is kept, and its holes are filled so "
  "that lesions inside the leaf are included.")
sub("Field photographs")
P(f"When the border is not uniform, colour cannot separate the leaf from the foliage behind it. The method "
  f"developed here exploits the camera's depth of field: the photographed leaf is in focus, while the "
  f"background is blurred. A local focus map is computed from the absolute Laplacian, smoothed with a Gaussian "
  f"of standard deviation 3% of the image size and normalised by its 99th percentile:")
equation(r"F(p) = \frac{\left(G_{\sigma} * \left|\nabla^{2} I\right|\right)(p)}{P_{99}}")
P(f"These cues seed the GrabCut algorithm {C('grabcut')}, which models foreground and background with Gaussian "
  f"mixture models and refines the boundary with graph cuts. Pixels with <i>F</i> &lt; 0.12 are marked as "
  f"definite background, in-focus plant-coloured pixels (<i>F</i> &gt; 0.35) as probable foreground, and all "
  f"others as probable background. Five iterations are run on a copy downscaled to 400 pixels, and the component "
  f"that best combines size and centrality is kept. {'Figure 2'} compares the two strategies on a field "
  f"photograph: colour thresholding selects {D['seg_naive']:.0%} of the frame, including the fence and post, whereas the "
  f"focus-seeded GrabCut isolates the leaf.")
figure("seg", FIG / "fig_segmentation.png",
       "Leaf segmentation on a field photograph from the PlantDoc test set. Green outline: detected leaf; blue: "
       "powdery growth; red: tissue classified as necrotic. Colour thresholding alone (b) includes the background, "
       "while focus-seeded GrabCut (c) isolates the leaf")
sub("Tissue classification")
P("Within the leaf mask, each pixel is labelled in HSV space (OpenCV hue scale 0&#8211;179) as <i>powdery</i> "
  "(saturation below max(15, 0.35&#183;median saturation) and value above max(170, median value + 60)), "
  "<i>healthy green</i> (hue 28&#8211;95, saturation above 20, value above 25), <i>chlorotic</i> (hue 15&#8211;28, "
  "saturation above 60, value above 90) or <i>necrotic</i> (remaining pixels with saturation above 35 or value "
  "below 70). Pixels matching none of these, such as glare and deep shadow, are excluded from the percentages. "
  "The adaptive thresholds for powdery tissue avoid confusing leaf veins and glossy highlights with mildew.")

section("Classification Model")
sub("Architecture")
P(f"The classifier uses MobileNetV3-Large {C('howard')} pre-trained on ImageNet (torchvision weights "
  f"IMAGENET1K_V2) as a feature extractor. The original 1000-class output layer is removed; the network up to "
  f"the 1280-dimensional penultimate layer (convolutional features, global average pooling, a fully connected "
  f"layer and hard-swish activation) maps an image <i>x</i> to an embedding:")
equation(r"z = f_{\theta}(x) \in \mathbb{R}^{1280}")
P("A classification head with one hidden layer of 512 units maps the embedding to logits for the 39 classes:")
equation(r"h(z) = W_{2}\,\mathrm{ReLU}\left(W_{1} z + b_{1}\right) + b_{2}, \quad W_{1} \in \mathbb{R}^{512 \times 1280}, \; W_{2} \in \mathbb{R}^{39 \times 512}")
P(f"Dropout with probability 0.3 is applied before each linear layer. The head has "
  f"{D['head_params']:,} trainable parameters, compared with {D['backbone_params']:,} parameters in the frozen "
  f"backbone. A single linear layer was evaluated first; the hidden layer improved both laboratory and field "
  f"validation accuracy and was retained.")
sub("Training by feature extraction")
P(f"Fine-tuning the entire network on a CPU would require a forward and backward pass through the backbone for "
  f"every image in every epoch. Because the backbone is frozen, each image needs to pass through it only once: "
  f"the embeddings of all images are computed and cached, after which the head is trained on the cached "
  f"embeddings in seconds per epoch {C('yosinski')}. Field photographs are mirrored horizontally as "
  f"augmentation and oversampled {D['field_repeat']} times, so that the {sc['field_train']:,} field images carry weight "
  f"comparable to the {sc['lab_train']:,} laboratory images; the final training set contains "
  f"{D['train_size']:,} embeddings. The loss is cross-entropy with label smoothing {C('szegedy')}:")
equation(r"\mathcal{L} = -\sum_{k=1}^{K} q_{k} \log p_{k}, \qquad q_{k} = (1-\varepsilon)\, y_{k} + \frac{\varepsilon}{K}, \quad \varepsilon = 0.05")
P(f"Optimisation uses AdamW {C('adamw')} with a cosine learning-rate schedule {C('sgdr')}. The model is "
  f"selected by the mean of laboratory and field validation accuracy, with early stopping after 15 epochs "
  f"without improvement. Table 5 lists the hyperparameters.")
table("hyper", [
    ["Parameter", "Value"],
    ["Backbone", "MobileNetV3-Large, ImageNet-1K (V2) weights, frozen"],
    ["Input size / embedding size", "224 &#215; 224 &#215; 3 / 1280"],
    ["Classification head", "1280 &#8594; 512 &#8594; 39, ReLU, dropout 0.3"],
    ["Optimiser", "AdamW, learning rate 10<super>&#8722;3</super>, weight decay 10<super>&#8722;4</super>"],
    ["Batch size / maximum epochs", "128 / 80 (cosine schedule)"],
    ["Early stopping", f"patience 15; stopped after {D['train_epochs']} epochs, best epoch {D['best_epoch']}"],
    ["Label smoothing", "0.05"],
    ["Field-image weighting", f"horizontal mirroring, {D['field_repeat']}&#215; oversampling"],
    ["Training embeddings", f"{D['train_size']:,}"],
    ["Temperature <i>T</i>", f"{D['temperature']:.3f}"],
    ["Abstention thresholds", f"0.60 (plain background), {D['field_threshold']:.2f} (field)"],
], [5.6 * cm, 9.9 * cm], "Model and training hyperparameters")
sub("Confidence calibration")
P(f"Raw softmax probabilities are not reliable confidence estimates {C('guo')}. After training, a temperature "
  f"<i>T</i> is fitted on the combined validation set by minimising the negative log-likelihood, and the "
  f"probability of class <i>k</i> is computed as:")
equation(r"p_{k} = \frac{\exp\left(h_{k}(z)/T\right)}{\sum_{j} \exp\left(h_{j}(z)/T\right)}")
P(f"The fitted value <i>T</i> = {D['temperature']:.3f} is below one, which sharpens the distribution. This is "
  f"expected: label smoothing deliberately trains the model to be less confident, and temperature scaling "
  f"restores probabilities that match observed accuracy.")

section("Abstention and the False Diagnosis Rate")
P(f"A wrong treatment recommendation is more harmful than a request for another photograph, so accuracy alone "
  f"is not the most relevant metric. Following the selective classification framework {C('geifman')}, for a "
  f"confidence threshold &#964; the system answers only images whose top probability <i>c</i> is at least "
  f"&#964;. Two quantities characterise the behaviour, coverage and the false diagnosis rate (FDR):")
equation(r"\mathrm{Cov}(\tau) = \frac{\left|\{ i : c_{i} \geq \tau \}\right|}{N}, \qquad \mathrm{FDR}(\tau) = \frac{\left|\{ i : c_{i} \geq \tau,\; \hat{y}_{i} \neq y_{i} \}\right|}{\left|\{ i : c_{i} \geq \tau \}\right|}")
P("For plain-background images the threshold is fixed at 0.60. Field photographs are much harder, so they "
  "receive their own threshold, selected automatically during training as the smallest value that keeps the "
  "false diagnosis rate on the field validation set at or below 20%:")
equation(r"\tau_{f} = \min \left\{ \tau \geq 0.60 \;:\; \mathrm{FDR}_{\mathrm{val}}(\tau) \leq 0.20 \right\}")
P(f"This yields &#964;<sub>f</sub> = {D['field_threshold']:.2f}. The photograph type is determined by the "
  f"same border-uniformity test used for segmentation. When the system abstains, it shows the three most "
  f"probable classes and specific advice for re-capture instead of a treatment.")

section("Category Routing and Nutrient Screening")
_cats = __import__("collections").Counter(v["category"] for v in load_kb()["classes"].values())
P(f"Each of the 39 classes belongs to one category in the knowledge base: disease ({_cats['disease']} classes), "
  f"pest ({_cats['pest']} class, spider-mite damage), healthy ({_cats['healthy']} classes, one per crop) or "
  f"invalid ({_cats['invalid']} class, no leaf). Category probabilities are obtained by summing class "
  f"probabilities:")
equation(r"P(\mathrm{cat}) = \sum_{k \,\in\, \mathrm{cat}} p_{k}")
P(f"Nutrient deficiencies are not labelled in either dataset, so they are screened with explainable colour "
  f"rules based on well-known deficiency signatures {C('marschner')} (Table 6). The rules are evaluated on the "
  f"leaf mask: the margin band is the outer 6% of the leaf's equivalent diameter, and vein-like green structures "
  f"are identified as green pixels removed by a morphological opening with a kernel of 1.5% of the diameter. A "
  f"deficiency is reported as the primary diagnosis only if the classifier considers the leaf healthy and the "
  f"stress index reaches 0.25; its probability is taken as the healthy probability multiplied by the stress "
  f"index. Results are always presented as probable, with a recommendation to confirm by soil or tissue "
  f"testing before fertiliser is applied.")
table("nutrient", [
    ["Deficiency", "Visual signature", "Rule applied to the segmented leaf"],
    ["Nitrogen (N)", "Uniform yellowing; older leaves first; reduced growth",
     "Chlorotic fraction &#8805; 25% without vein pattern or margin concentration"],
    ["Potassium (K)", "Yellow/brown scorching of leaf margins",
     "Margin damage &gt; 30% and exceeds interior damage by &gt; 20 percentage points"],
    ["Iron / Magnesium (Fe, Mg)", "Interveinal chlorosis: yellow lamina, green veins",
     "Chlorotic fraction &#8805; 12% and &gt; 35% of green pixels lie in thin vein-like lines"],
], [3.3 * cm, 5.4 * cm, 6.8 * cm], "Nutrient-deficiency signatures and screening rules")

section("Severity Estimation")
P("The damaged fraction <i>a</i> of the leaf is the share of classified leaf pixels that are chlorotic (Y), "
  "necrotic (B) or powdery (W) rather than healthy green (G):")
equation(r"a = \frac{|Y| + |B| + |W|}{|G| + |Y| + |B| + |W|}")
P("For leaves diagnosed with a disease or pest, the health score is a non-linear function of the damaged "
  "fraction, so that the first lesions reduce the score less than the loss of the remaining healthy tissue:")
equation(r"S = 100\,(1-a)^{1.6}")
P(f"Damage of 5%, 15%, 30% and 45% gives scores of 92, 77, 56 and 38 respectively ({'Figure 3'}). Because a "
  f"confirmed disease is never healthy, the score of a diseased leaf is capped at 89. Aggressive or systemic "
  f"conditions carry a minimum severity regardless of visible area: late blight, Tomato Yellow Leaf Curl Virus "
  f"and Tomato Mosaic Virus are at least <i>Moderate</i>, and citrus greening (Huanglongbing) is always "
  f"<i>Severe</i>. Healthy leaves score between 90 and 100 depending on confidence and residual discolouration. "
  f"Table 7 lists the bands.")
figure("sev", FIG / "fig_severity.png", "Mapping from damaged leaf area to the crop health score, with the four "
       "severity bands", width=11.5 * cm)
table("bands", [
    ["Health score", "Severity band", "Urgency of the recommendation"],
    ["90 &#8211; 100", "Healthy", "Routine weekly monitoring"],
    ["70 &#8211; 89", "Mild", "Monitor closely; re-check in 3&#8211;4 days; treat if spreading"],
    ["40 &#8211; 69", "Moderate", "Act this week; apply treatment"],
    ["0 &#8211; 39", "Severe", "Act today; isolate affected plants; inspect the whole field"],
], [3.2 * cm, 3.3 * cm, 9.0 * cm], "Severity bands and associated urgency", align=["C", "L", "L"])

section("Recommendation Engine")
kb = load_kb()["classes"]
P(f"A knowledge base stores, for each of the {len(kb)} classes, the crop, condition name, category, cause type "
  f"(fungal, bacterial, viral, oomycete or pest), causal organism, typical symptoms, cultural actions, a "
  f"treatment option, prevention measures, an optional minimum severity and the environmental conditions that "
  f"favour the pathogen. Treatments are described generically (for example, a locally approved protectant "
  f"fungicide such as chlorothalonil or mancozeb) and always point the user to the local agricultural extension "
  f"centre (Krishi Vigyan Kendra) for approved products and doses. The engine combines the knowledge base entry "
  f"with the factors in Table 8.")
table("factors", [
    ["Factor", "Effect on the recommendation"],
    ["Severity", "Selects the action set and urgency (Table 7); treatment is included from <i>Moderate</i> upwards"],
    ["Temperature and humidity", "Compared with the pathogen's favourable range; if conditions favour spread, "
     "a warning is added and treatment is recommended even for mild cases"],
    ["Growth stage", "Seedling: remove rather than treat; flowering: spray outside pollinator activity; "
     "fruiting: observe the pre-harvest interval"],
    ["Soil moisture and pH", "Low moisture supports spider-mite stress advice; high pH supports iron "
     "deficiency, low pH magnesium deficiency"],
    ["Diagnosis history", "The same problem in the same field within 30 days is reported as a recurring "
     "outbreak and escalated to expert consultation, resistant varieties and crop rotation"],
    ["Region", "Reminder to use only products approved in the user's state"],
    ["Crop selection", "If the user specifies the crop, only that crop's classes compete in the classifier"],
], [3.8 * cm, 11.7 * cm], "Context factors used by the recommendation engine")

# ================================================================== 5 IMPLEMENTATION
chapter("Implementation")
section("Software Organisation")
P("The core logic is implemented as a Python package, <font face='Mono' size='10'>agrivision</font>, that is "
  "shared by all interfaces, so that the web application, REST API and Android application produce identical "
  "results. Table 9 lists its modules.")
P(f"The full source code, the trained model, the Android application package, the training and evaluation "
  f"scripts and setup instructions are published in the project repository: {REPO_LINK}.")
table("modules", [
    ["Module", "Responsibility"],
    ["preprocessing.py", "Decoding, validation, CLAHE, both segmentation strategies, tissue colour maps, overlays"],
    ["model.py", "MobileNetV3 backbone, classification head, calibrated inference"],
    ["pipeline.py", "End-to-end workflow, abstention, category routing, result assembly"],
    ["severity.py", "Damaged-area statistics, health score and severity band"],
    ["nutrient.py", "Nutrient-deficiency screening"],
    ["recommender.py, knowledge_base.json", "Recommendation engine and knowledge base"],
    ["database.py", "SQLite history, recurrence queries"],
    ["report.py", "PDF crop-health reports"],
    ["scripts/", "Data preparation, feature extraction and training, evaluation, automated tests"],
], [5.2 * cm, 10.3 * cm], "Modules of the agrivision package",
    )

section("Web Application")
P(f"The web application, built with Streamlit, follows a single-screen design: capture or upload, analyse, "
  f"read, and download the report. Optional field context is placed in a collapsed panel so that it does not "
  f"distract users who do not need it. {'Figure 4'} shows the input screen and {'Figure 5'} the result for a "
  f"maize leaf: the category, diagnosis, cause, confidence and severity, the health score bar, observed "
  f"symptoms and prioritised actions. Confidence is colour-coded, and a low-confidence result looks visibly "
  f"different from a confident one. An expandable panel ({'Figure 6'}) explains how the result was reached: "
  f"the segmentation, the damage map, category probabilities, the five most probable classes, tissue "
  f"percentages, nutrient screening and image-quality measurements. Further tabs show the history of each "
  f"field with a health-score trend, and the model's evaluation results.")
figure("ui_in", FIG / "fig_webapp_input.png", "Web application: input screen with a sample image selected",
       width=14.5 * cm)
figure("ui_res", FIG / "fig_webapp_result.png", "Web application: diagnosis, crop status and recommended actions "
       "for a maize leaf with common rust", width=15.5 * cm)
figure("ui_exp", FIG / "fig_webapp_explain.png", "Web application: explanation panel with segmentation, damage "
       "map, category probabilities, top predictions and tissue analysis", width=15.5 * cm)

section("REST API")
P("The FastAPI service exposes the pipeline to any client (Table 10). The <font face='Mono' size='10'>"
  "/analyze</font> endpoint accepts the image as multipart form data together with the optional context "
  "fields and returns the full result as JSON; on request it also returns the original image, the segmented "
  "leaf and the damage map as base64-encoded JPEG images. Interactive documentation is generated automatically.")
table("api", [
    ["Method", "Endpoint", "Description"],
    ["POST", "/analyze", "Diagnose an image; optional crop, field, region, growth stage, temperature, humidity, "
     "soil moisture, soil pH, include_images"],
    ["GET", "/history", "List diagnoses, optionally filtered by field"],
    ["GET", "/diagnoses/{id}", "Retrieve one stored diagnosis"],
    ["GET", "/report/{id}", "Download the PDF crop-health report"],
    ["GET", "/crops", "List supported crops"],
    ["GET", "/health", "Service and model status"],
], [1.9 * cm, 3.6 * cm, 10.0 * cm], "REST API endpoints")

section("Android Application")
P("The Android application is written in Kotlin with Jetpack Compose and supports Android 9 and later. It "
  "contains four screens: <i>Diagnose</i> (camera capture or gallery selection, crop selection and field "
  "context), <i>Result</i> (the same information as the web application, including the damage map), "
  "<i>History</i> (previous diagnoses with health scores) and <i>Settings</i> (server address and connection "
  "test). Photographs are decoded with their orientation applied, downscaled to 1600 pixels and compressed "
  "before upload, which keeps transfers fast on mobile networks. PDF reports are downloaded and opened in the "
  "phone's PDF viewer or shared through other applications.")
P("The application connects to the API over a local network. In the intended field setup the laptop running "
  "the server joins the phone's mobile hotspot, which requires no internet connection; a launcher script on "
  "the laptop prints the address to enter in the application. The application is distributed as a 23 MB APK.")

section("Crop Health Report")
P(f"Every diagnosis can be exported as a PDF report ({'Figure 7'}). The report contains the crop, date and field, "
  f"the diagnosis and probable cause, confidence, severity, the health score bar with its scale, the input image "
  f"and damage map, observed symptoms, numbered recommended actions with their urgency, context notes, "
  f"prevention measures, the model output and a disclaimer that the diagnosis is an early-screening aid.")
figure("pdf", FIG / "fig_pdf_report.png", "First page of a generated crop-health report for a tomato leaf with "
       "early blight, with field context (fruiting stage, 27 &#176;C, 85% humidity)", width=11.0 * cm, max_h=16 * cm)

section("Testing")
P("Two automated test suites verify the system end to end. The first runs every sample image through the "
  "pipeline, generates a PDF report for each and exercises all REST endpoints, including report download and "
  "history. The second drives the Streamlit interface headlessly: it selects samples, submits field context and "
  "sensor readings, checks the rendered verdicts, including rejection of a non-leaf image, abstention on an "
  "ambiguous image and its resolution when the crop is specified, and confirms that every tab renders without "
  "errors. Both suites pass on the final system.")

# ================================================================== 6 RESULTS
chapter("Results and Analysis")
section("Experimental Setup")
P(f"All experiments were run on a laptop with an Intel Core i5-1035G1 processor and 8 GB of memory, without a "
  f"GPU. The laboratory test set consists of {M['test_images']:,} PlantVillage images not used in training or "
  f"model selection; the field test set consists of the {FM['test_images']} images of PlantDoc's official test "
  f"split. Accuracy, macro-averaged precision, recall and F1-score, category routing accuracy (whether the "
  f"disease / pest / healthy / no-leaf category is correct), coverage and false diagnosis rate are reported.")

section("Performance on Laboratory Images")
P(f"Table 11 summarises the results on the laboratory test set. The classifier reaches {pct(M['accuracy'])} "
  f"accuracy with balanced precision and recall, and assigns the correct category to {pct(M['category_accuracy'])} "
  f"of images. Without abstention, {pct(M['false_diagnosis_rate_no_abstention'])} of images would be "
  f"misdiagnosed; at the 0.60 threshold, {pct(M['coverage_at_threshold'])} of images are answered and the "
  f"false diagnosis rate falls to {pct(M['false_diagnosis_rate_at_threshold'], 2)}.")
table("lab", [
    ["Metric", "Value"],
    ["Accuracy", f"<b>{pct(M['accuracy'])}</b>"],
    ["Macro precision / recall / F1-score",
     f"{M['precision_macro']:.3f} / {M['recall_macro']:.3f} / {M['f1_macro']:.3f}"],
    ["Category routing accuracy", pct(M["category_accuracy"])],
    ["False diagnosis rate without abstention", pct(M["false_diagnosis_rate_no_abstention"])],
    ["False diagnosis rate at threshold 0.60", f"<b>{pct(M['false_diagnosis_rate_at_threshold'], 2)}</b>"],
    ["Coverage at threshold 0.60", pct(M["coverage_at_threshold"])],
], [9.0 * cm, 6.5 * cm], f"Results on the laboratory test set ({M['test_images']:,} images, 39 classes)",
    align=["L", "C"])
low = sorted(D["per_class"], key=lambda r: r["lab_f1"])[:5]
P(f"The confusion matrix ({'Figure 8'}) is strongly diagonal. The remaining errors are concentrated among "
  f"visually similar diseases of the same crop: the lowest F1-scores are obtained for "
  + ", ".join(f"{r['class'].replace(' - ', ' ')} ({r['lab_f1']:.3f})" for r in low[:4])
  + f" and {low[4]['class'].replace(' - ', ' ')} ({low[4]['lab_f1']:.3f}). Early blight and target spot both "
    f"produce brown lesions with concentric rings, and northern leaf blight and gray leaf spot of maize both form "
    f"elongated grey-tan lesions that differ mainly in shape and size, so these confusions mirror those of "
    f"human observers. Per-class results are listed in Appendix A.")
figure("cm", FIG / "fig_confusion.png", "Row-normalised confusion matrix on the laboratory test set", width=15.0 * cm)

section("Performance on Field Photographs")
dm = D["domain"]
P(f"Field photographs are substantially harder (Table 12, {'Figure 9'}). A model trained only on laboratory "
  f"images, with the same architecture, reaches {pct(dm['base_lab'])} on laboratory test images but only "
  f"{pct(dm['base_field'])} on the field test set: it has learned to rely on cues, such as the uniform grey "
  f"background, that are absent in the field. Adding the PlantDoc field photographs to training, together with "
  f"a larger laboratory sample, raises field accuracy to {pct(dm['final_field'])}, a factor of "
  f"{dm['final_field'] / dm['base_field']:.1f}, while accuracy on the same {dm['old_test_n']:,} laboratory test "
  f"images rises from {pct(dm['base_lab'])} to {pct(dm['final_lab'])}. (The two models are compared on the "
  f"original {dm['old_test_n']:,}-image laboratory test split, which neither model saw during training.) The correct class is "
  f"among the three most probable in {pct(FM['top3_accuracy'])} of field images, and the category is correct "
  f"in {pct(FM['category_accuracy'])}, which matters because the category determines the type of advice.")
table("field", [
    ["Metric", "Laboratory-only model", "Final model"],
    [f"Accuracy on original laboratory test split ({dm['old_test_n']:,} images)", pct(dm["base_lab"]), pct(dm["final_lab"])],
    [f"Accuracy on full laboratory test set ({M['test_images']:,} images)", "&#8212;", pct(dm["final_lab_full"])],
    ["Accuracy on field test set", pct(dm["base_field"]), f"<b>{pct(dm['final_field'])}</b>"],
    ["Field top-3 accuracy", "&#8212;", pct(FM["top3_accuracy"])],
    ["Field macro F1-score", "&#8212;", f"{FM['f1_macro']:.3f}"],
    ["Field category routing accuracy", "&#8212;", pct(FM["category_accuracy"])],
    [f"Field coverage at threshold {FM['confidence_threshold']:.2f}", "&#8212;", pct(FM["coverage_at_threshold"])],
    [f"Field false diagnosis rate at threshold {FM['confidence_threshold']:.2f}", "&#8212;",
     pct(FM["false_diagnosis_rate_at_threshold"])],
], [8.0 * cm, 3.8 * cm, 3.7 * cm], f"Laboratory versus field performance ({FM['test_images']} field images)",
    align=["L", "C", "C"])
figure("gap", FIG / "fig_domain_gap.png", "Effect of including field photographs in training on laboratory and "
       "field accuracy", width=12.5 * cm)
P(f"Performance varies by crop ({'Figure 10'}). Grape, squash, raspberry and strawberry, whose field images "
  f"are visually distinctive, reach high field accuracy, while tomato and potato, which have the largest number "
  f"of similar-looking diseases, are among the most difficult. The per-crop field figures are based on small samples "
  f"of 4 to 12 images per class and should be read as indicative.")
figure("crop", FIG / "fig_per_crop.png", "Accuracy by crop on the laboratory and field test sets. Citrus has no "
       "field test images", width=15.0 * cm)

section("Abstention Trade-off")
P(f"{'Figure 11'} shows coverage and false diagnosis rate as functions of the confidence threshold. On "
  f"laboratory images, almost all predictions are confident and correct, so a threshold of 0.60 removes "
  f"{1 - M['false_diagnosis_rate_at_threshold'] / M['false_diagnosis_rate_no_abstention']:.0%} of the remaining errors while answering {pct(M['coverage_at_threshold'])} of images. On field "
  f"photographs, the stricter threshold of {FM['confidence_threshold']:.2f} reduces the false diagnosis rate "
  f"from {pct(1 - FM['accuracy'])} without abstention to {pct(FM['false_diagnosis_rate_at_threshold'])}, at the "
  f"cost of asking for a new photograph for {pct(1 - FM['coverage_at_threshold'])} of field images. The "
  f"threshold can be moved along this curve depending on how cautious a deployment needs to be.")
figure("thr", FIG / "fig_threshold.png", "Coverage and false diagnosis rate as functions of the confidence "
       "threshold on the laboratory (a) and field (b) test sets; dashed lines mark the thresholds used",
       width=15.5 * cm)

section("Training Behaviour")
P(f"{'Figure 12'} shows the validation accuracy during head training. Laboratory accuracy exceeds 94% within a "
  f"few epochs, reflecting the quality of the pre-trained features, while field validation accuracy fluctuates "
  f"around 60% on the small field validation set. The model from epoch {D['best_epoch']}, which maximises the "
  f"mean of the two, was retained; training stopped after {D['train_epochs']} epochs.")
figure("train", FIG / "fig_training.png", "Validation accuracy on laboratory and field images and training loss "
       "during head training", width=13.5 * cm)

section("Qualitative Results")
q = D["qualitative"]
P(f"{'Figure 13'} shows the complete pipeline on two laboratory images and two field photographs. The "
  f"laboratory tomato leaf with early blight is diagnosed with {q[0]['confidence']:.0%} confidence and "
  f"{q[0]['affected']:.0%} damaged tissue, giving a <i>{q[0]['severity']}</i> rating, whereas the heavily affected potato leaf "
  f"has {q[1]['affected']:.0%} damaged tissue and is rated <i>Severe</i> with a health score of {q[1]['score']}. "
  f"The field photographs of cedar apple rust and grape black rot are correctly isolated from foliage and soil, "
  f"and their lesions are highlighted in the damage map.")
figure("qual", FIG / "fig_qualitative.png", "Qualitative results: input, leaf segmentation, damage map (red: "
       "necrotic, yellow: chlorotic, blue: powdery) and system output for two laboratory images (rows 1&#8211;2) "
       "and two field photographs (rows 3&#8211;4)", width=14.5 * cm)
P(f"{'Figure 14'} shows three characteristic difficulties on field photographs. In (a), the correct class is "
  f"the most probable but with only {D['field_cases'][0]['top_p']:.0%} confidence, below the {D['field_threshold']:.2f} field threshold, and the system correctly asks for a new photograph instead "
  f"of guessing. In (b), Septoria leaf spot is confidently classified as early blight; both diseases produce "
  f"dark lesions surrounded by yellowing, and the photograph shows several overlapping leaves. In (c), the diagnosis "
  f"of late blight is correct, but the dark, low-saturation lesion at the leaf edge is excluded by the "
  f"segmentation, so the damaged area is underestimated; the minimum severity for late blight still yields a "
  f"<i>{D['field_cases'][2]['severity']}</i> rating.")
figure("cases", FIG / "fig_field_cases.png", "Challenging field photographs: correct abstention (a), "
       "misclassification between similar diseases (b) and underestimated damage area (c)", width=15.5 * cm)

section("Computational Performance")
P("Table 13 summarises the computational cost. All figures were measured on the laptop described above.")
table("perf", [
    ["Item", "Value"],
    ["Feature extraction, all training/validation/test images (one-time)", "&#8776; 23 minutes"],
    ["Classification head training", "&#8776; 5 minutes"],
    ["Full diagnosis, plain-background photograph", f"{T_LAB:.2f} s"],
    ["Full diagnosis, field photograph (including GrabCut)", f"{T_FLD:.2f} s"],
    ["Model file size (backbone + head)", "19.7 MB"],
    ["Android application package", "23 MB"],
], [10.5 * cm, 5.0 * cm], "Computational cost on a laptop CPU (Intel Core i5-1035G1, 8 GB RAM)", align=["L", "C"])

# ================================================================== 7 DISCUSSION
chapter("Discussion")
section("Laboratory Accuracy Overstates Real-World Performance")
P(f"The most important finding of this work is the size of the gap between laboratory and field performance. "
  f"A model that is {pct(dm['base_lab'])} accurate on PlantVillage is correct on only "
  f"{pct(dm['base_field'])} of field photographs. This agrees with earlier observations {C('mohanty', 'barbedo2018a', 'plantdoc')} and shows that "
  f"accuracy on a held-out split of a laboratory dataset should not be presented as an estimate of usefulness "
  f"in the field. Including even a modest number of field photographs in training more than doubles field "
  f"accuracy without harming laboratory accuracy, which indicates that data diversity, rather than model "
  f"capacity, is the limiting factor. Field accuracy of {pct(FM['accuracy'])} is, however, far from sufficient "
  f"for unsupervised use, which motivates the design choices discussed next.")
section("The Value of Calibration and Abstention")
P("Because field accuracy is moderate, the system's behaviour on uncertain inputs is as important as its "
  "accuracy. Temperature scaling makes the reported confidence meaningful, and the abstention rule converts "
  "low-confidence predictions into requests for a better photograph, which costs the user a few seconds rather "
  "than a wrong treatment. Using a separate, stricter threshold for field photographs reflects the different "
  "difficulty of the two conditions; the photograph type is detected automatically, so the user does not need "
  "to make this distinction. The remaining false diagnoses on field images (Figure 14b) are mostly confusions "
  "between diseases of the same crop that share symptoms; in such cases the category, and therefore the broad "
  "type of response (for example, a fungal disease requiring sanitation and a fungicide), is usually still "
  "correct.")
section("Design Trade-offs")
P("Freezing the backbone and training only the head made it possible to train the complete model on a CPU in "
  "under half an hour, at the cost of not adapting the convolutional features to plant imagery. Severity "
  "and nutrient screening are implemented with explicit colour rules rather than learned models. This choice "
  "makes their output explainable &#8212; the damage map shows exactly which pixels were counted &#8212; and "
  "requires no labelled severity or deficiency data, which is not available in the public datasets; the price "
  "is lower robustness to unusual lighting and lesion colours. Finally, separating the pipeline into a shared "
  "package behind a REST API allowed three interfaces to be built without duplicating any diagnostic logic.")

# ================================================================== 8 LIMITATIONS
chapter("Limitations and Future Work")
section("Limitations")
bullets([
    f"<b>Field accuracy.</b> Accuracy on field photographs ({pct(FM['accuracy'])}) remains far below laboratory "
    "accuracy. The PlantDoc training set is small (2,005 images) and contains label noise and images with "
    "several leaves or plants.",
    "<b>Pest coverage.</b> The only pest class available in the training data is spider-mite damage; other "
    "pests such as aphids, caterpillars and thrips are not recognised.",
    "<b>Nutrient deficiencies</b> are screened with colour rules rather than a trained model and cannot be "
    "confirmed visually; soil or tissue testing is required before any fertiliser decision.",
    "<b>Severity estimation</b> depends on colour segmentation. On field photographs, dark low-saturation "
    "lesions at the leaf edge can be excluded from the leaf mask (Figure 14c), and early lesions that remain "
    "green-hued are not counted, so severity may be underestimated.",
    "<b>Single-leaf input.</b> The system analyses one leaf per photograph and does not assess whole plants, "
    "fruit or stems.",
    "<b>Connectivity.</b> The Android application requires a reachable server on the local network; inference "
    "does not yet run on the phone itself.",
    "<b>Recommendations</b> are generic within each class and must be adapted to locally approved products and "
    "regulations.",
])
section("Future Work")
bullets([
    "Collect and label field photographs from local farms, particularly for tomato and potato, and use them for "
    "training and evaluation.",
    "Fine-tune the full backbone on GPU hardware and evaluate larger architectures such as EfficientNet.",
    f"Add an object-detection model such as YOLO {C('yolo')} to localise individual pests and lesions.",
    "Learn severity and segmentation from annotated lesion masks instead of colour rules.",
    "Run the classifier on the phone for offline use, with the server providing reports and history when "
    "connectivity is available.",
    "Integrate IoT soil and weather sensors for continuous monitoring and automatic alerts, and aggregate "
    "diagnoses into regional disease maps.",
    "Provide multilingual and voice interfaces for farmers.",
])

# ================================================================== 9 CONCLUSION
chapter("Conclusion")
P(f"This project designed, implemented and evaluated AgriVision AI, a crop health diagnosis system that turns a "
  f"single photograph of a leaf into a diagnosis, a severity assessment and context-aware recommendations. The "
  f"system combines image validation, two complementary leaf-segmentation strategies, a MobileNetV3-Large "
  f"classifier trained by transfer learning on laboratory and field images, calibrated confidence with "
  f"abstention, rule-based severity and nutrient screening, and a knowledge-based recommendation engine that "
  f"considers crop, severity, growth stage, weather, soil readings, region and field history. It is delivered "
  f"through a web application, a REST API and an Android application, with PDF reports and persistent history, "
  f"and runs entirely on a laptop CPU.")
P(f"On laboratory images, the classifier reaches {pct(M['accuracy'])} accuracy and, with abstention, a false "
  f"diagnosis rate of {pct(M['false_diagnosis_rate_at_threshold'], 2)}. On real field photographs, including "
  f"field images in training raised accuracy from {pct(dm['base_field'])} to {pct(FM['accuracy'])}, with "
  f"{pct(FM['top3_accuracy'])} top-3 accuracy and {pct(FM['category_accuracy'])} category accuracy. These results "
  f"show both what the approach achieves and where its limits lie: laboratory accuracy alone is not a reliable "
  f"indicator of field performance, and a practical tool must communicate its uncertainty and decline to "
  f"answer when it is unsure. AgriVision AI is therefore positioned as an early-screening and decision-support "
  f"tool that brings a first diagnosis to the farmer within seconds, while high-impact decisions remain subject "
  f"to confirmation by an agricultural expert or laboratory testing.")

# ================================================================== REFERENCES
story.append(PageBreak())
story.append(Heading("References", ParagraphStyle("rh", parent=h1, spaceAfter=12), 0))
REFS_PLACEHOLDER = len(story)

# ================================================================== APPENDICES
appendix_story = [PageBreak(), Heading("Appendix A&nbsp;&nbsp;Per-Class Results", h1, 0),
                  HRule(ACCENT, 1.2, 14)]
story_backup, story = story, appendix_story
P("Precision, recall and F1-score on the laboratory test set, and accuracy on the field test set, for each "
  "class. Field accuracy is not available for classes without PlantDoc test images.")
rows = [["Class", "Precision", "Recall", "F1", "<i>n</i> (lab)", "Field acc.", "<i>n</i> (field)"]]
for r in D["per_class"]:
    rows.append([r["class"], f"{r['lab_p']:.3f}", f"{r['lab_r']:.3f}", f"{r['lab_f1']:.3f}", str(r["lab_n"]),
                 f"{r['field_acc']:.2f}" if r["field_acc"] is not None else "&#8212;",
                 str(r["field_n"]) if r["field_n"] else "&#8212;"])
table("perclass", rows, [5.6 * cm, 1.7 * cm, 1.5 * cm, 1.4 * cm, 1.6 * cm, 1.9 * cm, 1.8 * cm],
      "Per-class results on the laboratory and field test sets", align=["L", "C", "C", "C", "C", "C", "C"],
      font=9, keep=False)

story.append(PageBreak())
story.append(Heading("Appendix B&nbsp;&nbsp;Knowledge Base Entry", h1, 0))
story.append(HRule(ACCENT, 1.2, 14))
e = kb["Tomato___Early_blight"]
P("The knowledge-base entry for tomato early blight, as used by the recommendation engine:")
fav = e["favourable"]
table("kbentry", [
    ["Field", "Content"],
    ["Crop / condition / category", f"{e['crop']} / {e['name']} / {e['category']} ({e['cause_type']})"],
    ["Cause", e["cause"]],
    ["Symptoms", "<br/>".join(f"&#8226; {s}" for s in e["symptoms"])],
    ["Cultural actions", "<br/>".join(f"&#8226; {s}" for s in e["actions"])],
    ["Treatment", e["treatment"]],
    ["Prevention", "<br/>".join(f"&#8226; {s}" for s in e["prevention"])],
    ["Favourable conditions", f"{fav['temp_min']}&#8211;{fav['temp_max']} &#176;C, relative humidity &#8805; "
                              f"{fav['humidity_min']}%: {fav['note'].lower()}"],
], [4.2 * cm, 11.3 * cm], "Knowledge-base entry for tomato early blight", zebra=False)
appendix_story = story
story = story_backup

# references in order of first citation
refs = [Paragraph(f"[{i}]&nbsp;&nbsp;{REFS[k]}", ref_style) for i, k in enumerate(ORDER, 1)]
story[REFS_PLACEHOLDER:REFS_PLACEHOLDER] = refs
story += appendix_story

unused = set(REFS) - set(ORDER)
assert not unused, f"unused references: {unused}"

# ================================================================== BUILD
doc = Doc(OUT)
doc.multiBuild(story)
print(f"Wrote {OUT}  ({OUT.stat().st_size / 1e6:.1f} MB), {len(ORDER)} references, "
      f"{fig_no[0]} figures, {tab_no[0]} tables, {eq_no[0]} equations; timing lab {T_LAB:.2f}s field {T_FLD:.2f}s")
