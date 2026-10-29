# Memoria técnica acumulativa de Hiram — Hackathon INE, Reto 1

Este documento reúne decisiones, trabajo realizado y material reutilizable para el informe final. **No sustituye las tablas de evidencia ni certifica el origen RAW.** Fecha de cierre del bloque B4: 28/10/2026, zona America/Tijuana; los timestamps y hashes de cada ejecución están en sus reportes. La historia conserva la referencia k5: no se reescribe como si siempre hubieran existido cuatro perfiles.

## Objetivo, contribuciones y alcance

El proyecto describe perfiles estadísticos de participación electoral en agregados municipio × grupo de edad para seis elecciones federales. No identifica ciudadanos, no estima intención de voto individual y no interpreta agrupaciones como causas o tipos esenciales de personas.

Según el contexto aportado por Hiram, **la base previa fue aportada por Rubén**: pipeline, aplicación, modelos/fichas iniciales y documentación preceden a estos bloques. Esta memoria no atribuye todo el proyecto a Hiram. El reparto acordado es datos, modelo y vistas analíticas para Hiram; agentes, clasificación CSV, aprobación y PDF para Rubén. B4 autoriza a Hiram a hacer ajustes mínimos de integración en esas piezas y a implementar decisiones de contrato, **sin afirmar que Rubén las aprobó**. No se enviaron mensajes a terceros.

El trabajo documentado de Hiram comprende ejecución/preparación de B1, auditoría independiente B2, comparación controlada B3 y adopción local B4, con QA delegado exclusivamente a pruebas. No se hizo B5 visual ni despliegue.

## Fuentes, unidad y preparación

Fuente declarada: Conteos Censales de Participación Ciudadana (CCPC) del INE, 2009, 2012, 2015, 2018, 2021, 2024. La extracción original confiable fue confirmada por Hiram. Los 54,872,712 microregistros, incidencias, diccionarios y hashes de ZIP descritos por la extracción anterior son **evidencia heredada**, no un recuento RAW nuevo de B2/B3/B4.

La clave nacional es `(EDOCVE, MPIOCVE)`; MPIOCVE solo no identifica un municipio nacionalmente. La unidad analítica agrega esa clave con edad: 18–24, 25–34, 35–44, 45–59 y 60+. La serie añade año. No se une por nombre ni se reincorporan unidades por similitud ortográfica.

- `LN = SV + NV + NS`; observados=`SV+NV`.
- Participación observada=`100*SV/(SV+NV)`, excluyendo NS del denominador. NS no se convierte en abstención.
- `ns_pct=100*NS/LN`. Denominadores cero producen tasa indefinida, no cero.
- Elegibilidad: seis tasas válidas, identidad nominal estable, observados≥100 y NS≤20% en cada año. Se comprueban ausencias antes de mínimos/máximos.
- Identidad nominal es un filtro conservador: nombres iguales no acreditan geometría histórica. Los grupos etarios son cortes transversales, no cohortes rastreadas.

Presidenciales: 2012/2018/2024; intermedias: 2009/2015/2021. El vector, sin pesos poblacionales, contiene en ese orden: media presidencial; media intermedia; tasa2024−tasa2012; tasa2021−tasa2009. Las dos medias se expresan en % y los cambios en pp. Brecha y curvaturas son descriptivos, no nuevas features.

## Registro de bloques y procedencia de resultados

