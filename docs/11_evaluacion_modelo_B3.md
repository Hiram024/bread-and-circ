# B3, camino B — comparación controlada de perfiles

**Estado: APTO PARA B4 CON ADVERTENCIAS. Recomendación: K-Means k=4, StandardScaler, n_init=30, semilla 42.** Es un candidato revisable, no el modelo adoptado por la aplicación. No se declara un modelo científicamente validado ni se interpreta ARI como acierto contra etiquetas verdaderas.

## Base, protección y trazabilidad

Rama `feat/analysis-dashboard`; base efectiva `a5794fd008bbb2bdf4ec7d68c96d823812e399be`. El checkout estaba limpio y sincronizado al iniciar. A diferencia del estado histórico comunicado, B2 sí estaba cometido y publicado. B3 agrega código, pruebas, dependencias aisladas, documentación y resultados **sin commit**.

Se leyó el informe B2 y se comprobaron sus **89 huellas**: ninguna cambió. No se volvió a ejecutar toda B2. Se conservan 8,541 unidades elegibles de 1,825 municipios y las cuatro variables auditadas. Se registraron además huellas iniciales de **131 archivos versionados**, incluido el artefacto activo y los contratos de Rubén. Todos permanecen iguales al cierre de los experimentos y de la verificación del candidato.

Universo de cobertura heredado de B2, con vigencia de entradas comprobada: 8,541/12,385 unidades (68.9625%), 1,825/2,477 municipios (73.6778%) y LN 2024 de 81,666,826/98,330,348 (83.0535%). El denominador nacional es el agregado procesado de cinco grupos de edad. Un municipio representado puede tener solo algunas edades elegibles. No se recuperaron ni abrieron RAW; su extracción confiable sigue siendo la premisa aportada por Hiram.

`ml/resultados/b3/preparacion.json` registra la base protegida y el hash del protocolo antes de los nuevos ajustes. `ejecucion.json` registra fecha/zona `America/Tijuana`, versiones, parámetros, hashes de matriz, claves y features ordenadas, código y candidatos. `verificacion_candidato.json` recoge el control final. El SHA base no describe por sí solo este código nuevo sin commit.

## Entorno: referencia, reproducción y cambio metodológico

Se creó `.venv/` aislado, ya excluido por `.gitignore`; no se alteró Python global ni el entorno temporal previo. Versiones efectivas de entrenamiento y carga:

| Componente | Versión |
|---|---|
| Python | 3.11.15, Windows x86_64 |
| scikit-learn | 1.8.0 |
| NumPy | 2.4.6 |
| SciPy | 1.17.1 |
| pandas | 2.3.3 |
| joblib | 1.6.0 |
| threadpoolctl | 3.7.0 |

`requirements-b3.txt` fija estas dependencias e incluye las dependencias de la app para comprobar sus regresiones en el mismo entorno. `environment.lock.txt` registra todas las dependencias transitivas efectivamente instaladas. Los requirements activos no se modificaron: B4 deberá utilizar el entorno fijado al adoptar o servir un candidato; una instalación nueva con rangos amplios no garantiza esa coincidencia. No se reinició ni migró un servidor previo.

Se resolvió la diferencia 1.8.0/1.9.1 sin ocultar advertencias. La carga convierte `InconsistentVersionWarning` en error y se hizo con 1.8.0. La documentación oficial no soporta cargar un modelo persistido con otra versión de sklearn. Las versiones originales completas de NumPy/SciPy/joblib del entrenamiento antiguo no constan con garantía en el artefacto; se documentan las actuales comprobadas.

Tres comprobaciones distintas, registradas en `referencia.json`:

1. **Artefacto antiguo:** carga compatible sin advertencia de versión; sus predicciones coinciden exactamente con las 8,541 asignaciones publicadas, alineadas por clave. Modelo activo SHA-256: `af0a33a52e75dc5370844c799cb347a7c276491ed938f0fa11f396f316741a98`.
2. **Misma receta:** k=5, n_init=30, semilla 42, mismas unidades y orden. ARI=1 y emparejamiento máximo=1 frente al activo; diferencia máxima de centros emparejados, medias y escalas del escalador: **0**. Esto demuestra reproducción observada de esta referencia, no una garantía para cualquier versión o hardware.
3. **Cambio metodológico:** elegir cuatro surge de la comparación posterior, no de que hubiera una advertencia de carga. Los candidatos k4/k5/k6 de referencia también se serializaron, recargaron y verificaron en el mismo entorno.

