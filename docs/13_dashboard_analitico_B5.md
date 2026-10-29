# B5, camino B — dashboard analítico orientado a preguntas

Base: `7e43a2dfa2f07f5e54d7a4b934de649b31c9e2ff`, `feat/analysis-dashboard`, remoto Hiram024/bread-and-circ, checkout limpio comprobado antes de crear evidencia. Ejecución28/10/2026, zona America/Tijuana; timestamps/versiones en `analisis/reportes/b5/base.json` y `qa_baseline.json`. B5 son cambios locales sin commit; el SHA base no describe esas ediciones. No se hizo push, merge, PR, publicación ni entrenamiento.

El estado final de comprobaciones y veredicto independiente se registra en [QA B5](14_QA_B5.md). Este documento explica decisiones y fuentes; no sustituye sus ejecuciones. La [memoria Hiram](00_memoria_tecnica_Hiram.md) conserva B1–B4 y añade B5, y el README raíz contiene el contrato efectivo para Rubén.

## Diagnóstico real y cambios mínimos

La línea base ejecutó la suite completa:25 aprobadas,1 deprecación previa de Starlette/httpx, exit0. Chrome real recorrió las cuatro vistas antes de editar API/JS/HTML/CSS; QA comprobó sus hashes contra el estado inicial. Se conservaron paleta, tipografía del sistema, sidebar, tarjetas, Plotly offline, CSV, agentes y fichas. No se añadieron dependencias ni frameworks.

| Pantalla / pregunta | Fuente y cálculo anterior conservado | Carencia comprobada | Cambio B5 |
|---|---|---|---|
| Panorama: ¿qué ocurrió? | Nacional del snapshot B4; seis elecciones y distribución de unidades | Denominador poco explicado, KPI ambiguo, hallazgos genéricos y falta de valores sin hover | Razón de sumas recalculada, tabla nacional, diferencias del mismo tipo calculadas, símbolos/trazos, universo nacional/modelado explícito. |
| Perfiles: ¿qué distingue? | Cuatro nombres/tamaños y barras de medias del snapshot | Cambios pp y proporciones ocultos, nombres largos y comparación sin tabla completa | Nombres intactos, tabla de tamaño/nivel/cambio, única gráfica nueva de cambios pp; acceso explícito al filtro de perfil. |
| Explorador: ¿dónde aparecen? | Endpoint filtrado sobre observaciones del snapshot, ya incluía seis tasas | Solo primeras100, sin navegación/detalle, respuesta vieja podía pisar filtros recientes; nulos se formateaban como0% | Paginación100, rango y total, resumen antes de paginar, detalle por entidad+municipio+edad, carga/error/vacío separados y cancelación+contador. |
| Auditoría: ¿qué cobertura/límites? | Identidad nominal y hasta50 ejemplos del snapshot | No cobertura/exclusiones; códigos poco legibles | Fuente B2 vinculada al snapshot, numeradores/denominadores, causas superpuestas/combinaciones, selección por edad/entidad, interpretación y documentación local. |

### Fuentes, alcance y números comprobados ahora

`load_active` cargó el paquete `ccpc-2009-2024-k4-v1` en .venv compatible:Python3.11.15, sklearn1.8.0, NumPy2.4.6, SciPy1.17.1, pandas2.3.3, joblib1.6.0. Se reprodujeron las asignaciones durante esa carga validada. Digest del descriptor: `ae5243026dc27552abec02bafaba94819cb49b8dd6877416b79b188fccde1ed4`. No se serializó ni sobrescribió el modelo.

Al contrastar89huellas heredadas de B2,72coinciden y17difieren en código/documentación/tests/requirements adaptados en B4: se registran por nombre en `base.json`. **Ninguna discrepancia afecta los insumos procesados auditados.** No se dio por vigente todo el código B2 por asumir igualdad del SHA. Las49huellas de datos/productos/modelo protegidos por el principal y el inventario más amplio de QA permiten comprobar ausencia de cambios; los reportes B2/B3 se conservan. No se repitió toda B2 ni entrenamiento B3.

Las fuentes suplementarias B2 no se mezclan silenciosamente en el snapshot: `fuentes_auditoria.json` registra sus seis hashes y digest del paquete. La vista analítica comprueba esos bytes, hashes procesados B2, elegibilidad booleana, claves exactas, unicidad, conteos/tasas nacionales y cobertura. Si no corresponden devuelve503 sin mostrar cifras anteriores. Los hashes de evidencia son trazabilidad, no certificación oficial.