| Bloque | Estado/resultado | Versión, fecha y evidencia |
|---|---|---|
| B1 | Entorno, ejecución inicial, recuperación del historial Git de la copia local y rama de trabajo. Aplicación inicial k5 ejecutada sin cambiar sus datos. | Resultado de la sesión anterior comunicado; B4 verificó checkout efectivo, entorno y servicio antes de adoptar. No es auditoría RAW ni autoría de la base. |
| B2 | APTO CON ADVERTENCIAS, sin diferencias materiales de procesados/elegibilidad. | Ejecutado sobre eee428e; publicado en a5794fd. `src/validate_processed.py`, `docs/10_auditoria_procesados_B2.md`, `analisis/reportes/b2/`. |
| B3 | APTO PARA B4 CON ADVERTENCIAS; seleccionó k4 entre4/5/6 sin conservar cinco por defecto. | Ejecutado sobre a5794fd; publicado en6222f79. `src/evaluate_clustering.py`, `docs/11_evaluacion_modelo_B3.md`, `ml/resultados/b3/`. |
| B4 | Paquete preparado, validado y **activado localmente**: ccpc-2009-2024-k4-v1. Contrato, README y memoria implementados. | Base6222f79; cambios B4 sin commit. QA independiente y su veredicto final: `docs/12_QA_B4.md`, `analisis/reportes/b4/`. La activación no autoriza publicación. |

Al inicio de B4 el checkout estaba limpio en `6222f79dadc51f35735fbffd0c92425f8e2673cb`, rama feat/analysis-dashboard y remoto Hiram024/bread-and-circ. Se verificaron las 89 huellas B2 y los 131 originales inventariados por B3 **antes de editar**. Los datos procesados auditados, evidencia B2/B3, referencia k5 y candidato B3 permanecen intactos. Cambios posteriores de código/documentación de integración son deliberados y están delimitados en el diff B4; no se presentan como código del SHA base.

## B2 — datos, exclusiones y selección

Se contaron completamente seis agregados principales y doce secundarios sexo/tipo de sección. Se reconstruyeron serie y panel en ubicación separada, sin llamar a la transformación que se verificaba, sin pivot `first` para resolver ambigüedades y sin sobrescribir originales. Los conteos nacionales se reconciliaron contra auditorías/reportes y copias del producto; no se usaron medias municipales simples como tasa nacional.

| Medida comprobada en B2 | Resultado |
|---|---:|
| Filas anuales de serie | 73,895 |
| Unidades distintas del panel | 12,385 |
| Con seis tasas válidas | 11,925 |
| Elegibles | 8,541 |
| Excluidas únicas | 3,844 |
| Municipios representados | 1,825 de2,477 |
| Cobertura de unidades | 68.9624546% |
| Cobertura municipal | 73.6778361% |
| LN2024 elegible / nacional procesada | 81,666,826 / 98,330,348 =83.0535309% |

La igualdad del denominador LN del panel y del agregado nacional procesado2024 se demostró en B2. No implica cotejo nuevo con un denominador externo oficial.

Causas superpuestas: falta de tasa460; identidad nominal190 unidades/38 claves; observados<100 en algún año863; NS>20% en algún año3,307. Hay110 unidades con años de conteos/NS ausentes, contenidas en las tasas incompletas. No se suman causas: la unión es3,844. Las780 celdas unidad-año sin tasa son415 ausencias y365 presentes con cero observados, no780 unidades distintas.

Oaxaca concentra1,207 exclusiones (31.40% de los excluidos), y Sinaloa/Sonora pierden alrededor de60% de sus unidades. Edad18–24 pierde32.74% frente a29.23% en60+. En2024, NS ponderado por LN es5.0123% entre incluidos y13.3964% entre excluidos. La cercanía de medias simples de participación no prueba ausencia de sesgo. Los valores y todos los grupos se conservan en `seleccion_entidad.csv`, `seleccion_edad.csv`, `seleccion_anual.csv` y cruces de B2.

B4 no repitió esa auditoría: comprobó la vigencia de sus entradas mediante hashes, y reconstruyó únicamente las salidas de producto requeridas para adoptar B3.

## B3 — comparación controlada y decisión

Quince ajustes principales, K-Means k4/5/6, StandardScaler, n_init30, init k-means++, max_iter300, tol1e-4, lloyd. Semillas7/21/42/64/98; referencia42 fijada antes de comparar. Dos muestras comunes de2,000, semillas64/2026; ajuste sobre todas las8,541. Las muestras comparten474 claves, no constituyen intervalo de confianza. La receta histórica de comparación n_init20 no se mezcló con n_init30.

