"""AgriVision AI - Streamlit demo UI (Phase 1 prototype).

    streamlit run app.py
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from agrivision import config, database, report
from agrivision.pipeline import AgriVision, images_for

st.set_page_config(page_title="AgriVision AI", page_icon="🌿", layout="wide")

SEV_COLOURS = {"Healthy": "#2e7d32", "Mild": "#b8961a", "Moderate": "#d9822b",
               "Severe": "#c0392b", "Unknown": "#7a6f64"}
RISK_TEXT = {"Healthy": "Low Risk", "Mild": "Low-Moderate Risk", "Moderate": "Moderate Risk",
             "Severe": "High Risk", "Unknown": "Re-capture"}
SAMPLES_DIR = config.ROOT / "samples"

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,700&family=IBM+Plex+Mono:wght@400;600&display=swap');
h1, h2, h3, .serif { font-family: 'Fraunces', Georgia, serif !important; letter-spacing: -0.01em; }
.mono, .kicker { font-family: 'IBM Plex Mono', Consolas, monospace; }
.kicker { font-size: 0.72rem; letter-spacing: 0.14em; text-transform: uppercase; color: #8a7d6e; }
.brand { font-family: 'Fraunces', Georgia, serif; font-size: 2.6rem; font-weight: 700; line-height: 1.05; margin: 0; }
.tagline { color: #6b5f52; margin-top: 4px; }
.card { background: #faf5ec; border: 1px solid #e3d8c6; border-radius: 6px; padding: 1.2rem 1.4rem; height: 100%; }
.card-dark { background: #1f1a15; color: #efe6d8; border-radius: 6px; padding: 1.2rem 1.4rem; height: 100%; }
.card-dark .kicker { color: #a39482; }
.verdict { font-family: 'Fraunces', Georgia, serif; font-size: 2.3rem; font-weight: 700; line-height: 1.1; margin: 0.2rem 0 0.5rem; }
.big { font-family: 'Fraunces', Georgia, serif; font-size: 2.1rem; font-weight: 600; line-height: 1.1; }
.chip { display: inline-block; font-family: 'IBM Plex Mono', monospace; font-size: 0.72rem; padding: 2px 9px;
        border-radius: 99px; border: 1px solid currentColor; letter-spacing: 0.06em; text-transform: uppercase; }
.bar { background: #3a322a; border-radius: 3px; height: 14px; width: 100%; overflow: hidden; margin: 6px 0 4px; }
.bar > div { height: 100%; border-radius: 3px; }
.scale { font-family: 'IBM Plex Mono', monospace; font-size: 0.68rem; color: #a39482; display: flex; justify-content: space-between; }
.step { font-family: 'IBM Plex Mono', monospace; color: #3a6b35; margin-right: 0.6rem; }
.item { padding: 0.32rem 0; border-bottom: 1px solid #ebe1d1; }
.note { background: #fff7e6; border-left: 3px solid #d9822b; padding: 0.55rem 0.8rem; margin: 0.35rem 0; border-radius: 3px; }
.disclaimer { font-size: 0.8rem; color: #a39482; margin-top: 0.8rem; }
</style>
""", unsafe_allow_html=True)


@st.cache_resource(show_spinner="Loading AI model ...")
def get_engine() -> AgriVision:
    return AgriVision()


def html(s: str):
    st.markdown(s, unsafe_allow_html=True)


def health_bar(score: int | None, colour: str) -> str:
    width = score or 0
    return (f'<div class="bar"><div style="width:{width}%;background:{colour}"></div></div>'
            '<div class="scale"><span>0 SEVERE</span><span>40 MOD.</span><span>70 MILD</span>'
            '<span>90 HEALTHY 100</span></div>')


# ---------------------------------------------------------------- header
html('<div class="kicker">Crop health intelligence</div>'
     '<div class="brand">AgriVision AI</div>'
     '<div class="tagline">Detect crop diseases, pest damage and nutrient deficiencies from a single photograph.</div>')

