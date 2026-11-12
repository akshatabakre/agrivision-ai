// AgriVision AI - final presentation (16 slides, follows the mid-sem deck)
//   cd presentation && node build_deck.js
const path = require("path");
const fs = require("fs");
const pptxgen = require("pptxgenjs");

const SKILL = "C:/Users/HP/.claude/skills/synced/7247c6c1-9eb5-4e77-92e9-4901990cbca4_db084f2d-7415-4023-a509-49b210d5cf8f/pptx";
const { applyTheme } = require(path.join(SKILL, "scripts", "apply_theme.js"));

const D = JSON.parse(fs.readFileSync(path.join(__dirname, "deck_data.json"), "utf8"));
const A = (f) => path.join(__dirname, "assets", f);
const OUT = path.join(__dirname, "AgriVision_AI_Final_Presentation.pptx");
const pct = (x, d = 1) => `${(x * 100).toFixed(d)}%`;

// ---------------------------------------------------------------- theme (mid-sem palette)
const THEME = {
  name: "AgriVision",
  headFontFace: "Georgia",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "221C16", lt1: "FFFFFF", dk2: "1E1A15", lt2: "F3EBDD",
    accent1: "3A6B35", accent2: "D9822B", accent3: "B5452F", accent4: "2B6C9E",
    accent5: "B8961A", accent6: "8DBF6A", hlink: "3A6B35", folHlink: "6B5B95",
  },
};
const H = {   // hex for decorative fills that sit outside the 12 theme slots
  paper: "FAF5EC", line: "E3D8C6", muted: "7D7063", mutedDark: "A39482", card: "2A241D", deep: "15120F",
  rule: "D9CDBA", ruleDark: "3A332B", cream: "F2EBDD", tintG: "E6EDDF", tintO: "F6E7D3", tintR: "F2DDD6",
  tintB: "DCE7F0", tintY: "F1EAD0",
};
const MONO = "Consolas";

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";       // 13.333 x 7.5 in
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "AgriVision AI - Final Presentation";
pres.author = "Akshata Bakre, Himanshu Kashyap";
pres.subject = "Minor Project - AI-Powered Crop Health Monitoring and Failure Diagnosis";
const C = pres.SchemeColor;
const INK = C.text1, DARK = C.text2, CREAM = C.background2, WHITE = C.background1;
const GREEN = C.accent1, ORANGE = C.accent2, RED = C.accent3, BLUE = C.accent4, MUSTARD = C.accent5, LGREEN = C.accent6;

// ---------------------------------------------------------------- layouts
function contentLayout(name, dark) {
  pres.defineSlideMaster({
    title: name,
    background: { color: dark ? "1E1A15" : "F3EBDD" },
    margin: [0.5, 0.6, 0.5, 0.6],
    objects: [
      { text: { text: "AGRIVISION AI", options: { x: 0.6, y: 0.3, w: 4, h: 0.3, fontFace: MONO, fontSize: 10, charSpacing: 3,
        color: dark ? H.mutedDark : H.muted, margin: 0, valign: "top" } } },
      { placeholder: { options: { name: "section", type: "body", x: 6.73, y: 0.3, w: 6.0, h: 0.3, fontFace: MONO, fontSize: 10,
        charSpacing: 2, color: dark ? "8DBF6A" : "3A6B35", align: "right", valign: "top", margin: 0 }, text: "" } },
      { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.62, w: 12.13, h: 0.82, fontFace: "Georgia",
        fontSize: 34, bold: true, color: dark ? H.cream : "221C16", valign: "bottom", align: "left", margin: 0 }, text: "" } },
      { line: { x: 0.6, y: 1.56, w: 12.13, h: 0, line: { color: dark ? H.ruleDark : H.rule, width: 0.75 } } },
      { placeholder: { options: { name: "presenter", type: "body", x: 0.6, y: 7.02, w: 7, h: 0.26, fontFace: MONO, fontSize: 9.5,
        charSpacing: 2, color: dark ? H.mutedDark : H.muted, valign: "top", margin: 0 }, text: "" } },
      { text: { text: "/ 16", options: { x: 12.33, y: 7.02, w: 0.4, h: 0.26, fontFace: MONO, fontSize: 9.5, margin: 0, valign: "top",
        color: dark ? H.mutedDark : H.muted } } },
    ],
    slideNumber: { x: 11.78, y: 7.02, w: 0.5, h: 0.26, fontFace: MONO, fontSize: 9.5, align: "right",
      color: dark ? H.mutedDark : H.muted, margin: 0 },
  });
}
contentLayout("LIGHT", false);
contentLayout("DARK", true);
pres.defineSlideMaster({ title: "COVER", background: { color: "1E1A15" } });

const AKSHATA = "PRESENTED BY AKSHATA BAKRE", HIMANSHU = "PRESENTED BY HIMANSHU KASHYAP";

function contentSlide(layout, section, kicker, title, presenter) {
  const s = pres.addSlide({ masterName: layout, sectionTitle: section });
  s.addText(kicker, { placeholder: "section" });
  s.addText(title, { placeholder: "title" });
  s.addText(presenter, { placeholder: "presenter" });
  return s;
}

// ---------------------------------------------------------------- drawing helpers
function T(s, text, o) { s.addText(text, Object.assign({ isTextBox: true, margin: 0, valign: "top", align: "left" }, o)); }
function kicker(s, text, x, y, w, color) {
  T(s, text, { x, y, w, h: 0.28, fontFace: MONO, fontSize: 10.5, charSpacing: 2, color: color || H.muted });
}
function box(s, x, y, w, h, fill, opts = {}) {
  s.addShape(opts.round === false ? pres.shapes.RECTANGLE : pres.shapes.ROUNDED_RECTANGLE,
    Object.assign({ x, y, w, h, fill: { color: fill }, line: { color: opts.line || fill, width: opts.lw || 0.75 } },
      opts.round === false ? {} : { rectRadius: 0.06 }, opts.name ? { objectName: opts.name } : {}));
}
function arrowDown(s, x, y, len, color) {
  s.addShape(pres.shapes.LINE, { x, y, w: 0, h: len, line: { color, width: 1.25, endArrowType: "triangle" } });
}
function arrowRight(s, x, y, len, color) {
  s.addShape(pres.shapes.LINE, { x, y, w: len, h: 0, line: { color, width: 1.25, endArrowType: "triangle" } });
}
function img(s, file, x, y, w, h, name) {
  s.addImage({ path: A(file), x, y, w, h, altText: name || file, objectName: name || file });
}
function phone(s, file, x, y, h, caption, dark) {
  const w = h * 0.45;
  img(s, file, x, y, w, h, "Screenshot placeholder - right-click, Change Picture");
  if (caption) T(s, caption, { x: x - 0.2, y: y + h + 0.08, w: w + 0.4, h: 0.26, fontFace: MONO, fontSize: 10,
    align: "center", color: dark ? H.mutedDark : H.muted });
  return w;
}
function chip(s, text, x, y, w, fill, color, size = 12) {
  box(s, x, y, w, 0.34, fill);
  T(s, text, { x, y, w, h: 0.34, align: "center", valign: "middle", fontSize: size, bold: true, color });
}
function healthBar(s, x, y, w, score, color, track) {
  box(s, x, y, w, 0.16, track, { round: false });
  box(s, x, y, w * score / 100, 0.16, color, { round: false });
}
const sevColour = (sev) => ({ Healthy: GREEN, Mild: MUSTARD, Moderate: ORANGE, Severe: RED }[sev] || H.muted);
const sevHex = (sev) => ({ Healthy: "3A6B35", Mild: "B8961A", Moderate: "D9822B", Severe: "B5452F" }[sev] || "7D7063");

const ex = D.ex, tom = ex.tomato, pot = ex.potato, mite = ex.mite, L = D.lab, F = D.field;

