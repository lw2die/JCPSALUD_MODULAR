# === amazfit_ocr.py – versión robusta simplificada (solo kcal) ===
from pathlib import Path
from typing import List, Tuple
import re, cv2, pytesseract, unidecode
import numpy as np

def _pre(p: Path):
    g = cv2.cvtColor(cv2.imread(str(p)), cv2.COLOR_BGR2GRAY)
    g = cv2.bilateralFilter(g, 9, 75, 75)
    _, th = cv2.threshold(g, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    th = cv2.medianBlur(th, 3)
    th = cv2.dilate(th, None, iterations=1)
    return th

_fix = lambda s: (
    s.replace("l", "1").replace("I", "1").replace("|", "1")
     .replace("O", "0").replace("o", "0")
     .replace(" ", "").replace(".", "").replace(",", "")
)

def extraer_amazfit(img: Path | str) -> List[Tuple[str, float]]:
    out = []
    txt = unidecode.unidecode(
        pytesseract.image_to_string(_pre(img), lang="spa+eng", config="--oem 3 --psm 6")
    )

    dig = r"(\d[\d\s]{2,6})"

    patrones = [
        ("Comido",    "AMAZFIT_KCAL_COMIDO"),
        ("Ejercicio", "AMAZFIT_KCAL_EJERCICIO"),
        ("Restante",  "AMAZFIT_KCAL_RESTANTE"),
        ("Meta",      "AMAZFIT_KCAL_META"),
    ]

    for lbl, key in patrones:
        m = re.search(fr"\b{dig}\b[^\d]{{0,10}}{lbl}", txt, re.I) or \
            re.search(fr"{lbl}[^\d]{{0,10}}\b{dig}\b", txt, re.I)
        if m and m.groups():
            val = _fix(m.group(1))
            try:
                out.append((key, float(val)))
            except ValueError:
                continue

    return out