if not config.MODEL_PATH.exists():
    st.error("No trained model found. Run `python scripts/prepare_data.py` and `python scripts/train.py` first.")
    st.stop()

engine = get_engine()
tab_diag, tab_hist, tab_model, tab_about = st.tabs(["Diagnose", "Field history", "Model performance", "About"])

# ---------------------------------------------------------------- diagnose
with tab_diag:
    left, right = st.columns([1.15, 1], gap="large")
    with left:
        html('<div class="kicker">01 &middot; Capture or upload a crop image</div>')
        source = st.radio("Image source", ["Upload photo", "Use camera", "Try a sample"],
                          horizontal=True, label_visibility="collapsed")
        image_bytes, image_name = None, None
        if source == "Upload photo":
            up = st.file_uploader("Leaf photo", type=["jpg", "jpeg", "png", "webp", "bmp"],
                                  label_visibility="collapsed")
            if up:
                image_bytes, image_name = up.getvalue(), up.name
        elif source == "Use camera":
            cam = st.camera_input("Photograph a single leaf", label_visibility="collapsed")
            if cam:
                image_bytes, image_name = cam.getvalue(), "camera.jpg"
        else:
            samples = sorted(SAMPLES_DIR.glob("*.jpg")) if SAMPLES_DIR.exists() else []
            if samples:
                pick = st.selectbox("Sample image", samples, format_func=lambda p: p.stem.replace("_", " "))
                image_bytes, image_name = pick.read_bytes(), pick.name
            else:
                st.info("No sample images found in the samples/ folder.")

        crop = st.selectbox("Crop", ["Auto-detect"] + engine.crops,
                            help="Telling the model the crop removes confusion with other crops.")
        with st.expander("Field context (optional - makes recommendations specific to your farm)"):
            c1, c2 = st.columns(2)
            field_id = c1.text_input("Field / plot name", placeholder="e.g. North plot",
                                     help="Used to track history and detect recurring outbreaks.")
            region = c2.text_input("Region / state", placeholder="e.g. Maharashtra")
            stage = c1.selectbox("Growth stage", ["Not specified", "Seedling", "Vegetative", "Flowering", "Fruiting"])
            use_sensors = c2.checkbox("Add weather / IoT sensor readings")
            sensors = {}
            if use_sensors:
                s1, s2 = st.columns(2)
                sensors["temperature"] = s1.number_input("Temperature (C)", -5.0, 50.0, 26.0, 0.5)
                sensors["humidity"] = s2.number_input("Relative humidity (%)", 0.0, 100.0, 75.0, 1.0)
                sensors["soil_moisture"] = s1.number_input("Soil moisture (%)", 0.0, 100.0, 40.0, 1.0)
                sensors["soil_ph"] = s2.number_input("Soil pH", 3.0, 10.0, 6.8, 0.1)

        analyse = st.button("Analyse crop", type="primary", disabled=image_bytes is None,
                            width="stretch")

    with right:
        if image_bytes:
            st.image(image_bytes, caption=image_name, width="stretch")
        else:
            html('<div class="card" style="text-align:center;padding:5rem 1rem;color:#8a7d6e">'
                 '<div class="kicker">No image yet</div>'
                 '<p>Photograph one leaf in daylight, filling most of the frame.</p></div>')

    if analyse and image_bytes:
        ctx = {"crop": None if crop == "Auto-detect" else crop, "field_id": field_id.strip(),
               "region": region.strip(), "growth_stage": stage, **sensors}
        with st.spinner("Analysing image ..."):
            try:
                result, images = engine.analyze(image_bytes, ctx, save=True, filename=image_name)
                st.session_state["last"] = (result, images)
            except Exception as e:  # unreadable upload etc.
                st.session_state.pop("last", None)
                st.error(f"Could not analyse this image: {e}")

    if "last" in st.session_state:
        result, images = st.session_state["last"]
        sev = result["severity"]
        colour = SEV_COLOURS[sev]
        conf = result["confidence"]
        conf_colour = "#2e7d32" if conf >= 0.85 else "#b8961a" if conf >= config.CONFIDENCE_THRESHOLD else "#c0392b"
        st.divider()
        html('<div class="kicker">02 &middot; Diagnosis</div>')

        if result["status"] != "ok":
            st.warning("**" + result["messages"][0] + "**")
            for m in result["messages"][1:]:
                st.caption("- " + m)

        a, b = st.columns([1.7, 1], gap="medium")
        with a:
            verdict_colour = colour if result["status"] == "ok" else "#7a6f64"
            html(f'''<div class="card">
              <span class="chip" style="color:{verdict_colour}">{result["category_label"]}</span>
              &nbsp;<span class="kicker">Crop: {result["crop"]}</span>
              <div class="verdict" style="color:{verdict_colour}">{result["display_name"]}</div>
              <div>{"Probable cause: " if result["status"] == "ok" else ""}{result["cause"]}</div>
              <div style="display:flex;gap:3rem;margin-top:1rem">
                <div><div class="kicker">Confidence</div><div class="big" style="color:{conf_colour}">{conf:.0%}</div></div>
                <div><div class="kicker">Severity</div><div class="big" style="color:{colour}">{sev}</div></div>
              </div></div>''')
        with b:
            score = result["health_score"]
            score_txt = f"{score} / 100" if score is not None else "-- / 100"
            html(f'''<div class="card-dark">
              <div class="kicker">Crop status</div>
              <div class="verdict" style="color:{colour}">{RISK_TEXT[sev]}</div>
              <div class="mono">HEALTH SCORE &nbsp;<b style="color:{colour}">{score_txt}</b></div>
              {health_bar(score, colour)}
              <div class="disclaimer">An AI diagnosis is an initial screening tool, not a definitive agricultural verdict.</div>
            </div>''')

        if result["status"] == "ok":
            rec = result["recommendation"]
            s_col, a_col = st.columns([1, 1.4], gap="large")
            with s_col:
                html('<div class="kicker" style="margin-top:1rem">Observed symptoms</div>')
                if result["symptoms"]:
                    html("".join(f'<div class="item">&middot; {s}</div>' for s in result["symptoms"]))
                else:
                    html('<div class="item">No visible abnormality</div>')
                if rec.get("prevention"):
                    html('<div class="kicker" style="margin-top:1rem">Prevent it happening again</div>')
                    html("".join(f'<div class="item">&middot; {s}</div>' for s in rec["prevention"]))
            with a_col:
                html(f'<div class="kicker" style="margin-top:1rem">Recommended actions &middot; '
                     f'<span style="color:{colour}">{rec["urgency"]}</span></div>')
                html("".join(f'<div class="item"><span class="step">{i:02d}</span>{t}</div>'
                             for i, t in enumerate(rec["actions"], 1)))
                for n in rec.get("notes", []):
                    html(f'<div class="note">{n}</div>')

        with st.expander("How the AI reached this result", expanded=result["status"] != "ok"):
            i1, i2, i3 = st.columns(3)
            i1.image(images["original"], caption="1. Input (validated, resized)", width="stretch")
            i2.image(images["leaf"], caption="2. Leaf region detected", width="stretch")
            i3.image(images["overlay"], caption="3. Abnormal tissue: red necrotic, yellow chlorotic, blue powdery",
                     width="stretch")
            m1, m2 = st.columns(2)
            with m1:
                st.markdown("**Category probabilities**")
                st.bar_chart(pd.Series(result["category_probs"]) * 100, horizontal=True, height=210,
                             color="#3a6b35")
                st.markdown("**Top predictions**")
                st.dataframe(pd.DataFrame([{"Crop": t["crop"], "Condition": t["name"],
                                            "Probability": f"{t['probability']:.1%}"} for t in result["top_k"]]),
                             hide_index=True, width="stretch")
            with m2:
                d, q, n = result["damage"], result["quality"], result["nutrient"]
                st.markdown("**Leaf tissue analysis (OpenCV)**")
                st.dataframe(pd.DataFrame({
                    "Measure": ["Healthy green", "Chlorotic (yellow)", "Necrotic (brown/dark)",
                                "Powdery (white)", "Total affected"],
                    "Share of leaf": [f"{d[k]:.1%}" for k in ("green", "yellow", "brown", "white", "affected")]}),
                    hide_index=True, width="stretch")
                st.markdown("**Nutrient screening**")
                st.write(f"Pattern: **{n['pattern'] or 'none detected'}** - stress index {n['index']:.2f}")
                for e in n["evidence"]:
                    st.caption(e)
                if n["pattern"] and result["category"] in ("disease", "pest"):
                    st.caption("The discolouration is better explained by the detected "
                               f"{result['category']}, so no fertiliser advice is given.")
                st.markdown("**Image quality checks**")
                st.caption(f"{q['width']}x{q['height']} px - sharpness {q['blur_score']:.0f} - "
                           f"brightness {q['brightness']:.0f} - leaf covers {q['leaf_fraction']:.0%} of frame"
                           + (" - auto-enhanced (CLAHE)" if q["enhanced"] else ""))

        pdf = report.build_pdf(result, images)
        st.download_button("Generate report (PDF)", pdf, file_name=f"agrivision_report_{result.get('id', 'x')}.pdf",
                           mime="application/pdf", type="primary")

