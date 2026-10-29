# B2 — auditoría independiente de procesados

**Decisión: APTO CON ADVERTENCIAS para iniciar B3 exploratorio.** No hay diferencias materiales pendientes en estructura, aritmética, reconciliación, panel o elegibilidad. Esto no valida el modelo, la elección de k ni los perfiles.

Ejecución del 28 de octubre de 2026, zona `America/Tijuana`. Checkout inicial limpio, rama `feat/analysis-dashboard`, base `eee428ecf2bd3eb8a13b172e354e525d4de97b43`. El módulo, pruebas, documentación y evidencia de B2 están **sin commit**; sus huellas están en `analisis/reportes/b2/resultados.json`. No se atribuye este código nuevo al SHA base.

## Qué se comprobó ahora y qué se hereda

Se leyeron completos los seis `municipio_edad.csv`, los doce agregados secundarios por sexo/tipo de sección, nombres anuales, auditorías JSON, serie, matriz, auditorías nominales, reportes nacionales/edad/sexo/sección/cobertura/exclusiones y copias pertinentes del producto. Se contrastó también el universo de las observaciones segmentadas y del dashboard con la elegibilidad reconstruida, y los totales de unidades/LN de las fichas con ese universo. No se evaluaron las asignaciones de perfiles ni su utilidad estadística.

La extracción original confiable es una **premisa aportada por Hiram**. Los controles, hashes de ZIP, microfilas, edades originales, faltantes DEL e incidencias RAW descritos en documentos anteriores y `auditoria.json` son evidencia heredada. B2 **no abrió ni descargó RAW**, no reprodujo los 54,872,712 registros originales y no certificó geografía histórica. Sí verificó que los totales agregados actuales coinciden con los JSON y que los metadatos de microfilas son coherentes entre los reportes. No se deducen microfilas contando agregados. Los SHA-256 actuales dan trazabilidad, no certifican procedencia oficial.

## Método y protección

- Módulo: `src/validate_processed.py`; no importa ni ejecuta `pipeline.panel`, `reporting.summarize`, entrenamiento ni construcción del producto.
- Claves compuestas de entidad/municipio, normalizadas en memoria a cadenas de dos/tres dígitos. No se modifica la representación de los archivos originales, no se une por nombres ni se hace fuzzy matching.
- Unicidad antes de unir: `(anio, EDOCVE, MPIOCVE, grupo_edad)`, y las dimensiones adicionales en secundarios. No se usa `drop_duplicates`, `first` ni sumas para resolver duplicados. Las sumas de secundarios eliminan solamente la dimensión sexo/sección, después de comprobar su unicidad.
- `LN/SV/NV/NS`: finitos, íntegros y no negativos; sin rellenar errores o nulos con cero. Los conteos se conservan como enteros para las identidades aritméticas. Se rechazan magnitudes mayores de `2**53` para evitar comparaciones flotantes inexactas; no se encontraron.
- Reconstrucción independiente: concatenación anual y seis joins `one_to_one`, alineados por claves. La identidad nominal se recompone de nombres anuales usando la regla documentada, sin reutilizar la transformación del pipeline.
- `observados=SV+NV`; `tasa=100*SV/observados`; `ns_pct=100*NS/LN`. Denominador cero implica nulo, nunca tasa cero. Todos los valores definidos están en 0–100.
- Conteos, claves y booleanos se comparan exactamente. Para tasas/features CSV de precisión completa: `atol=1e-10` puntos porcentuales y `rtol=0`, sin redondear antes. JSON de evidencia sin NaN/Infinity.
- Los booleanos CSV aceptan únicamente `True`/`False` explícitos; otras etiquetas o nulos se informan como error. Se exige disponibilidad de todos los años antes de aplicar umbrales; mínimos/máximos descriptivos que omiten nulos no determinan elegibilidad por sí solos.
- Se contrastan las cuatro features y también brecha/curvaturas descriptivas. Las medias disponibles de unidades incompletas reproducen el contrato existente; esas unidades no se admiten al modelo.
- Reconstrucciones separadas en `analisis/reportes/b2/`. La comprobación SHA-256 antes/después confirma que durante la ejecución no cambiaron los insumos, código ni consumidores inventariados. No se sustituyeron panel, modelo, perfiles ni contratos de Rubén.

## Totales recalculados desde CSV

Las seis igualdades nacionales `LN=SV+NV+NS` y las 73,895 igualdades por fila del agregado principal pasan. Los secundarios también pasan y sus marginales coinciden exactamente con el principal por clave. No hay conversiones fallidas, negativos, fracciones ni duplicados. Las tasas nacionales se calculan desde las sumas, **no** como media de tasas municipales.