## Protocolo registrado antes de los resultados

Archivo `ml/resultados/b3/protocolo.json`, huella registrada `ec95b6dc2f9936c3a25ae06dd85fcd033619244e3ef5def33a35ef4fdd848202`.

- Todas las elegibles, orden de claves estable `(EDOCVE, MPIOCVE, grupo_edad)`. Sin unir por nombres, sin perder ceros a la izquierda y sin comparar archivos de diferente procedencia por posición.
- Features, en este orden: `media_presidencial`, `media_intermedia`, `cambio_presidencial_pp`, `cambio_intermedia_pp`. Se contrastaron las fórmulas contra tasas: media 2012/2018/2024; media 2009/2015/2021; 2024−2012; 2021−2009. Tasas 0–100 y cambios en pp.
- Booleanos explícitos, unicidad, valores finitos y filtros B2; sin imputación de features. Las reducciones no esconden años ausentes.
- Una unidad agregada, un peso. No se usó `sample_weight` poblacional ni se incluyeron edad, sexo o identificadores como features. Los grupos pequeños y grandes tienen igual peso analítico por unidad; las medias no describen una persona promedio nacional.
- StandardScaler principal; KMeans k=4/5/6, `init='k-means++'`, `n_init=30`, `max_iter=300`, `tol=1e-4`, `algorithm='lloyd'`. Semillas 7, 21, 42, 64, 98; referencia 42 prefijada. Un hilo mediante threadpoolctl.
- Silhouette en **las mismas dos muestras de 2,000 claves** por candidato principal, semillas 64 y 2026; ajuste sobre todas las unidades. `RandomState(seed).permutation(n)[:2000]`, claves guardadas. Las muestras comparten 474 unidades: no son dos conjuntos disjuntos ni un intervalo de confianza.
- DB y Calinski-Harabasz en todas las unidades; tamaños, medias, IQR y silhouette negativo por grupo en muestra. Distancias muestrales se calculan una vez por geometría para reutilizarlas entre k/semillas.
- ARI para los diez pares de semillas por k; media, mediana y rango. No se equiparan IDs ni se trata ARI como exactitud supervisada.
- Sensibilidades prefijadas: RobustScaler sobre las mismas unidades; NS≤10% cada año con **escalador y modelo reajustados en ese subconjunto**, mismos parámetros y semilla 42. No se promociona el mejor número de otra geometría.
- Decisión conjunta de separación, estabilidad, tamaños, dispersión e interpretación; sin índice ponderado inventado ni umbrales universales. Un grupo adicional requiere un patrón defendible. La semilla no se selecciona por conveniencia.

La comparación antigua usaba n_init=20; el modelo activo final usaba 30. B3 usa 30 en todos sus ajustes comparables. Que algunas cifras coincidan con las anteriores no convierte esas recetas históricas en idénticas.

## Comparación ejecutada

Quince ajustes principales y seis ajustes de sensibilidad; todos completaron. Los tiempos de KMeans.fit por configuración y las iteraciones están en los CSV, separados del coste de lectura, escalado, métricas y escritura.

| k | Silhouette semilla42, muestra64 | Silhouette semilla42, muestra2026 | DB, semilla42 | CH, semilla42 | Grupo mínimo/máximo | ARI semillas: media [mín., máx.] |
|---|---:|---:|---:|---:|---|---|
| 4 | 0.247070 | 0.251644 | 1.186598 | 3800.418 | 21.54% / 29.40% | 0.963304 [0.928580, 0.987496] |
| 5 | 0.232284 | 0.238248 | 1.217939 | 3433.946 | 14.74% / 24.35% | 0.970438 [0.953057, 0.985856] |
| 6 | 0.222114 | 0.228712 | 1.210639 | 3219.447 | 8.91% / 21.47% | 0.822530 [0.704082, 0.996685] |

Variación de silhouette entre las cinco semillas, sin interpretarla como intervalo de confianza:

| k | Muestra64: mínimo–máximo | Muestra2026: mínimo–máximo | Mediana ARI entre semillas |
|---|---|---|---:|
| 4 | 0.247070–0.247461 | 0.250742–0.252389 | 0.963429 |
| 5 | 0.231786–0.232598 | 0.237913–0.238506 | 0.971655 |
| 6 | 0.222114–0.226526 | 0.228641–0.229334 | 0.710704 |

k4 supera a los otros dos en ambas muestras para todas las semillas. La separación sigue siendo moderada. No hay microgrupos dominantes o vacíos en los candidatos principales; los tamaños completos de cada semilla están en `tamanos_grupos.csv`.