// ======================================================================== 1 TITLE (Akshata)
pres.addSection({ title: "Problem & Solution" });
{
  const s = pres.addSlide({ masterName: "COVER", sectionTitle: "Problem & Solution" });
  box(s, 0, 0, 0.14, 7.5, "3A6B35", { round: false, name: "Brand edge" });
  T(s, "CROP HEALTH INTELLIGENCE  \u00B7  MINOR PROJECT", { x: 0.75, y: 0.62, w: 6.5, h: 0.3, fontFace: MONO, fontSize: 11,
    charSpacing: 2, color: H.mutedDark });
  T(s, "AgriVision AI", { x: 0.75, y: 1.0, w: 6.7, h: 1.25, fontFace: "Georgia", fontSize: 60, bold: true, color: H.cream });
  s.addShape(pres.shapes.LINE, { x: 0.78, y: 2.4, w: 3.0, h: 0, line: { color: H.mutedDark, width: 1 } });
  T(s, "AI-Powered Crop Health Monitoring\n& Failure Diagnosis", { x: 0.75, y: 2.6, w: 6.6, h: 1.05, fontFace: "Georgia",
    fontSize: 25, bold: true, color: H.cream });
  T(s, "Detect crop diseases, pest damage and nutrient deficiencies from a single leaf photograph \u2014 on the web or an Android phone.",
    { x: 0.75, y: 3.78, w: 6.4, h: 0.75, fontSize: 15, color: "C9BDAC" });
  T(s, "PRESENTED BY", { x: 0.75, y: 4.75, w: 3, h: 0.25, fontFace: MONO, fontSize: 10.5, charSpacing: 2, color: H.mutedDark });
  T(s, "Akshata Bakre \u2014 23118007\nHimanshu Kashyap \u2014 23118043", { x: 0.75, y: 5.02, w: 5.5, h: 0.62, fontFace: MONO,
    fontSize: 14, color: H.cream, paraSpaceAfter: 2 });
  T(s, [{ text: "GUIDED BY  ", options: { color: H.mutedDark, fontSize: 10.5, charSpacing: 2 } },
        { text: "Dr. Sanjay Kumar", options: { color: H.cream, fontSize: 14 } }],
    { x: 0.75, y: 5.8, w: 6, h: 0.3, fontFace: MONO });
  T(s, "DEPARTMENT OF INFORMATION TECHNOLOGY  \u00B7  NIT RAIPUR", { x: 0.75, y: 6.25, w: 6.5, h: 0.28, fontFace: MONO,
    fontSize: 10.5, charSpacing: 2, color: H.mutedDark });

  // live output card
  const X = 7.75, Y = 0.85, W = 4.95;
  box(s, X, Y, W, 5.7, H.deep, { line: H.ruleDark, name: "Live output card" });
  T(s, "// LIVE OUTPUT FROM OUR TRAINED MODEL", { x: X + 0.3, y: Y + 0.25, w: W - 0.5, h: 0.28, fontFace: MONO, fontSize: 10.5,
    charSpacing: 1, color: H.mutedDark });
  img(s, "ex_tomato_original_sq.png", X + 0.3, Y + 0.68, 2.05, 2.05, "Input tomato leaf photo");
  img(s, "ex_tomato_overlay_sq.png", X + 2.6, Y + 0.68, 2.05, 2.05, "Damage map produced by the system");
  T(s, "Input photo", { x: X + 0.3, y: Y + 2.77, w: 2.05, h: 0.22, fontFace: MONO, fontSize: 9.5, color: H.mutedDark, align: "center" });
  T(s, "Damage map", { x: X + 2.6, y: Y + 2.77, w: 2.05, h: 0.22, fontFace: MONO, fontSize: 9.5, color: H.mutedDark, align: "center" });
  const rows = [
    ["DETECTED", `${tom.crop} \u2014 ${tom.display_name}`, H.cream, true],
    ["CONFIDENCE", pct(tom.confidence, 0), "8DBF6A", true],
    ["SEVERITY", `${tom.severity}  \u00B7  health ${tom.health_score} / 100`, sevHex(tom.severity), true],
    ["CAUSE", "Fungal infection (Alternaria solani)", H.cream, false],
    ["ACTION", tom.rec.actions.slice(0, 2).join("; "), H.cream, false],
  ];
  rows.forEach((r, i) => {
    const yy = Y + 3.15 + i * 0.44;
    T(s, r[0], { x: X + 0.3, y: yy, w: 1.35, h: 0.4, fontFace: MONO, fontSize: 10.5, color: H.mutedDark });
    T(s, r[1], { x: X + 1.6, y: yy - 0.03, w: W - 1.85, h: 0.42, fontFace: MONO, fontSize: i < 3 ? 13 : 11, bold: r[3], color: r[2] });
  });
  T(s, "A field photograph from the held-out test set, never seen during training. AI diagnosis is an early-screening aid, not a definitive agricultural verdict.",
    { x: X, y: 6.68, w: W, h: 0.5, fontSize: 10, italic: true, color: H.mutedDark });
  s.addNotes(
`Good morning. We are presenting AgriVision AI, our minor project on crop health monitoring. I am Akshata, and Himanshu will present the technical parts.

The idea in one line: a farmer takes one photo of a crop leaf and our system tells what is wrong, how sure it is, how serious it is, and what to do.

The card on the right is not a mock-up. It is a real output of our trained model on a tomato leaf photographed in a field, from a test set the model never saw. It detects Early Blight with ${pct(tom.confidence, 0)} confidence, rates it ${tom.severity} with a health score of ${tom.health_score} out of 100, shows the damage map, and gives actions.`);
}

// ======================================================================== 2 PROBLEM (Akshata)
{
  const s = contentSlide("LIGHT", "Problem & Solution", "01 \u00B7 THE PROBLEM", "Damage is usually noticed too late", AKSHATA);
  T(s, "Farmers often identify crop problems only after the visible damage has already become severe.",
    { x: 0.6, y: 1.85, w: 5.9, h: 0.85, fontFace: "Georgia", fontSize: 19, italic: true, color: "3D342B" });
  kicker(s, "WHY IT HAPPENS", 0.6, 2.95, 4);
  const ch = ["Diseases look alike in their early stages", "Nutrient deficiencies mimic disease symptoms",
    "Pests spread before they are noticed", "Few agricultural experts are nearby",
    "Manual field inspection is slow and tiring", "Wrong treatment increases the losses"];
  ch.forEach((c, i) => {
    const y = 3.3 + i * 0.55;
    T(s, String(i + 1).padStart(2, "0"), { x: 0.6, y, w: 0.5, h: 0.4, fontFace: MONO, fontSize: 13, color: RED });
    T(s, c, { x: 1.15, y: y - 0.02, w: 5.3, h: 0.42, fontSize: 16, color: INK });
  });
  s.addChart(pres.charts.BAR, [{ name: "Yield lost", labels: ["Rice", "Maize", "Wheat", "Soybean", "Potato"],
    values: [30.0, 22.5, 21.5, 21.4, 17.2] }], {
    x: 6.95, y: 1.8, w: 5.78, h: 2.7, barDir: "bar", chartColors: ["B5452F"], showValue: true,
    dataLabelFormatCode: '0.0"%"', dataLabelColor: "221C16", dataLabelFontSize: 12, dataLabelFontFace: "+mn-lt",
    catAxisLabelColor: "4A4038", catAxisLabelFontSize: 12, catAxisLabelFontFace: "+mn-lt", catAxisOrientation: "maxMin",
    valAxisHidden: true, valGridLine: { style: "none" }, catGridLine: { style: "none" }, showLegend: false,
    showTitle: true, title: "Global yield lost to pathogens and pests (%)", titleFontSize: 13, titleColor: "221C16",
    titleFontFace: "+mn-lt", barGapWidthPct: 60, objectName: "Yield loss chart",
  });
  T(s, "Source: Savary et al., Nature Ecology & Evolution, 2019", { x: 6.95, y: 4.5, w: 5.78, h: 0.25, fontSize: 10,
    italic: true, color: H.muted });
  box(s, 6.95, 4.9, 5.78, 1.85, "221C16", { name: "Impact chain" });
  kicker(s, "// IMPACT CHAIN", 7.2, 5.05, 3, H.mutedDark);
  const chain = ["Late\ndetection", "Wrong\ndiagnosis", "Wrong\ntreatment", "Lower\nyield", "Financial\nloss"];
  chain.forEach((c, i) => {
    const x = 7.2 + i * 1.07;
    box(s, x, 5.42, 0.88, 0.66, i === 4 ? "B5452F" : "3A332B");
    T(s, c, { x, y: 5.42, w: 0.88, h: 0.66, align: "center", valign: "middle", fontSize: 11.5, bold: true, color: H.cream });
    if (i < 4) arrowRight(s, x + 0.9, 5.75, 0.15, H.mutedDark);
  });
  T(s, "Each step makes the next one worse \u2014 so the intervention must happen at detection.",
    { x: 7.2, y: 6.25, w: 5.3, h: 0.35, fontSize: 12, color: "C9BDAC" });
  s.addNotes(
`The problem: farmers usually notice a crop problem only when the damage is already severe.

Six reasons on the left: diseases look alike early, a plant lacking nutrients can look diseased, pests spread before anyone notices, experts are far away, checking fields by hand is slow, and a wrong treatment makes losses worse.

The chart shows how big this is: a 2019 global study estimated that pathogens and pests destroy about 30% of rice and over 20% of maize, wheat and soybean.

The impact chain at the bottom is the key idea: late detection leads to a wrong diagnosis, wrong treatment, lower yield and money lost. Each step makes the next worse, so we attack the first one - detection.`);
}

// ======================================================================== 3 SOLUTION (Akshata)
{
  const s = contentSlide("LIGHT", "Problem & Solution", "02 \u00B7 OUR SOLUTION", "One photograph, seven answers", AKSHATA);
  kicker(s, "WHAT THE FARMER GETS FROM ONE PHOTO", 0.6, 1.82, 4.6);
  const ans = [["Is the photo usable?", "Blur, lighting and leaf-presence checks"],
    ["What is wrong?", "38 crop conditions across 14 crops"],
    ["What type of problem?", "Disease, pest, nutrient deficiency or healthy"],
    ["How sure is the AI?", "Calibrated confidence; asks for a re-capture if unsure"],
    ["How bad is it?", "Health score 0\u2013100 and a severity band"],
    ["What should I do?", "Advice that fits the crop, weather and field history"],
    ["A record to keep", "PDF report and per-field history"]];
  ans.forEach((a, i) => {
    const y = 2.18 + i * 0.66;
    box(s, 0.6, y + 0.03, 0.42, 0.42, i === 6 ? "221C16" : "3A6B35");
    T(s, String(i + 1), { x: 0.6, y: y + 0.03, w: 0.42, h: 0.42, align: "center", valign: "middle", fontFace: MONO,
      fontSize: 13, bold: true, color: WHITE });
    T(s, a[0], { x: 1.17, y, w: 3.9, h: 0.27, fontSize: 15, bold: true, color: INK });
    T(s, a[1], { x: 1.17, y: y + 0.27, w: 3.9, h: 0.26, fontSize: 12, color: H.muted });
  });
  // worked example
  const X = 5.3, W = 4.6;
  box(s, X, 1.82, W, 4.95, "221C16", { name: "Worked example" });
  kicker(s, "// WORKED EXAMPLE \u2014 REAL SYSTEM OUTPUT", X + 0.25, 1.98, W - 0.4, H.mutedDark);
  img(s, "ex_tomato_original_sq.png", X + 0.25, 2.38, 1.15, 1.15, "Tomato leaf input");
  T(s, [{ text: "INPUT\n", options: { fontFace: MONO, fontSize: 10.5, color: H.mutedDark } },
        { text: "Tomato leaf photographed in a field", options: { fontSize: 13, color: H.cream } }],
    { x: X + 1.55, y: 2.45, w: W - 1.8, h: 0.9 });
  arrowDown(s, X + 0.82, 3.6, 0.25, H.mutedDark);
  T(s, "AI ANALYSIS", { x: X + 0.25, y: 3.9, w: 2, h: 0.25, fontFace: MONO, fontSize: 10.5, color: H.mutedDark });
  const an = [["Disease", tom.display_name, "E8A57A"], ["Confidence", pct(tom.confidence, 0), "8DBF6A"],
    ["Severity", `${tom.severity} (health ${tom.health_score}/100)`, sevHex(tom.severity)]];
  an.forEach((r, i) => {
    T(s, r[0], { x: X + 0.4, y: 4.18 + i * 0.32, w: 1.4, h: 0.3, fontFace: MONO, fontSize: 12.5, color: H.cream });
    T(s, r[1], { x: X + 1.85, y: 4.18 + i * 0.32, w: W - 2.0, h: 0.3, fontFace: MONO, fontSize: 12.5, bold: true, color: r[2] });
  });
  arrowDown(s, X + 0.82, 5.17, 0.22, H.mutedDark);
  T(s, "RECOMMENDATION", { x: X + 0.25, y: 5.42, w: 2.5, h: 0.25, fontFace: MONO, fontSize: 10.5, color: H.mutedDark });
  T(s, tom.rec.actions.slice(0, 3).map((a, i) => ({ text: a, options: { bullet: true, breakLine: i < 2 } })),
    { x: X + 0.4, y: 5.68, w: W - 0.6, h: 0.95, fontSize: 12.5, color: H.cream, paraSpaceAfter: 2 });
  phone(s, "ph_diagnose.png", 10.35, 1.82, 4.62, "Diagnose screen");
  s.addNotes(
`Our solution: one photograph gives seven answers - listed on the left. Is the photo usable, what is wrong, what type of problem it is, how sure the AI is, how bad it is, what to do, and a record to keep.

The dark card is a real example from our system, not an illustration. A tomato leaf photo goes in; the AI says Early Blight with ${pct(tom.confidence, 0)} confidence, severity ${tom.severity}; and the recommendation engine gives concrete actions.

The point from our mid-sem still holds: the farmer never sees a model - they see a verdict, a severity and a next action.

On the right is the Diagnose screen of our Android app.`);
}

