# === scripts/uploader.py ===
import json
import logging
import re
from pathlib import Path
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ----------------------------------------------------------------------
# 1) Config y logger
# ----------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
cfg = json.loads((BASE_DIR / 'config.json').read_text(encoding='utf-8'))

LOG_DIR = BASE_DIR / 'logs'
LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    filename=str(LOG_DIR / f"{datetime.now():%Y-%m-%d}.log"),
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    level=logging.INFO
)
logger = logging.getLogger('uploader')

# ----------------------------------------------------------------------
# 2) Conexión a Google Sheets
# ----------------------------------------------------------------------
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
creds = ServiceAccountCredentials.from_json_keyfile_name(
    cfg.get('CREDS_FILE', 'creds.json'), scope
)
gc = gspread.authorize(creds)
sheet = gc.open_by_key(cfg['SHEET_ID'])
capturas_ws = sheet.worksheet("CAPTURAS")

# ----------------------------------------------------------------------
# 3) Función principal
# ----------------------------------------------------------------------
def upload_data(img_path, datos):
    """
    img_path: Path de la primera captura procesada (todas comparten la misma fecha interna).
    datos: lista de tuplas (métrica, valor).
    Se sube: [fecha_extraída, métrica, valor, archivo].
    """
    archivo = Path(img_path).name

    # Intentamos extraer YYYYMMDD del nombre
    m = re.search(r"(\d{8})", archivo)
    if m:
        try:
            fecha_dt = datetime.strptime(m.group(1), "%Y%m%d").date()
            fecha = fecha_dt.isoformat()
        except ValueError:
            fecha = datetime.now().date().isoformat()
    else:
        fecha = datetime.now().date().isoformat()

    # Construir filas a subir
    rows = [
        [fecha, metrica, f"{valor:.2f}", archivo]
        for metrica, valor in datos
    ]

    # Leer existentes (sin cabecera)
    try:
        existing = capturas_ws.get_all_values()[1:]
    except Exception as e:
        logger.error(f"No pude leer CAPTURAS: {e}")
        return

    existentes = set(tuple(r) for r in existing)

    # Filtrar duplicados exactos
    nuevos = [r for r in rows if tuple(r) not in existentes]
    if not nuevos:
        logger.info("⚠️ No hay métricas nuevas para CAPTURAS.")
        return

    try:
        capturas_ws.append_rows(nuevos, value_input_option="USER_ENTERED")
        logger.info(f"✅ Subidos {len(nuevos)} registros a CAPTURAS.")
    except Exception as e:
        logger.error(f"❌ Error subiendo a CAPTURAS: {e}")

# ----------------------------------------------------------------------
# 4) Módulo ejecutado directamente
# ----------------------------------------------------------------------
if __name__ == "__main__":
    print("⚠️ Este módulo sólo exporta upload_data()")


