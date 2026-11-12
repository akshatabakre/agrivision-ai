"""End-to-end smoke test: runs every sample image through the full pipeline,
builds a PDF report and exercises the REST API.

    python scripts/smoke_test.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from agrivision import report  # noqa: E402
from agrivision.pipeline import get_engine  # noqa: E402


def main():
    engine = get_engine()
    samples = sorted((ROOT / "samples").glob("*.jpg"))
    assert samples, "no sample images in samples/"
    print(f"{'image':38} {'status':9} {'diagnosis':38} {'conf':>5} {'sev':9} score")
    for path in samples:
        res, imgs = engine.analyze(path.read_bytes(), {"field_id": "smoke-test"}, save=False)
        print(f"{path.stem:38} {res['status']:9} {res['crop'] + ' - ' + res['display_name']:38.38} "
              f"{res['confidence']:5.0%} {res['severity']:9} {res['health_score']}")
        pdf = report.build_pdf(res, imgs)
        assert pdf[:4] == b"%PDF"

    client = TestClient(__import__("api").app)
    assert client.get("/health").json()["status"] == "ok"
    with open(samples[0], "rb") as f:
        r = client.post("/analyze", files={"image": (samples[0].name, f, "image/jpeg")},
                        data={"field_id": "api-test", "temperature": "27", "humidity": "85"})
    assert r.status_code == 200, r.text
    did = r.json()["id"]
    assert client.get(f"/report/{did}").content[:4] == b"%PDF"
    assert any(h["id"] == did for h in client.get("/history").json())
    print("\nAPI: /health /analyze /report /history OK")
    print("SMOKE TEST PASSED")


if __name__ == "__main__":
    main()