// ======================================================================== 4 FEATURES (Akshata)
{
  const s = contentSlide("LIGHT", "Problem & Solution", "03 \u00B7 KEY FEATURES", "Six capabilities, one upload", AKSHATA);
  const cards = [
    ["01", "Image-based diagnosis", "MobileNetV3 deep-learning model trained on 41,141 lab and 2,578 field photos.", `${pct(L.accuracy)} lab accuracy`, "3A6B35", H.tintG],
    ["02", "Disease detection", "25 diseases: blight, rust, mildew, scab, leaf spots and viruses.", "14 crops", "B5452F", H.tintR],
    ["03", "Pest detection", "Spider-mite damage is recognised and routed as a pest, with pest-specific advice.", "Category: Pest", "D9822B", H.tintO],
    ["04", "Nutrient deficiency", "N \u00B7 K \u00B7 Fe/Mg yellowing patterns detected by colour analysis of the leaf.", "Confirm with soil test", "2B6C9E", H.tintB],
    ["05", "Severity estimation", "Damaged leaf area becomes a 0\u2013100 health score: Healthy \u2192 Mild \u2192 Moderate \u2192 Severe.", "Damage map shown", "B8961A", H.tintY],
    ["06", "Recommendations", "Advice adapts to severity, weather, growth stage, soil, region and field history.", "39-entry knowledge base", "8DBF6A", "3A332B"],
  ];
  cards.forEach((c, i) => {
    const x = 0.6 + (i % 3) * 4.13, y = 1.85 + Math.floor(i / 3) * 2.5, w = 3.87, h = 2.3;
    const dark = i === 5;
    box(s, x, y, w, h, dark ? "221C16" : H.paper, { line: dark ? "221C16" : H.line, round: false, name: `Feature ${c[0]}` });
    box(s, x, y, w, 0.06, c[4], { round: false });
    T(s, c[0], { x: x + 0.25, y: y + 0.22, w: 1, h: 0.25, fontFace: MONO, fontSize: 10.5, color: dark ? H.mutedDark : H.muted });
    T(s, c[1], { x: x + 0.25, y: y + 0.45, w: w - 0.5, h: 0.45, fontFace: "Georgia", fontSize: 20, bold: true, color: dark ? H.cream : INK });
    T(s, c[2], { x: x + 0.25, y: y + 0.95, w: w - 0.5, h: 0.8, fontSize: 14, color: dark ? "D8CDBE" : "3D342B" });
    chip(s, c[3], x + 0.25, y + h - 0.5, w - 0.5, c[5], dark ? H.cream : INK, 12);
  });
  s.addNotes(
`Six capabilities, all from one upload.

One - diagnosis: a MobileNetV3 deep-learning model trained on about 41 thousand lab photos and 2,600 real field photos; ${pct(L.accuracy)} accurate on lab test photos.
Two - disease detection: 25 diseases across 14 crops - blights, rusts, mildew, scab, leaf spots and viruses.
Three - pest detection: spider-mite damage is detected and labelled as a pest, so the advice is pest advice, not fungicide.
Four - nutrient deficiency: nitrogen, potassium and iron or magnesium deficiencies have typical yellowing patterns; we detect them by analysing leaf colours and always ask for a soil test to confirm.
Five - severity: we measure how much of the leaf is damaged and convert it to a 0 to 100 health score.
Six - recommendations: advice changes with severity, weather, growth stage and the field's history.`);
}

// ======================================================================== 5 WORKFLOW (Himanshu)
pres.addSection({ title: "Technical Approach" });
{
  const s = contentSlide("DARK", "Technical Approach", "04 \u00B7 WORKFLOW & CV PIPELINE", "From shutter to report", HIMANSHU);
  kicker(s, "// END-TO-END WORKFLOW", 0.6, 1.82, 5, H.mutedDark);
  const steps = [["Capture or upload", "Phone camera, gallery or web upload"],
    ["Validate & enhance", "Blur, exposure, leaf present; CLAHE for dark photos"],
    ["Find the leaf", "Colour threshold, or focus-seeded GrabCut in the field"],
    ["Classify", "MobileNetV3 \u2192 probabilities for 39 classes"],
    ["Abstain if unsure", `Below 60% (${Math.round(D.field_threshold * 100)}% for field photos) \u2192 re-capture`],
    ["Severity & nutrients", "Damaged-area score; N / K / Fe-Mg patterns"],
    ["Advise & report", "Knowledge base + context \u2192 screen, PDF, history"]];
  steps.forEach((st, i) => {
    const y = 2.18 + i * 0.65;
    s.addShape(pres.shapes.OVAL, { x: 0.6, y: y + 0.04, w: 0.4, h: 0.4, fill: { color: i === 4 ? "B5452F" : "3A6B35" }, line: { color: "1E1A15" } });
    T(s, String(i + 1), { x: 0.6, y: y + 0.04, w: 0.4, h: 0.4, align: "center", valign: "middle", fontFace: MONO, fontSize: 12, bold: true, color: WHITE });
    T(s, st[0], { x: 1.15, y, w: 4.5, h: 0.27, fontSize: 15, bold: true, color: H.cream });
    T(s, st[1], { x: 1.15, y: y + 0.27, w: 4.6, h: 0.26, fontSize: 12, color: H.mutedDark });
  });
  kicker(s, "// COMPUTER VISION PIPELINE \u2014 REAL IMAGES", 6.15, 1.82, 6.5, H.mutedDark);
  const ims = [["ex_apple_original_sq.png", "1  Input photo"], ["ex_apple_leaf_sq.png", "2  Leaf isolated"], ["ex_apple_overlay_sq.png", "3  Damage map"]];
  ims.forEach((m, i) => {
    const x = 6.15 + i * 2.25;
    img(s, m[0], x, 2.2, 1.95, 1.95, m[1]);
    T(s, m[1], { x, y: 4.2, w: 1.95, h: 0.25, align: "center", fontFace: MONO, fontSize: 10.5, color: H.cream });
    if (i < 2) arrowRight(s, x + 1.98, 3.17, 0.24, H.mutedDark);
  });
  const facts = [["BLUR CHECK", "Variance of Laplacian must be \u2265 40"], ["EXPOSURE", "Mean brightness between 40 and 225"],
    ["MODEL INPUT", "Resized to 224 \u00D7 224, ImageNet-normalised"], ["DAMAGE COLOURS", "Red necrotic \u00B7 yellow chlorotic \u00B7 blue powdery"]];
  facts.forEach((f, i) => {
    const x = 6.15 + (i % 2) * 3.32, y = 4.7 + Math.floor(i / 2) * 1.05;
    box(s, x, y, 3.17, 0.9, H.card, { line: H.ruleDark });
    T(s, f[0], { x: x + 0.2, y: y + 0.12, w: 2.8, h: 0.24, fontFace: MONO, fontSize: 10, color: "8DBF6A" });
    T(s, f[1], { x: x + 0.2, y: y + 0.38, w: 2.85, h: 0.45, fontSize: 13, color: H.cream });
  });
  s.addNotes(
`This is what happens to one photo, step by step.

First the photo is checked: is it sharp enough, is it too dark or too bright, is there a leaf? Then we find the leaf. For plain-background photos, colour is enough. For field photos, we use GrabCut seeded by focus - the leaf you photograph is sharp, the background is blurred.

Then the MobileNetV3 model classifies the image. If confidence is too low, the app asks for a new photo instead of guessing. Otherwise we measure severity, check nutrient patterns, and generate advice and a report.

On the right are real images from our pipeline: the input, the isolated leaf, and the damage map where red is dead tissue and yellow is weakened tissue.`);
}