Para k4/semilla42, silhouette media por grupo en muestra64: 0.2697, 0.2317, 0.2191 y 0.2749; fracción negativa: 3.53%, 7.25%, 1.03% y 0.20%. En la muestra2026: 3.47%, 7.85%, 4.39% y 0%. Hay solapamiento, particularmente en el grupo de crecimiento; ningún perfil es una clase inequívoca.

k5 tiene mayor estabilidad de inicialización que k4, aunque ambos son altos en esta comparación. k6 admite dos patrones de solución: ARI entre algunos pares cercano a 0.9967 y entre otros alrededor de 0.7041; mediana 0.7107. No se eligió la semilla 7 de k6 para sustituir a 42 por su mayor silhouette.

## Sensibilidad: universos y cambio descriptivo

| k | ARI RobustScaler vs principal, 8,541 comunes | ARI NS10 vs principal restringido, 5,671 comunes |
|---|---:|---:|
| 4 | 0.869001 | 0.842758 |
| 5 | 0.794300 | 0.862080 |
| 6 | 0.757685 | 0.892882 |

RobustScaler mantiene las 8,541 unidades, 1,825 municipios y 83.0535% de LN 2024. En k4, el emparejamiento máximo cubre 95.0240% de unidades. Los cuatro patrones de nivel/cambio siguen siendo reconocibles, pero hay reasignaciones: el grupo de crecimiento tiene medias de cambio +8.60/+27.78 pp frente a +7.97/+28.58 en el principal. Son estadísticas bajo particiones distintas, no un efecto causal del escalador.

NS10 conserva **5,671 unidades**, 1,273 municipios y LN 2024 **56,895,504/98,330,348 = 57.8616%**. No se cambió el filtro B2 de producción. Se reajusta StandardScaler sobre ese subconjunto, a diferencia del script histórico que reutilizaba z del conjunto completo. Por eso la sensibilidad B3 NS10 no es una reproducción idéntica de la tabla antigua.

En k4/NS10, tamaños 1,229/1,357/1,619/1,466; medias presidencial/intermedia 47.78/34.60, 64.74/49.17, 62.81/53.87 y 76.62/68.04. El emparejamiento máximo contra la referencia restringida es 93.8811%. La comparación ARI usa solo claves comunes; las métricas de separación NS10 usan sus propias muestras fijadas del subconjunto y no son una comparación pareada sobre el universo principal.

k4 es el menos sensible de los tres al escalador, pero el más sensible de los tres al filtro NS10 según ARI. No es invulnerable a decisiones de calidad. Se conserva como recomendación por el conjunto de evidencia; se documenta esa fragilidad en lugar de sustituir el filtro o escoger otra geometría. No se hicieron remuestreos de municipios: estabilidad entre semillas y cambio de muestra de evaluación no equivalen a estabilidad del ajuste ante remuestreo.

## Interpretación y elección entre cuatro, cinco y seis

Los cruces se calcularon sobre las mismas claves. **Las particiones no son jerárquicas.**

- k4→k5: el grupo k4-2 de crecimiento envía 942 unidades a k5-2 y 1,184 a k5-4. Pero k5-2 también recibe 479 de k4-1 y 446 de k4-3. No es una simple división de un solo grupo.
- El patrón adicional plausible de k5 es participación media-baja con cambio presidencial cercano a cero: n=1,872, medias 58.98/45.01%, cambios +0.30/+18.68 pp; IQR de cambio presidencial −3.65 a +4.52 y de intermedio +12.40 a +24.92. No es un perfil trivial por tamaño y k5 es estable entre semillas. Sin embargo, pierde separación en ambas muestras y es más sensible al escalador. Además k5-4, crecimiento más intenso, tiene silhouette media 0.1856 y 13.49% negativa en la segunda muestra. Su utilidad adicional no compensa aquí de forma demostrada la mayor complejidad.
- k5→k6: k5-4 se reparte principalmente entre k6-3 (690) y k6-5 (561); k5-5 entre k6-5 (958) y k6-6 (1,117). También se redistribuye k5-3. k6-3 aporta un crecimiento fuerte (+14.89/+35.48 pp) con 761 unidades; IQR +8.97 a +17.44 / +30.09 a +41.28, pero tiene 12.65–16.57% de silhouette negativa y la solución global es mucho menos estable entre semillas.

