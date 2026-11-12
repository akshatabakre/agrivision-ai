"""Recommendation engine: turns a label into an instruction that fits this
farm, this crop and this week (slide 9).

Factors: crop + detected class (knowledge base), severity, growth stage,
environment (temperature / humidity / soil sensors), region and the field's
diagnosis history (recurring outbreaks are escalated).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from functools import lru_cache

from . import config

HELPLINE = ("Consult your nearest Krishi Vigyan Kendra (KVK) or the Kisan Call Centre "
            "(1800-180-1551) for locally approved products and doses")


@lru_cache(maxsize=1)
def load_kb() -> dict:
    with open(config.KB_PATH, encoding="utf-8") as f:
        return json.load(f)


def class_info(label: str) -> dict:
    """Knowledge-base entry for a class, with a sensible fallback for unknown labels."""
    kb = load_kb()["classes"]
    if label in kb:
        return kb[label]
    crop, _, cond = label.partition("___")
    healthy = cond.lower() == "healthy"
    return {
        "crop": crop.replace("_", " "),
        "name": "Healthy" if healthy else cond.replace("_", " "),
        "category": "healthy" if healthy else "disease",
        "cause": "See local extension guidance",
        "symptoms": [], "actions": [], "prevention": [],
    }


@dataclass
class Recommendation:
    urgency: str
    actions: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    prevention: list[str] = field(default_factory=list)


def _environment_note(info: dict, ctx: dict) -> tuple[str | None, bool]:
    """Return (note, favourable) comparing live conditions with what the pathogen likes."""
    fav = info.get("favourable")
    temp, hum = ctx.get("temperature"), ctx.get("humidity")
    if not fav or (temp is None and hum is None):
        return None, False

    checks = []
    if temp is not None and "temp_min" in fav:
        checks.append(fav["temp_min"] <= temp <= fav["temp_max"])
    if hum is not None and "humidity_min" in fav:
        checks.append(hum >= fav["humidity_min"])
    if hum is not None and "humidity_max" in fav:
        checks.append(hum <= fav["humidity_max"])
    if not checks:
        return None, False

    reading = ", ".join(s for s in (
        f"{temp:.0f} C" if temp is not None else "",
        f"{hum:.0f}% humidity" if hum is not None else "") if s)
    if all(checks):
        return (f"Current conditions ({reading}) favour {info['name']} - "
                f"{fav['note'].lower()}. Expect faster spread; act sooner."), True
    return (f"Current conditions ({reading}) are less favourable for {info['name']} "
            f"({fav['note'].lower()}), so spread should be slower."), False


def _stage_note(stage: str | None, category: str) -> str | None:
    if category in ("healthy", "nutrient"):
        return None
    return {
        "Seedling": "Seedlings are fragile: remove infected seedlings rather than treating them, "
                    "and protect the rest of the nursery.",
        "Flowering": "Crop is flowering: spray only in the early morning or evening to protect pollinators.",
        "Fruiting": "Crop is fruiting: check the pre-harvest interval (PHI) on any product label "
                    "before spraying close to harvest.",
    }.get(stage or "")


def recommend(label: str, category: str, severity: str, ctx: dict | None = None,
              recurrence: int = 0, nutrient_pattern: str | None = None) -> Recommendation:
    ctx = ctx or {}
    kb = load_kb()
    info = class_info(label)

    if category == "healthy":
        rec = Recommendation("Routine", list(kb["healthy"]["actions"]))
        if nutrient_pattern:
            rec.notes.append("Mild colour changes were seen; re-scan in a week to rule out nutrient stress.")
        return rec

    if category == "nutrient":
        nut = kb["nutrients"][nutrient_pattern]
        rec = Recommendation("Within a week", list(nut["actions"]))
        ph = ctx.get("soil_ph")
        if ph is not None and nutrient_pattern == "Fe/Mg":
            if ph > 7.5:
                rec.notes.append(f"Soil pH {ph:.1f} is alkaline, which locks up iron - supports Fe deficiency.")
            elif ph < 5.5:
                rec.notes.append(f"Soil pH {ph:.1f} is acidic, which favours Mg leaching - supports Mg deficiency.")
        rec.notes.append("Image analysis gives a probable diagnosis only. Confirm with a soil / tissue "
                         "test before applying any fertiliser.")
        return rec

    env_note, favourable = _environment_note(info, ctx)
    escalate = recurrence > 0 or favourable

    actions = list(info.get("actions", []))
    treatment = info.get("treatment")
    if severity == "Mild":
        urgency = "Monitor closely"
        if escalate and treatment:
            actions.append(treatment)
        actions.append("Re-check the plant in 3-4 days and treat if the problem spreads")
    elif severity == "Moderate":
        urgency = "Act this week"
        if treatment:
            actions.append(treatment)
    else:
        urgency = "Act today"
        actions.insert(0, "Isolate or remove the most heavily affected plants first")
        if treatment:
            actions.append(treatment)
        actions.append("Inspect the whole field - severe cases rarely stay on one plant")

    if severity in ("Moderate", "Severe") or escalate:
        actions.append(HELPLINE)

    rec = Recommendation(urgency, actions, prevention=list(info.get("prevention", [])))
    if recurrence:
        field_name = ctx.get("field_id") or "this field"
        rec.notes.append(
            f"Recurring outbreak: {info['name']} was diagnosed {recurrence} time(s) in {field_name} "
            f"in the last {config.RECURRENCE_WINDOW_DAYS} days. Escalate to an expert and plan "
            "resistant varieties / crop rotation for the next season.")
    if env_note:
        rec.notes.append(env_note)
    if (sm := ctx.get("soil_moisture")) is not None and info.get("cause_type") == "pest" and sm < 30:
        rec.notes.append(f"Soil moisture is low ({sm:.0f}%). Water-stressed plants suffer worse mite attacks - irrigate.")
    if note := _stage_note(ctx.get("growth_stage"), category):
        rec.notes.append(note)
    if region := ctx.get("region"):
        rec.notes.append(f"Region: {region}. Use only products approved for use in your state.")
    return rec