// ======================================================================== 6 AI MODEL (Himanshu)
{
  const s = contentSlide("LIGHT", "Technical Approach", "05 \u00B7 AI MODEL", "Transfer learning, deliberately small", HIMANSHU);
  kicker(s, "CANDIDATE BACKBONES", 0.6, 1.82, 4);
  const bb = [["MobileNetV3-L", "5.5 M params", true], ["EfficientNet-B0", "5.3 M params", false], ["ResNet-50", "25.6 M params", false], ["ConvNeXt-T", "28.6 M params", false]];
  bb.forEach((b, i) => {
    const y = 2.18 + i * 0.6;
    T(s, b[0], { x: 0.6, y, w: 2.5, h: 0.45, fontFace: "Georgia", fontSize: 20, bold: b[2], color: b[2] ? GREEN : INK });
    T(s, b[1], { x: 3.0, y: y + 0.1, w: 1.4, h: 0.3, fontFace: MONO, fontSize: 11, color: H.muted, align: "right" });
  });
  chip(s, "\u2713 Chosen: fast, small, phone-friendly", 0.6, 4.65, 3.8, H.tintG, GREEN, 12);
  T(s, "We reuse a network that already learned to \u201csee\u201d from 1.2 million everyday photos (ImageNet) and teach only a small plant-specific part \u2014 far less data and compute.",
    { x: 0.6, y: 5.15, w: 3.85, h: 1.5, fontSize: 14, color: "3D342B" });
  // training card
  const X = 4.8, W = 4.1;
  box(s, X, 1.82, W, 4.95, "3A6B35", { name: "How we trained it" });
  T(s, "HOW WE TRAINED IT", { x: X + 0.3, y: 2.0, w: W - 0.5, h: 0.28, fontFace: MONO, fontSize: 10.5, charSpacing: 2, color: "D5E6C8" });
  const tr = [["Frozen backbone", "4.2 M weights reused as-is"], ["Image \u2192 1,280-number fingerprint", "computed once per photo, then cached"],
    ["Small MLP head (trained)", "1,280 \u2192 512 \u2192 39 classes \u00B7 676 K weights"], ["Confidence calibration", `temperature scaling, T = ${D.temperature.toFixed(2)}`]];
  tr.forEach((t, i) => {
    const y = 2.4 + i * 0.78;
    T(s, t[0], { x: X + 0.3, y, w: W - 0.5, h: 0.3, fontSize: 15, bold: true, color: WHITE });
    T(s, t[1], { x: X + 0.3, y: y + 0.3, w: W - 0.5, h: 0.28, fontSize: 12.5, color: "D5E6C8" });
    if (i < 3) arrowDown(s, X + 0.4, y + 0.6, 0.15, "D5E6C8");
  });
  T(s, "\u2248 25 min", { x: X + 0.3, y: 5.65, w: 2.2, h: 0.6, fontFace: "Georgia", fontSize: 30, bold: true, color: WHITE });
  T(s, "total training on a laptop CPU \u2014 no GPU", { x: X + 0.3, y: 6.25, w: W - 0.5, h: 0.3, fontSize: 12.5, color: "D5E6C8" });
  // output card
  const X2 = 9.2, W2 = 3.53;
  box(s, X2, 1.82, W2, 4.95, "221C16", { name: "Model output" });
  kicker(s, "// MODEL OUTPUT", X2 + 0.25, 1.98, 3, H.mutedDark);
  img(s, "ex_tomato_original_sq.png", X2 + 0.25, 2.35, 1.0, 1.0, "Input leaf");
  T(s, [{ text: "INPUT\n", options: { fontFace: MONO, fontSize: 10, color: H.mutedDark } }, { text: "field photo of a tomato leaf", options: { fontSize: 12, color: H.cream } }],
    { x: X2 + 1.4, y: 2.42, w: W2 - 1.6, h: 0.9 });
  T(s, "TOP-3 PREDICTIONS", { x: X2 + 0.25, y: 3.55, w: 3, h: 0.25, fontFace: MONO, fontSize: 10, color: H.mutedDark });
  tom.top_k.slice(0, 3).forEach((t, i) => {
    const y = 3.88 + i * 0.52;
    T(s, `${t.crop} \u2013 ${t.name}`, { x: X2 + 0.25, y, w: W2 - 0.5, h: 0.24, fontSize: 12, color: H.cream });
    box(s, X2 + 0.25, y + 0.27, 2.3, 0.13, "3A332B", { round: false });
    box(s, X2 + 0.25, y + 0.27, Math.max(0.03, 2.3 * t.probability), 0.13, i === 0 ? "8DBF6A" : H.mutedDark, { round: false });
    T(s, pct(t.probability), { x: X2 + 2.6, y: y + 0.2, w: 0.7, h: 0.24, fontFace: MONO, fontSize: 11, color: H.cream, align: "right" });
  });
  T(s, "NEXT", { x: X2 + 0.25, y: 5.55, w: 2, h: 0.25, fontFace: MONO, fontSize: 10, color: H.mutedDark });
  T(s, "\u2192 Severity engine\n\u2192 Recommendation engine", { x: X2 + 0.25, y: 5.82, w: W2 - 0.5, h: 0.6, fontFace: MONO, fontSize: 12, color: H.cream });
  s.addNotes(
`Which AI model? We compared four well-known backbones and chose MobileNetV3-Large: small, fast, and designed for phones.

We used transfer learning. MobileNetV3 already learned to see shapes and textures from 1.2 million everyday photos. We keep that part frozen - 4.2 million weights unchanged - and train only a small head of 676 thousand weights that maps the image fingerprint to our 39 classes. That is why training took about 25 minutes on a normal laptop CPU.

We also calibrate the confidence, so when the model says 90%, it is right about 90% of the time.

On the right is the real model output for the tomato leaf: its top three guesses with probabilities, which then go to the severity and recommendation engines.`);
}

// ======================================================================== 7 MULTI-CLASS (Himanshu)
{
  const s = contentSlide("LIGHT", "Technical Approach", "06 \u00B7 MULTI-CLASS DIAGNOSIS", "Not every crop problem is a disease", HIMANSHU);
  T(s, "A routing layer sorts every photo into a category, so the advice fits the problem.",
    { x: 0.6, y: 1.82, w: 7.2, h: 0.4, fontSize: 15, color: "3D342B" });
  const rows = [["Category", "What it covers", "Classes"],
    ["Disease", "Blight \u00B7 rust \u00B7 mildew \u00B7 scab \u00B7 leaf spots \u00B7 viruses", String(D.cats.disease)],
    ["Pest", "Spider-mite damage", String(D.cats.pest)],
    ["Nutrient", "Nitrogen \u00B7 potassium \u00B7 iron / magnesium (colour rules)", "3"],
    ["Healthy", "No visible abnormality \u2014 one class per crop", String(D.cats.healthy)],
    ["Not a leaf", "Rejects photos without a crop leaf", String(D.cats.invalid)]];
  const colours = [INK, RED, ORANGE, BLUE, GREEN, H.muted];
  s.addTable(rows.map((r, i) => r.map((c, j) => ({ text: c, options: {
    fontFace: i === 0 ? MONO : (j === 0 ? "Georgia" : "Calibri"), fontSize: i === 0 ? 10.5 : (j === 0 ? 17 : 14),
    bold: i === 0 ? false : j === 0, color: i === 0 ? H.muted : (j === 0 ? colours[i] : INK),
    fill: { color: i === 0 ? H.paper : (i % 2 ? "FFFFFF" : H.paper) }, valign: "middle", align: j === 2 ? "center" : "left",
    border: [{ type: "none" }, { type: "none" }, { pt: i === 0 ? 1 : 0.5, color: i === 0 ? "221C16" : H.line }, { type: "none" }] } }))),
    { x: 0.6, y: 2.35, w: 7.2, colW: [1.55, 4.65, 1.0], rowH: 0.48, objectName: "Category table" });
  kicker(s, "SUPPORTED CROPS", 0.6, 5.42, 4);
  D.crops.forEach((c, i) => {
    const x = 0.6 + (i % 7) * 1.03, y = 5.75 + Math.floor(i / 7) * 0.44;
    chip(s, c.replace(" (Corn)", "").replace("Citrus (Orange)", "Citrus"), x, y, 0.95, H.tintG, GREEN, 11);
  });
  const X = 8.2, W = 4.53;
  box(s, X, 1.82, W, 4.95, "221C16", { name: "Deficiency signatures" });
  kicker(s, "// DEFICIENCY SIGNATURES", X + 0.3, 1.98, W - 0.5, H.mutedDark);
  const sig = [["NITROGEN (N)", "Uniform yellowing over \u2265 25% of the leaf"], ["POTASSIUM (K)", "Yellow / brown scorching at the leaf edge"],
    ["IRON / MAGNESIUM (Fe, Mg)", "Yellow between veins while veins stay green"]];
  sig.forEach((g, i) => {
    const y = 2.4 + i * 0.85;
    T(s, g[0], { x: X + 0.3, y, w: W - 0.5, h: 0.26, fontFace: MONO, fontSize: 11.5, color: "8DBF6A" });
    T(s, g[1], { x: X + 0.3, y: y + 0.28, w: W - 0.5, h: 0.5, fontSize: 13.5, color: H.cream });
  });
  T(s, [{ text: "Important. ", options: { bold: true, color: "E8A57A" } },
        { text: "Colour analysis gives a probable result \u2014 confirm with a soil or tissue test before applying fertiliser.", options: { color: "D8CDBE" } }],
    { x: X + 0.3, y: 5.0, w: W - 0.55, h: 0.75, fontSize: 13 });
  T(s, [{ text: pct(L.category_accuracy), options: { fontFace: "Georgia", fontSize: 22, bold: true, color: "8DBF6A" } },
        { text: "  right category (lab)   ", options: { fontSize: 11.5, color: H.mutedDark } },
        { text: pct(F.category_accuracy), options: { fontFace: "Georgia", fontSize: 22, bold: true, color: "E8A57A" } },
        { text: "  (field)", options: { fontSize: 11.5, color: H.mutedDark } }],
    { x: X + 0.3, y: 6.0, w: W - 0.5, h: 0.5, valign: "middle" });
  s.addNotes(
`Not every crop problem is a disease, so the system first decides the type of problem.

The table shows our categories: 25 disease classes, one pest class (spider mites), three nutrient patterns, 12 healthy classes - one per crop - and a "not a leaf" class that rejects random photos.

Nutrient deficiencies are not in any public photo dataset, so we detect them with rules based on known symptoms, shown on the right: nitrogen - uniform yellowing; potassium - burnt edges; iron or magnesium - yellow between green veins. We always say "probable" and ask for a soil test.

The category is correct ${pct(L.category_accuracy)} of the time on lab photos and ${pct(F.category_accuracy)} on field photos. This matters because the category decides the type of advice.`);
}

