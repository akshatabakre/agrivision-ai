"""Headless UI test: drives app.py through Streamlit's AppTest.

    python scripts/ui_test.py
"""
from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parent.parent


def run(sample: str, crop: str = "Auto-detect", sensors: bool = False):
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=120).run()
    assert not at.exception, at.exception
    at.radio[0].set_value("Try a sample").run()
    sb = next(s for s in at.selectbox if s.label == "Sample image")
    sb.select_index(next(i for i, o in enumerate(sb.options) if sample.replace("_", " ") in o))
    next(s for s in at.selectbox if s.label == "Crop").set_value(crop)
    next(t for t in at.text_input if t.label.startswith("Field")).input("UI test plot")
    if sensors:
        next(c for c in at.checkbox if "sensor" in c.label).check().run()
    at.button[0].click().run()
    assert not at.exception, at.exception
    html = " ".join(m.value for m in at.markdown)
    verdict = html.split('class="verdict"')[1].split(">")[1].split("<")[0]
    print(f"{sample:32} crop={crop:12} -> {verdict}")
    return at


if __name__ == "__main__":
    run("tomato_early_blight", sensors=True)
    run("tomato_healthy")
    run("not_a_leaf")
    run("hard_case_potato_late_blight")
    run("hard_case_potato_late_blight", crop="Potato")
    at = run("orange_citrus")
    for tab in at.tabs:
        assert not at.exception
    print("UI TEST PASSED - all tabs rendered without exceptions")
