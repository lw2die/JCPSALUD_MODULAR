# === conftest.py ===
import sys
from pathlib import Path

# Asegura que el proyecto (y su carpeta scripts/) esté en sys.path
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