// ======================================================================== 8 PEST & SEVERITY (Himanshu)
{
  const s = contentSlide("DARK", "Technical Approach", "07 \u00B7 PEST DETECTION & SEVERITY", "A verdict is useless without a magnitude", HIMANSHU);
  // pest trace
  let X = 0.6, W = 3.9;
  box(s, X, 1.82, W, 4.95, H.card, { line: H.ruleDark, name: "Pest trace" });
  kicker(s, "// PEST DETECTION TRACE", X + 0.25, 1.98, W - 0.4, H.mutedDark);
  img(s, "ex_mite_original_sq.png", X + 0.25, 2.35, 1.3, 1.3, "Spider mite damage leaf");
  T(s, [{ text: "DETECTED\n", options: { fontFace: MONO, fontSize: 10, color: H.mutedDark } },
        { text: `${mite.display_name}\n`, options: { fontSize: 14, bold: true, color: "E8A57A" } },
        { text: `${pct(mite.confidence, 0)} confidence \u00B7 Pest`, options: { fontSize: 12, color: H.cream } }],
    { x: X + 1.7, y: 2.4, w: W - 1.9, h: 1.2 });
  T(s, "RECOMMENDATION", { x: X + 0.25, y: 3.85, w: 3, h: 0.25, fontFace: MONO, fontSize: 10, color: H.mutedDark });
  T(s, mite.rec.actions.slice(0, 3).map((a, i) => ({ text: a, options: { bullet: true, breakLine: i < 2 } })),
    { x: X + 0.3, y: 4.12, w: W - 0.5, h: 1.6, fontSize: 12.5, color: H.cream, paraSpaceAfter: 3 });
  T(s, "Future: an object detector (YOLO) to locate individual insects.", { x: X + 0.25, y: 6.05, w: W - 0.45, h: 0.55,
    fontSize: 11, italic: true, color: H.mutedDark });
  // score bands
  X = 4.75; W = 3.9;
  box(s, X, 1.82, W, 4.95, H.card, { line: H.ruleDark, name: "Health score" });
  kicker(s, "// CROP HEALTH SCORE", X + 0.25, 1.98, W - 0.4, H.mutedDark);
  [["90\u2013100", "HEALTHY", "3A6B35"], ["70\u201389", "MILD", "B8961A"], ["40\u201369", "MODERATE", "D9822B"], ["0\u201339", "SEVERE", "B5452F"]]
    .forEach((b, i) => {
      const y = 2.42 + i * 0.5;
      T(s, b[0], { x: X + 0.3, y, w: 1.1, h: 0.35, fontFace: MONO, fontSize: 15, color: H.cream, align: "right" });
      box(s, X + 1.6, y + 0.08, 0.2, 0.2, b[2], { round: false });
      T(s, b[1], { x: X + 2.0, y, w: 1.7, h: 0.35, fontFace: MONO, fontSize: 15, color: H.cream });
    });
  T(s, "score = 100 \u00D7 (1 \u2212 damaged area)^1.6", { x: X + 0.25, y: 4.6, w: W - 0.4, h: 0.3, fontFace: MONO, fontSize: 12, color: "8DBF6A" });
  T(s, [{ text: "A confirmed disease never scores \u201cHealthy\u201d", options: { bullet: true, breakLine: true } },
        { text: "Late blight and viruses are at least \u201cModerate\u201d", options: { bullet: true, breakLine: true } },
        { text: "Citrus greening is always \u201cSevere\u201d", options: { bullet: true } }],
    { x: X + 0.3, y: 5.05, w: W - 0.5, h: 1.4, fontSize: 12.5, color: H.cream, paraSpaceAfter: 3 });
  // worked example
  X = 8.9; W = 3.83;
  box(s, X, 1.82, W, 4.95, H.card, { line: H.ruleDark, name: "Severity example" });
  kicker(s, "// WORKED EXAMPLE", X + 0.25, 1.98, W - 0.4, H.mutedDark);
  img(s, "ex_potato_overlay_sq.png", X + 0.25, 2.35, 1.55, 1.55, "Potato damage map");
  T(s, [{ text: `${pot.crop} \u2013 ${pot.display_name}\n`, options: { fontSize: 12.5, bold: true, color: H.cream } },
        { text: `${pct(pot.confidence, 0)} confidence`, options: { fontSize: 12, color: H.mutedDark } }],
    { x: X + 1.95, y: 2.4, w: W - 2.1, h: 1.2 });
  T(s, [{ text: String(pot.health_score), options: { fontSize: 58, bold: true, color: "B5452F" } },
        { text: " / 100", options: { fontSize: 24, color: H.mutedDark } }],
    { x: X + 0.25, y: 4.0, w: W - 0.4, h: 1.0, fontFace: "Georgia", valign: "middle" });
  [["Damaged tissue", pct(pot.damage.affected, 0), H.cream], ["Status", pot.severity.toUpperCase(), "E8A57A"], ["Urgency", pot.rec.urgency, "E8A57A"]]
    .forEach((r, i) => {
      T(s, r[0], { x: X + 0.25, y: 5.15 + i * 0.42, w: 1.8, h: 0.32, fontFace: MONO, fontSize: 12, color: H.cream });
      T(s, r[1], { x: X + 2.0, y: 5.15 + i * 0.42, w: W - 2.2, h: 0.32, fontFace: MONO, fontSize: 12, bold: true, color: r[2] });
    });
  s.addNotes(
`A diagnosis alone is not enough - the farmer needs to know how bad it is.

Left: pest detection. This leaf has spider-mite damage; the model labels it as a pest with ${pct(mite.confidence, 0)} confidence and gives pest advice such as inspecting the undersides of leaves.

Middle: the health score. We measure the damaged share of the leaf and convert it with this formula, so the first spots cost few points and heavy damage costs many. Four bands, as planned in the mid-sem. Two safety rules: a confirmed disease is never called healthy, and fast-spreading diseases are at least Moderate.

Right: a real example. This potato leaf has ${pct(pot.damage.affected, 0)} damaged tissue, so its score is ${pot.health_score} - Severe - and the system says "${pot.rec.urgency}".`);
}

// ======================================================================== 9 RECOMMENDATION (Akshata)
pres.addSection({ title: "Engine, Architecture & Interface" });
{
  const s = contentSlide("LIGHT", "Engine, Architecture & Interface", "08 \u00B7 RECOMMENDATION ENGINE", "One label is not a recommendation", AKSHATA);
  kicker(s, "// RESOLUTION CHAIN", 0.6, 1.82, 3.3);
  const chain = [["AI diagnosis", "221C16", H.cream], ["Disease / pest / nutrient", "3A332B", H.cream], ["Knowledge base \u00B7 39 entries", "3A6B35", WHITE],
    ["+ crop \u00B7 severity \u00B7 growth stage\n+ weather \u00B7 soil \u00B7 region \u00B7 history", H.paper, INK], ["Recommendation", "B5452F", WHITE]];
  let y = 2.2;
  chain.forEach((c, i) => {
    const h = i === 3 ? 0.78 : 0.46;
    box(s, 0.6, y, 3.3, h, c[1], { line: i === 3 ? H.line : c[1] });
    T(s, c[0], { x: 0.7, y, w: 3.1, h, align: "center", valign: "middle", fontSize: i === 3 ? 12.5 : 14, bold: i !== 3, color: c[2] });
    y += h;
    if (i < 4) { arrowDown(s, 2.25, y + 0.02, 0.16, H.muted); y += 0.22; }
  });
  T(s, "The model gives a label; the engine turns it into an instruction for this farm, this crop and this week.",
    { x: 0.6, y: 5.95, w: 3.3, h: 0.8, fontSize: 12, italic: true, color: H.muted });
  // two farms
  kicker(s, "SAME DISEASE, TWO FARMS \u2014 REAL ENGINE OUTPUT", 4.2, 1.82, 5.8);
  const short = (a) => a.replace("Remove severely affected leaves", "Remove affected leaves")
    .replace("Avoid prolonged leaf wetness", "Avoid long leaf wetness").replace("Improve plant spacing and airflow", "Improve spacing & airflow")
    .replace("Re-check the plant in 3-4 days and treat if the problem spreads", "Re-check in 3\u20134 days")
    .replace("Apply a locally approved fungicide (e.g. chlorothalonil or mancozeb)", "Apply approved fungicide now");
  const A1 = D.recA.actions.map(short);
  const cards = [
    ["FARM A", "Tomato early blight \u00B7 Mild\nno extra details", A1.map((a) => [a, false])],
    ["FARM B", "+ 27 \u00B0C \u00B7 85% humidity\n+ fruiting \u00B7 seen 2 weeks ago", [
      ...A1.slice(0, 4).map((a) => [a, false]), ["Apply approved fungicide now", true],
      ["Weather favours spread \u2014 act sooner", true], ["Check pre-harvest interval (fruiting)", true],
      ["Recurring outbreak \u2192 consult expert", true], ["Contact KVK / Kisan Call Centre", true]]]];
  cards.forEach((c, i) => {
    const x = 4.2 + i * 2.95, w = 2.8;
    box(s, x, 2.18, w, 4.6, i ? "FFFFFF" : H.paper, { line: i ? "3A6B35" : H.line, lw: i ? 1.25 : 0.75, name: c[0] });
    T(s, c[0], { x: x + 0.2, y: 2.3, w: w - 0.4, h: 0.26, fontFace: MONO, fontSize: 11, bold: true, color: i ? GREEN : H.muted });
    T(s, c[1], { x: x + 0.2, y: 2.58, w: w - 0.35, h: 0.6, fontSize: 11.5, italic: true, color: H.muted });
    T(s, c[2].map(([t, add], k) => ({ text: (add ? "+ " : "") + t, options: { bullet: !add, breakLine: k < c[2].length - 1,
      bold: add, color: add ? GREEN : INK } })), { x: x + 0.2, y: 3.25, w: w - 0.35, h: 3.45, fontSize: 12, paraSpaceAfter: 3 });
  });
  phone(s, "ph_actions.png", 10.4, 1.82, 4.62, "Actions in the app");
  s.addNotes(
`The AI only gives a label, like "Tomato Early Blight". A label is not advice. Our recommendation engine turns it into instructions.

The chain on the left: diagnosis, then the category, then our knowledge base - a notebook with one entry for each of the 39 classes: cause, symptoms, actions, treatment, prevention and the weather the disease likes. Then the engine adjusts the advice using the farm's context.

The two cards are real outputs of our engine for the same disease. Farm A gave no extra details, so it gets basic actions and "re-check in 3 to 4 days". Farm B is warm and humid, the crop is fruiting, and the field had the same disease two weeks ago. Now the engine adds a fungicide because the weather favours spread, warns about the pre-harvest interval, flags a recurring outbreak, and suggests the Krishi Vigyan Kendra.

Same label - different, farm-specific advice.`);
}