**Se recomienda k4** por mejor separación observada en ambas muestras/semillas, tamaños equilibrados, menor sensibilidad al escalador y cuatro patrones descriptivos conservados. k5 no queda científicamente refutado: ofrece un refinamiento plausible que podría justificarse por utilidad sustantiva futura, pero no se mantiene por necesitar cinco fichas. k6 añade complejidad y reasignaciones con menor estabilidad. No se combinan las métricas en una puntuación ni se afirma un k verdadero universal.

Perfiles candidatos, medias simples entre unidades; tasas en %, cambios en pp:

| ID nuevo | Nombre propuesto | Unidades | Municipios* | Presidencial | Intermedia | Cambio presidencial | Cambio intermedio |
|---|---|---:|---:|---:|---:|---:|---:|
| 1 | Menor participación media; descenso presidencial | 1,840 | 837 | 48.4418 | 35.7219 | −7.5790 | +6.3771 |
| 2 | Crecimiento medio en ambos tipos de elección | 2,155 | 779 | 64.5437 | 49.2185 | +7.9693 | +28.5846 |
| 3 | Participación media; descenso presidencial | 2,511 | 1,115 | 64.1276 | 55.7941 | −8.1161 | +3.2817 |
| 4 | Mayor participación media; cambio presidencial cercano a cero | 2,035 | 928 | 78.1001 | 69.5572 | −1.0033 | +15.4785 |

*Los municipios pueden aparecer en varios perfiles por sus distintas edades: no sumar esa columna.* Los nombres son propuestas descriptivas, no motivaciones, propiedades individuales ni equivalencias con los nombres activos. No afirman crecimiento monotónico en todos los comicios.

Dispersión de cambio presidencial (p25 / mediana / p75): perfil1 −12.70/−7.01/−2.36; perfil2 +2.82/+6.92/+11.86; perfil3 −12.26/−7.41/−3.23; perfil4 −4.88/−0.76/+3.38. Los IQR completos de las cuatro features y seis tasas están en `estadisticas_candidato.csv`; los rangos muestran heterogeneidad que una media sola oculta.

La cobertura no cambió respecto a B2: Oaxaca concentra 1,207 de 3,844 exclusiones y Sinaloa/Sonora pierden alrededor de 60% de sus unidades. Las tablas del candidato por entidad y edad describen la población incluida, no eliminan esa selección. Nombres iguales no garantizan fronteras históricas; los grupos etarios son cortes transversales, no cohortes de personas rastreadas.

## Aclaración de la evaluación temporal anterior

Se revisaron `src/modeling.py`, `ml/resultados/validacion_temporal_descriptiva.json` y la model card activa `docs/03_model_card.md`. El diagnóstico anterior ajustaba features 2009–2021, pero elegía unidades a partir de `apto_modelo`, que exige seis elecciones e incluye calidad/disponibilidad de 2024. El eta²=0.543666 es un **resultado histórico leído, no recalculado en B3**.

La expresión anterior «utilidad descriptiva fuera de la ventana de entrenamiento» debe leerse como **diagnóstico retrospectivo condicionado a elegibilidad multianual**, no como validación temporal completamente independiente. No sustenta capacidad prospectiva ni generalización independiente de la selección. Esta aclaración corrige la interpretación excesiva en el informe vigente de B3. Se preserva la model card histórica del modelo activo; B4 debe incorporar esta precisión en la documentación y generadores que adopte. No se rediseñó ni volvió a entrenar el experimento temporal.

## Candidato y comprobación de coherencia

Directorio: `ml/resultados/b3/`. Artefacto recomendado: `candidato_recomendado.joblib`, SHA-256 `246da2f60bf2d951be8c52368a9ea9730b37e5a1d2a028f07b05b9d3801b3865`.

Incluye `model`, `scaler`, `features`, `k`, `label_mapping`, `filters`, `scope` y metadatos de ejecución/decisión. El mapeo 1–4 ordena por media conjunta de centroides presidencial/intermedia; desempata por las cuatro coordenadas en unidades originales y finalmente por etiqueta interna. No es un ranking moral ni una equivalencia con IDs anteriores.

Se exportaron y comprobaron:

