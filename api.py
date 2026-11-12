"""AgriVision AI - REST API (FastAPI). Also the backend for the Android app.

    uvicorn api:app --reload --port 8000
    open http://localhost:8000/docs for interactive Swagger docs

For the phone app use `python serve_mobile.py`, which listens on the network.
"""
from __future__ import annotations

import base64
import io
from typing import Optional

import numpy as np
from PIL import Image

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from agrivision import __version__, config, database, report
from agrivision.pipeline import get_engine, images_for

app = FastAPI(title="AgriVision AI", version=__version__,
              description="Crop disease, pest and nutrient-deficiency diagnosis from a leaf photograph.")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def encode_images(images: dict[str, np.ndarray], max_side: int = 640) -> dict[str, str]:
    """Base64 JPEGs for clients that can't call the Python pipeline directly."""
    out = {}
    for name, arr in images.items():
        img = Image.fromarray(arr)
        img.thumbnail((max_side, max_side))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
        out[name] = base64.b64encode(buf.getvalue()).decode("ascii")
    return out


@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": config.MODEL_PATH.exists(), "version": __version__}


@app.get("/crops")
def crops():
    return {"crops": get_engine().crops}


@app.post("/analyze")
async def analyze(
    image: UploadFile = File(..., description="Leaf photograph (jpg / png)"),
    crop: Optional[str] = Form(None),
    field_id: Optional[str] = Form(None),
    region: Optional[str] = Form(None),
    growth_stage: Optional[str] = Form(None),
    temperature: Optional[float] = Form(None),
    humidity: Optional[float] = Form(None),
    soil_moisture: Optional[float] = Form(None),
    soil_ph: Optional[float] = Form(None),
    include_images: bool = Form(False, description="Add base64 JPEGs of the original / leaf / overlay"),
):
    data = await image.read()
    if not data:
        raise HTTPException(400, "Empty upload")
    ctx = dict(crop=crop, field_id=field_id, region=region, growth_stage=growth_stage,
               temperature=temperature, humidity=humidity, soil_moisture=soil_moisture, soil_ph=soil_ph)
    try:
        result, images = get_engine().analyze(data, ctx, save=True, filename=image.filename)
    except Exception as e:
        raise HTTPException(422, f"Could not analyse image: {e}") from e
    if include_images:
        result["images"] = encode_images(images)
    return result


@app.get("/history")
def history(field_id: Optional[str] = None, limit: int = 100):
    return database.history(field_id, limit)


@app.get("/diagnoses/{diagnosis_id}")
def diagnosis(diagnosis_id: int, include_images: bool = False):
    rec = database.get(diagnosis_id)
    if not rec:
        raise HTTPException(404, "Diagnosis not found")
    rec["result"]["id"] = rec["id"]
    if include_images:
        rec["result"]["images"] = encode_images(images_for(rec))
    return rec


@app.get("/report/{diagnosis_id}")
def report_pdf(diagnosis_id: int):
    rec = database.get(diagnosis_id)
    if not rec:
        raise HTTPException(404, "Diagnosis not found")
    result = rec["result"]
    result["id"] = rec["id"]
    pdf = report.build_pdf(result, images_for(rec))
    return Response(pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="agrivision_report_{diagnosis_id}.pdf"'})