| Año | Filas agregadas | Municipios | LN | SV | NV | NS | Participación observada % | NS/LN % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2009 | 12,290 | 2,458 | 77,481,831 | 33,316,974 | 42,298,963 | 1,865,894 | 44.060783 | 2.408170 |
| 2012 | 12,275 | 2,455 | 76,490,962 | 47,383,154 | 28,939,159 | 168,649 | 62.082964 | 0.220482 |
| 2015 | 12,290 | 2,458 | 83,563,462 | 36,926,612 | 41,517,874 | 5,118,976 | 47.073560 | 6.125854 |
| 2018 | 12,315 | 2,463 | 89,123,997 | 51,784,399 | 31,249,856 | 6,089,742 | 62.365103 | 6.832887 |
| 2021 | 12,340 | 2,468 | 93,532,133 | 46,389,189 | 43,099,624 | 4,043,320 | 51.837976 | 4.322921 |
| 2024 | 12,385 | 2,477 | 98,330,348 | 54,899,228 | 37,105,466 | 6,325,654 | 59.670029 | 6.433064 |

Los valores completos están en `totales_anuales.csv`. Los totales coinciden exactamente con las seis auditorías JSON, `auditoria_resumen.csv`, `resumen_nacional.csv` y la copia nacional del producto. No fue necesario invocar una explicación por exclusión etaria: la diferencia de conteos CSV frente a esas referencias es cero. Las incidencias etarias de RAW permanecen sin verificación nueva.

## Panel y exclusiones

| Medida | Recalculado |
|---|---:|
| Filas de la serie | 73,895 |
| Unidades distintas municipio × edad | 12,385 |
| Municipios en la unión | 2,477 |
| Municipios presentes en los seis años | 2,455 |
| Unidades con seis tasas válidas | 11,925 |
| Unidades con identidad nominal estable | 12,195 |
| Elegibles | 8,541 |
| Excluidas únicas | 3,844 |
| Municipios con al menos una edad elegible | 1,825 |
| Municipios con las cinco edades elegibles | 1,598 |
| Falsos incluidos / falsos excluidos frente a `apto_modelo` | 0 / 0 |

No hay pérdidas ni filas extra en la serie o la matriz guardadas. No hay discrepancias de conteos, tasas, NS, observados, identidad, indicadores ni features respecto a la reconstrucción. El pivote `aggfunc='first'` del pipeline **no oculta duplicados en esta base** porque se verificó la unicidad antes de construir el panel de control; B2 no cambia el pipeline.

| Causa superpuesta | Unidades |
|---|---:|
| Falta al menos una tasa | 460 |
| Identidad nominal inestable | 190 |
| Algún año con menos de 100 observados | 863 |
| Algún año con NS mayor de 20% | 3,307 |
| Falta algún conteo anual o NS anual | 110 |

La última causa explicita años ausentes y está contenida en las tasas incompletas: no añade excluidos únicos. No sumar estas filas. `combinaciones_exclusion.csv` contiene las 16 combinaciones presentes, incluida la combinación elegible sin causas; la unión de causas es exactamente 3,844 unidades.

Hay 38 claves con variantes nominales, equivalentes a 190 unidades. Se preserva la exclusión conservadora, incluidos posibles renombres inocuos. Una clave estable no certifica límites históricos. `identidad_nominal.csv` distingue además claves no observadas los seis años.

### Tasas indefinidas y ausencias

| Año | Unidad ausente en ese CSV | Presente, con cero observados | Total sin tasa respecto al panel |
|---|---:|---:|---:|
| 2009 | 95 | 35 | 130 |
| 2012 | 110 | 5 | 115 |
| 2015 | 95 | 150 | 245 |
| 2018 | 70 | 65 | 135 |
| 2021 | 45 | 50 | 95 |
| 2024 | 0 | 60 | 60 |

Son 780 celdas unidad-año sin tasa: 415 ausencias y 365 filas presentes con cero observados. No equivalen a 780 unidades distintas; son 460 unidades con alguna tasa ausente. No hay LN cero en ninguno de los 18 agregados: el manejo de ese denominador se comprobó con casos sintéticos. Los ejemplos se identifican por clave en `controles.csv`; las ausencias del principal están completas en `tasas_ausentes.csv`.

## Cobertura y diagnóstico de selección

