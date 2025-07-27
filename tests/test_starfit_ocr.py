import pytest
from pathlib import Path
import scripts.starfit_ocr as starfit

# Sample canonical mapping for tests (ensure your dict includes these keys)
@pytest.fixture(autouse=True)
def ensure_canon(tmp_path, monkeypatch):
    # Monkeypatch CANON dict for isolated testing
    starfit.CANON = {
        "Peso (kg)": ["peso"],
        "Grasa Corporal (%)": ["grasa corporal"],
        "IMC": ["imc"]
    }
    yield

def test_map_lbl_starfit_exact():
    assert starfit.map_lbl_starfit("Peso") == "Peso (kg)"
    assert starfit.map_lbl_starfit("Grasa Corporal") == "Grasa Corporal (%)"
    assert starfit.map_lbl_starfit("IMC") == "IMC"

def test_extraer_starfit_simple(monkeypatch, tmp_path):
    # Simulate OCR output
    ocr_text = """
81.9
Peso
22.9%
Grasa Corporal
26.1
IMC
"""
    monkeypatch.setattr(starfit.pytesseract, "image_to_string", lambda *args, **kwargs: ocr_text)
    monkeypatch.setattr(starfit, "preprocess_starfit", lambda p: None)

    img = tmp_path / "dummy.jpg"
    img.write_bytes(b"")

    datos = starfit.extraer_starfit(img)
    assert ("Peso (kg)", 81.9) in datos
    assert ("Grasa Corporal (%)", 22.9) in datos
    assert ("IMC", 26.1) in datos
    assert len(datos) == 3