// ======================================================================== 10 ARCHITECTURE (Akshata)
{
  const s = contentSlide("DARK", "Engine, Architecture & Interface", "09 \u00B7 ARCHITECTURE & STACK", "Prototype architecture", AKSHATA);
  const rows = [
    [["Web app \u00B7 Streamlit", "3A6B35"], ["Android app \u00B7 Kotlin", "3A6B35"]],
    [["REST API \u00B7 FastAPI   /analyze  /history  /report", "F2EBDD"]],
    [["Vision \u00B7 OpenCV\nvalidate \u00B7 segment \u00B7 damage map", "2B6C9E"], ["AI \u00B7 PyTorch\nMobileNetV3 classifier", "D9822B"]],
    [["Decision \u00B7 abstain \u00B7 route \u00B7 severity \u00B7 nutrients", "6B5B95"]],
    [["Recommendation engine + knowledge base", "7A4F2A"]],
    [["Crop health report \u00B7 screen + PDF", "3A6B35"], ["History \u00B7 SQLite", "3A332B"]],
  ];
  let y = 1.85;
  rows.forEach((r, i) => {
    const h = i === 2 ? 0.68 : 0.52, n = r.length, gap = 0.2, W = 6.0, w = (W - gap * (n - 1)) / n;
    r.forEach((c, j) => {
      const x = 0.6 + j * (w + gap);
      box(s, x, y, w, h, c[1]);
      T(s, c[0], { x, y, w, h, align: "center", valign: "middle", fontSize: 13, bold: true, color: c[1] === "F2EBDD" ? "221C16" : WHITE });
    });
    y += h;
    if (i < rows.length - 1) { arrowDown(s, 3.6, y + 0.02, 0.18, H.mutedDark); y += 0.24; }
  });
  kicker(s, "TECHNOLOGY STACK \u2014 PLANNED AT MID-SEM vs BUILT", 7.05, 1.82, 5.7, H.mutedDark);
  const stack = [["LAYER", "PLANNED", "BUILT"],
    ["Frontend", "React / Streamlit", "Streamlit web app + native Android app"],
    ["Backend", "Python + FastAPI", "FastAPI REST API \u2713"],
    ["Vision", "OpenCV \u00B7 PIL \u00B7 NumPy", "OpenCV \u00B7 Pillow \u00B7 NumPy \u2713"],
    ["ML", "PyTorch \u00B7 EfficientNet / MobileNet \u00B7 YOLO", "PyTorch + MobileNetV3 \u2713 (YOLO: future)"],
    ["Database", "PostgreSQL / MongoDB", "SQLite (as planned for v1) \u2713"],
    ["Deploy", "Docker \u00B7 cloud", "Laptop server + phone hotspot"]];
  s.addTable(stack.map((r, i) => r.map((c, j) => ({ text: c, options: {
    fontFace: (i === 0 || j === 0) ? MONO : "Calibri", fontSize: i === 0 ? 9.5 : (j === 0 ? 10.5 : 12.5),
    color: i === 0 ? H.mutedDark : (j === 0 ? "8DBF6A" : (j === 1 ? H.mutedDark : H.cream)), bold: j === 2 && i > 0,
    valign: "middle", fill: { color: "1E1A15" },
    border: [{ type: "none" }, { type: "none" }, { pt: 0.5, color: H.ruleDark }, { type: "none" }] } }))),
    { x: 7.05, y: 2.15, w: 5.68, colW: [1.05, 2.0, 2.63], rowH: 0.5, objectName: "Stack table" });
  box(s, 7.05, 5.9, 5.68, 0.85, "3A6B35", { name: "First version note" });
  T(s, [{ text: "MID-SEM \u201cRECOMMENDED FIRST VERSION\u201d \u2192 BUILT\n", options: { fontFace: MONO, fontSize: 9.5, color: "D5E6C8" } },
        { text: "Python + Streamlit + OpenCV + PyTorch + SQLite \u2014 plus an Android app on top.", options: { fontSize: 13, bold: true, color: WHITE } }],
    { x: 7.25, y: 5.98, w: 5.3, h: 0.72 });
  s.addNotes(
`This is the architecture we built, layer by layer - like a restaurant.

Customers are the web app and the Android app. The waiter is the REST API built with FastAPI: it receives the photo and returns the answer. The kitchen is OpenCV for image processing and PyTorch for the AI model. Then the decision layer, then the recommendation engine with its knowledge base - the recipe book. Finally the report, and a SQLite database that keeps the history.

Because everything goes through one API, the website and the phone app share the same brain.

The table compares what we planned at mid-sem with what we built. We built exactly the recommended first version - Python, Streamlit, OpenCV, PyTorch and SQLite - and added a native Android app. YOLO for pests and cloud deployment are future work.`);
}

// ======================================================================== 11 UI (Akshata)
{
  const s = contentSlide("LIGHT", "Engine, Architecture & Interface", "10 \u00B7 PROTOTYPE UI", "Two buttons is the whole interface", AKSHATA);
  kicker(s, "DESIGN PRINCIPLES \u2192 HOW WE BUILT THEM", 0.6, 1.82, 5.8);
  const pr = [["One screen, one decision", "Photo \u2192 Analyse crop \u2192 read \u2192 report. Optional field details stay folded away.", "3A6B35", H.tintG],
    ["Confidence is always visible", `Green \u2265 85%, amber, red. Below 60% (${Math.round(D.field_threshold * 100)}% for field photos) the app asks for a re-capture.`, "D9822B", H.tintO],
    ["Severity before advice", "Health score and risk appear first, so mild cases don\u2019t trigger heavy spraying.", "B5452F", H.tintR],
    ["Same brain, any screen", "Web app and Android app call one API \u2014 the model never changes.", "2B6C9E", H.tintB]];
  pr.forEach((p, i) => {
    const y = 2.18 + i * 1.15;
    box(s, 0.6, y, 5.75, 1.02, p[3], { name: `Principle ${i + 1}` });
    s.addShape(pres.shapes.OVAL, { x: 0.8, y: y + 0.27, w: 0.46, h: 0.46, fill: { color: p[2] }, line: { color: p[2] } });
    T(s, String(i + 1), { x: 0.8, y: y + 0.27, w: 0.46, h: 0.46, align: "center", valign: "middle", fontFace: MONO, fontSize: 13, bold: true, color: WHITE });
    T(s, p[0], { x: 1.45, y: y + 0.1, w: 4.75, h: 0.32, fontFace: "Georgia", fontSize: 16, bold: true, color: INK });
    T(s, p[1], { x: 1.45, y: y + 0.44, w: 4.75, h: 0.55, fontSize: 12.5, color: "3D342B" });
  });
  const h = 4.3, w = h * 0.45;
  [["ph_diagnose.png", "1 \u00B7 Diagnose"], ["ph_result.png", "2 \u00B7 Result"], ["ph_history.png", "3 \u00B7 History"]].forEach((p, i) => {
    phone(s, p[0], 6.75 + i * (w + 0.18), 1.95, h, p[1]);
  });
  s.addNotes(
`Our mid-sem said "two buttons is the whole interface", and that is what we built.

Four design principles. One: one screen, one decision - pick a photo, tap Analyse, read the result, tap Report; extra details like weather are hidden unless you need them. Two: confidence is always visible and colour-coded; if the AI is not sure enough, the app asks for a new photo instead of recommending a treatment. Three: severity comes before advice, so a mild case does not cause panic spraying. Four: the website and the Android app use the same API, so the model is the same everywhere.

On the right are screenshots of our Android app: the Diagnose screen, the Result screen and the History screen.`);
}