- `asignaciones_candidato.csv`: 8,541 claves únicas; recarga en proceso nuevo reproduce todas las asignaciones, comparando por clave.
- `perfiles_candidato.json`: resúmenes recalculados desde las predicciones; conteos, LN, medias, brecha y edades coherentes. Sumas: 8,541 unidades y LN 81,666,826.
- `estadisticas_candidato.csv`: distribución en unidades originales.
- `verificacion_candidato.json`: comprobación efectiva, no un estado escrito antes de ejecutar controles.
- `correspondencia_activo_candidato.csv`: cruce completo con nombres y porcentajes con ambos denominadores explícitos. ARI activo5/candidato4=0.636450; emparejamiento máximo 75.1200% (6,416/8,541). Las 2,125 restantes fuera de ese emparejamiento no son errores de clasificación: cambió el número de grupos.

Resumen del cruce: activo1→nuevo1, 1,351/1,366; activo3→nuevo3, 1,940/1,964; activo4→nuevo2, 1,184/1,259; activo5→nuevo4, 1,941/2,080. Activo2 se redistribuye principalmente en nuevos1/2/3 (479/942/446). No se puede renombrar simplemente el antiguo perfil 3 ni reutilizar textos y aprobaciones por igualdad de ID.

## Adopción pendiente de B4 y Rubén

**Nada de lo siguiente se hizo en B3.** La aplicación sigue sirviendo cinco perfiles y su artefacto original.

| Consumidor / pieza | Cambio a revisar coordinadamente en B4 |
|---|---|
| `src/prepare_product.py` | `LABELS` fijo 1–5, texto `KMeans k=5 exploratorio` y preparación desde resultados activos. Adoptar nuevas asignaciones/nombres/estadísticas como una entrega coherente, no mezclar archivos de versiones diferentes. |
| `src/dashboard_api.py` | Ruta activa a `kmeans5_exploratorio.joblib`; verificar bundle/orden de features/mapeo y correspondencia con `perfiles.json`. La validación de CSV y las fórmulas permanecen; no se cambian silenciosamente. `ApprovalRequest` permite hasta 6 y luego valida existencia: no asumir que requiere el mismo cambio que una lista fija de cinco. |
| `src/education.py` | Texto de metodología fijo «cinco clusters»; actualizar al número adoptado y generar fichas desde resúmenes nuevos. API y revisión/PDF siguen bajo Rubén. |
| `datos/processed/producto/*`, `ml/modelos/*`, resultados activos | Adopción coherente de artefacto, observaciones, perfiles y metadatos; registrar versión de entrega, entorno y huellas. No promover uno solo de estos archivos. |
| `dashboard/index.html`, textos JS y generadores de reportes/notebooks | Revisar menciones a cinco y rangos, sin rediseñar UI. Los bucles dinámicos pueden continuar, pero los textos no deben prometer cinco. |
| `tests/test_dashboard.py` | Mantiene aserción de cinco y rango 1..5 para el activo. En B3 no se rebajó. B4 deberá probar cuatro, ausencia del ID retirado, correspondencia de nombres, CSV, borradores, PDF y transición de aprobaciones. |
| Aprobaciones SQLite/PDF existentes | El ID nuevo no equivale al anterior. Definir versionado/invalidación de aprobaciones y trazabilidad de PDF; no reutilizar una aprobación de la ficha antigua por su ID numérico. |
| Model card, README, docs/generadores y contrato | Distinguir activo/candidato, explicar la recomendación k4 y el diagnóstico temporal condicionado. Hiram/Rubén deben cerrar adopción y revisión de nombres; B3 no congela ese contrato. |

Campos que necesita Rubén: bundle con escalador/modelo/features/mapeo/umbral/scope; por unidad claves, `perfil_id`, features y tasas/observados requeridos por el producto; por perfil `perfil_id`, `nombre`, `n_unidades`, `municipios`, `porcentaje_unidades`, `lista_nominal_2024`, `edad_predominante`, las cuatro medias/cambios y `brecha_pres_intermedia`, con notas de alcance. No se alteró el contrato actual por iniciativa de B3.

## Ejecución y pruebas reales

Comandos desde la raíz, entorno ya creado:

```powershell
& .\.venv\Scripts\python.exe -B -m src.evaluate_clustering --root .
& .\.venv\Scripts\python.exe -B -m src.evaluate_clustering --root . --select
& .\.venv\Scripts\python.exe -B -m src.evaluate_clustering --root . --verify
$testB3 = Join-Path $env:TEMP ('bread-and-circ-b3-tests-' + [guid]::NewGuid().ToString('N'))
& .\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider --basetemp $testB3 tests
git status --short --branch
```

`--select` lee la decisión revisada `seleccion.json`, no decide k por un máximo automático. Para una comparación metodológica nueva debe registrarse un protocolo antes de observar sus resultados. Repetir este protocolo reproduce el mismo diseño y sobrescribe únicamente sus salidas B3.