| k | Silhouette64 /2026, seed42 | DB seed42 | ARI semillas media [mín., máx.] |
|---|---|---:|---|
| 4 | 0.247070 /0.251644 | 1.186598 | 0.963304 [0.928580,0.987496] |
| 5 | 0.232284 /0.238248 | 1.217939 | 0.970438 [0.953057,0.985856] |
| 6 | 0.222114 /0.228712 | 1.210639 | 0.822530 [0.704082,0.996685] |

k4 tuvo mayor separación en ambas muestras y cinco semillas, tamaños equilibrados y patrones interpretables. **k5 tuvo algo más de estabilidad entre semillas**, un refinamiento plausible, pero peor separación/sensibilidad al escalador. k6 mostró particiones alternativas y mediana ARI0.710704. No se usó una suma ponderada de métricas ni se cambiaron semillas para favorecer un resultado.

Sensibilidad k4: ARI RobustScaler0.869001 en8,541; NS10=0.842758 en5,671 comunes. NS10 reajustó escalador/modelo sobre el subconjunto:1,273 municipios, LN56,895,504/98,330,348 =57.8616%. No se modificó el filtro principal. No se hizo remuestreo municipal: estabilidad de inicialización no demuestra estabilidad al remuestreo.

La advertencia sklearn1.8.0/1.9.1 se resolvió para B3 en .venv aislado1.8.0. Referencia antigua:8,541 predicciones por clave coincidentes. Repetir su receta k5 n_init30 produjo ARI1 y diferencias cero en escalador/centroides. No se infirió equivalencia solo porque joblib.load funcionara.

El eta²0.543666 de la evaluación temporal antigua fue **leído como evidencia histórica**, no recalculado en B3/B4. Aunque sus features de ajuste terminaban en2021, su selección de unidades dependía de elegibilidad/calidad en seis años incluida2024. Es un diagnóstico retrospectivo condicionado, no validación temporal completamente independiente, prospectiva ni causal.

## B4 — paquete, contrato y operación

Paquete activo: `datos/processed/producto/ccpc-2009-2024-k4-v1/manifest.json`; puntero único `datos/processed/producto_activo.json`; implementación `src/product_contract.py`. Digest `ae5243026dc27552abec02bafaba94819cb49b8dd6877416b79b188fccde1ed4`.

Contiene modelo/escalador/mapeo copiados del candidato B3 comprobado; perfiles, observaciones, metadatos, histórico nacional y auditoría territorial enlazados por SHA256. `load_active` valida entorno, contenido y coherencia de todas las asignaciones/estadísticas antes de ofrecer un snapshot. No hay selector operativo, registro de modelos, servicios nuevos ni entrenamiento B4.

`src.prepare_product` prepara en temporal dentro del directorio de producto, valida, instala una carpeta inmutable y solo con `--activate` reemplaza el puntero. No puede reutilizar la identidad para otros bytes. Renombrar requiere JSON de IDs/nombres completos/únicos y nueva versión; no editar a mano perfiles estadísticos de B3. Las copias de metadatos se generan, no se mantienen listas de nombres en cada consumidor.

Tabla final reutilizable; medias simples entre unidades y cambios en pp:

| ID | Nombre adoptado por Hiram | Unidades | Presidencial | Intermedia | Δ presidencial | Δ intermedia |
|---|---|---:|---:|---:|---:|---:|
| 1 | Menor participación media; descenso presidencial | 1,840 | 48.4418% | 35.7219% | −7.5790 | +6.3771 |
| 2 | Crecimiento medio en ambos tipos de elección | 2,155 | 64.5437% | 49.2185% | +7.9693 | +28.5846 |
| 3 | Participación media; descenso presidencial | 2,511 | 64.1276% | 55.7941% | −8.1161 | +3.2817 |
| 4 | Mayor participación media; cambio presidencial cercano a cero | 2,035 | 78.1001% | 69.5572% | −1.0033 | +15.4785 |