// ======================================================================== 12 REPORT (Akshata)
{
  const s = contentSlide("LIGHT", "Engine, Architecture & Interface", "11 \u00B7 SAMPLE AI REPORT", "Crop health report", AKSHATA);
  const ph = 4.95, pw = ph * 0.7071;
  box(s, 0.6, 1.82, pw, ph, "FFFFFF", { round: false, line: H.line });
  img(s, "pdf_report_page.png", 0.6, 1.82, pw, ph, "Generated PDF crop health report");
  kicker(s, "WHAT EVERY REPORT CONTAINS", 4.55, 1.82, 5);
  const items = [["Diagnosis", "condition and probable cause"], ["Confidence", "how sure the model is"],
    ["Severity", "band plus health-score bar (0\u2013100 scale)"], ["Images", "leaf photo next to its damage map"],
    ["Symptoms", "what this condition typically looks like"], ["Actions", "numbered, with an urgency level"],
    ["Context notes", "weather risk, growth stage, recurrence"], ["Prevention", "how to avoid it next season"],
    ["Disclaimer", "screening aid, not a final verdict"]];
  items.forEach((it, i) => {
    const y = 2.16 + i * 0.46;
    T(s, it[0], { x: 4.55, y, w: 1.55, h: 0.3, fontSize: 14, bold: true, color: GREEN });
    T(s, it[1], { x: 6.1, y, w: 3.8, h: 0.3, fontSize: 14, color: INK });
  });
  T(s, "Downloadable from the web app, and opened or shared (e.g. on WhatsApp) from the Android app.",
    { x: 4.55, y: 6.38, w: 5.5, h: 0.4, fontSize: 12, italic: true, color: H.muted });
  phone(s, "ph_report.png", 10.35, 1.82, 4.62, "Report on the phone");
  s.addNotes(
`Every diagnosis can become a crop health report - this is a real PDF generated by our system, on the left.

It contains everything from our mid-sem report design: the diagnosis and probable cause, confidence, severity with a health-score bar, the leaf photo next to its damage map, symptoms, numbered actions with an urgency level, context notes like weather risk, prevention tips, and a disclaimer that this is a screening aid.

The report can be downloaded from the website, or opened and shared from the phone app - for example sent on WhatsApp to an expert. The phone screenshot on the right shows it in the app.`);
}

// ======================================================================== 13 DATASET & EVALUATION (Himanshu)
pres.addSection({ title: "Evaluation & Outlook" });
{
  const s = contentSlide("DARK", "Evaluation & Outlook", "12 \u00B7 DATASET & EVALUATION", "Lab images are not field images", HIMANSHU);
  kicker(s, "TRAINING DATA", 0.6, 1.82, 3.5, H.mutedDark);
  const ds = [["PlantVillage", "41,141 lab photos \u00B7 plain background \u00B7 39 classes"], ["PlantDoc", "2,578 field photos \u00B7 real backgrounds \u00B7 28 classes"]];
  ds.forEach((d, i) => {
    T(s, d[0], { x: 0.6, y: 2.15 + i * 1.0, w: 3.6, h: 0.42, fontFace: "Georgia", fontSize: 22, color: H.cream });
    T(s, d[1], { x: 0.6, y: 2.57 + i * 1.0, w: 3.6, h: 0.5, fontSize: 12.5, color: H.mutedDark });
  });
  box(s, 0.6, 4.3, 3.6, 2.45, H.card, { line: H.ruleDark });
  kicker(s, "// DATASET PIPELINE", 0.8, 4.42, 3.2, H.mutedDark);
  T(s, "Raw images \u2192 cleaning \u2192 label mapping\n\u2192 split 70 / 15 / 15 \u2192 training\n\u2192 evaluation on unseen photos",
    { x: 0.8, y: 4.75, w: 3.3, h: 1.1, fontFace: MONO, fontSize: 11.5, color: H.cream, paraSpaceAfter: 2 });
  T(s, "PlantDoc\u2019s own test set (236 photos) is kept aside to measure real-world performance.",
    { x: 0.8, y: 5.9, w: 3.25, h: 0.75, fontSize: 12, color: "8DBF6A" });
  const stats = [[pct(L.accuracy), "lab accuracy", `${L.test_images.toLocaleString("en-US")} unseen lab photos`, "8DBF6A"],
    [pct(F.accuracy), "field accuracy", `${F.test_images} unseen field photos`, "E8A57A"],
    [pct(L.category_accuracy), "right category", "disease / pest / healthy (lab)", "8DBF6A"],
    [pct(F.top3_accuracy), "field top-3", "correct answer in top 3", "E8A57A"]];
  stats.forEach((st, i) => {
    const x = 4.55 + (i % 2) * 2.08, y = 1.85 + Math.floor(i / 2) * 2.0;
    box(s, x, y, 1.93, 1.82, H.card, { line: H.ruleDark, name: `Stat ${st[1]}` });
    T(s, st[0], { x: x + 0.15, y: y + 0.18, w: 1.7, h: 0.6, fontFace: "Georgia", fontSize: 30, bold: true, color: st[3] });
    T(s, st[1], { x: x + 0.15, y: y + 0.85, w: 1.7, h: 0.3, fontSize: 13.5, bold: true, color: H.cream });
    T(s, st[2], { x: x + 0.15, y: y + 1.16, w: 1.7, h: 0.55, fontSize: 11, color: H.mutedDark });
  });
  T(s, `Abstention cuts lab misdiagnoses from ${pct(L.false_diagnosis_rate_no_abstention)} to ${pct(L.false_diagnosis_rate_at_threshold)}.`,
    { x: 4.55, y: 5.95, w: 4.0, h: 0.75, fontSize: 13, color: H.cream });
  s.addChart(pres.charts.BAR, [{ name: "Field accuracy", labels: ["Lab photos only", "+ field photos", "+ 2.7\u00D7 more data"],
    values: [D.field_baseline * 100, D.field_400 * 100, F.accuracy * 100] }], {
    x: 8.95, y: 1.82, w: 3.78, h: 4.95, barDir: "col", chartColors: ["D9822B"], showValue: true,
    dataLabelFormatCode: '0.0"%"', dataLabelColor: "F2EBDD", dataLabelFontSize: 12, dataLabelFontFace: "+mn-lt", dataLabelPosition: "outEnd",
    catAxisLabelColor: "C9BDAC", catAxisLabelFontSize: 11, catAxisLabelFontFace: "+mn-lt", valAxisHidden: true, valAxisMaxVal: 70,
    valGridLine: { style: "none" }, catGridLine: { style: "none" }, showLegend: false, showTitle: true,
    title: "Field accuracy as the data improved", titleColor: "F2EBDD", titleFontSize: 13, titleFontFace: "+mn-lt",
    barGapWidthPct: 55, objectName: "Field accuracy chart",
  });
  s.addNotes(
`How well does it work? We trained on two datasets: PlantVillage, 41 thousand clean lab photos, and PlantDoc, 2,578 real field photos with messy backgrounds. Every result here is measured on photos the model never saw during training.

On lab photos the model is ${pct(L.accuracy)} accurate, and it gets the problem category right ${pct(L.category_accuracy)} of the time. On real field photos it is ${pct(F.accuracy)} accurate, and the right answer is in its top three ${pct(F.top3_accuracy)} of the time.

The chart is our most important finding - the mid-sem title "lab images are not field images". A model trained only on lab photos got just ${pct(D.field_baseline)} on field photos. Adding field photos raised it to ${pct(D.field_400)}, and 2.7 times more training data to ${pct(F.accuracy)}.

Because field photos are hard, the system abstains when unsure; on lab photos this cuts misdiagnoses to ${pct(L.false_diagnosis_rate_at_threshold)}.`);
}

// ======================================================================== 14 IOT & ROADMAP (Himanshu)
{
  const s = contentSlide("LIGHT", "Evaluation & Outlook", "13 \u00B7 IOT INTEGRATION & ROADMAP", "Vision plus context", HIMANSHU);
  box(s, 0.6, 1.82, 4.55, 4.95, "221C16", { name: "Sensor fusion" });
  kicker(s, "// SENSOR INPUTS \u2014 BUILT INTO THE APP", 0.85, 1.98, 4.2, H.mutedDark);
  const si = [["Temperature & humidity", "warns when weather favours the disease"], ["Soil moisture", "flags water stress behind mite attacks"],
    ["Soil pH", "points to iron vs magnesium deficiency"], ["Growth stage", "seedling, flowering and harvest precautions"]];
  si.forEach((r, i) => {
    const y = 2.4 + i * 0.78;
    T(s, r[0], { x: 0.85, y, w: 4.1, h: 0.3, fontSize: 14.5, bold: true, color: H.cream });
    T(s, r[1], { x: 0.85, y: y + 0.3, w: 4.1, h: 0.3, fontSize: 12.5, color: H.mutedDark });
  });
  T(s, "Entered in the app today \u2014 an IoT sensor can fill the same fields automatically.",
    { x: 0.85, y: 5.65, w: 4.1, h: 0.8, fontSize: 12.5, italic: true, color: "8DBF6A" });
  kicker(s, "SCALABILITY ROADMAP", 5.5, 1.82, 4);
  const ph = [["PHASE 1 \u00B7 PROTOTYPE", "Upload \u00B7 classification \u00B7 disease detection \u00B7 advice \u00B7 report", "DONE", "3A6B35", H.tintG, false],
    ["PHASE 2 \u00B7 INTELLIGENT DIAGNOSIS", "Pest \u00B7 nutrients \u00B7 severity \u00B7 14 crops \u00B7 history \u00B7 Android app", "DONE", "3A6B35", H.tintG, false],
    ["PHASE 3 \u00B7 IoT", "Sensor inputs ready \u00B7 live sensors and alerts next", "PARTIAL", "B8961A", H.tintY, false],
    ["PHASE 4 \u00B7 LARGE-SCALE PLATFORM", "Disease maps \u00B7 yield prediction \u00B7 voice \u00B7 drones", "FUTURE", "7D7063", "221C16", true]];
  ph.forEach((p, i) => {
    const y = 2.18 + i * 1.15, x = 5.5, w = 4.75;
    box(s, x, y, w, 1.02, p[5] ? "221C16" : "FFFFFF", { line: p[5] ? "221C16" : H.line, name: p[0] });
    T(s, p[0], { x: x + 0.2, y: y + 0.12, w: 3.4, h: 0.26, fontFace: MONO, fontSize: 10.5, color: p[5] ? "E8A57A" : p[3] });
    T(s, p[1], { x: x + 0.2, y: y + 0.42, w: w - 0.35, h: 0.55, fontSize: 12.5, color: p[5] ? H.cream : INK });
    chip(s, p[2], x + w - 1.15, y + 0.1, 0.98, p[4] === "221C16" ? "3A332B" : p[4], p[5] ? H.cream : p[3], 10.5);
  });
  phone(s, "ph_context.png", 10.6, 1.82, 4.62, "Field context in app");
  s.addNotes(
`Vision plus context. A photo alone cannot tell everything, so the app also accepts sensor-style inputs: temperature, humidity, soil moisture, soil pH and growth stage. Today the farmer types them in; an IoT sensor can fill the very same fields later. They change the advice - for example, warm humid weather triggers a "disease will spread faster" warning.

The roadmap from our mid-sem: Phase 1, the prototype, is done. Phase 2, intelligent diagnosis - pests, nutrients, severity, history and the Android app - is done. Phase 3, IoT, is partial: the inputs are ready, live sensors are next. Phase 4 is the future platform.

The screenshot shows the field-context screen of our app.`);
}