Creación efectiva del entorno en esta laptop:

```powershell
& "$env:APPDATA\uv\python\cpython-3.11-windows-x86_64-none\python.exe" -m venv .venv
& .\.venv\Scripts\python.exe -m pip install --disable-pip-version-check -r requirements-b3.txt
```

Para reconstruir exactamente todas las versiones registradas, usar Python 3.11.15 y `pip install -r ml/resultados/b3/environment.lock.txt` en un entorno aislado. No se cambia el Python global.

Resultados reales: comparación exit 0; selección exit 0; verificación independiente exit 0. **16 pruebas aprobadas**: doce existentes y cuatro pruebas agrupadas de B3, sin fallos. La única advertencia es la deprecación previa del TestClient Starlette/httpx. Ya no aparecen las dos advertencias de versión sklearn. `pruebas.txt` conserva el comando real y el transcript UTF-8. No se ocultaron advertencias ni se modificaron pruebas anteriores.

Las pruebas B3 cubren orden de features pese a columnas reordenadas, False explícito, etiquetas inválidas/nulas, features no finitas o fórmulas alteradas, calidad inválida, duplicados/universos diferentes, comparación por clave, ARI invariante a permutación, desempate de IDs, serialización/predicciones/resúmenes, corrupción deliberada de estadísticas y protección de salida/entorno. El control B2 de datos reales se ejecutó por sus huellas; los mocks del test sintético aíslan ese control y no se usan en la ejecución real.

Los experimentos se repitieron durante el desarrollo para completar diagnósticos y trazabilidad; las tablas finales corresponden al código cuya huella figura en `ejecucion.json`. No hubo fallos de ajuste o aserciones. Un comando auxiliar de inspección falló por comillas de PowerShell y se corrigió sin modificar datos ni resultados.

## Archivos y lectura de evidencia

Nuevos: `src/evaluate_clustering.py`, `tests/test_evaluate_clustering.py`, `requirements-b3.txt`, este informe y `ml/resultados/b3/`. No se modificaron archivos versionados de la base, incluidos B2, modelo servido, módulos de Rubén y app.

- `protocolo.json`, `preparacion.json`, `ejecucion.json`, `referencia.json`, `environment.lock.txt`: diseño, trazabilidad y compatibilidad.
- `comparacion.csv`, `tamanos_grupos.csv`, `estadisticas_grupos.csv`, `silhouette_grupos.csv`: separación, tamaño y dispersión sin ocultar grupos.
- `estabilidad_pares.csv`, `estabilidad_resumen.csv`: todos los pares ARI y su rango.
- `sensibilidad.csv`, `sensibilidad_perfiles.csv`, `sensibilidad_distribuciones.csv`: universos, métricas y cambios descriptivos de ambos escenarios.
- `cruces.csv`, `comparacion_particiones.csv`, `correspondencia_activo_candidato.csv`, `impacto_particion.json`: solapamientos sin equiparar IDs.
- `muestras_evaluacion.csv`, `muestras_NS10.csv`, `asignaciones_experimentos.csv`: claves y asignaciones que permiten repetir comparaciones.
- `candidatos/`: tres bundles de referencia semilla42 y sus resúmenes; el recomendado y su paquete están en el directorio B3 principal.

No hay commit, push, merge ni PR de B3. Propuesta: `feat: evaluate clustering candidates and recommend four profiles`. Sigue pendiente autorización expresa de Hiram antes de un commit.

## Límites y siguiente paso

B3 compara únicamente K-Means 4/5/6 con las features y filtro principal existentes. No agrega variables, ponderación poblacional, nuevas familias de modelos, remuestreo municipal, auditoría RAW ni homologación geométrica. La separación y sensibilidad aconsejan una adopción exploratoria con advertencias. Alta estabilidad no prueba verdad sustantiva; clustering no demuestra causalidad. B4 debe acordar adopción y contrato con Rubén, manteniendo los datos y la app actuales hasta ese paso.

Referencias técnicas primarias consultadas el 28/10/2026: [persistencia y compatibilidad de scikit-learn](https://scikit-learn.org/stable/model_persistence.html#security-maintainability-limitations), [parámetros y convergencia de KMeans 1.8](https://scikit-learn.org/1.8/modules/generated/sklearn.cluster.KMeans.html), [silhouette por observación](https://scikit-learn.org/1.8/modules/generated/sklearn.metrics.silhouette_samples.html).
