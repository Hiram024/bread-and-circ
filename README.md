# Hackathon INE — Plataforma de perfiles estadísticos de participación (Reto 1)

**Aplicación local lista para ejecutar + seis bases CCPC originales + análisis histórico + modelo no supervisado exploratorio + fichas educativas neutrales.** No es una herramienta oficial del INE.

## Arranque inmediato en VS Code

**Requisito:** Python 3.11 (Windows, macOS o Linux). Usa un navegador moderno.

- **Windows:** ejecuta `run.bat`.
- **macOS/Linux:** ejecuta `./run.sh`.
- **Manual:** crea un `venv`, instala `pip install -r requirements-app.txt` y ejecuta `python -m uvicorn src.dashboard_api:app --host 127.0.0.1 --port 8501`.

Abre **http://127.0.0.1:8501**. La primera ejecución instala dependencias desde PyPI; una vez instaladas, la aplicación no depende de servicios externos. `run.*` no cambia ni recalcula las fuentes originales.

Para revisar notebooks o rehacer análisis completo instala también `pip install -r requirements.txt` y ejecuta `python -m pytest -q tests`. El procesamiento original desde los seis ZIP es `python -m src.pipeline --root .` y el entrenamiento `python -m src.modeling --root .`; **no** es necesario para operar el dashboard preconstruido.

## Lo que contiene

La auditoría independiente **B2 de los CSV procesados** está documentada en
[`docs/10_auditoria_procesados_B2.md`](docs/10_auditoria_procesados_B2.md).
Se repite con `python -m src.validate_processed --root . --out analisis/reportes/b2`
desde un entorno con las dependencias instaladas; conserva los insumos y no entrena.

- **6 elecciones** (2009, 2012, 2015, 2018, 2021, 2024); 54,872,712 registros RAW documentados por la extracción anterior y 73,895 filas municipio × edad verificadas en B2. B2 no recontó los RAW.
- **Panel:** 12,385 unidades municipio × grupo de edad; **8,541 aptas** para clustering exploratorio; **1,825 municipios**.
- **5 perfiles experimentales** con etiquetas y estadísticos, `StandardScaler` + K-Means, comparación contra 4 y 6 clusters y otros algoritmos.
- **Dashboard local** con gráficos, filtros, auditoría municipal, clasificación por CSV y fichas PDF con revisión humana.
- **6 notebooks** organizados en auditoría, historia, territorios, modelo, producto y fichas.
- **6 ZIP de datos RAW** originales intactos, separados por año, más datos procesados por año y derivados.

## Estructura resumida

```text
hackathon_ine_proyecto/
├── README.md, requirements.txt, requirements-app.txt, run.sh, run.bat
├── .vscode/                     # configuración y depuración
├── dashboard/                   # app HTML, CSS y JS + Plotly offline
├── src/                         # pipeline, ML, API, auditoría, fichas
├── analisis/notebooks/          # EDA y análisis territorial
├── ml/notebooks/, modelos/, resultados/
├── datos/raw/{2009,2012,...,2024}/  # ZIP oficiales intactos
├── datos/processed/{año}/, producto/ # panel, perfiles, auditoría
├── samples/                     # CSV sintético listo para probar
├── entregables/fichas/          # 5 PDF de muestra no aprobados
├── docs/                        # metodología, decisiones y próximos pasos
└── tests/                       # controles automatizados
```

## Ciclo de agentes (implementado sin API externa)

`data_agent` valida las métricas → `narrative_agent` redacta texto neutro → `verification_agent` contrasta cifras y expresiones → revisión y aprobación manual en el dashboard → exportación PDF. **No es un LLM autónomo**: es un flujo determinista auditable; la IA generativa externa está pospuesta y no hay publicación automática.

## Límites y advertencias

- Datos **agregados**, no ciudadanos identificables. Los grupos de edad de cada elección no siguen a las mismas personas.
- Los nombres/IDs municipales son un filtro conservador, **no** una correspondencia histórica cartográfica verificada. Ver `docs/07_homologacion_territorial.md`.
- K-Means k=4 tiene mayor silhouette que k=5: los cinco grupos son útiles para demostrar el Reto 1, no una decisión científicamente inmutable.
- El ingreso CSV requiere seis tasas históricas y calidad comparable. No permite clasificar datos nuevos de un único año ni reentrenar sin rehacer el análisis.
- No hay autenticación; ejecutar únicamente en `127.0.0.1`, **no publicar directamente en internet**.
- Las cinco fichas de ejemplo son **BORRADORES NO APROBADOS**; para obtener un PDF revisado usar la interfaz y aprobación humana.
- No produce mensajes partidistas, recomendaciones persuasivas a segmentos demográficos ni marketing político personalizado.

## Documentación principal

1. `analisis/reportes/RESUMEN_EJECUTIVO.md` — análisis histórico.
2. `docs/02_decisiones_metodologicas.md` — elecciones, filtros y modelo.
3. `docs/03_model_card.md` — métricas y riesgos de clustering.
4. `docs/06_producto_dashboard.md` — rutas y contrato CSV.
5. `docs/07_homologacion_territorial.md` — pendientes cartográficos.
6. `docs/08_entrega_y_siguientes_pasos.md` — manual de demo y entrega.

**Fuentes:** <https://ine.mx/transparencia/datos-abiertos/visualizacion-datos/conteos-censales-participacion/> y la convocatoria incluida en `docs/referencias/`.
