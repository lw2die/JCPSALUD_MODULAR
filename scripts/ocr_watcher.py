# === scripts/ocr_watcher.py ===
import json
import logging
import time
import subprocess
import shutil
import re
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# ----------------------------------------------------------------------
# 1) Configuración
# ----------------------------------------------------------------------
BASE_DIR  = Path(__file__).resolve().parent.parent
cfg       = json.loads((BASE_DIR / 'config.json').read_text(encoding='utf-8'))
ROOT      = Path(cfg['ROOT'])
INCOMING  = ROOT / cfg['INCOMING']
PROCESSED = ROOT / cfg['PROCESSED']

# Asegurar carpetas raíz
for d in (INCOMING, PROCESSED):
    d.mkdir(parents=True, exist_ok=True)

# Hot-folders
POLAR_IN    = INCOMING / 'Polar'
STARFIT_IN  = INCOMING / 'starfit'
AMAZFIT_IN  = INCOMING / 'amazfit'
LAB_IN      = INCOMING / 'laboratorio'
for d in (POLAR_IN, STARFIT_IN, AMAZFIT_IN, LAB_IN):
    d.mkdir(parents=True, exist_ok=True)

# Procesados
POLAR_OUT    = PROCESSED / 'Polar'
STARFIT_OUT  = PROCESSED / 'starfit'
AMAZFIT_OUT  = PROCESSED / 'amazfit'
LAB_OUT      = PROCESSED / 'laboratorio'
for d in (POLAR_OUT, STARFIT_OUT, AMAZFIT_OUT, LAB_OUT):
    d.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------
# 2) Logger (archivo + consola)
# ----------------------------------------------------------------------
LOG_DIR = BASE_DIR / 'logs'
LOG_DIR.mkdir(parents=True, exist_ok=True)
logfile = LOG_DIR / f"{time.strftime('%Y-%m-%d')}.log"

logging.basicConfig(
    filename=str(logfile),
    format='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
    level=logging.INFO
)
logger = logging.getLogger('ocr_watcher')
ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter('[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s'))
logger.addHandler(ch)

# Mostrar rutas para confirmar
logger.info(f"🔧 Config: ROOT = {ROOT}")
logger.info(f"🔧 Config: INCOMING = {INCOMING}")
logger.info(f"🔧 Config: STARFIT_IN = {STARFIT_IN}")

# ----------------------------------------------------------------------
# 3) Funciones de Procesamiento
# ----------------------------------------------------------------------

# POLAR (sin cambios)
def _extract_polar_base(name):
    m = re.search(r"(\d{8}_\d{4})", name)
    return m.group(1) if m else None

def detect_polar_sets():
    txts = list(POLAR_IN.glob('*.txt'))
    groups = {}
    for f in txts:
        base = _extract_polar_base(f.name)
        if not base: continue
        g = groups.setdefault(base, {})
        if '_RR.txt' in f.name:  g['RR']  = f
        if '_ACC.txt' in f.name: g['ACC'] = f
        if '_HR.txt' in f.name:  g['HR']  = f
    return [(b, g) for b,g in groups.items() if {'RR','ACC','HR'}.issubset(g)]

def process_polar(base, files):
    logger.info(f"Procesando POLAR {base}")
    try:
        subprocess.run([
            'python', str(BASE_DIR/'scripts'/'polar_hrv_analyzer.py'),
            str(files['RR']), str(files['ACC']), str(files['HR'])
        ], check=True)
        subprocess.run(['python', str(BASE_DIR/'scripts'/'uploader.py')], check=True)
        for f in files.values():
            dst = POLAR_OUT / f.name
            shutil.move(str(f), str(dst))
            logger.info(f" → Moved POLAR file {f.name}")
        logger.info(f"✅ POLAR {base} procesado y movido")
    except Exception as e:
        logger.error(f"❌ Error POLAR {base}: {e}")