Los IQR se conservan en B3; por ejemplo Δpresidencial p25–p75: P1−12.70..−2.36; P2+2.82..+11.86; P3−12.26..−3.23; P4−4.88..+3.38. La dispersión y solapamiento impiden atribuir los promedios a cada unidad o persona.

No hay equivalencia automática de IDs entre versiones. Cruce activo anterior5/nuevo4, ARI0.636450: antiguo2 se redistribuye principalmente479/942/446 entre nuevos1/2/3. Emparejamiento máximo75.1200% no equivale al ARI ni a exactitud contra clases verdaderas. Ver `ml/resultados/b3/correspondencia_activo_candidato.csv`.

La API de consulta, clasificación, agentes, revisión y PDF usa el mismo paquete. CSV conserva seis tasas, observados y NS por año; valores finitos, rango0–100, observados enteros≥100 y NS≤20%, máximo5,000 filas/2MB. No almacena el CSV ni entrena. La UI deriva cuatro opciones/nombres y muestra versión; no hay B5 visual.

### Confirmación e historial

`GET /api/draft/{id}` devuelve paquete/digest de contenido. `POST /api/approve` exige `profile_id`, revisor, confirmed y los tres tokens `package_version`, `package_digest`, `draft_digest` del borrador mostrado. El digest incluye facts/texto/ID/versión, no timestamps variables de verificación. Cambiar perfil invalida revisión en UI y servidor; cambiar texto o versión produce rechazo409.

SQLite agrega dos columnas, conserva digest y filas anteriores, y respalda mediante Connection.backup antes de migrar esquema antiguo. Las filas sin versión son heredadas/no verificables. Sin una snapshot histórica suficiente no se inventa su contenido ni se regeneran estadísticas nuevas: exportar PDF exige mismo paquete y digest actual o devuelve409. Se conserva el historial y se pide nueva revisión. La aprobación local no es una aprobación institucional ni autoriza difusión automática.

No existía SQLite de usuario al inicio de B4; el bloque no creó aprobaciones ficticias en esa ruta. Nuevas/antiguas bases, backups y migraciones repetidas se probaron en temporales. El artefacto k5 y su producto original se conservaron y son recuperables con el commit completo6222f79 en un temporal, sin reset/clean, sin selector y sin borrar historial.

### Entorno, proceso y recuperación

Operación comprobada Windows/CPython3.11.15, sklearn1.8.0, NumPy2.4.6, SciPy1.17.1, pandas2.3.3, joblib1.6.0 y threadpoolctl3.7.0. Los requirements de app fijan las bibliotecas matemáticas; los de análisis/B3 mantienen compatibilidad. No se modificó Python global. Linux/Docker permanecen alternativas no ejecutadas en esta sesión.

El proceso anterior en8501 mantenía k5 en memoria. Se identificó su comando y se detuvo la sesión conocida; el nuevo proceso se inició con .venv y se verificó `/health` k4/8,541/versión/digest correctos. Se repitió arranque con el comando real `cmd /c run.bat`. Un intento inicial Stop-Process emitió error y el primer arranque encontró puerto ocupado; se corrigió deteniendo la sesión anterior, sin matar servicios desconocidos. Evidencia: `analisis/reportes/b4/activacion.json`.

`.gitattributes` preserva bytes de datos/evidencias/paquetes y LF del código/documentos para evitar roturas de hashes tras pull en Windows. QA probó roundtrip Git temporal con core.autocrlf=true sin commits y recargó el paquete resultante. El puntero no limpia cachés de procesos: hay que detener/reiniciar como indica README.

## QA y evidencia real

Subagente realmente utilizado: **qa_b4**, dedicado a pruebas/evidencia; el principal conserva responsabilidad de implementación. QA fue separado por archivos: tests/informe QA pertenecieron al tester, producción/documentación al principal. La independencia es de responsabilidad en este trabajo, no certificación externa.

