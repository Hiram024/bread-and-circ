# HackINE — Plataforma de perfiles estadísticos de participación (Reto 1)

**Aplicación local con cuatro perfiles adoptados en B4, análisis histórico y fichas educativas neutrales.** No es una herramienta oficial del INE. La extracción RAW confiable fue confirmada por Hiram; B2/B3/B4 no la certifican nuevamente.

**Nombre del proyecto: HackINE.** El repositorio sigue en [Hiram024/bread-and-circ](https://github.com/Hiram024/bread-and-circ). Los nombres oficiales de la competencia y las fuentes del INE se conservan; las evidencias históricas de QA mantienen los títulos y rutas registrados en su ejecución. Los documentos y fichas generados a partir del código actual usan HackINE.

Entrada para integrar: [Contrato de integración para Rubén — B4](#contrato-de-integración-para-rubén--b4). Historia y material del informe final: [memoria técnica de Hiram](docs/00_memoria_tecnica_Hiram.md).

## Arranque inmediato en VS Code

**Requisito:** CPython 3.11 y las versiones de `requirements-app.txt`; entorno comprobado Windows/Python 3.11.15. Usa un navegador moderno.

- **Windows:** ejecuta `run.bat`.
- **macOS/Linux:** ejecuta `./run.sh`.
- **Manual:** crea un `venv`, instala `pip install -r requirements-app.txt` y ejecuta `python -m uvicorn src.dashboard_api:app --host 127.0.0.1 --port 8501`.

Abre **http://127.0.0.1:8501**. La primera ejecución instala dependencias desde PyPI; una vez instaladas, la aplicación no depende de servicios externos. `run.*` no cambia ni recalcula las fuentes originales.

Para desarrollo/pruebas instala `pip install -r requirements-b3.txt` en el entorno aislado: incluye app compatible, pytest y httpx. Los notebooks/análisis adicionales usan `requirements.txt`. `src.pipeline` y `src.modeling` son rutas históricas que pueden sobrescribir resultados o entrenar; **no se ejecutan para preparar ni arrancar B4**.

## Lo que contiene

La auditoría independiente **B2 de los CSV procesados** está documentada en
[`docs/10_auditoria_procesados_B2.md`](docs/10_auditoria_procesados_B2.md).
Se repite con `python -m src.validate_processed --root . --out analisis/reportes/b2`
desde un entorno con las dependencias instaladas; conserva los insumos y no entrena.

- **6 elecciones** (2009, 2012, 2015, 2018, 2021, 2024); 54,872,712 registros RAW documentados por la extracción anterior y 73,895 filas municipio × edad verificadas en B2. B2 no recontó los RAW.
- **Panel:** 12,385 unidades municipio × grupo de edad; **8,541 aptas** para clustering exploratorio; **1,825 municipios**.
- **4 perfiles activos**, `StandardScaler` + K-Means; B3 conserva por separado la comparación 4/5/6 y la referencia anterior k=5.
- **Dashboard local** con gráficos, filtros, auditoría municipal, clasificación por CSV y fichas PDF con revisión humana.
- **6 notebooks** de auditoría, historia, territorios, modelo y producto; el notebook de producto se adaptó a B4 y sus salidas anteriores se retiraron, sin presentarlo como reejecutado.
- CSV procesados de seis años y evidencia de extracción anterior. La operación B4 no necesita recuperar ZIP RAW.

## Estructura resumida

```text
HackINE/
├── README.md, requirements.txt, requirements-app.txt, run.sh, run.bat
├── .vscode/                     # configuración y depuración
├── dashboard/                   # app HTML, CSS y JS + Plotly offline
├── src/                         # pipeline, ML, API, auditoría, fichas
├── analisis/notebooks/          # EDA y análisis territorial
├── ml/notebooks/, modelos/, resultados/
├── datos/raw/{2009,2012,...,2024}/  # ZIP oficiales intactos
├── datos/processed/{año}/, producto/ # panel y paquetes; producto_activo.json apunta al activo
├── samples/                     # CSV sintético listo para probar
├── entregables/fichas/{versión}/ # borradores; no reemplazan aprobaciones
├── docs/                        # metodología, decisiones y próximos pasos
└── tests/                       # controles automatizados
```

## Ciclo de agentes (implementado sin API externa)

`data_agent` valida las métricas → `narrative_agent` redacta texto neutro → `verification_agent` contrasta cifras y expresiones → revisión y aprobación manual en el dashboard → exportación PDF. **No es un LLM autónomo**: es un flujo determinista auditable; la IA generativa externa está pospuesta y no hay publicación automática.

## Límites y advertencias

- Datos **agregados**, no ciudadanos identificables. Los grupos de edad de cada elección no siguen a las mismas personas.
- Los nombres/IDs municipales son un filtro conservador, **no** una correspondencia histórica cartográfica verificada. Ver `docs/07_homologacion_territorial.md`.
- B3 seleccionó cuatro por separación, tamaños e interpretación; cinco tuvo algo más de estabilidad entre semillas. La solución sigue siendo exploratoria y sensible a decisiones de calidad/escalado.
- El ingreso CSV requiere seis tasas históricas y calidad comparable. No permite clasificar datos nuevos de un único año ni reentrenar sin rehacer el análisis.
- No hay autenticación; ejecutar únicamente en `127.0.0.1`, **no publicar directamente en internet**.
- Las fichas de ejemplo son **BORRADORES NO APROBADOS**; para obtener un PDF revisado usar la interfaz y aprobación humana vinculada al contenido y versión.
- No produce mensajes partidistas, recomendaciones persuasivas a segmentos demográficos ni marketing político personalizado.

## Documentación principal

1. `analisis/reportes/RESUMEN_EJECUTIVO.md` — análisis histórico, anterior a adopción B4.
2. `docs/02_decisiones_metodologicas.md` — metodología histórica; selección vigente en B3 y adopción en este README.
3. `docs/03_model_card.md` — model card **histórica k5**; descriptor del activo y memoria técnica documentan B4.
4. `docs/06_producto_dashboard.md` — contrato **histórico**; el contrato efectivo B4 está en este README.
5. `docs/07_homologacion_territorial.md` — pendientes cartográficos.

**Fuentes:** <https://ine.mx/transparencia/datos-abiertos/visualizacion-datos/conteos-censales-participacion/> y la convocatoria incluida en `docs/referencias/`.

## Contrato de integración para Rubén — B4

### Decisión, estado y versión

Hiram adoptó localmente el candidato B3 **K-Means k=4, StandardScaler, n_init=30, semilla42**, con las mismas cuatro variables, población y filtros. Esta es una decisión implementada de Hiram para integrar el trabajo; **no afirma aprobación de Rubén**. El reparto sigue siendo datos/modelo/analítica para Hiram y agentes/clasificación/aprobación/PDF para Rubén.

Versión activa: **`ccpc-2009-2024-k4-v1`**. Digest del paquete: `ae5243026dc27552abec02bafaba94819cb49b8dd6877416b79b188fccde1ed4`. `/health`, resumen, CSV, borradores y PDF permiten identificarla. Las cuatro estadísticas de perfiles se recalcularon desde las asignaciones, sin copiar filas del anterior k5 por posición.

B4 fue publicado con autorización de Hiram en **`7e43a2d`** sobre `feat/analysis-dashboard`; B2 y B3 están en `a5794fd` y `6222f79`. **B5 fue publicado con autorización de Hiram en `c3170d9`. B6 permanece local sin commit/push:** hacer pull aún no incorpora la aceptación B6. El estado de QA B4 y sus comandos se documentan en [docs/12_QA_B4.md](docs/12_QA_B4.md); la memoria acumulativa es [docs/00_memoria_tecnica_Hiram.md](docs/00_memoria_tecnica_Hiram.md).

### Dónde vive cada decisión

| Dato/configuración | Campo/símbolo y fuente autoritativa | Consumidores / forma de cambiar |
|---|---|---|
| Referencia activa | `datos/processed/producto_activo.json`: `manifest`, `sha256`; ubicación `POINTER` en `src/product_contract.py` | `load_active(root)` carga un único snapshot validado. Preparar primero, detener servidor, activar con el comando inferior y reiniciar. No editar un archivo de datos suelto. |
| Identidad, k, features/orden, años, filtros, compatibilidad y archivos | `datos/processed/producto/ccpc-2009-2024-k4-v1/manifest.json` | Descriptor inmutable generado por `src.prepare_product`; valida hashes y coherencia antes de exponer el paquete. `VERSION` solo es el valor inicial del constructor; el runtime lee el descriptor. |
| Modelo/escalador/mapeo | Entrada `files.artifact` del descriptor; bundle `model`, `scaler`, `features`, `k`, `label_mapping`, `filters` | API/CSV. El builder copia el candidato B3 comprobado; no entrena. Cambiarlo requiere evaluación nueva y una versión coherente. |
| Nombres y estadísticas activas | Entrada `files.profiles`, campos de `perfiles.json` | Consulta, UI, agentes y PDF. Se generan desde B3 y se verifican contra observaciones/modelo; no se mantienen listas `LABELS` paralelas. Renombrar requiere nuevo paquete/revisión. |
| Asignaciones y municipio/edad | Entrada `files.observations`, `observaciones_dashboard.csv` | Filtros/API; unicidad entidad+municipio+edad, predicciones reconciliadas por clave con B3. |
| Resumen/serie nacional/auditoría | Entradas `files.metadata`, `files.national`, `files.territory_audit` | `metadata()` y vistas. Las copias derivadas de k/version/perfiles se generan y validan, no se editan manualmente. |
| Fórmulas de inferencia | `src/dashboard_api.py:classify_dataframe`, orden `FEATS` de `src/modeling.py` contrastado contra descriptor/bundle | Seis tasas → cuatro features. Identificadores, edad, nombre y sexo no entran al modelo. Cambios de fórmulas requieren volver a evaluar, no editar una variable y seguir. |
| Textos educativos | `src/education.py:data_agent`, `narrative_agent`, `verification_agent` | `build_draft(profile, package_digest)`. k/nombre/versión vienen del perfil activo. Cambiar texto cambia el digest del borrador e invalida revisión anterior. |
| Persistencia | `src/dashboard_api.py:DB_PATH`; por defecto `entregables/revision_local.sqlite3`; env `CCPC_REVIEW_DB` solo para aislamiento/ruta explícita | Historial local, sin publicación. Migración aditiva y respaldo SQLite antes de cambiar esquema anterior. No borrar para obtener tests verdes. |
| Entorno y arranque | `requirements-app.txt`, `run.bat`, `run.sh`; versiones efectivas en B3 lock y QA B4 | Bibliotecas matemáticas fijadas al entorno1.8.0; tests en `.venv`. El loader rechaza versión incompatible, no silencia warnings. |

La autoridad de ejecución es el snapshot señalado por el descriptor. Los archivos k5 que siguen directamente en `datos/processed/producto/` son **referencia histórica**, no el activo. No consumirlos por una ruta antigua. Para Python:

```python
from pathlib import Path
from src.product_contract import load_active
p = load_active(Path('.'))
print(p['package_version'], p['manifest']['k'])
profiles = p['profiles']   # dict por perfil_id
observations = p['data']  # DataFrame del mismo paquete
bundle = p['artifact']    # escalador/modelo/mapeo del mismo paquete
```

El loader comprueba entorno, SHA-256, IDs, predicciones de todas las filas y estadísticas. `dashboard_api.package()` lo cachea **una vez**: cambiar el puntero no invalida mágicamente el proceso ni `lru_cache`. No hay selector de modelos ni recarga parcial de archivos.

### Datos y unidades del contrato

| Campo | Tipo / obligatoriedad | Significado y ejemplo real comprobado |
|---|---|---|
| `perfil_id` | entero requerido; 1–4 en esta versión | ID local del perfil. Perfil1 tiene 1,840 unidades; no significa que un ID1 futuro o anterior sea la misma población. |
| `nombre` / `perfil_nombre` | texto requerido | Nombre descriptivo del perfil / copia derivada en observaciones y CSV. No atribuye motivaciones individuales. |
| `package_version` | texto requerido | `ccpc-2009-2024-k4-v1`, fijo para ese contenido; nunca timestamp nuevo al arrancar. |
| `package_digest` | SHA-256 hexadecimal, 64 caracteres | Identifica bytes del descriptor, que enlaza hashes de los archivos; aparece en metadatos/CSV/borrador. No certifica origen oficial. |
| `n_unidades` | entero requerido | 1,840 en perfil1; filas municipio×edad, no ciudadanos. |
| `municipios` | entero requerido | 837 en perfil1; municipios pueden aparecer en varios perfiles por edades, no sumar entre perfiles. |
| `lista_nominal_2024` | entero requerido | LN 2024 sumada; 27,693,625 en perfil1. |
| `porcentaje_unidades` | número requerido, % | 21.543144830816065 en perfil1; denominador8,541 unidades elegibles. |
| `edad_predominante` | texto requerido | `18-24` para perfil1; descriptor agregado, no feature. |
| `media_presidencial`, `media_intermedia` | números requeridos, % escala0–100 | Medias simples de tasas; perfil1: 48.44176823940163 y 35.72189919163344. No se ponderan por LN. |
| `cambio_presidencial_pp`, `cambio_intermedia_pp` | números requeridos, pp | Diferencias entre extremos del mismo tipo; perfil1: −7.578960804751601 y +6.377071254945573. |
| `brecha_pres_intermedia` | número requerido, pp | Diferencia de medias; perfil1: 12.71986904776819. Descriptiva, **no quinta feature**. |
| `EDOCVE`, `MPIOCVE`, `grupo_edad` | clave compuesta requerida en observaciones | Entidad+municipio+edad, nunca municipio solo ni unión por nombre. `clave_municipal` preserva representación `01-001`. |
| `distancia_centroide` | número derivado no negativo | Distancia en espacio escalado, no probabilidad ni confianza de predicción individual. |

Nombres/IDs y tamaños activos:

| ID | Nombre | Unidades |
|---|---|---:|
| 1 | Menor participación media; descenso presidencial | 1,840 |
| 2 | Crecimiento medio en ambos tipos de elección | 2,155 |
| 3 | Participación media; descenso presidencial | 2,511 |
| 4 | Mayor participación media; cambio presidencial cercano a cero | 2,035 |

La correspondencia [B3 activo5/candidato4](ml/resultados/b3/correspondencia_activo_candidato.csv) no es un simple renombre: antiguo1→nuevo1 conserva1,351/1,366; antiguo3→nuevo3,1,940/1,964; antiguo4→nuevo2,1,184/1,259; antiguo5→nuevo4,1,941/2,080. Antiguo2 se reparte principalmente479/942/446 entre nuevos1/2/3. ARI=0.636450 mide similitud de particiones, **no porcentaje de coincidencia**.

### Features y clasificación CSV

Orden inmutable del vector: `media_presidencial`, `media_intermedia`, `cambio_presidencial_pp`, `cambio_intermedia_pp`.

1. `(tasa_2012 + tasa_2018 + tasa_2024) / 3`, %.
2. `(tasa_2009 + tasa_2015 + tasa_2021) / 3`, %.
3. `tasa_2024 - tasa_2012`, pp.
4. `tasa_2021 - tasa_2009`, pp.

`POST /api/classify`: multipart, campo `file`, extensión `.csv`. Requiere `tasa_Y`, `observados_Y`, `ns_pct_Y` para **cada** Y=2009/2012/2015/2018/2021/2024. Valores finitos/no nulos; tasas0–100, observados enteros≥100, NS0–20%. De1 a5,000 filas, máximo2,000,000 bytes. `unidad_id` y `grupo_edad` son columnas descriptivas opcionales para el CSV de inferencia; no se incorporan al vector ni se acredita equivalencia territorial de datos nuevos por recibirlas.

Respuesta CSV conserva entradas y agrega las cuatro features, `perfil_id`, `perfil_nombre`, `package_version`, `package_digest`, `distancia_centroide`, `nota`. Cabeceras `X-Row-Count` y `X-Package-Version`. Texto aportado por usuario se protege contra fórmulas de hoja de cálculo. Archivo no se guarda ni se usa para entrenar.

Ejemplo real de `/api/template`: tasas `[43.5,61,45.5,63,52,60]` en orden de años, observados300 y NS5% en todos. Se obtuvo vector `[61.333333333333336,47,-1,8.5]`, perfil3 `Participación media; descenso presidencial`, distancia1.0383266279127885, versión actual. Evidencia completa: `analisis/reportes/b4/ejemplos_contrato.json`.

Errores: extensión400, tamaño413; columnas/años/valores/filas inválidos422. `/api/observations?perfil=5` y `/api/draft/5` devuelven404: no se ofrece un quinto perfil inexistente.

### Borrador, confirmación y PDF

`GET /api/draft/{id}` conserva `facts`, `draft`, `validation`, `agent_steps`, `requires_human_approval=true`, `automated_publication=false`; añade `package_version`, `package_digest`, `draft_digest`. El digest canónico incluye ID, versión/digest del paquete, facts y draft; excluye `validation.checked_at`, que cambia en cada verificación y no es contenido revisado.

`POST /api/approve` requiere JSON:

```json
{
  "profile_id": 1,
  "reviewer": "Nombre de quien realmente revisa",
  "confirmed": true,
  "package_version": "ccpc-2009-2024-k4-v1",
  "package_digest": "ae5243026dc27552abec02bafaba94819cb49b8dd6877416b79b188fccde1ed4",
  "draft_digest": "5523c0c8d4bb5b6d21102f945bc43ad0f509e24b026cb6e3d99b6f7ecd6bea23"
}
```

Es el token real observado para el borrador1 en esta entrega; **el cliente debe usar los tokens del borrador que acaba de mostrar**, no copiar permanentemente este ejemplo ni enviar confirmed=true sin revisión humana. Revisor≥3 caracteres tras quitar espacios. Falta de confirmación400; token/versión/contenido o perfil mostrado distinto409; esquema incompleto422. La UI invalida el borrador y desmarca revisión al cambiar perfil. La API comprueba los tokens otra vez; no confía solo en la interfaz.

Una respuesta aprobada incluye `approval_id`, `profile_id`, `reviewer`, `reviewed_at`, `package_version`, `draft_digest`, `download_url`. `GET /api/approved-pdf/{approval_id}` solo regenera si paquete y contenido siguen coincidiendo; PDF incluye versión, datos, revisor/fecha y digest. Se revisó texto y legibilidad, no solo `%PDF-`.

**Política histórica mínima, sin snapshots inventadas:** las aprobaciones anteriores sin versión quedan heredadas/no verificables y exportar su PDF devuelve409 explicativo. Las nuevas también se bloquean si cambia paquete o texto; se conserva la fila y se exige nueva revisión, sin regenerar estadísticas nuevas bajo aprobación vieja. No hay selector histórico ni reimpresión de contenido antiguo sin snapshot suficiente. Una migración aditiva agrega `package_version`/`package_digest`, con backup consistente `.pre-b4-*.bak` y ejecución repetible. Las filas viejas no se asignan automáticamente a k4. En esta laptop no había SQLite real al inicio de B4; se probó migración con bases temporales antiguas y nuevas.

### Arranque, preparación y cambios controlados

Windows: `run.bat` desde la raíz instala requirements compatibles en `.venv` y arranca únicamente localhost8501. Se comprobó ese comando real. Si no hay entorno, usa CPython3.11 mediante `py -3.11` o el CPython administrado que ya exista; no uses el Python MSYS2 como sustituto del CPython Windows. En VS Code selecciona `.venv/Scripts/python.exe`.

```powershell
# Instalación de operación; para tests instalar requirements-b3.txt en vez de app únicamente.
& .\.venv\Scripts\python.exe -m pip install -r requirements-app.txt
# Preparar y validar: NO activa, NO entrena.
& .\.venv\Scripts\python.exe -B -m src.prepare_product --root .
# Detener servidor conocido con Ctrl+C antes de adoptar; luego cambiar solo referencia validada.
& .\.venv\Scripts\python.exe -B -m src.prepare_product --root . --activate
cmd /c run.bat
```

Arranque manual equivalente: `& .\.venv\Scripts\python.exe -B -m uvicorn src.dashboard_api:app --host 127.0.0.1 --port 8501`. macOS/Linux usa Python3.11 y `run.sh`; Docker sigue instalando requirements compatibles, pero esas alternativas no se ejecutaron en esta laptop Windows.

Si regeneras sin cambios, el paquete existente se verifica y conserva. Si los bytes cambiaran con la misma identidad, la preparación rechaza la operación. Para **renombrar**: crea un JSON de cuatro objetos `{ "perfil_id": 1, "nombre": "..." }` (IDs completos/únicos), y prepara una identidad nueva, sin tocar los archivos históricos B3:

```powershell
& .\.venv\Scripts\python.exe -B -m src.prepare_product --root . --version ccpc-2009-2024-k4-v2 --names ruta/nombres_v2.json
# Revisar paquete y pruebas antes de repetir el mismo comando con --activate y reiniciar.
```

Clasificación de cambios:

- **Nombre:** editar el JSON de nombres de la nueva entrega; regenerar perfiles/observaciones/metadatos/manifest y usar nueva versión. No reutilizar confirmaciones o PDFs antiguos.
- **Texto educativo:** editar `narrative_agent` y repetir verificación negativa, borradores, tokens/PDF y QA visual. El digest cambia aunque no cambie la geometría del modelo; exige nueva revisión. Documentar la revisión del código.
- **Rutas/metadatos:** modificar el constructor y generar/verificar una versión coherente, no apuntar el modelo nuevo a perfiles viejos. No mantener rutas activas paralelas en API/notebook.
- **Modelo/k, features/orden, escalado o filtros:** requiere evaluación/entrenamiento acordado y nueva entrega integral. No basta editar `k` o un umbral del manifest; el loader rechaza discrepancias. `prepare_product` B4 no entrena ni adopta candidatos distintos del B3 comprobado.

`python -m src.build_delivery` exporta únicamente borradores del activo a `entregables/fichas/{package_version}/`. `src.technical_report` lee perfiles activos y separa resultados históricos; el informe final completo se revalidará antes de entrega. El generador histórico `src.generate_docs` se niega a sobrescribir README/model card cuando existe el puntero B4. Los notebooks históricos conservan su significado; el06 de producto lee `load_active` y quedó explícitamente sin salidas ejecutadas de B4.

Pruebas completas, sin seleccionar solo las nuevas:

```powershell
$qaTemp = Join-Path $env:TEMP ('ccpc-tests-' + [guid]::NewGuid().ToString('N'))
& .\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider --basetemp $qaTemp tests
Invoke-RestMethod http://127.0.0.1:8501/health
```

Los tests usan SQLite temporal, nunca el historial real. Para un servidor QA separado puede fijarse `CCPC_REVIEW_DB` a un archivo temporal y otro puerto. Scripts/comandos de navegador y PDF están en el informe QA; PDFium es una herramienta temporal de QA, no dependencia de la app. `.gitattributes` evita conversiones Git LF/CRLF que invaliden hashes del paquete/evidencias después de pull; no ejecutar renormalizaciones indiscriminadas sobre datos auditados.

### Recuperación y checklist después de pull

Referencia anterior recuperable: commit `6222f79dadc51f35735fbffd0c92425f8e2673cb`, artefacto `ml/modelos/kmeans5_exploratorio.joblib` (SHA256 `af0a33a52e75dc5370844c799cb347a7c276491ed938f0fa11f396f316741a98`) y CSV/JSON k5 originales directamente en `datos/processed/producto/`. Se preservaron, no se crearon copias repetidas del paquete histórico.

Para comprobar o recuperar la referencia, exportar **ese commit completo con `git archive` a un directorio temporal nuevo**, usar Python/sklearn compatibles y arrancar la app anterior en puerto distinto y con historial temporal. Se probó esa recuperación real. No cambiar solo la ruta al modelo k5 dentro del runtime B4 ni hacer reset/clean/checkout forzado sobre trabajo pendiente. Para volver operacionalmente, detener el servidor, operar desde la copia completa recuperada con sus metadatos coherentes y conservar aparte SQLite/evidencia; sus aprobaciones no se trasladan automáticamente entre versiones. No borrar filas para volver atrás.

Después de la publicación autorizada y pull, Rubén debe:

1. Confirmar rama, versión esperada, estado Git y dependencias del entorno aislado.
2. Consultar `/health`: k4, 8,541 observaciones, versión/digest anteriores; revisar cuatro opciones y sus nombres.
3. Ejecutar suite completa y comparar el CSV de ejemplo con el modelo real.
4. Mostrar/revisar borrador nuevo y enviar su token; probar rechazo al cambiar selección/contenido. Usar DB temporal para el ensayo, no crear aprobaciones ficticias reales.
5. Revisar PDF con versión, cifras, revisor/digest y confirmar política de heredados; consultar informe QA.
6. Coordinar cualquier modificación de contrato con Hiram. El contrato ya está implementado localmente, pero no se presume que Rubén haya aprobado estas decisiones.

Quedan límites de separación moderada, sensibilidad, selección territorial/etaria desigual y geografía nominal. El diagnóstico temporal previo es retrospectivo condicionado a elegibilidad de seis años, no validación temporal independiente. B5 visual, despliegue, autenticación, cartografía y modelos nuevos quedan fuera de B4.

## Dashboard analítico — B5, camino B

B5 amplía la presentación y la consulta analítica sobre **el mismo paquete B4**. No entrena, cambia filtros ML, nombres o asignaciones, ni modifica agentes, clasificación, aprobaciones o PDF. Es una decisión implementada de Hiram para integración; no presupone aprobación de Rubén. QA y resultados finales: [docs/14_QA_B5.md](docs/14_QA_B5.md); diagnóstico y ejecución: [docs/13_dashboard_analitico_B5.md](docs/13_dashboard_analitico_B5.md).

Recorrido: **Panorama → Perfiles → Explorador → Auditoría**. CSV y Fichas conservan su acceso. Los filtros pertenecen solamente al explorador: no cambian las cifras nacionales, perfiles completos o auditoría. «Explorar Pn» cambia explícitamente el filtro de perfil y conserva los otros criterios visibles; no cambia el perfil ni contenido de una ficha revisada.

### Indicadores, fórmulas y universos

| Indicador / visualización | Fuente autoritativa | Cálculo y unidad | Universo / filtros |
|---|---|---|---|
| Historia nacional, gráfica y tabla | `files.national` del manifest activo; totales reconciliados con B2 | `100*SV/(SV+NV)` por año, SV/NV ya sumados nacionalmente. NS/LN en %. Denominador cero → nulo. No media de tasas municipales. | Agregado nacional procesado de cinco edades; sin filtros. `filas` en esta fuente es microfilas documentadas, no unidades: no se usa como contador del panel. |
| Hallazgos de Panorama | Mismas tasas de la historia nacional | Última menos primera elección de cada tipo, en pp: 2024−2012 y 2021−2009. Se calculan al renderizar. | Nacional procesado, no selección modelada. Sin causalidad. |
| Panel, elegibles, municipios, cobertura LN | `files.metadata`; complemento B2 validado en Auditoría | Panel 12,385; elegibles 8,541; municipios distintos por entidad+municipio 1,825. LN elegible2024 / LN nacional procesada2024. | No ciudadanos clasificados; municipio representado puede tener solo algunas edades aptas. |
| Tamaños de perfiles | `files.profiles` contrastado con `files.observations` por loader B4 | Unidades y `100*n/8541`; municipios entre perfiles no son disjuntos. | Todas las elegibles; sin filtros. |
| Nivel de perfiles | Mismas fuentes del paquete | Media por unidad 2012/2018/2024 o 2009/2015/2021, luego media simple entre unidades de cada perfil; %. | Sin ponderar por población/observados; no tasa nacional. |
| Cambios de perfiles | `cambio_presidencial_pp`, `cambio_intermedia_pp` del perfil | Media simple de 2024−2012 y 2021−2009; pp. Tabla, etiquetas y barras con cero visible. | Mismos perfiles; no variación porcentual relativa ni evolución individual. |
| Tabla del explorador | `files.observations` | Filas ordenadas por `(EDOCVE,MPIOCVE,grupo_edad)`, 100 por página. Rango visible separado del total. | Todas las elegibles que cumplen entidad, perfil, edad y búsqueda literal municipal; combinaciones AND. |
| Resumen de selección | `analytics` de `/api/observations`, antes de paginar | Conteos de unidades/municipios, suma LN2024, medias simples de las cuatro variables y distribución por perfil. | **Todas** las coincidencias, nunca solo la página. Sin coincidencias: conteos0, medias nulas. |
| Detalle de unidad | Mismo `items` de la consulta, identificado por clave compuesta | Seis tasas %, observados SV+NV por año, cambios pp, LN2024 y máximo NS %. | Una unidad municipio×edad. Se invalida al filtrar/paginar; no unión por posición o nombre. |
| Cobertura / exclusiones | B2 `resultados.json`, `cobertura.csv`, `elegibilidad_y_causas.csv` y selección por edad/entidad, vinculados mediante `analisis/reportes/b5/fuentes_auditoria.json` | Numerador/denominador y %. Excluidas únicas3,844. Causas superpuestas y combinaciones presentes; estas últimas suman3,844. | Panel12,385 / municipios2,477 / LN nacional2024 de cinco edades98,330,348, según fila. Sin filtros del explorador. |
| Identidad nominal | `files.territory_audit` del paquete | Conteos por estado de identidad y hasta50 ejemplos no estables; no cobertura de edades. | 2,477 claves municipales. No certifica fronteras históricas constantes. |

Las tablas dan valores accesibles sin depender de hover o color. Presidencial e intermedia usan nombres, círculos/rombos y trazos diferentes. Las tasas nulas dicen **«Sin dato»**, no0%. El explorador limpia resultados anteriores durante carga/error y aborta/invalida respuestas antiguas incluso mientras espera el debounce de búsqueda.

### Ampliación compatible de API para Rubén

`GET /api/observations` conserva `total`, `items`, `package_version` y las columnas previas. Añade los campos siguientes, sin cambiar inferencia ni contrato de fichas:

| Parámetro | Tipo y validación | Default |
|---|---|---|
| `estado` | entero opcional,1–32; no etiqueta/nombre | sin filtro |
| `perfil` | entero opcional, ID existente en el paquete; inexistente404 | sin filtro |
| `edad` | texto opcional: `18-24`, `25-34`, `35-44`, `45-59`, `60+`; otra etiqueta422 | sin filtro |
| `q` | texto de hasta120 caracteres, búsqueda literal sin regex, insensible a mayúsculas en MPIONOM | vacío |
| `limit` | entero1–500 |100|
| `offset` | entero≥0 |0|

Respuesta: `total:int`, `offset:int`, `limit:int`, `package_version:str`, `items:list`, `analytics:object`. Orden estable por clave. Offset más allá del total devuelve `items:[]` y mantiene total/resumen del universo; el cliente evita navegar fuera de rango. `items` añade `EDOCVE:int`, `MPIOCVE:int`, `LN_2024:int`, `max_ns_pct:number` y `observados_<año>:number`. `clave_municipal` conserva ceros a la izquierda; tasas nulas se serializan como JSON `null`. `analytics` contiene `unidades:int`, `municipios:int`, `lista_nominal_2024:int`, `medias:{<cuatro features>:number|null}`, `perfil_conteos:[{perfil_id:int,unidades:int}]`, `historico:[{anio:int,tipo:str,media_tasa_pct:number|null,unidades_con_tasa:int}]`. Sus medias son simples entre unidades, no ponderadas ni nacionales.

Ejemplo real: `/api/observations?estado=2&edad=18-24&limit=2` devuelve total5,offset0,limit2; analytics5unidades/5municipios, LN2024=446745, medias presidencial44.65497528168656 e intermedia25.834164362249954; primera clave `(2,1,"18-24")`, `clave_municipal:"02-001"`. Cambiar offset no cambia `analytics`. Respuestas completas efectivamente ejecutadas: `analisis/reportes/b5/ejemplos_api.json`. Búsqueda literal sin coincidencias devuelve200,total0,itemsvacíos,mediasnull. Tipos/rangos/edades inválidos devuelven422; perfil inexistente404.

`GET /api/analysis-audit` es **nuevo y separado**: devuelve panel/elegibles/excluidas únicas, cobertura con numerador/denominador/porcentaje/universo, causas, combinaciones, selección por edad/entidad y las huellas de las fuentes B2. Valida hashes de evidencia e insumos procesados B2, claves elegibles exactas frente al snapshot, totales/tasas nacionales y denominadores. Si cambia alguna fuente o el paquete ya no corresponde: **503**, sin presentar cobertura anterior como vigente. No reemplaza el manifest ni agrega silenciosamente archivos al paquete. Se cachea una vez, igual que el snapshot: reiniciar el proceso después de cambios deliberados; cualquier nuevo paquete necesita una nueva reconciliación y vínculo B2, no editar cifras para que pase.

`GET /api/documentation/{name}` sirve texto UTF-8 de una lista fija: `b2`, `b3`, `metodologia` (histórico), `memoria`, `contrato` (este README). Nombres desconocidos404; no acepta rutas arbitrarias. OpenAPI de FastAPI sigue disponible localmente en `/openapi.json` y `/docs`. No se creó una colección/Postman workspace ni servicio adicional: pytest/TestClient y navegador ejercitan la API local existente.

### Ubicación de decisiones y cambios posteriores

- Datos/modelo/nombres/umbrales: manifest y builder B4, sin modificaciones B5. Cambiarlos exige proceso de evaluación/adopción y nuevo paquete/revisión conforme a B3/B4.
- Filtros/agregaciones/nacional/auditoría: `src/analytics.py`; rutas y límites de consulta en `src/dashboard_api.py`. `AGES` centraliza categorías aceptadas en backend. No agregar reglas de elegibilidad visuales divergentes.
- Presentación: `dashboard/index.html`, `dashboard/static/app.js`, `app.css`; los nombres/valores se leen de la API. Cambios de diseño, formato, títulos o símbolos no requieren entrenar. Las cuatro variables no se duplican como cifras sueltas en JS.
- La identidad editorial de fichas permanece en `src/education.py`; B5 no modifica sus textos ni digests. Una modificación futura sí requiere revisión nueva conforme a B4.
- `fuentes_auditoria.json` registra hashes de los reportes B2 utilizados y digest del paquete. Los hashes dan trazabilidad de esta vinculación, no certifican procedencia oficial. No ejecutar pipeline/modeling/prepare_product para iniciar B5.

Arranque sin cambios: `cmd /c run.bat`, o `.\.venv\Scripts\python.exe -B -m uvicorn src.dashboard_api:app --host 127.0.0.1 --port 8501`. Detener y reiniciar el proceso conocido después de editar backend; no mezclar frontend B5 con API B4 cacheada. Si8501 está ocupado, identificar primero el proceso o usar otro puerto local, sin matar servicios desconocidos.

Suite completa reproducible desde la raíz (PowerShell):

```powershell
$qaB5Temp = Join-Path $env:TEMP ('ccpc-b5-tests-' + [guid]::NewGuid().ToString('N'))
& .\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider --basetemp $qaB5Temp tests
# Chrome/Playwright ya existentes en esta laptop; servidor y SQLite temporales propios.
& .\.venv\Scripts\python.exe -B analisis\reportes\b5\qa_browser_run.py
```

El segundo comando requiere las herramientas externas de QA descritas en el informe; no son dependencias de app. Las pruebas no usan ni limpian el historial SQLite real. Los resultados finales y límites se leen en el informe QA, sin confundirlos con la referencia histórica de25testsB4. Al cerrar B5 esos controles quedaron pendientes. B6 ejecuta aceptación analítica/zoom/teclado en el entorno local; B7 conserva la revisión conjunta con Rubén. Otros navegadores/sistemas y notebook pertenecen a compatibilidad/reproducibilidad, y el informe técnico visual completo a B8/B10. B5 fue publicado en `c3170d9`; B6 aún no.

## Aceptación analítica — B6, camino B

**B6: COMPLETADO CON ADVERTENCIAS. QA independiente: APROBADO CON ADVERTENCIAS no bloqueantes.** Resultado autoritativo: [aceptación B6](docs/15_aceptacion_analitica_B6.md) y [dictamen qa_b6](docs/16_QA_B6.md). B6 parte deB5publicado `c3170d9`; sus propias modificaciones siguen locales sin commit/push. Hiram implementa correcciones acotadas/documentación; no se asume aceptación deRubén.

Contrato B4/B5 **sin cambios**:mismos endpoints,campos,paginación,filtros,paquete,nombres,modelo y aprobación vinculada a versión/contenido. Corrección de presentación en `dashboard/static/app.js`:la versión Plotly3.3.1local ignoraba `axis.title` como cadena;se cambia a `{text:...}` en historia nacional/detalle,distribución,medias y cambios. Se comprobarán los títulos efectivamente renderizados, no solo strings del código. Referencias oficiales:[ejeY](https://plotly.com/javascript/reference/layout/yaxis/#layout-yaxis-title-text) y [ejeX](https://plotly.com/javascript/reference/layout/xaxis/#layout-xaxis-title-text). No se actualizó Plotly ni se añadieron dependencias. Además, `app.css` permite desplazamiento vertical propio del menú (`.sidebar{overflow-y:auto}`): al zoom200% los botones inferiores antes quedaban fuera de la ventana aun recibiendo foco. QA comprobó nuevamente que los seis controles enfocados entren en la vista. Recargar la página para obtener el JS/CSS actual.

Reconciliación:el reporte histórico de cuatro causas suma4820incidencias;la evidencia B2/B5 de cinco causas suma4930porque añade110por conteos/NSausentes. Las110ya están excluidas por otras causas;la unión continúa3844y las8541elegibles coinciden por clave. «Existe observado<100» cuenta863;«no cumple seis observados>=100» cuenta952porque incluye faltantes (110con ausencias,21también<100). No se redefine una causa histórica ni se confunde ausencia de desglose con cero. Tabla/versiones/fórmulas y casos identificables en el informe15 y `analisis/reportes/b6/reconciliacion_causas.csv`/`casos_faltantes.csv`.

La matriz `analisis/reportes/b6/matriz_trazabilidad.csv` une fuente,universo,fórmula,ponderación,unidad,precisión,endpoint/campo,componente,filtros,esperado independiente,observado,diferencia/tolerancia y estado. Las tasas se recalculan de los seis CSVanuales;los perfiles desde esas tasas y asignaciones por clave. La capa de pantalla requiere además la evidencia del navegador deqa_b6;el CSVnumérico no la sustituye.

Comprobación de lectura con la app local ejecutándose:

```powershell
& .\.venv\Scripts\python.exe -B analisis\reportes\b6\verificar_trazabilidad.py --root . --out analisis/reportes/b6 --base-url http://127.0.0.1:8501
$qaB6Temp = Join-Path $env:TEMP ('ccpc-b6-tests-' + [guid]::NewGuid().ToString('N'))
& .\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider --basetemp $qaB6Temp tests
```

El verificador solo haceGET/lecturas y escribe su evidencia;no entrena ni regenera paquetes. Código distinto de0indica discrepancia/fallo;el JSONregistra fecha/zona,base,versiones,comando y hashes. Arranque manual si fuera necesario:`.\.venv\Scripts\python.exe -B -m uvicorn src.dashboard_api:app --host 127.0.0.1 --port 8501`;no iniciarlo encima de otro proceso del mismo puerto. Herramientas/ejecuciones de Chrome y zoom real200%,teclado y límites de lector de pantalla se describen enQA16;no se presentan cambios deviewport como zoom.

Pendientes separados:B7revisión y aceptación conjunta conRubén;B8/B10documento técnico y QAvisual final;B9ensayo de presentación;reproducibilidad/cierre para notebook y otros entornos requeridos. B6no exige aprobación deRubén para cerrar ni termina esos bloques. Lector de pantalla no probado,otros navegadores/sistemas y límites metodológicos se registran sin declarar conformidadWCAG ni validez científica definitiva.

Propuesta de commit B6,no ejecutado:`fix: complete analytical acceptance and restore chart and zoom accessibility`.

## Cierre B6 — aceptación con advertencias

**B6: COMPLETADO CON ADVERTENCIAS. qa_b6:APROBADO CON ADVERTENCIAS no bloqueantes en integración.** La suite completa posterior a las dos correcciones ejecutó **32passed,1advertencia previa Starlette/httpx,exit0**, sin cambiar los31tests anteriores y con un grupo nuevo B6justificado. La matriz numérica ejecutada devuelve135pasa,0fallas;no cambia elegibilidad ni contrato. Los registros `qa_integration_tests.txt`/`qa_integration_state.json` distinguen este resultado de la pasada final formal posterior al cierre documental.

Navegador real Chrome156:cuatro vistas100/200con zoom real de navegador,teclado,filtros,paginación/detalle,títulos/unidades de ejes y los seis botones del menú enfocados dentro deviewport. Regresión del harness B5contra código actual con salida B6:CSVválido/inválido,asincronía/error/nulos/HTML,revisión/aprobación/PDFy rechazo de versión obsoleta,anchos1440/390,exit0. CeroerroresJS y cero solicitudesexternas durante esos recorridos. Las capturas finales de zoom utilizan CDPsololectura,no una imagen recortada del harness. Datos/modelo/paquete/historial permanecen intactos;no se creóSQLite real.

La pasada formal final se ejecuta después de este cierre documental,con todos los archivos del principal congelados. Sus resultados,comandos,tiempos,huellas del estado exacto y revisión visual autoritativa están en `docs/16_QA_B6.md` y `analisis/reportes/b6/qa_final_resultados.json`, `qa_final_state.json`, `qa_final_pytest.txt`, `qa_final_browser.txt` y `qa_visual_final.json`. El informe QA se excluye de autorreferencia,pero incluye el estado de documentación del principal. Cualquier fallo de esa pasada exige corrección y comprobación correspondiente;no se transforma en éxito por este texto.

Límites no bloqueantes:lector de pantalla no ejecutado,otros navegadores/sistemas no probados,deprecación previa Starlette/httpx y favicon404heredado. Las respuestas422delCSVinválido son negativos esperados. No se afirma conformidadWCAG ni certificación científica del clustering. B7mantiene revisión conjunta conRubén;B8/B10documento técnico/QAvisual final;B9ensayo;reproducibilidad/cierre para notebook y otros entornos requeridos. No se declara su aceptación por asociación.

No se hizo commit,push,merge,PR ni publicación. Propuesta en inglés Conventional Commits:`fix: complete analytical acceptance and restore chart and zoom accessibility`.