| Medida | Numerador | Denominador / universo | Resultado |
|---|---:|---|---:|
| Unidades elegibles / panel |8,541|12,385 unidades municipio×edad de la unión anual|68.9624545822%|
| Municipios con alguna edad elegible / panel |1,825|2,477 claves municipales de la unión anual|73.6778360920%|
| LN2024 elegible / nacional procesado |81,666,826|98,330,348 registros LN del agregado2024 de cinco edades|83.0535309404%|
| Excluidas únicas |3,844|12,385 unidades del panel|31.0375454178%|

Los denominadores panel/nacional para LN2024 coinciden en esta base; se conservan ambos rótulos, no se equiparan por definición. Causas superpuestas:460sin alguna tasa,190identidad inestable,863observados<100,3307NS>20%,110faltan conteos/NS. Suman4930incidencias, no3844unidades. Las combinaciones presentes sí suman3844excluidas únicas. El reporte y la API muestran explícitamente esta diferencia.

| Año / tipo | Participación nacional % | Fuente / denominador |
|---|---:|---|
|2009 / Intermedia|44.0607831124|SV/(SV+NV), agregado nacional procesado|
|2012 / Presidencial|62.0829638641|Misma razón de sumas|
|2015 / Intermedia|47.0735597656|Misma razón de sumas|
|2018 / Presidencial|62.3651034142|Misma razón de sumas|
|2021 / Intermedia|51.8379755467|Misma razón de sumas|
|2024 / Presidencial|59.6700294444|Misma razón de sumas|

Hallazgos derivados, sin causalidad:intermedias2009→2021+7.7771924343pp; presidenciales2012→2024−2.4129344197pp. Los dos se calculan desde la respuesta de la API, no cifras copiadas a JS. NS sigue excluido de SV+NV, no convertido en abstención. Estas tasas son nacionales; las medias de perfiles/selección son simples entre unidades y se etiquetan como tales.

Los perfiles permanecen P1=1840,P2=2155,P3=2511,P4=2035, mismos nombres B4 y estadísticas comprobadas contra B3/observaciones. Ver tabla reutilizable en la memoria y respuesta completa `ejemplos_api.json`. La selección real estado2/edad18-24 tiene5unidades/5municipios,LN446745:limit2no cambia los5del resumen. QA añade un oráculo sintético de103filas donde las tres finales cambian la media para detectar agregaciones limitadas a la primera página.

## Integración, responsabilidades y límites

Cambios de producción: `src/analytics.py`, ampliación compatible de `src/dashboard_api.py` y tres archivos frontend. B4 conserva snapshot, agentes, validación CSV, contrato de aprobación/digest/PDF, persistencia y migración. `src/education.py`, builder, modelo y fuentes originales no se editan. Rubén debe conocer los campos nuevos y el alcance de filtros del README; su aprobación no se presume.

El explorador usa orden estable de claves, nunca une nombres ni selecciona por posición tras cambiar universo. Los filtros reinician offset y detalle; la búsqueda invalida solicitudes incluso antes de que termine su debounce. Se distinguen carga/error/sin coincidencias; el resumen anterior desaparece durante error. Nulos se muestran como «Sin dato». Texto interpolado se escapa; no se añadieron URLs de fuentes/iconos/librerías remotas.

El servidor conocido de B4 PID45128se identificó por comando/puerto y se reinició únicamente ese proceso. B5 quedó ejecutándose en127.0.0.1:8501con .venv, PID24988al comprobar; `/health`, consulta nueva y auditoría devolvieron200con la misma versión/digest. `ejecucion_local.json` registra esa comprobación; el PID puede cambiar después. No se hicieron aprobaciones en SQLite real, que seguía ausente al comprobarlo. QA usa su propio puerto y base temporal.

Los nombres de estado nominal son legibles;2423claves estables,32a revisar y22incompletas en la base. Ningún estado acredita fronteras iguales. Algunas descripciones `universo` del CSV B2 contienen U+FFFD heredado: no se alteró esa evidencia; la presentación usa rótulos semánticos de las cinco medidas verificadas. La API conserva el campo fuente y su hash.