| Cobertura | Numerador | Denominador y universo | % |
|---|---:|---|---:|
| Unidades elegibles | 8,541 | 12,385 unidades de la unión histórica | 68.962455 |
| Municipios representados | 1,825 | 2,477 claves de la unión histórica | 73.677836 |
| LN 2024 del panel | 81,666,826 | 98,330,348 LN de todas las unidades del panel en 2024 | 83.053531 |
| LN 2024 nacional procesada | 81,666,826 | 98,330,348 LN sumada del agregado anual 2024 | 83.053531 |

Se comprobó la igualdad de ambos denominadores LN 2024. Aquí la cobertura del panel coincide con la nacional **del agregado procesado de las cinco edades**; no es una validación de un denominador oficial externo. La cobertura por municipios significa al menos una edad elegible, no cinco edades en cada municipio.

- Oaxaca concentra 1,207 exclusiones, el **31.40% de los 3,844 excluidos**; pierde 42.35% de sus propias 2,850 unidades.
- Exclusión dentro de entidad: Sinaloa 60.00% (60/100), Sonora 59.72% (215/360), Nuevo León 57.25% (146/255), Campeche 53.85% (35/65), Chihuahua 53.73% (180/335) y Chiapas 53.23% (330/620). Son porcentajes de unidades, no de población.
- Por edad, se excluye 32.74% de 18–24 (811/2,477), 31.01% de 25–34 (768/2,477), 31.85% de 35–44 (789/2,477), 30.36% de 45–59 (752/2,477) y 29.23% de 60+ (724/2,477).
- Los incluidos cubren 83.9296% de LN 2009 y 83.0535% de LN 2024. La tabla anual también distingue presencia temporal del grupo y cobertura de unidades respecto a cada agregado anual.
- En 2024, participación ponderada por observados: **59.9714% incluidos frente a 58.0503% excluidos**; medias simples entre unidades con tasa: 61.9716% y 61.9920%. Son estimandos distintos. La cercanía de las medias simples no demuestra ausencia de sesgo.
- En 2024, NS ponderado por LN: **5.0123% incluidos frente a 13.3964% excluidos**. En 2015: 4.3313% y 15.2387%; en 2018: 5.1690% y 15.2081%. Los excluidos tienen mucho más NS en esos cortes. No se infiere que el filtro cause diferencias de participación.

Las tablas por entidad, edad y su cruce cubren todos los grupos, no solo estos ejemplos. Las reducciones anuales separan tasas disponibles y registros ausentes. El filtro puede afectar representatividad; no se cambiaron los umbrales 100/20 para mejorar cobertura. La sensibilidad y decisiones de ponderación se reservan a B3. Los grupos etarios son cortes transversales, no personas seguidas longitudinalmente.

## Pruebas, incidencias y coordinación

