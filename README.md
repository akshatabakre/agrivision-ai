# AgriVision AI — Crop Health Monitoring & Failure Diagnosis

Detect crop diseases, pest damage and nutrient deficiencies from a single leaf photograph,
estimate severity, and get a context-aware recommendation plus a downloadable crop-health report.

Minor Project — Akshata Bakre (23118007), Himanshu Kashyap (23118043) · Guide: Dr. Sanjay Kumar

---

## What is implemented (Phase 1 + Phase 2 of the roadmap)

| Slide | Feature | Where |
|---|---|---|
| 5 | Image validation (resolution, blur, exposure, leaf presence), CLAHE enhancement, resize & normalise, leaf/background segmentation | `agrivision/preprocessing.py` |
| 6 | MobileNetV3-Large transfer learning (ImageNet backbone + trained head), temperature-calibrated confidence | `agrivision/model.py`, `scripts/train.py` |
| 7 | Routing into **Disease / Pest / Nutrient / Healthy** (+ "not a leaf") with category probabilities; N / K / Fe-Mg deficiency signatures | `agrivision/pipeline.py`, `agrivision/nutrient.py` |
| 8 | Severity from lesion area → 0-100 health score → Healthy / Mild / Moderate / Severe | `agrivision/severity.py` |
| 9 | Recommendation engine: crop, problem, severity, growth stage, temperature/humidity, soil moisture/pH, region, **diagnosis history (recurring outbreak escalation)** | `agrivision/recommender.py`, `agrivision/knowledge_base.json` |
| 10 | Streamlit UI · FastAPI REST API · OpenCV · PyTorch · SQLite | `app.py`, `api.py`, `agrivision/database.py` |
| 11 | "Upload → Analyse → Report" UI, confidence always visible, severity before advice | `app.py` |
| 12 | PDF crop-health report | `agrivision/report.py` |
| 13 | Dataset pipeline (clean → label → split), accuracy / precision / recall / F1 / confusion matrix, **False Diagnosis Rate with abstention threshold** | `scripts/prepare_data.py`, `scripts/evaluate.py` |
| 14 | IoT-ready sensor inputs (temperature, humidity, soil moisture, soil pH) fused into recommendations | `app.py`, `api.py` |

## Results

Trained on PlantVillage (lab photos) **plus PlantDoc (real field photos)**, MobileNetV3-Large backbone + MLP head.

**Lab photos** — PlantVillage held-out test set, 2,270 images, 39 classes

| Metric | Value |
|---|---|
| Accuracy | **97.0%** |
| Macro precision / recall / F1 | 0.970 / 0.970 / 0.970 |
| Category routing (disease / pest / healthy / not-a-leaf) | 98.9% |
| False diagnosis rate, no abstention | 3.0% |
| False diagnosis rate at 60% confidence threshold | **1.8%** (answers 97.2% of images, asks for re-capture on the rest) |

**Field photos** — PlantDoc test split, 236 photos with cluttered backgrounds, 28 classes

| Metric | Value |
|---|---|
| Accuracy, lab-only model (before) | 19.9% |
| Accuracy, current model | **53.8%** (top-3: 73.7%) |
| Category routing (disease / pest / healthy) | 89.8% |
| False diagnosis rate at field threshold 0.73 | 27.7% (answers 55.1%, asks for re-capture on the rest) |

Field photos are detected automatically (non-uniform border); for them the leaf is isolated with
focus-seeded GrabCut and a stricter confidence threshold applies, calibrated on field validation photos.
Published PlantDoc classification results are in a similar range — field photos are genuinely hard,
which is why the system abstains rather than guesses.

| | |
|---|---|
| Training time (CPU, i5-1035G1) | ~8 min feature extraction (once, cached) + ~3 min head training |
| Model size | 19.7 MB |

Plots: `models/confusion_matrix.png`, `models/threshold_curve.png`; full numbers in `models/metrics.json`.

## Project structure

```
agrivision/
  config.py            paths, thresholds, severity bands
  preprocessing.py     OpenCV: validation, enhancement, leaf segmentation, lesion colour maps
  model.py             MobileNetV3 backbone + head, inference
  severity.py          lesion area -> health score -> severity band
  nutrient.py          N / K / Fe-Mg deficiency screening (colour-pattern rules)
  recommender.py       context-aware recommendation engine
  knowledge_base.json  39 classes: cause, symptoms, actions, treatment, prevention, favourable weather
  database.py          SQLite diagnosis history
  report.py            PDF report
  pipeline.py          end-to-end workflow
scripts/
  prepare_data.py      sample + split PlantVillage into train/val/test
  train.py             feature extraction + head training + calibration
  evaluate.py          metrics, confusion matrix, threshold curve
  smoke_test.py        end-to-end test of pipeline, PDF and API
  ui_test.py           headless test of the Streamlit UI
  sample_report.py     writes an example PDF to storage/reports/
  make_samples.py      copies demo images from the test split into samples/
app.py                 Streamlit web app
api.py                 FastAPI REST API (also the Android app's backend)
serve_mobile.py        starts the API on the network and prints the address for the phone
START_MOBILE_SERVER.bat  double-click launcher for serve_mobile.py
android/               Android app source (Kotlin, Jetpack Compose)
AgriVision.apk         built Android app
samples/               demo images (from the held-out test split)
models/                trained model + metrics + plots
```