# ---------------------------------------------------------------- history
with tab_hist:
    html('<div class="kicker">Monitor &rarr; prevent</div>')
    st.subheader("Diagnosis history")
    fields = database.fields()
    sel = st.selectbox("Field", ["All fields"] + fields)
    rows = database.history(None if sel == "All fields" else sel)
    if not rows:
        st.info("No diagnoses yet. Analyse an image on the Diagnose tab - add a field name to track it over time.")
    else:
        df = pd.DataFrame(rows)
        df["created_at"] = pd.to_datetime(df["created_at"])
        df["confidence"] = (df["confidence"] * 100).round(1)
        if sel != "All fields":
            trend = df[df["status"] == "ok"].sort_values("created_at").set_index("created_at")["health_score"]
            if len(trend) > 1:
                st.markdown("**Health score over time**")
                st.line_chart(trend, height=220, color="#d9822b")
        c1, c2, c3 = st.columns(3)
        c1.metric("Diagnoses", len(df))
        ok = df[df["status"] == "ok"]
        c2.metric("Problems found", int((ok["category"] != "healthy").sum()))
        c3.metric("Average health score", f"{ok['health_score'].mean():.0f}" if len(ok) else "-")
        st.dataframe(df[["id", "created_at", "field_id", "crop", "display_name", "category", "confidence",
                         "severity", "health_score", "status"]].rename(columns={
                             "created_at": "date", "field_id": "field", "display_name": "diagnosis",
                             "confidence": "confidence %", "health_score": "health"}),
                     hide_index=True, width="stretch")
        h1, h2 = st.columns([1, 2])
        rid = h1.selectbox("Re-download report for diagnosis #", df["id"].tolist())
        rec = database.get(int(rid))
        if rec:
            res = rec["result"]
            res["id"] = rec["id"]
            h1.download_button("Download PDF", report.build_pdf(res, images_for(rec)),
                               file_name=f"agrivision_report_{rid}.pdf", mime="application/pdf")
        with h2.popover("Clear history"):
            st.write("This deletes every stored diagnosis.")
            if st.button("Yes, delete all history"):
                database.delete_all()
                st.rerun()

