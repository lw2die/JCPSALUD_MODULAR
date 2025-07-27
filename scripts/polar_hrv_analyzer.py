# === polar_hrv_analyzer.py ===
import os
import numpy as np
import pandas as pd
from datetime import datetime
from scipy.signal import welch
from scipy.interpolate import interp1d

INPUT_FOLDER = r"G:\My Drive\SALUD_JCP\incoming\POLAR"
OUTPUT_CSV = os.path.join(INPUT_FOLDER, "polar_hrv_output.csv")

def leer_rr(filepath):
    df = pd.read_csv(filepath, sep=";")
    return df.iloc[:, 1].values.astype(float)

def leer_hr(filepath):
    df = pd.read_csv(filepath, sep=";")
    return df.iloc[:, 1].values.astype(float)

def leer_acc(filepath):
    df = pd.read_csv(filepath, sep=";")
    x = df.iloc[:, 2].values.astype(float)
    y = df.iloc[:, 3].values.astype(float)
    z = df.iloc[:, 4].values.astype(float)
    mov = np.sqrt(x**2 + y**2 + z**2)
    return mov

def detectar_reposo(rr, acc, umbral=20):
    acc = acc[:len(rr)] if len(acc) >= len(rr) else np.pad(acc, (0, len(rr) - len(acc)), constant_values=0)
    reposo = acc < (np.median(acc) + umbral)
    return rr[reposo]

def calcular_hrv(rr_ms):
    rr_s = rr_ms / 1000.0
    diff_rr = np.diff(rr_s)
    rmssd = np.sqrt(np.mean(diff_rr**2)) * 1000
    sdnn = np.std(rr_ms)
    avnn = np.mean(rr_ms)
    return rmssd, sdnn, avnn

def calcular_frecuencia(rr_ms):
    t = np.cumsum(rr_ms) / 1000.0
    rr_s = rr_ms / 1000.0
    fs_interp = 4.0
    ti = np.arange(t[0], t[-1], 1/fs_interp)
    f = interp1d(t, rr_s, kind='cubic')
    rr_interp = f(ti)
    freqs, psd = welch(rr_interp, fs=fs_interp, nperseg=256)

    lf_band = (0.04, 0.15)
    hf_band = (0.15, 0.4)

    lf = np.trapz(psd[(freqs >= lf_band[0]) & (freqs <= lf_band[1])],
                  freqs[(freqs >= lf_band[0]) & (freqs <= lf_band[1])])
    hf = np.trapz(psd[(freqs >= hf_band[0]) & (freqs <= hf_band[1])],
                  freqs[(freqs >= hf_band[0]) & (freqs <= hf_band[1])])
    ratio = lf / hf if hf > 0 else np.nan
    return lf, hf, ratio

def calcular_triangular_index(rr_ms):
    bins = np.arange(min(rr_ms), max(rr_ms) + 8, 7)
    hist, _ = np.histogram(rr_ms, bins)
    return len(rr_ms) / np.max(hist) if np.max(hist) > 0 else np.nan

def detectar_fecha_desde_nombre(nombre_archivo):
    partes = nombre_archivo.split("_")
    for parte in partes:
        if parte.isdigit() and len(parte) == 8:
            return datetime.strptime(parte, "%Y%m%d").date().isoformat()
    return datetime.today().date().isoformat()

def main():
    archivos = os.listdir(INPUT_FOLDER)
    rr_file = next((f for f in archivos if "RR" in f.upper()), None)
    hr_file = next((f for f in archivos if "HR" in f.upper()), None)
    acc_file = next((f for f in archivos if "ACC" in f.upper()), None)

    if not rr_file:
        print("❌ No se encontró archivo RR.")
        return

    rr = leer_rr(os.path.join(INPUT_FOLDER, rr_file))
    fecha = detectar_fecha_desde_nombre(rr_file)

    if acc_file:
        acc = leer_acc(os.path.join(INPUT_FOLDER, acc_file))
        rr = detectar_reposo(rr, acc)
        print(f"🟢 RR reducido a {len(rr)} puntos en reposo")

    rmssd, sdnn, avnn = calcular_hrv(rr)
    lf, hf, ratio = calcular_frecuencia(rr)
    tri_index = calcular_triangular_index(rr)

    data = [
        (fecha, "POLAR_HRV_RMSSD", round(rmssd, 1)),
        (fecha, "POLAR_HRV_SDNN", round(sdnn, 1)),
        (fecha, "POLAR_HRV_AVNN", round(avnn, 1)),
        (fecha, "POLAR_HRV_LF_POWER", round(lf, 1)),
        (fecha, "POLAR_HRV_HF_POWER", round(hf, 1)),
        (fecha, "POLAR_HRV_LF_HF_RATIO", round(ratio, 2)),
        (fecha, "POLAR_HRV_TRIANGULAR_INDEX", round(tri_index, 1)),
    ]

    if hr_file:
        hr = leer_hr(os.path.join(INPUT_FOLDER, hr_file))
        data += [
            (fecha, "POLAR_HR_MIN", round(np.min(hr), 1)),
            (fecha, "POLAR_HR_PROMEDIO", round(np.mean(hr), 1)),
            (fecha, "POLAR_HR_MAX", round(np.max(hr), 1)),
        ]

    df = pd.DataFrame(data, columns=["fecha", "metrica", "valor"])
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    print(f"✅ Archivo generado: {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