// ======================================================================== 15 IMPACT & LIMITATIONS (Himanshu)
{
  const s = contentSlide("LIGHT", "Evaluation & Outlook", "14 \u00B7 IMPACT & LIMITATIONS", "Who benefits \u2014 and what it can\u2019t do", HIMANSHU);
  kicker(s, "IMPACT", 0.6, 1.82, 3);
  const imp = [["For farmers", "A diagnosis in seconds, before the damage spreads"], ["For agricultural experts", "Faster triage and a digital history of every field"],
    ["For organisations", "Aggregated diagnoses for regional disease surveillance"]];
  imp.forEach((m, i) => {
    const y = 2.2 + i * 1.5;
    s.addShape(pres.shapes.LINE, { x: 0.6, y, w: 3.7, h: 0, line: { color: ["3A6B35", "D9822B", "2B6C9E"][i], width: 1.5 } });
    T(s, m[0], { x: 0.6, y: y + 0.12, w: 3.7, h: 0.42, fontFace: "Georgia", fontSize: 19, color: INK });
    T(s, m[1], { x: 0.6, y: y + 0.55, w: 3.7, h: 0.6, fontSize: 13.5, color: "3D342B" });
  });
  box(s, 4.65, 1.82, 3.7, 4.95, "221C16", { name: "Business model" });
  kicker(s, "// BUSINESS MODEL", 4.9, 1.98, 3.3, H.mutedDark);
  T(s, "Freemium + B2B", { x: 4.9, y: 2.3, w: 3.3, h: 0.45, fontFace: "Georgia", fontSize: 21, bold: true, color: H.cream });
  [["FREE", "Limited photo diagnoses", "8DBF6A"], ["PREMIUM", "Unlimited \u00B7 history \u00B7 PDF reports", "E8C66A"], ["ENTERPRISE", "IoT \u00B7 farm analytics \u00B7 dashboards", "E8A57A"]]
    .forEach((b, i) => {
      const y = 3.0 + i * 0.95;
      T(s, b[0], { x: 4.9, y, w: 3.3, h: 0.28, fontFace: MONO, fontSize: 11.5, color: b[2] });
      T(s, b[1], { x: 4.9, y: y + 0.3, w: 3.3, h: 0.3, fontSize: 13, color: H.cream });
    });
  T(s, "Free diagnoses drive adoption; institutions pay for analytics.", { x: 4.9, y: 5.95, w: 3.25, h: 0.65, fontSize: 11.5, italic: true, color: H.mutedDark });
  kicker(s, "CURRENT LIMITATIONS", 8.7, 1.82, 4, RED);
  const lim = [`Field photos: ${pct(F.accuracy, 0)} accuracy \u2014 the app abstains when unsure`, "Only one pest class (spider mites) in public data",
    "Nutrient results need soil-test confirmation", "Dark lesions at the leaf edge can be undercounted", "One leaf per photo; the phone needs the laptop server"];
  T(s, lim.map((l, i) => ({ text: l, options: { bullet: true, breakLine: i < lim.length - 1 } })),
    { x: 8.7, y: 2.15, w: 4.03, h: 2.9, fontSize: 13.5, color: INK, paraSpaceAfter: 5 });
  box(s, 8.7, 5.25, 4.03, 1.5, "3A6B35", { name: "Positioning" });
  T(s, [{ text: "POSITIONING\n", options: { fontFace: MONO, fontSize: 10, color: "D5E6C8" } },
        { text: "Decision support and early screening \u2014 with an expert or soil test for every high-impact decision.", options: { fontSize: 13.5, bold: true, color: WHITE } }],
    { x: 8.9, y: 5.38, w: 3.7, h: 1.3 });
  s.addNotes(
`Who benefits? Farmers get a diagnosis in seconds, before damage spreads. Experts get faster triage and a digital history of each field. Organisations could combine many diagnoses to watch disease spread across a region.

The business model stays as planned: free basic diagnoses to drive adoption, premium for history and reports, and enterprise for IoT and analytics.

We are also honest about limitations. On real field photos accuracy is ${pct(F.accuracy, 0)}, so the app refuses to answer when unsure. Only spider mites are covered as a pest. Nutrient results need a soil test. Dark lesions at the leaf edge can be under-counted. And today the phone needs the laptop server nearby.

So we position AgriVision as decision support and early screening, not a replacement for an expert.`);
}

// ======================================================================== 16 CONCLUSION (Himanshu)
{
  const s = pres.addSlide({ masterName: "COVER", sectionTitle: "Evaluation & Outlook" });
  box(s, 0, 0, 0.14, 7.5, "D9822B", { round: false, name: "Brand edge" });
  T(s, "FROM DETECTION TO PREVENTION", { x: 0.75, y: 0.62, w: 6, h: 0.3, fontFace: MONO, fontSize: 11, charSpacing: 2, color: "E8A57A" });
  T(s, "\u201CWhat is happening, why, how severe is it, what should I do \u2014 and how do I prevent it happening again?\u201D",
    { x: 0.75, y: 1.05, w: 7.2, h: 1.9, fontFace: "Georgia", fontSize: 26, italic: true, color: H.cream });
  T(s, "AgriVision AI", { x: 0.75, y: 3.15, w: 6, h: 0.8, fontFace: "Georgia", fontSize: 40, bold: true, color: H.cream });
  T(s, "SEE \u2192 DIAGNOSE \u2192 RECOMMEND \u2192 MONITOR \u2192 PREVENT", { x: 0.75, y: 3.95, w: 7.3, h: 0.35, fontFace: MONO, fontSize: 14, color: "8DBF6A" });
  const res = [["39", "classes \u00B7 14 crops"], [pct(L.accuracy), "lab accuracy"], [pct(F.accuracy), "field accuracy"], ["< 2 s", "per diagnosis"]];
  res.forEach((r, i) => {
    const x = 0.75 + i * 1.82;
    T(s, r[0], { x, y: 4.6, w: 1.75, h: 0.55, fontFace: "Georgia", fontSize: 26, bold: true, color: i === 2 ? "E8A57A" : H.cream });
    T(s, r[1], { x, y: 5.15, w: 1.75, h: 0.3, fontSize: 12, color: H.mutedDark });
  });
  T(s, "Thank you \u2014 questions?", { x: 0.75, y: 5.75, w: 6, h: 0.5, fontFace: "Georgia", fontSize: 22, color: H.cream });
  T(s, "AKSHATA BAKRE \u00B7 HIMANSHU KASHYAP  \u2014  GUIDED BY DR. SANJAY KUMAR", { x: 0.75, y: 6.45, w: 7.5, h: 0.3, fontFace: MONO,
    fontSize: 10.5, charSpacing: 1, color: H.mutedDark });
  const X = 8.7, W = 4.03;
  box(s, X, 0.85, W, 5.9, H.deep, { line: H.ruleDark, name: "Future scope" });
  kicker(s, "// FUTURE SCOPE", X + 0.3, 1.05, W - 0.5, H.mutedDark);
  const fut = [["DATA", "More field photos from local farms"], ["AI", "Fine-tune the full model on a GPU"], ["PESTS", "YOLO to locate individual insects"],
    ["OFFLINE", "Run the model on the phone itself"], ["IoT", "Live sensors and automatic alerts"], ["SCALE", "Regional disease maps and forecasting"],
    ["VOICE", "Multilingual voice for farmers"]];
  fut.forEach((f, i) => {
    const y = 1.45 + i * 0.73;
    T(s, f[0], { x: X + 0.3, y, w: W - 0.5, h: 0.24, fontFace: MONO, fontSize: 10, color: "8DBF6A" });
    T(s, f[1], { x: X + 0.3, y: y + 0.25, w: W - 0.5, h: 0.3, fontSize: 13.5, color: H.cream });
    if (i < fut.length - 1) s.addShape(pres.shapes.LINE, { x: X + 0.3, y: y + 0.64, w: W - 0.6, h: 0, line: { color: H.ruleDark, width: 0.5 } });
  });
  s.addNotes(
`To conclude: our goal was never just "what is wrong with my crop", but what is happening, why, how severe, what to do, and how to prevent it.

What we delivered: a working system covering 39 classes across 14 crops, ${pct(L.accuracy)} accurate on lab photos, ${pct(F.accuracy)} on real field photos - nearly three times better than a lab-only model - with a full diagnosis in under two seconds, available on the web, through an API, and on an Android phone.

Future scope on the right: more local field photos, fine-tuning on a GPU, YOLO for pests, running the model offline on the phone, live IoT sensors, regional disease maps, and a multilingual voice interface.

Thank you. We are happy to take questions, and we can show a live demo on the phone.`);
}

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("Wrote", OUT);
})();