- Antes de los cambios: **8 pruebas existentes aprobadas**, tres advertencias.
- Después: **12 aprobadas** (ocho existentes y cuatro pruebas agrupadas de B2), con las mismas tres advertencias previas. Transcript: `analisis/reportes/b2/pruebas.txt`.
- Los casos B2 cubren selección válida/excluida, causas superpuestas, conteos inválidos e inconsistentes, denominadores cero, claves duplicadas/cardinalidad, año ausente, parsing booleano, orden de filas distinto y corrupción deliberada de tasa/elegibilidad/conteo en el panel guardado. También verifican salida bloqueada ante insumos ausentes y rechazo de un directorio de salida protegido.
- Un primer intento de la nueva prueba con `tmp_path` falló en su preparación por permisos del directorio global `pytest-of-Hiram`; **no fue un fallo de los datos ni una aserción del validador**. Se repitió con `--basetemp` en una carpeta temporal nueva y pasó. Los comandos reproducibles incluyen esa opción.
- Durante la revisión del validador se añadió un caso límite de enteros grandes que garantiza que la igualdad aritmética se compruebe antes de perder precisión; se corrigió el manejo del tipo numérico del módulo. Una advertencia de tipo introducida en ese fixture se eliminó usando una conversión explícita en la prueba. No se rebajaron aserciones existentes.
- Dos advertencias previas de `InconsistentVersionWarning`: KMeans y StandardScaler persistidos con scikit-learn **1.8.0**, entorno actual **1.9.1**. La prueba de inferencia pasa, pero la documentación oficial no soporta cargar artefactos con otra versión. Es una coordinación de reproducibilidad del modelo/backend para Rubén y B3/B4; no impide verificar los CSV con pandas/NumPy. No se cambió el artefacto, la inferencia ni requirements. Referencia: [scikit-learn, persistencia y compatibilidad](https://scikit-learn.org/stable/model_persistence.html#security-maintainability-limitations), consultada el 28/10/2026.
- Una advertencia previa de deprecación del TestClient de Starlette con httpx; las pruebas siguen pasando. Se registra sin modificar contratos ni añadir httpx2 al proyecto.
- En el entorno temporal existente solo se instalaron pytest y httpx, necesarios para las pruebas. No se repitió la instalación del programa ni se agregaron dependencias al repositorio.

## Repetir desde la raíz del proyecto en PowerShell

Estos comandos usan el intérprete del entorno que ya existe en esta laptop. `python` sin ruta apunta aquí a MSYS2 y no es el mismo entorno. El módulo no contiene rutas personales.

```powershell
$pythonB2 = Join-Path $env:TEMP 'bread-and-circ-runtime-win-20261028\Scripts\python.exe'
& $pythonB2 -B -m src.validate_processed --root . --out analisis/reportes/b2
$pytestB2 = Join-Path $env:TEMP ('bread-and-circ-b2-pytest-' + [guid]::NewGuid().ToString('N'))
& $pythonB2 -B -m pytest -q -p no:cacheprovider --basetemp $pytestB2 tests
git status --short --branch
```

Resultado real de auditoría: **756 controles pasan, 20 advertencias, 7 no comprobados y 0 bloqueos; exit code 0**. Los siete no comprobados son seis metadatos RAW etarios y el origen/extracción RAW, expresamente fuera del CAMINO B y sin marcarlos como aprobados. Las advertencias incluyen denominadores cero bien tratados, variantes nominales y límites de selección/geografía. El validador devuelve código distinto de cero cuando hay fallos materiales o un insumo esencial no comprobado; se probó con insumos ausentes.

En otra máquina o si desaparece el entorno temporal, usar un Python compatible con pandas/NumPy y, para la suite existente, las dependencias de ejecución más pytest/httpx. El validador solo importa biblioteca estándar, pandas y NumPy. No ejecutar `src.pipeline`, `src.reporting`, `src.modeling` o `src.prepare_product` para repetir B2: esos comandos pueden sobrescribir la base o entrenar.

## Evidencia y siguiente bloque

Entrada principal para revisión: `analisis/reportes/b2/RESUMEN.md`; evidencia completa: `resultados.json` y `controles.csv`. Los CSV de control, selección, cobertura, ausencias e identidad están en ese mismo directorio. `diferencias_elegibilidad.csv` tiene solo cabecera porque no hay falsos incluidos o excluidos.

Los resultados existentes no requieren corrección ni adopción de un panel nuevo: la reconstrucción coincide con la base. No se modificaron los archivos de Rubén, el modelo, los perfiles, la API ni el dashboard. No se hizo commit, push, merge ni PR. Mensaje de commit sugerido para revisión posterior: `feat: add independent processed-data audit for B2`.

Se corrigió una imprecisión documental del README: llamaba «filas agregadas originales» a 54,872,712 microregistros documentados. Ahora distingue ese número heredado de las 73,895 filas anuales municipio × edad contadas en B2.

B3 puede evaluar sensibilidad, pesos, modelo y k con el universo confirmado. B4 debe cerrar el contrato de perfiles con Rubén. La certificación geométrica y una eventual auditoría de RAW exigirían un alcance separado.

## Contexto para continuar en otro chat

Hiram y Rubén trabajan en el Reto 1 del Hackathon INE. B2 quedó ejecutado en `feat/analysis-dashboard`, base `eee428e`, **APTO CON ADVERTENCIAS**. Módulo nuevo `src/validate_processed.py`, pruebas `tests/test_validate_processed.py`, informe `docs/10_auditoria_procesados_B2.md`, evidencia y reconstrucciones en `analisis/reportes/b2/`. Se confirmaron desde los seis procesados 73,895 filas de serie, 12,385 unidades, 11,925 completas, 8,541 elegibles, 1,825 municipios representados y 3,844 excluidas únicas. LN 2024 elegible 81,666,826/98,330,348 = 83.0535%; unidades 68.9625%; municipios 73.6778%. Sin discrepancias materiales, duplicados ni cambios de elegibilidad; los originales y contratos están intactos. La exclusión es desigual, la identidad es nominal y RAW se acepta por premisa de Hiram, sin nueva verificación. Auditoría exit 0; 12 tests pasan con tres advertencias previas, incluidas versiones de sklearn 1.8.0 del artefacto frente a 1.9.1 del entorno. No se entrenó ni cambió k/perfiles. No hay commit/push/merge/PR; antes de cualquier commit Hiram debe recibir propuesta en Conventional Commits e inglés y autorizarlo. Hiram lleva datos/modelo/analítica; Rubén agentes, clasificación CSV y aprobación/PDF. El siguiente bloque es B3, únicamente con un encargo nuevo; B4 cerrará el contrato con Rubén.