Referencias técnicas puntuales consultadas:[AbortController/MDN](https://developer.mozilla.org/en-US/docs/Web/API/AbortController) para cancelación nativa y [W3C SC1.4.3](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html) para contraste mínimo. Las comprobaciones acotadas de foco/contraste no son certificación WCAG completa.

## Repetición y entrega

Desde la raíz, con .venv y dependencias de desarrollo ya instaladas:

```powershell
$qaB5Temp = Join-Path $env:TEMP ('ccpc-b5-tests-' + [guid]::NewGuid().ToString('N'))
& .\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider --basetemp $qaB5Temp tests
& .\.venv\Scripts\python.exe -B analisis\reportes\b5\qa_browser_run.py
& .\.venv\Scripts\python.exe -B -m uvicorn src.dashboard_api:app --host 127.0.0.1 --port 8501
```

El último comando es de arranque manual: detener antes el servidor conocido o elegir otro puerto libre. Los comandos QA, herramientas Chrome/Playwright, resultados, huellas finales y defectos corregidos se documentan en `docs/14_QA_B5.md`. No se usa `git diff --check` de PDFs/textos de evidencia como sustituto de verificación de código ni se alteran logs previos para ocultar fallos.

QA posee `tests/test_b5_analytics.py`, scripts/evidencia `qa_*` e informe; el principal no cambia sus aserciones. Los25tests anteriores se conservan. Las nuevas pruebas comparan cifras/casos calculados independientemente; los defectos controlados se inyectan en fixtures/transporte, nunca datos o modelo de producción.

Pendiente B6:demo y aceptación con Rubén sobre la entrega publicada cuando Hiram lo autorice, navegador/sistema previstos, recorrido con lectores de pantalla y zoom, informe técnico PDF completo y notebook completo. Linux/macOS/Docker no ejecutados; no se amplía la evidencia Chrome a otros entornos. Persisten cobertura desigual, geografía nominal, RAW asumidos y diagnóstico temporal retrospectivo condicionado. B5 no valida científicamente el modelo, no cambia k/features/filtros ni introduce mapas/LLM/autenticación/despliegue.

Propuesta de commit (no ejecutado): `feat: add question-driven analytics dashboard with verified selection summaries`.

## Resultado de cierre B5 y QA independiente

**B5: COMPLETADO CON ADVERTENCIAS. QA `qa_b5`: APROBADO CON ADVERTENCIAS no bloqueantes.** El recorrido y sus universos quedaron comprobados, manteniendo intactos paquete/modelo/datos y reglas B4. Pasada completa sobre código congelado: **31 pruebas aprobadas, una deprecación previa Starlette/httpx, exit0**; navegador Chrome156.0.8078.48 real, exit0, anchos1440y390sin desborde global estable,0erroresJavaScript y0solicitudesexternas. La advertencia favicon404es heredada;422corresponde al CSVinválido inducido, no un error silencioso de funcionamiento.

QA inspeccionó visualmente Panorama/Perfiles/Explorador/Auditoría/móvil y un PDFP2real aprobado enSQLite temporal: nombre/tamaño2155/medias/cambios/versión/revisor/limitaciones comprobados;1página sin cortes esenciales. Comprobó teclado/foco, muestras de contraste y rechazo de respuesta antigua/red/nulos/HTML,inferenciay revisión/PDF/digestobsoleto. No es certificación WCAG ni científica. Los25tests previos no se modificaron; se añadieron6grupos B5 con oráculos independientes. Se corrigió el defecto de opciones de entidad detectado por el navegador; los fallos de sincronización del harness quedaron documentados por separado.

Después de incorporar este cierre documental se repite la pasada final sin ediciones concurrentes. Su resultado autoritativo, tiempos, huellas definitivas, cambios durante la pasada y alcance visual quedan en `analisis/reportes/b5/qa_final_resultados.json`, `qa_final_state.json`, `qa_final_pytest.txt`, `qa_final_browser.txt`, `qa_visual_final.json` y `docs/14_QA_B5.md`. No hubo cambios en historial real ni fuentes auditadas. B6 mantiene aceptación conRubén, otros navegadores/sistemas, lector de pantalla/zoom, notebook e informe técnico completo; no se declara completado. B5 sigue sin commit/push/merge/PR, con propuesta en inglés Conventional Commits en README/informe13.
