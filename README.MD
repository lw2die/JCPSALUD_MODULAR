# Proyecto jcpsalud_modular

Este proyecto procesa datos de múltiples dispositivos (Polar, Starfit, Amazfit, Laboratorio) via OCR y sube métricas a Google Sheets.

## Requisitos
- Python 3.9+
- Dependencias en `requirements.txt` (cv2, pytesseract, gspread, rapidfuzz, etc.)
- `creds.json` con credenciales de Google Service Account

## Configuración
1. Copiar `config.json` y ajustar si es necesario.
2. Colocar `creds.json` en la raíz del proyecto.

## Uso
```bash
pip install -r requirements.txt
python scripts/ocr_watcher.py