- Baseline anterior a cambios: suite completa16 aprobadas, una deprecación Starlette/httpx, exit0.
- Primera integración: suite completa23 aprobadas, misma advertencia, exit0; controles adicionales de nombres duplicados y Git roundtrip también se ejecutaron.
- Navegador real Chrome/Playwright en puerto y SQLite temporales: cuatro opciones/nombres, filtroP4, invalidación de revisión al cambiar perfil, aprobación y descarga PDF, sin page_errors.
- Cuatro PDFs desde aprobaciones temporales reales: texto extraído con PDFium y páginas renderizadas/revisadas visualmente, sin cortes ni solapes. No se confunde el prefijo PDF con revisión de contenido.
- Instalación limpia temporal de requirements-app: carga del paquete, salud, consulta e inferencia reales; no se alteró .venv de usuario para simularlo.
- Negativos: hash adulterado, estadísticas adulteradas incluso recalculando hashes, tokens/contenido incompatibles, CSV inválido, historial heredado y salida a versión duplicada. No se adulteró producción ni se eliminaron aserciones.
- La **pasada final completa**, comandos, exit codes, archivos/hashes de estado estable, limitaciones y veredicto del tester se registran en [docs/12_QA_B4.md](12_QA_B4.md) y `analisis/reportes/b4/qa_*`. Esa referencia es la evidencia autoritativa del cierre de QA.

Las expectativas antiguas de cinco en `tests/test_dashboard.py` se actualizaron justificadamente a cuatro y tamaños B3, preservando seis años, controles negativos y rechazo de confirmación. No se modificaron los tests B2/B3 para ocultar fallos. Fallos de harness por stderr/encoding/comillas se distinguieron de resultados de producción y se corrigieron; no se presentaron pruebas no ejecutadas como aprobadas.

Comando reproducible de suite completa:

```powershell
$qaTemp = Join-Path $env:TEMP ('ccpc-tests-' + [guid]::NewGuid().ToString('N'))
& .\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider --basetemp $qaTemp tests
```

Para regenerar producto sin entrenar: `& .\.venv\Scripts\python.exe -B -m src.prepare_product --root .`; activar solo después de revisar/validar y con el servidor detenido, añadiendo `--activate`, luego `cmd /c run.bat`. La especificación de campos y ejemplos reales está en la sección B4 del README. El notebook06 de producto fue adaptado y sus outputs antiguos retirados; **no se declara ejecutado completo en B4**. El documento técnico PDF completo de entrega requiere render/QA propios antes de presentarlo como final.

## Límites, pendientes y material de entrega

Persisten separación moderada, sensibilidad, cobertura desigual, territorio nominal, calidad NS potencialmente selectiva y diagnóstico temporal condicionado. No hay etiquetas verdaderas, validación causal, predicción individual ni garantía de representatividad nacional plena. La cobertura83.0535% no es precisión del modelo.

B4 implementa decisiones de Hiram para Rubén; la revisión de Rubén no se presupone. Tras publicación autorizada deberá leer README, confirmar versión/entorno, probar contrato y revisar política editorial/histórica. Quedan B5 visual si se solicita, documentación final del hackathon con revisión de tablas/figuras, posibles sensibilidades adicionales y eventual cartografía certificada. Autenticación, despliegue y generación externa de agentes están fuera de este bloque.

Tablas reutilizables: totales anuales/exclusiones/cobertura B2; comparación, estabilidad, sensibilidad, cruces e IQR B3; perfiles/observaciones/versionado activos B4. Figuras previas en `analisis/figuras` pueden ser históricas k5: deben identificarse o regenerarse de forma controlada antes de usarse como figuras actuales. No se inventaron gráficos ni resultados para llenar apartados.