## How to run

All commands are run from the project folder in PowerShell:

```powershell
cd "D:\minor project"
.\.venv\Scripts\Activate.ps1
```

> If PowerShell blocks activation, run once: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`
> (or skip activation and call `.\.venv\Scripts\python.exe` directly).

### 1. Start the web app (the demo)

```powershell
streamlit run app.py
```

Open http://localhost:8501 → choose **Try a sample** (or upload / use camera) → **Analyse crop** →
**Generate report (PDF)**.

### 2. Start the REST API (optional)

```powershell
uvicorn api:app --port 8000
```

Open http://localhost:8000/docs for interactive Swagger docs. Endpoints: `POST /analyze`,
`GET /history`, `GET /diagnoses/{id}`, `GET /report/{id}`, `GET /crops`, `GET /health`.

### 2b. Android app (phone + laptop on the phone's hotspot)

`AgriVision.apk` (project root) is the Android app (Kotlin + Jetpack Compose, Android 9+). It sends the
photo to the FastAPI backend on the laptop and shows the diagnosis, health score, recommendations,
damage map, history and the PDF report.

1. Phone: turn on mobile hotspot. Laptop: connect to it.
2. Laptop: double-click `START_MOBILE_SERVER.bat` — it prints the address, e.g. `http://192.168.43.20:8000`.
3. Phone: install `AgriVision.apk`, open it, go to **Settings**, type that address, tap **Save & test connection**.
4. If it can't connect, allow Python through Windows Firewall (or set the hotspot network to *Private*).

Source: `android/` · rebuild with `android\build_apk.bat` (JDK 17, Android SDK and Gradle live in `D:\android`).

### 3. Run the tests

```powershell
python scripts/smoke_test.py   # pipeline + PDF + REST API
python scripts/ui_test.py      # Streamlit UI, headless
```

### Demo script (suggested for the viva)

1. **tomato_early_blight** → diagnosis, confidence, severity, health score, actions → *Generate report (PDF)*.
2. Same image, open *Field context*, set field "North plot", tick sensor readings (27 C, 85% humidity),
   growth stage "Fruiting" → recommendations now mention weather risk and pre-harvest interval.
   Analyse it again → **recurring outbreak** escalation appears; see the *Field history* tab.
3. **not_a_leaf_background** → rejected: "No crop leaf was recognised".
4. **hard_case_potato_late_blight** → model abstains (53%) and asks for re-capture.
   Set *Crop = Potato* and re-analyse → confident Late Blight. (Shows "confidence is always visible".)
5. **Model performance** tab → accuracy, confusion matrix, abstain-vs-misdiagnose curve.

### Re-training from scratch (already done — only if you want to repeat it)

```powershell
python scripts/prepare_data.py --per-class 400   # sample & split dataset (data/plantvillage.zip)
python scripts/add_field_data.py                 # add PlantDoc field photos (data/plantdoc.zip)
python scripts/train.py                          # ~10 min on a laptop CPU, then evaluates
python scripts/train.py --reuse                  # retrain head only from cached features (seconds)
python scripts/train.py --augment                # add flipped copies (slower, slightly better)
python scripts/evaluate.py                       # metrics only
```

Datasets: PlantVillage (Hughes & Salathé), "Plant leaf diseases dataset without augmentation",
Mendeley Data, doi:10.17632/tywbtsjrjv.1 · PlantDoc (Singh et al., "PlantDoc: A Dataset for Visual
Plant Disease Detection", CODS-COMAD 2020), github.com/pratikkayal/PlantDoc-Dataset, CC-BY-4.0.

## Why this training method

The slides recommend fine-tuning a pre-trained CNN (MobileNetV3 / EfficientNet-B0). On a CPU-only laptop
the fastest variant is **feature extraction**: the ImageNet backbone is frozen, each image passes through
it once, and only the final classification layer is trained on the cached 1280-d embeddings. Training the
head takes seconds; extraction takes minutes. Backbone and head are saved together so the app runs
offline.

## Limitations (honest)

- Field photos are much harder than lab photos (53.8% vs 97.0%); the app abstains on unsure field photos. More real field photos from local farms are the main way to improve this further.
- Pest coverage = spider-mite damage (the only pest class in PlantVillage). YOLO-based pest localisation is future work.
- Nutrient deficiencies are screened with explainable colour rules, not a trained model — always confirm with a soil / tissue test.
- AI diagnosis is an early-screening aid, not a definitive agricultural verdict.
