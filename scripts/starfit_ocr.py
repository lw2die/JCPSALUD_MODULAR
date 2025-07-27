# === scripts/starfit_ocr.py ===
import sys
from pathlib import Path

# ----------------------------------------------------------------------
# 1) Stub uploader si no existe
# ----------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
try:
    from uploader import upload_data
except ModuleNotFoundError:
    def upload_data(img, datos):
        print("⚠️ uploader.py no disponible, skip upload")

# ----------------------------------------------------------------------
# 2) Imports OCR
# ----------------------------------------------------------------------
import cv2
import pytesseract
import re
import json
from unidecode import unidecode
from rapidfuzz import fuzz

# ----------------------------------------------------------------------
# 3) Cargar CANON (métricas “oficiales”)
# ----------------------------------------------------------------------
DICT_FILE = BASE_DIR / "ocr_starfit" / "metricas_dict_starfit.json"
try:
    with open(DICT_FILE, encoding="utf-8") as f:
        CANON = json.load(f)
except Exception:
    CANON = {}

# Prepara lista de claves
VALID_KEYS = set(CANON.keys())

STOP_S = {"medida","perfil","grafico","gráfico","x","t","&","ba","o","a","h","=",":",";"}

# ----------------------------------------------------------------------
# 4) Preprocesado y mapeo
# ----------------------------------------------------------------------
def preprocess_starfit(p: Path):
    img = cv2.imread(str(p))
    img = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.bilateralFilter(gray, 9,75,75)
    _, th = cv2.threshold(blur,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
    ker = cv2.getStructuringElement(cv2.MORPH_RECT,(3,3))
    return cv2.morphologyEx(th, cv2.MORPH_CLOSE, ker)

def clean_starfit(lbl: str) -> str:
    txt = re.sub(r"[^A-Za-zÁÉÍÓÚÜáéíóúüÑñ\s]","", lbl)
    return " ".join(t for t in txt.split() if len(t)>2 and t.lower() not in STOP_S)

def map_lbl_starfit(raw: str):
    t = unidecode(clean_starfit(raw)).strip().lower()
    if not t:
        return None
    # DEBUG
    print(f"🔍 map_lbl: '{raw}' → '{t}'")
    # 1) busc. directa (umbral 80)
    for canon in VALID_KEYS:
        base = unidecode(canon.split(" (")[0]).lower()
        if t.startswith(base) or fuzz.ratio(t, base) >= 80:
            print(f"    → matched DIRECTO '{canon}'")
            return canon
    # 2) aliases
    for canon, aliases in CANON.items():
        for alias in aliases:
            if fuzz.ratio(t, unidecode(alias).lower()) >= 80:
                print(f"    → matched ALIAS '{canon}' (alias='{alias}')")
                return canon
    # fallback
    fallback = clean_starfit(raw)
    print(f"    → sin match, usando FALLBACK '{fallback}'")
    return fallback or None

# ----------------------------------------------------------------------
# 5) Extracción de métricas
# ----------------------------------------------------------------------
def extraer_starfit(img: Path):
    texto = pytesseract.image_to_string(
        preprocess_starfit(img),
        lang="spa+eng", config="--oem 3 --psm 3"
    )
    lines = [unidecode(l).strip() for l in texto.splitlines() if l.strip()]
    datos, i = [], 0

    while i < len(lines):
        m = re.match(r"([\d]+(?:[\.,]\d+)?)(?:\s*(kg|%|kcal))?", lines[i], re.I)
        if not m:
            i += 1
            continue

        num, uni = m.groups()
        uni = (uni or "").lower()
        # descartar ruido
        if len(num.replace(",", "").replace(".", "")) == 1:
            i += 1
            continue

        # capturar etiqueta
        lbl_parts, j = [], i+1
        while j < len(lines) and not re.search(r"\d", lines[j]):
            if len(lines[j]) > 2:
                lbl_parts.append(lines[j])
            if len(lbl_parts) == 2:
                break
            j += 1

        raw_lbl = " ".join(lbl_parts).strip()
        canon = map_lbl_starfit(raw_lbl)
        if not canon:
            i = j
            continue

        try:
            val = float(num.replace(",", "."))
            # ajustes
            if canon.startswith("Grasa Visceral") and val >= 10:
                val = float(str(int(val))[0])
            val = round(val, 2)
            if "%" in canon and val > 100:
                while val > 100:
                    val /= 10
            if canon.startswith("Edad Corporal") and val > 120:
                val //= 10

            # filtros mínimos (por ejemplo IMC 5–60)
            if canon == "IMC" and not (5 <= val <= 60):
                i = j; continue

            # añadir unidad si falta
            if uni and uni not in canon.lower():
                canon = f"{canon} ({uni})"

            datos.append((canon, val))
        except ValueError:
            pass

        i = j

    return datos

# ----------------------------------------------------------------------
# 6) Bloque principal
# ----------------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("⚠️ Uso: python starfit_ocr.py <imagen1> [<imagen2> …]")
        sys.exit(1)

    rutas = [Path(p).resolve() for p in sys.argv[1:]]
    for img in rutas:
        if not img.exists():
            print(f"❌ Imagen no encontrada: {img}")
            sys.exit(1)

    print(f"📷 Analizando {len(rutas)} capturas…")
    todas = []
    for img in rutas:
        todas += extraer_starfit(img)

    # desduplicar
    seen = {}
    for k, v in todas:
        if k not in seen:
            seen[k] = v
    datos = list(seen.items())

    if not datos:
        print("⚠️ No se detectaron métricas válidas.")
        sys.exit(0)

    print(f"✅ Métricas detectadas: {len(datos)}")
    for m, v in datos:
        print(f" • {m}: {v}")

    upload_data(rutas[0], datos)
    print("✅ Subida a CAPTURAS completada.")
