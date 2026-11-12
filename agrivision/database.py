"""SQLite storage for diagnosis history."""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS diagnoses (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at    TEXT NOT NULL,
    field_id      TEXT,
    crop          TEXT,
    label         TEXT,
    display_name  TEXT,
    category      TEXT,
    status        TEXT,
    confidence    REAL,
    severity      TEXT,
    health_score  INTEGER,
    image_path    TEXT,
    context_json  TEXT,
    result_json   TEXT
);
CREATE INDEX IF NOT EXISTS idx_field_label ON diagnoses (field_id, label, created_at);
"""


@contextmanager
def connect():
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        conn.executescript(SCHEMA)
        yield conn
        conn.commit()
    finally:
        conn.close()


def save(result: dict, image_path: str | None) -> int:
    ctx = result.get("context", {})
    with connect() as conn:
        cur = conn.execute(
            """INSERT INTO diagnoses (created_at, field_id, crop, label, display_name, category,
               status, confidence, severity, health_score, image_path, context_json, result_json)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (result["timestamp"], ctx.get("field_id") or None, result["crop"], result["label"],
             result["display_name"], result["category"], result["status"], result["confidence"],
             result["severity"], result["health_score"], image_path,
             json.dumps(ctx), json.dumps(result)),
        )
        return int(cur.lastrowid)


def recurrence_count(field_id: str | None, label: str) -> int:
    if not field_id:
        return 0
    since = (datetime.now() - timedelta(days=config.RECURRENCE_WINDOW_DAYS)).isoformat(timespec="seconds")
    with connect() as conn:
        row = conn.execute(
            """SELECT COUNT(*) FROM diagnoses WHERE field_id = ? AND label = ?
               AND status = 'ok' AND created_at >= ?""",
            (field_id, label, since),
        ).fetchone()
    return int(row[0])


def history(field_id: str | None = None, limit: int = 200) -> list[dict]:
    query = ("SELECT id, created_at, field_id, crop, display_name, category, status, confidence, "
             "severity, health_score, image_path FROM diagnoses")
    args: tuple = ()
    if field_id:
        query += " WHERE field_id = ?"
        args = (field_id,)
    query += " ORDER BY created_at DESC LIMIT ?"
    with connect() as conn:
        return [dict(r) for r in conn.execute(query, args + (limit,)).fetchall()]


def get(diagnosis_id: int) -> dict | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM diagnoses WHERE id = ?", (diagnosis_id,)).fetchone()
    if not row:
        return None
    out = dict(row)
    out["result"] = json.loads(out.pop("result_json"))
    out["context"] = json.loads(out.pop("context_json"))
    return out


def fields() -> list[str]:
    with connect() as conn:
        return [r[0] for r in conn.execute(
            "SELECT DISTINCT field_id FROM diagnoses WHERE field_id IS NOT NULL ORDER BY field_id")]


def delete_all() -> None:
    with connect() as conn:
        conn.execute("DELETE FROM diagnoses")