# STARFIT (modificado)
def detect_starfit_sets():
    # Listamos TODOs, sin glob rígido
    all_files = list(STARFIT_IN.iterdir())
    # Filtramos solo por sufijo, case‐insensitive
    files = [
        f for f in all_files
        if f.suffix.lower() in {'.jpg', '.jpeg', '.png'}
    ]
    logger.info(f"🔍 detect_starfit_sets: listado crudo = {[p.name for p in all_files]}")
    logger.info(f"🔍 detect_starfit_sets: imágenes detectadas = {[p.name for p in files]}")
    # Agrupamos por fecha YYYYMMDD en el nombre
    groups = {}
    for f in files:
        m = re.search(r"(\d{8})", f.name)
        key = m.group(1) if m else '<sin_fecha>'
        groups.setdefault(key, []).append(f)
    for day, imgs in groups.items():
        logger.info(f"  • Grupo {day}: {[p.name for p in imgs]}")
    valid = [(day, imgs) for day, imgs in groups.items() if len(imgs) >= 2]
    logger.info(f"🔍 detect_starfit_sets: {len(valid)} grupos válidos (>=2 imágenes)")
    return valid

def process_starfit(base, files):
    logger.info(f"Procesando STARFIT {base} con {len(files)} capturas")
    try:
        cmd = ['python', str(BASE_DIR/'scripts'/'starfit_ocr.py')] + [str(f) for f in files]
        subprocess.run(cmd, check=True)
        for f in files:
            dst = STARFIT_OUT / f.name
            shutil.move(str(f), str(dst))
            logger.info(f" → Moved STARFIT file {f.name}")
        logger.info(f"✅ STARFIT {base} procesado y movido")
    except Exception as e:
        logger.error(f"❌ Error STARFIT {base}: {e}")

# AMAZFIT (sin cambios)
def process_amazfit(img_file):
    logger.info(f"Procesando AMAZFIT: {img_file.name}")
    try:
        subprocess.run([
            'python', str(BASE_DIR/'scripts'/'amazfit_ocr.py'),
            str(img_file)
        ], check=True)
        dst = AMAZFIT_OUT / img_file.name
        shutil.move(str(img_file), str(dst))
        logger.info(f" → Moved AMAZFIT file {img_file.name}")
        logger.info(f"✅ AMAZFIT {img_file.name} procesado y movido")
    except Exception as e:
        logger.error(f"❌ Error AMAZFIT {img_file.name}: {e}")

# LABORATORIO (sin cambios)
def process_lab(img_file):
    logger.info(f"Procesando LABORATORIO: {img_file.name}")
    try:
        subprocess.run([
            'python', str(BASE_DIR/'scripts'/'laboratorio_ocr.py'),
            str(img_file)
        ], check=True)
        dst = LAB_OUT / img_file.name
        shutil.move(str(img_file), str(dst))
        logger.info(f" → Moved LAB file {img_file.name}")
        logger.info(f"✅ LABORATORIO {img_file.name} procesado y movido")
    except Exception as e:
        logger.error(f"❌ Error LABORATORIO {img_file.name}: {e}")

# ----------------------------------------------------------------------
# 4) Handler de eventos
# ----------------------------------------------------------------------
class Handler(FileSystemEventHandler):
    def on_created(self, event): self._handle('CREATED ', event)
    def on_modified(self, event): self._handle('MODIFIED', event)
    def on_moved(self,   event): self._handle('MOVED  ', event)

    def _handle(self, tag, event):
        if event.is_directory: return
        p = Path(event.src_path)
        ext = p.suffix.lower()
        parent = p.parent.name.lower()
        logger.info(f"[{tag}] {p}")
        if ext == '.txt' and parent == 'polar':
            for b,grp in detect_polar_sets():
                process_polar(b,grp)
        elif ext in {'.jpg','.jpeg','.png'} and parent == 'starfit':
            for b,fs in detect_starfit_sets():
                process_starfit(b,fs)
        elif ext in {'.jpg','.jpeg','.png'} and parent == 'amazfit':
            process_amazfit(p)
        elif ext in {'.jpg','.jpeg','.png','.pdf'} and parent == 'laboratorio':
            process_lab(p)

# ----------------------------------------------------------------------
# 5) Main + escaneo inicial
# ----------------------------------------------------------------------
if __name__ == '__main__':
    print(f"[ocr_watcher] 🟢 Vigilando {INCOMING} (Ctrl-C para salir)")
    obs = Observer()
    obs.schedule(Handler(), str(INCOMING), recursive=True)
    obs.start()
    logger.info("🟢 Watcher iniciado")
    logger.info("🔍 Escaneando pendientes al inicio…")
    # procesamos StarFit ya al arrancar
    for day, files in detect_starfit_sets():
        process_starfit(day, files)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("🔴 Watcher detenido")
        obs.stop()
    obs.join()
