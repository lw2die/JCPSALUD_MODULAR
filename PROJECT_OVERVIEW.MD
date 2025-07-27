# Visión general
El proyecto es un sistema de recomendación diaria cuyo propósito último es aumentar tu longevidad enseñándote cada mañana qué hacer y por qué, en función de tus datos personales de sueño, nutrición y ejercicio.

# Objetivos
- Proporcionar una guía práctica y fundamentada cada día.  
- Acercarte a tu peso y porcentaje de grasa ideales.  
- Mejorar indicadores de salud a largo plazo.

# Arquitectura
1. **Ingestión de datos**  
   - **Amazfit**: calorías, macronutrientes, sueño y variabilidad cardíaca.  
   - **StarFit**: composición corporal (peso, grasa, masa muscular, etc.).  
   - **Polar H10**: HRV y carga nocturna (archivos TXT).  
   - **Laboratorio**: marcadores bioquímicos (colesterol, inflamación, etc.) desde PDF.  

2. **Canonización y almacenamiento**  
   - Normalizar nombres de métricas a claves únicas (“Peso (kg)”, “Grasa Corporal (%)”, etc.).  
   - Guardar en Google Sheets hoja **CAPTURAS** con columnas:  
     **Fecha | Métrica | Valor | Origen | Archivo**.  

3. **Generación de pivotes**  
   - **PIVOT_IA**: métricas críticas para la IA de recomendación.  
   - **PIVOT_SEC**: métricas secundarias.  
   - Encabezados abreviados y centrados para optimizar espacio.  

4. **Motor de IA y análisis de Pareto**  
   - Identificar el “gap” respecto a objetivos (peso/grasa ideales y longevidad).  
   - Aplicar análisis de Pareto para seleccionar las ~30 métricas que explican el 80 % del desvío.  

5. **Recomendación diaria**  
   - Generar texto y escribirlo en la hoja **ULTIMA_RECO!B2**.  
   - Guardar histórico en **RECO_HISTORICO** para seguimiento continuo.  

# Flujo de datos
1. Nuevos archivos llegan a `incoming/`  
2. `ocr_watcher.py` detecta y lanza OCR → `scripts/*.py`  
3. `uploader.py` sube a **CAPTURAS** y mueve archivos a `processed/`  
4. Tablas dinámicas en **PIVOT_IA** y **PIVOT_SEC**  
5. IA escribe la recomendación en **ULTIMA_RECO** y archiva en **RECO_HISTORICO**

# Configuración central (`config.json`)
```json
{
  "ROOT":       "G:/My Drive/jcpsalud_modular",
  "INCOMING":   "incoming",
  "PROCESSED":  "processed",
  "SHEET_ID":   "1M-FPz1gJpflDOSn2I9ysxw69mZbWNSBDx3Ti3sMvw-Q",
  "CREDS_FILE": "creds.json",
  "SHEETS": {
    "CAPTURAS": "CAPTURAS",
    "PIVOT_IA": "PIVOT_IA",
    "PIVOT_SEC": "PIVOT_SEC",
    "ULTIMA_RECO": "ULTIMA_RECO",
    "RECO_HISTORICO": "RECO_HISTORICO"
  }
}