# ---------------------------------------------------------------- model
with tab_model:
    st.subheader("Model performance on the held-out test set")
    if config.METRICS_PATH.exists():
        m = json.loads(config.METRICS_PATH.read_text())
        c = st.columns(5)
        c[0].metric("Accuracy", f"{m['accuracy']:.1%}")
        c[1].metric("Macro F1", f"{m['f1_macro']:.3f}")
        c[2].metric("Category routing", f"{m['category_accuracy']:.1%}")
        c[3].metric("False diagnosis rate", f"{m['false_diagnosis_rate_at_threshold']:.2%}",
                    delta=f"{m['false_diagnosis_rate_at_threshold'] - m['false_diagnosis_rate_no_abstention']:+.2%} "
                          "vs. no abstention", delta_color="inverse")
        c[4].metric("Coverage", f"{m['coverage_at_threshold']:.1%}",
                    help=f"Share of images answered at confidence threshold {m['confidence_threshold']:.0%}; "
                         "the rest get a re-capture request.")
        st.caption(f"MobileNetV3-Large backbone (ImageNet) + MLP classification head - {m['num_classes']} classes - "
                   f"{m['train_images']} training / {m['test_images']} test images - "
                   f"temperature-calibrated (T = {m['temperature']:.2f})")
        if "field" in m:
            fm = m["field"]
            st.markdown("**Real field photographs** (PlantDoc test split - cluttered backgrounds, natural light)")
            fc = st.columns(5)
            fc[0].metric("Field accuracy", f"{fm['accuracy']:.1%}")
            fc[1].metric("Top-3 accuracy", f"{fm['top3_accuracy']:.1%}")
            fc[2].metric("Category routing", f"{fm['category_accuracy']:.1%}")
            fc[3].metric("False diagnosis rate", f"{fm['false_diagnosis_rate_at_threshold']:.1%}")
            fc[4].metric("Coverage", f"{fm['coverage_at_threshold']:.1%}")
            if m.get("field_baseline_accuracy") is not None:
                st.caption(f"A model trained on laboratory images only reached {m['field_baseline_accuracy']:.1%} "
                           "on the same field photographs.")
            st.caption("The laboratory test set (PlantVillage) has plain backgrounds; field accuracy is the "
                       "representative estimate for photographs taken on a farm.")
        g1, g2 = st.columns([1.3, 1])
        if config.CONFUSION_PNG.exists():
            g1.image(str(config.CONFUSION_PNG), width="stretch")
        if config.THRESHOLD_PNG.exists():
            g2.image(str(config.THRESHOLD_PNG), width="stretch")
            g2.markdown("Wrongly recommending a treatment is worse than asking for another photo, so the system "
                        "**abstains** below the confidence threshold. The chart shows the trade-off.")
        per = pd.DataFrame(m["per_class"]).T[["precision", "recall", "f1-score", "support"]]
        g2.markdown("**Per-class results**")
        g2.dataframe(per.style.format({"precision": "{:.3f}", "recall": "{:.3f}", "f1-score": "{:.3f}",
                                       "support": "{:.0f}"}), height=400, width="stretch")
    else:
        st.info("Run `python scripts/evaluate.py` to generate metrics.")

# ---------------------------------------------------------------- about
with tab_about:
    st.subheader("How AgriVision works")
    st.markdown("""
**Pipeline:** upload / capture &rarr; image validation (resolution, blur, exposure, leaf presence) &rarr;
resize & normalise &rarr; leaf / background segmentation (OpenCV) &rarr; MobileNetV3 classification &rarr;
disease / pest / nutrient routing &rarr; severity from lesion area &rarr; knowledge-base recommendation &rarr;
crop-health report.

**Supported crops:** """ + ", ".join(engine.crops) + """

**Recommendation factors:** crop, detected problem, severity, growth stage, temperature & humidity,
soil moisture & pH (IoT-ready inputs), region and field history (recurring outbreaks are escalated).

**Limitations**
- Trained on PlantVillage (lab images with plain backgrounds); field photos with cluttered backgrounds are harder.
- Pest coverage is limited to spider-mite damage present in the dataset.
- Nutrient deficiencies are screened with colour rules, not a trained model - always confirm with a soil / tissue test.
- Similar diseases (e.g. early blight vs target spot) can look alike; the system abstains when unsure.

*AgriVision is a decision-support and early-screening system. Confirm every high-impact decision
with an agricultural expert or a soil test.*
""")