Fuentes/evidencia: [B2](10_auditoria_procesados_B2.md), [B3](11_evaluacion_modelo_B3.md), [QA B4](12_QA_B4.md), README raíz, `analisis/reportes/b2/`, `ml/resultados/b3/`, `analisis/reportes/b4/`, paquete activo y scripts citados. Referencias primarias consultadas para B4: [compatibilidad de persistencia sklearn1.8](https://scikit-learn.org/1.8/model_persistence.html#security-maintainability-limitations), [backup SQLite](https://docs.python.org/3.11/library/sqlite3.html#sqlite3.Connection.backup), [reemplazo de referencia os.replace](https://docs.python.org/3.11/library/os.html#os.replace). Fuente institucional declarada: [CCPC INE](https://ine.mx/transparencia/datos-abiertos/visualizacion-datos/conteos-censales-participacion/); no se reauditaron RAW ni mapas institucionales.

B4 queda sin commit/push/merge/PR hasta autorización expresa. Propuesta: `feat: adopt versioned four-profile package and bind approvals to reviewed content`.

## B5 — recorrido analítico orientado a preguntas

Actualización28/10/2026, America/Tijuana. **B4 fue publicado con autorización posterior en7e43a2d**; sus menciones previas «sin commit» describen el cierre original, no el estado al iniciar B5. B5 parte de ese SHA, rama feat/analysis-dashboard y checkout limpio comprobado. Las ediciones nuevas permanecen locales sin commit/push; no llegan por pull hasta autorización/publicación.

Esta continuación conserva y reorganiza la base de Rubén, con Hiram responsable de datos/modelo/analítica y decisiones de integración documentadas para Rubén, sin asumir su aprobación. No se entrenó ni cambió el paquete adoptado, features, nombres, umbrales, agentes, clasificación o reglas de aprobación/PDF.

### Diagnóstico, fuentes y decisiones

El recorrido real previo ya tenía los gráficos nacionales, distribución de perfiles, barras de medias, filtros y fichas; se conservaron. Faltaba comparar cambios en pp, recorrer más de100filas, consultar detalle por unidad y entender cobertura/exclusiones. El formateo de nulos podía mostrar0%. La línea base de QA ejecutó25tests aprobados, una deprecación previa y Chrome real sin errores de JS; estos sí son resultados nuevos B5, separados del informe histórico B4.

| Pregunta | Solución B5 y significado |
|---|---|
|¿Qué ocurrió entre2009y2024?|Panorama nacional cronológico, presidencial/intermedia por símbolos/trazos/nombres, tabla y dos hallazgos calculados. Razón de sumas `100*SV/(SV+NV)`, no media municipal. NS no es abstención.|
|¿Qué distingue a los perfiles?|Nombres completos intactos, proporciones y tabla de tamaño/nivel/cambio; barras de medias conservadas y única gráfica nueva de cambios pp. Las medias son simples entre unidades elegibles.|
|¿Dónde aparecen esos patrones?|Explorador con filtros combinados,100por página, rango/total, resumen de TODASlas coincidencias y detalle por entidad+municipio+edad. Seis tasas y observados por elección; cortes transversales, no seguimiento individual.|
|¿Hasta dónde interpretar?|Auditoría con cobertura, denominadores, exclusiones únicas y solapadas, selección por edad/entidad y advertencias. Se conserva la auditoría nominal original sin presentarla como certificación geométrica.|

El filtro «Explorar Pn» cambia explícitamente el explorador, sin modificar la ficha revisada. Panorama/perfiles/auditoría no cambian con filtros del explorador. Al filtrar o paginar se invalida detalle/offset según corresponda. Cancelación nativa y contador de solicitud impiden que una respuesta antigua reemplace otra reciente; carga/error/vacío se distinguen y no retienen cifras anteriores como vigentes. Texto interpolado escapado, nulo«Sin dato», controles etiquetados, foco visible, tablas con scroll contenido y valores sin hover.

`src/analytics.py` contiene filtros compartidos, medias antes de paginar, razones nacionales y vinculación de evidencia B2. `src/dashboard_api.py` amplía `/api/observations` conservando campos previos, añade `/api/analysis-audit` y documentación local por allowlist. `README.md` conserva el contrato B4, añade campos/tipos/errores/ejemplo real, fuentes/fórmulas/universos, efecto de filtros y forma de modificar presentación frente a paquete/modelo. No se creó otro README ni framework de gráficos.

### Cifras y evidencia verificadas en B5

Paquete activo `ccpc-2009-2024-k4-v1`; descriptor SHA256 `ae5243026dc27552abec02bafaba94819cb49b8dd6877416b79b188fccde1ed4`. La carga compatible comprueba hashes, todas las asignaciones y estadísticas B4; ningún artefacto se reserializó. Python3.11.15/sklearn1.8.0/NumPy2.4.6/SciPy1.17.1/pandas2.3.3/joblib1.6.0. B5 usa las mismas dependencias, JS/CSS/HTML y Plotly offline ya existente.

De89huellas B2 heredadas,72siguen iguales y17son código/docs/tests/requirements adaptados legítimamente enB4; se registran en `analisis/reportes/b5/base.json`. Ninguna diferencia afecta los datos procesados auditados. No se afirmó que todo el código antiguo seguía idéntico. Se preservan49archivos de datos/productos/modelo inventariados por el principal y el inventario más amplio de QA para B2/B3/contratos.

La auditoría complementaria se vincula mediante `analisis/reportes/b5/fuentes_auditoria.json`:digest activo y hashes de resultados/cobertura/elegibilidad/totales/selección deB2. Además compara claves exactas de elegibles, totales/tasas nacionales y denominadores. Fuente alterada o paquete no correspondiente devuelve503 sin mostrar cobertura caduca. Estas huellas no prueban origen oficial ni vuelven a certificar RAW.

Resultados reutilizables, sin modificar las tablas B2/B3:

|Indicador|Numerador / denominador|Resultado|
|---|---|---:|
|Unidades elegibles / panel|8,541 /12,385|68.9624545822%|
|Municipios con alguna edad elegible / panel|1,825 /2,477|73.6778360920%|
|LN2024elegible / agregado nacional procesado de cinco edades|81,666,826 /98,330,348|83.0535309404%|
|Exclusión única|3,844 /12,385|31.0375454178%|

Las4930incidencias de las cinco causas se superponen; no son4930excluidas. Las combinaciones presentes suman3844unidades únicas. Algunas descripciones de universo enCSVheredadoB2tienen caracteresU+FFFD:se conserva el archivo y sus hashes;la vista usa descripciones semánticas legibles para las cinco medidas conocidas.

Participación nacional procesada:2009=44.060783%;2012=62.082964%;2015=47.073560%;2018=62.365103%;2021=51.837976%;2024=59.670029%. Diferencias del mismo tipo:intermedias2009→2021+7.777192pp;presidenciales2012→2024−2.412934pp. No son causas ni cambios individuales. PerfilesP1/P2/P3/P4mantienen1840/2155/2511/2035y todos los nombres/medias de la tabla B4 anterior.

Ejemplo real verificable de filtros:estado2,edad18-24produce5unidades/5municipios,LN446745,media presidencial44.65497528% e intermedia25.83416436%;limit2solo cambia filas visibles,no el resumen. Fuente: `analisis/reportes/b5/ejemplos_api.json`. Las figuras actuales renderizadas se registran como capturas de QA; no se vuelven a etiquetar las figuras antiguas k5 como k4.

### QA independiente, ejecución y pendientes

Se creó y utilizó realmente **qa_b5**, dedicado exclusivamente a suite, fixtures, navegador, evidencia e informe; el principal implementa y corrige producción/documentación. El QA posee `tests/test_b5_analytics.py`, `analisis/reportes/b5/qa_*` y `docs/14_QA_B5.md`. No es certificación externa. Los25tests previos se mantienen; las aserciones nuevas usan CSVanuales, claves, datos B3 y fixtures calculadas a mano. Una fixture103filas cambia las medias más allá de la primera página; otra diferencia tasa agregada19/110de media simple50%. Alterar tasa/unidad en fixtures debe ser rechazado.

El navegador detectó un defecto real en la incorporación de opciones de entidad (`innerHTML+` sin asignación); el principal corrigió `+=` y QA repitió filtros. Fallos de sincronización del harness se registran separados, sin declararlos defectos del producto ni ocultar logs. La revisión responsive espera condiciones observables de Plotly tras redimensionar y no confunde una captura durante resize con estado final. El informe independiente detalla todos los fallos, repeticiones y veredicto final sobre el estado congelado.

Se reinició solo el servidor conocido de B4en8501después de identificar comando/PID; salud y endpointsB5devuelven200con misma versión/digest. QA usa puerto y SQLite propios temporales para CSV/revisión/PDF; no escribe ni limpia historial real. La comprobación de arranque está en `ejecucion_local.json`. Comandos repetibles en README e informe13; final suite/navegador y huellas en el informe14.

B6 conserva aceptación con Rubén en su entorno de demo y revisión completa de notebook/informe técnico. Quedan otros navegadores/sistemas, lector de pantalla/zoom y escenarios de uso adicionales; B5 no completaB6por asociación. Persisten cobertura desigual, RAW asumidos, geografía nominal y diagnóstico temporal retrospectivo condicionado. No se añadieron mapas, LLM,autenticación,despliegue ni reentrenamiento. La evidencia descriptiva/reproducibilidad no convierte el modelo en científicamente validado.

Propuesta de commitB5,no ejecutado: `feat: add question-driven analytics dashboard with verified selection summaries`.

## Resultado de cierre B5 y QA independiente

**B5: COMPLETADO CON ADVERTENCIAS. QA `qa_b5`: APROBADO CON ADVERTENCIAS no bloqueantes.** El recorrido y sus universos quedaron comprobados, manteniendo intactos paquete/modelo/datos y reglas B4. Pasada completa sobre código congelado: **31 pruebas aprobadas, una deprecación previa Starlette/httpx, exit0**; navegador Chrome156.0.8078.48 real, exit0, anchos1440y390sin desborde global estable,0erroresJavaScript y0solicitudesexternas. La advertencia favicon404es heredada;422corresponde al CSVinválido inducido, no un error silencioso de funcionamiento.

QA inspeccionó visualmente Panorama/Perfiles/Explorador/Auditoría/móvil y un PDFP2real aprobado enSQLite temporal: nombre/tamaño2155/medias/cambios/versión/revisor/limitaciones comprobados;1página sin cortes esenciales. Comprobó teclado/foco, muestras de contraste y rechazo de respuesta antigua/red/nulos/HTML,inferenciay revisión/PDF/digestobsoleto. No es certificación WCAG ni científica. Los25tests previos no se modificaron; se añadieron6grupos B5 con oráculos independientes. Se corrigió el defecto de opciones de entidad detectado por el navegador; los fallos de sincronización del harness quedaron documentados por separado.

Después de incorporar este cierre documental se repite la pasada final sin ediciones concurrentes. Su resultado autoritativo, tiempos, huellas definitivas, cambios durante la pasada y alcance visual quedan en `analisis/reportes/b5/qa_final_resultados.json`, `qa_final_state.json`, `qa_final_pytest.txt`, `qa_final_browser.txt`, `qa_visual_final.json` y `docs/14_QA_B5.md`. No hubo cambios en historial real ni fuentes auditadas. B6 mantiene aceptación conRubén, otros navegadores/sistemas, lector de pantalla/zoom, notebook e informe técnico completo; no se declara completado. B5 sigue sin commit/push/merge/PR, con propuesta en inglés Conventional Commits en README/informe13.
