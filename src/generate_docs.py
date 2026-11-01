"""Regenerate the narrative docs from already-computed, versioned analysis outputs."""
from pathlib import Path
import json,pandas as pd
R=Path(__file__).resolve().parents[1]
if (R/'datos/processed/producto_activo.json').exists():
    raise SystemExit('Generador histórico k5: no sobrescribe README/model card activos de B4. Consulte docs/00_memoria_tecnica_Hiram.md.')
nat=pd.read_csv(R/'analisis'/'reportes'/'resumen_nacional.csv')
comp=pd.read_csv(R/'ml'/'resultados'/'comparacion_modelos.csv')
prof=pd.read_csv(R/'ml'/'resultados'/'fichas_perfiles_exploratorias.csv')
sens=pd.read_csv(R/'ml'/'resultados'/'sensibilidad.csv')
stab=pd.read_csv(R/'ml'/'resultados'/'estabilidad_semillas.csv')
meta=json.loads((R/'ml'/'resultados'/'resumen_modelado.json').read_text())
temp=json.loads((R/'ml'/'resultados'/'validacion_temporal_descriptiva.json').read_text())
ex=pd.read_csv(R/'analisis'/'reportes'/'causas_exclusion_superpuestas.csv')
fmt=lambda n:f'{int(n):,}'
tab='| Año | Tipo | Filas | Municipios | Participación observada | NS / LN |\n|---|---|---:|---:|---:|---:|\n'
for _,r in nat.iterrows():tab+=f"| {int(r.anio)} | {r.tipo} | {fmt(r.filas)} | {fmt(r.municipios)} | {r.participacion_pct:.2f}% | {r.ns_pct:.2f}% |\n"
mods='| Algoritmo | k | Silhouette* | Davies-Bouldin | Cluster mínimo |\n|---|---:|---:|---:|---:|\n'
for _,r in comp.sort_values(['algoritmo','k']).iterrows():mods+=f"| {r.algoritmo} | {int(r.k)} | {r.silhouette_muestra_2000:.3f} | {r.davies_bouldin:.3f} | {r.min_fraccion*100:.1f}% |\n"
profiles='| Perfil | Unidades | Municipios | Presidencial | Intermedia | Cambio presidencial | Cambio intermedio |\n|---|---:|---:|---:|---:|---:|---:|\n'
for _,r in prof.iterrows():profiles+=f"| {int(r.perfil_id)} | {fmt(r.n_unidades)} | {fmt(r.municipios)} | {r.media_presidencial:.1f}% | {r.media_intermedia:.1f}% | {r.cambio_presidencial_pp:+.1f} pp | {r.cambio_intermedia_pp:+.1f} pp |\n"

(R/'README.md').write_text(f'''# HackINE — Perfiles de participación ciudadana (Reto 1)

Proyecto de **auditoría, preparación, análisis exploratorio y segmentación no supervisada** con las seis bases CCPC del INE (2009, 2012, 2015, 2018, 2021 y 2024).

> **Estado:** análisis exploratorio reproducible completo sobre los ZIP proporcionados; segmentación preliminar, **no** modelo institucional validado ni clasificación de personas.

## Hallazgos principales

- {fmt(nat.filas.sum())} registros originales de 192 archivos estatales (32 por año).
- Sin inconsistencias aritméticas (`LN == SV + NV + NS`) o conteos negativos en el barrido realizado.
- {fmt(meta['n_panel'])} unidades únicas municipio × edad en el panel; {fmt(meta['n_completo6'])} con tasas observables en los seis años.
- {fmt(meta['n_validas'])} unidades aptas para el experimento, {fmt(meta['n_municipios'])} municipios, {meta['cobertura_LN_2024_pct']:.1f}% de la lista nominal de 2024.
- K-Means con k=4 es el mejor entre los algoritmos evaluados según silhouette ({comp.iloc[0].silhouette_muestra_2000:.3f}); **k=5 se conserva como demostración narrativa**, no óptimo probado.
- Existe incertidumbre cartográfica pendiente de conciliar mediante correspondencias oficiales, más allá de la comprobación conservadora de nombres.

## Estructura

```text
HackINE/
├── README.md
├── requirements.txt
├── analisis/
│   ├── notebooks/             # Auditoría y análisis histórico ejecutados
│   ├── reportes/              # CSV y reportes metodológicos
│   └── figuras/               # PNG reproducibles
├── ml/
│   ├── notebooks/             # Clustering reproducible, resultados embebidos
│   ├── resultados/            # Métricas, sensibilidad y etiquetas agregadas
│   └── modelos/               # Artifact sklearn exploratorio (joblib)
├── datos/
│   ├── raw/{{2009,2012,...,2024}}/ # ZIPs íntegros, sin extracción masiva
│   └── processed/{{año}}/     # Agregaciones y auditorías, matrices históricas
├── docs/
│   ├── 01_fuentes_y_diccionario.md
│   ├── 02_decisiones_metodologicas.md
│   ├── 03_model_card.md
│   ├── 04_limitaciones_y_etica.md
│   └── 05_siguiente_paso_vscode.md
├── src/                      # ETL, modelado, reporting y documentación
└── tests/                    # Validaciones automatizadas
```

## Reproducir

Requiere Python 3.10+ (recomendado 3.11) y suficientes recursos para procesar archivos estatales comprimidos.

```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
python -m src.pipeline --root .      # volver a procesar los 6 ZIP: varios minutos
python -m src.modeling --root .
python -m src.reporting .
python -m src.generate_docs
python -m pytest -q tests
jupyter lab
```

Los notebooks **ya contienen salidas ejecutadas** y pueden volver a ejecutarse desde la raíz del repositorio (o desde su carpeta; detectan ambas ubicaciones). **Evite cargar cada CSV original completo a la vez**: el pipeline lee un estado por iteración, y los datos crudos se conservan como ZIP para ahorrar espacio.

### Orden sugerido de lectura

1. [`analisis/reportes/RESUMEN_EJECUTIVO.md`](analisis/reportes/RESUMEN_EJECUTIVO.md)
2. [`docs/01_fuentes_y_diccionario.md`](docs/01_fuentes_y_diccionario.md)
3. [`analisis/notebooks/01_auditoria.ipynb`](analisis/notebooks/01_auditoria.ipynb)
4. [`analisis/notebooks/02_historico.ipynb`](analisis/notebooks/02_historico.ipynb)
5. [`ml/notebooks/03_modelado.ipynb`](ml/notebooks/03_modelado.ipynb)
6. [`docs/03_model_card.md`](docs/03_model_card.md)
7. [`docs/05_siguiente_paso_vscode.md`](docs/05_siguiente_paso_vscode.md)

## Alcance responsable

Los archivos ofrecen **conteos agregados** por sección, edad y sexo; ningún modelo predice ni identifica participación de individuos. El resultado es exploratorio y debe utilizarse únicamente para análisis estadístico y educación cívica neutral, no para persuasión política personalizada. Las categorías demográficas pueden describirse, pero no se usan aquí para dirigir mensajes políticos.

## Documentación externa consultada

- [INE — plataforma oficial CCPC 2009–2024](https://ine.mx/transparencia/datos-abiertos/visualizacion-datos/conteos-censales-participacion/)
- [IBM — CRISP-DM](https://www.ibm.com/docs/en/SS3RA7_18.5.0/pdf/ModelerCRISPDM.pdf)
- [Scikit-learn — pitfalls, pipelines y leakage](https://scikit-learn.org/stable/common_pitfalls.html)
- [Scikit-learn — clustering y métricas de validación](https://scikit-learn.org/stable/modules/clustering.html)
- [Google ML — evaluación de clustering](https://developers.google.com/machine-learning/clustering/kmeans/evaluate-results)
- [Artículo académico sobre inferencia ecológica](https://pmc.ncbi.nlm.nih.gov/articles/PMC33746/)

**Datos originales:** proporcionados por el usuario; los SHA-256 de cada ZIP constan en `datos/processed/{{año}}/auditoria.json`.
''',encoding='utf8')

(R/'analisis'/'reportes'/'RESUMEN_EJECUTIVO.md').write_text(f'''# Resumen ejecutivo — evidencia del análisis CCPC 2009–2024

## Qué se hizo
Se recorrieron 192 CSV alojados en seis ZIP oficiales, se calcularon controles de calidad y se agregaron los conteos por municipio y cinco grupos etarios. Se construyó un panel de seis elecciones y se compararon 9 configuraciones de clustering.

## Auditoría anual
{tab}
**Nota:** SV/(SV+NV) excluye NS; son tasas de *participación observada* en los cuadernillos, no porcentajes de cómputos oficiales. Las elecciones no son intercambiables: 2009, 2015 y 2021 son intermedias; 2012, 2018 y 2024 presidenciales.

## Matriz histórica y exclusiones

- Filas municipio × edad identificadas en al menos un año: **{fmt(meta['n_panel'])}**.
- Panel con tasa válida en seis años: **{fmt(meta['n_completo6'])}**.
- Panel elegible del experimento: **{fmt(meta['n_validas'])}** ({fmt(meta['n_municipios'])} municipios; cobertura de LN 2024 {meta['cobertura_LN_2024_pct']:.1f}%).
- 38 códigos municipales muestran más de una grafía normalizada del nombre entre elecciones; sus 190 unidades municipio-edad quedan excluidas conservadoramente.
- Filtros: cobertura temporal completa, clave con nombre consistente, >=100 SV+NV por año, y NS/LN <=20% en cada año.

Motivos *superpuestos* (no sumar las filas):

{ex.to_markdown(index=False)}

## Comparación de modelos
{mods}
*Silhouette calculado con muestra aleatoria fijada de hasta 2,000 registros.* Escalado StandardScaler. k=4 maximiza esta métrica entre las alternativas probadas. La separación general es moderada: los perfiles **no** son clases inequívocas.

## Cinco perfiles exploratorios (no clases verdaderas)
{profiles}
**Interpretación:** la media presidencial refleja 2012/2018/2024 y la intermedia 2009/2015/2021. Los cambios miden la diferencia entre extremos dentro de cada categoría (2012→2024 y 2009→2021). Las medias no están ponderadas por población de las unidades; los tamaños LN se reportan separadamente.

## Robustez y prueba temporal descriptiva
- ARI entre semillas de KMeans: {', '.join([f'k={int(r.k)}: {r.ARI_semillas_media:.3f}' for _,r in stab.iterrows()])}.
- Para k=5: ARI al cambiar StandardScaler por RobustScaler: {sens.loc[sens.k.eq(5),'ARI_escalador_robusto_vs_estandar'].iloc[0]:.3f}; al reajustar con NS<=10%: {sens.loc[sens.k.eq(5),'ARI_NS_hasta_10_por_ciento'].iloc[0]:.3f}.
- Clustering de cinco grupos ajustado **solo con 2009–2021**: la pertenencia a esos grupos explica descriptivamente un {temp['eta_cuadrada_tasa_2024']*100:.1f}% de la variación entre las tasas 2024 (eta²). Este diagnóstico **no** constituye validación predictiva causal ni garantía de generalización.

## Qué no sabemos aún
1. No hay homologación geográfica certificada por INE. Nombres iguales no garantizan fronteras inmutables.
2. La tasa de NS varía considerablemente entre años, por lo que los observados pueden no ser una muestra aleatoria.
3. No hay variables de escolaridad, ingreso o intención de voto; no se infieren.
4. El modelo no usa microdatos ni permite etiquetar ciudadanos particulares.
5. La evaluación interna de clustering favorece ciertas geometrías; se requiere contrastar utilidad sustantiva con analistas.

## Decisión recomendada
**Avanzar a VS Code para convertir este pipeline en un prototipo reproducible y un dashboard**, sin cerrar aún el modelo ni presentar perfiles como definitivos. Mantener este análisis como línea base y priorizar tablas de homologación municipal verificadas, validación con expertos e interpretación de los clusters antes de automatizar contenidos.
''',encoding='utf8')

(R/'docs'/'01_fuentes_y_diccionario.md').write_text('''# 01 — Fuentes, linaje y diccionario de datos

## Origen
Bases de datos abiertos de los Conteos Censales de Participación Ciudadana (CCPC) del Instituto Nacional Electoral para seis elecciones federales: 2009, 2012, 2015, 2018, 2021 y 2024. Las seis ZIP originales suministradas por el equipo se conservan íntegras en `datos/raw/<año>/`, junto con su diccionario `.txt` **dentro del propio ZIP**. Se calculó SHA-256 para verificar su integridad.

## Columnas originales (16)

| Original | Qué significa / manejo |
|---|---|
| AELEC | Año electoral; verificar contra nombre del ZIP. |
| FELECCION | Fecha jornada electoral; no se utiliza como feature. |
| EDOCVE | Clave de entidad; clave compuesta con MPIOCVE. |
| EDONOM | Nombre de entidad, informativo. |
| MPIOCVE | Clave municipal, no única a nivel nacional. |
| MPIONOM | Nombre municipal, normalización conservadora para detectar choques. |
| SECCION | Sección electoral; no adecuada para panel sin equivalencias. |
| TIPOSEC | Tipo U/M/R: urbano, mixto, rural; agregado descriptivo. |
| DEF | Distrito federal; cartografía puede diferir entre años. |
| DEL | Distrito local; 20,912 valores faltantes en 2024. |
| SEXO | 0 hombres, 1 mujeres; 2024 incluye 2 no binario (LN=105). Agregado descriptivo. |
| EDAD | Edad cumplida; agrupar 18–24, 25–34, 35–44, 45–59, 60+. |
| LN | Lista nominal. |
| SV | Registros con marca de voto. |
| NV | Registros sin marca de voto. |
| NS | Estado no especificado (no debe contarse como abstención). |

**Definición:** `observados=SV+NV`, `participacion_pct=100*SV/(SV+NV)`, `ns_pct=100*NS/LN`. No calculamos `SV/LN` como tasa principal porque NS no equivale a abstención.

## Datos procesados

- `datos/processed/<año>/municipio_edad.csv`: una fila por entidad, municipio, grupo y año, con los cuatro conteos.
- `municipio_edad_sexo.csv` y `municipio_edad_tipo_seccion.csv`: tablas secundarias para caracterización, no features para perfilar personas.
- `municipios_nombres.csv`: nombres observados (puede haber diferentes variantes).
- `auditoria.json`: conteos, checksums, incidencias, cobertura.
- `serie_municipio_edad_2009_2024.csv`: tabla larga de las seis elecciones.
- `matriz_modelo_6_anios.csv`: tabla ancha con features, flags y tasas históricas, incluso filas excluidas.
- `municipios_auditoria_identidad.csv`: indicador *heurístico* de consistencia nominal; no sustituye tabla cartográfica INE.

## Alcance de datos
Los CSV no contienen escolaridad, ingreso, intención de voto, pertenencia individual ni historial de una misma persona. Aunque la plataforma de visualización tiene filtros adicionales, esas variables **no** están entre las 16 columnas de estos seis ZIP. No mezclar inferencias sobre ciudadanos con promedios de municipio–edad.
''',encoding='utf8')

(R/'docs'/'02_decisiones_metodologicas.md').write_text('''# 02 — Metodología, decisiones y análisis exploratorio

Marco: **CRISP-DM** (objetivo → comprensión de datos → preparación → modelado → evaluación → eventual uso institucional). Son ciclos iterativos, no una línea sin revisiones.

## Usuario y problema
Analistas del INE necesitan perfiles estadísticos reproducibles para describir participación ciudadana y diseñar materiales cívicos neutrales. El Reto 1 exige **4–6 perfiles** con descripción, método y estrategias diferenciadas de fomento a la participación.

## Del dato al panel
1. Leer ZIP estado por estado sin modificar crudos.
2. Verificar 16 columnas y `LN == SV + NV + NS`, conteos no negativos y cobertura.
3. Agregar `EDOCVE, MPIOCVE, grupo_edad` y tasas por año.
4. Evaluar estabilidad nominal de clave municipal entre elecciones (se excluye cualquier código con nombres normalizados distintos; genera falsos positivos por renombres y falsos negativos por fronteras similares).
5. Construir matriz ancha 2009–2024 y marcar seis años presentes.
6. Restringir observaciones de entrenamiento: mínimo 100 observados por año, máximo 20% NS/LN en todos los años.
7. Guardar tanto admitidos como no admitidos, y reportar cobertura. El umbral es experimental, no institucional.

## Feature engineering
Para cada unidad *municipio × grupo de edad*:
- `media_presidencial`: media simple de tasas (2012, 2018, 2024).
- `media_intermedia`: media simple de tasas (2009, 2015, 2021).
- `cambio_presidencial_pp`: P2024 - P2012.
- `cambio_intermedia_pp`: P2021 - P2009.
- `brecha_pres_intermedia`: diferencia de medias, variable **descriptiva** no añadida al modelo para evitar redundancia.
- Curvatura de cada serie: tasa intermedia de la serie menos media de extremos; **diagnóstico**, no feature.

**Nota:** no se sigue a las mismas personas en el tiempo; se comparan poblaciones transversales de edad equivalente. Los promedios de tasas por unidad no están ponderados por LN; son una decisión de diseño para dar voz a municipios menores, con el coste de amplificar ruido. Se requiere análisis de sensibilidad ponderado antes de uso institucional.

## Modelos y evaluación
- `StandardScaler` ajustado solo sobre la matriz de entrenamiento; transformaciones guardadas en el mismo artefacto que el modelo.
- K-Means, GaussianMixture (covarianza completa) y Birch; 4, 5 y 6 grupos.
- Métricas: silhouette en submuestra reproducible de n<=2000, Davies-Bouldin (menor mejor), Calinski-Harabasz (mayor mejor), proporción de cluster mínimo, BIC solo GMM.
- Estabilidad K-Means: ARI entre tres semillas; sensibilidad a `RobustScaler` y filtro NS <=10%.
- Prueba temporal separada: ajuste de cinco perfiles con características de 2009–2021, seguido de descripción de diferencias de tasa de 2024 entre grupos. Esto no es evaluación causal ni de predicción individual.

## Selección
K-Means k=4 fue el ganador del criterio silhouette de las nueve variantes evaluadas; k=5 está guardado **solo para demostrar cinco fichas** dentro del requerimiento del hackathon. El k final debe decidirse con evaluación sustantiva, no por silhouette o narrativas impuestas.

## Peligros metodológicos
- Confundir elecciones presidenciales e intermedias.
- Dar lectura individual a tasas agregadas (falacia ecológica).
- Verificar únicamente igualdad de nombres como prueba de geografía estable.
- Tomar NS como NV o asumir NS faltante completamente al azar.
- Elegir k por una única métrica; no evaluar robustez.
- Filtración temporal: no entrenar con 2024 al pretender medir utilidad en datos 2024 retenidos.

## Criterios de aceptación antes del producto
Documentar y resolver equivalencias municipales, revisar efectos de filtros y pesos poblacionales, validar interpretabilidad con especialistas, presentar bandas de incertidumbre/muestras y elaborar fichas de 4–6 perfiles con su cobertura y limitaciones.
''',encoding='utf8')

(R/'docs'/'03_model_card.md').write_text(f'''# 03 — Model card: K-Means 5 (exploratorio)

**Propósito:** particionar {fmt(meta['n_validas'])} grupos agregados municipio × edad según tendencias de participación en elecciones federales. **NO** es clasificación de personas. **NO** recomendado para uso institucional sin revisión geográfica y sustantiva.

## Entradas y features
Cuatro features continuas: `media_presidencial`, `media_intermedia`, `cambio_presidencial_pp`, `cambio_intermedia_pp`, en puntos porcentuales, usando exclusivamente observaciones elegibles con seis tasas y filtros de cobertura.

Transformación `StandardScaler` y `KMeans(n_clusters=5, n_init=30, random_state=42)`. Modelo y escalador guardados en `ml/modelos/kmeans5_exploratorio.joblib`. Etiquetas arbitrarias reordenadas 1–5 según promedio conjunto de participación, **no** ranking de ciudadanía.

## Rendimiento y comparación
{mods}
La métrica que favorece k=4 no respalda afirmar que k=5 es óptimo. Varias particiones alternativas se superponen. ARI semilla k=5: {stab.loc[stab.k.eq(5),'ARI_semillas_media'].iloc[0]:.3f}; ARI escalador robusto: {sens.loc[sens.k.eq(5),'ARI_escalador_robusto_vs_estandar'].iloc[0]:.3f}. El clustering no tiene accuracy frente a etiquetas reales (no existen).

## Descripción numérica de perfiles exploratorios
{profiles}
**Importante:** descripción de centroides/promedios agregados, no tipos esenciales de persona ni relación causal. El nombre puede definirse solo después de revisión de gráficos y evidencia.

## Generalización y evaluación temporal
Para comprobar utilidad descriptiva fuera de la ventana de entrenamiento, un segundo modelo k=5 **ajustado solo con datos 2009–2021** generó grupos con diferencias de tasa 2024 (eta²={temp['eta_cuadrada_tasa_2024']:.3f}). Esta prueba no valida predicción de voto individual ni causalidad.

## Límites
- Excluye unidades sin panel completo, nombre municipal inconsistente, observados <100 o NS>20% cualquier año.
- Cobertura LN 2024: {meta['cobertura_LN_2024_pct']:.1f}%. Los excluidos pueden tener un perfil distinto; no extrapolar sin comprobar sesgo.
- Cambios de claves municipales y fronteras pendientes de homologación institucional.
- Mezcla de poblaciones transversales, no trayectorias individuales.
- Variación de NS no aleatoria potencial y cambios de condiciones electorales.
- No usar como guía para dirigir campañas partidistas o persuasión demográfica individualizada.

## Uso seguro
Exploración institucional, comparación territorial de agregados, materiales neutrales de educación cívica con verificación humana y publicación de supuestos. Para inferencia sobre individuos se requerirían otros datos, otra pregunta de investigación y garantías especiales: **fuera del proyecto**.
''',encoding='utf8')

(R/'docs'/'04_limitaciones_y_etica.md').write_text('''# 04 — Limitaciones, ética y control de calidad

## Riesgos estadísticos de mayor importancia
1. **Falacia ecológica:** un municipio–edad con participación del 70% no implica que una persona de ese grupo tenga probabilidad individual validada del 70%.
2. **No equivalencia de comicios:** las elecciones presidenciales e intermedias tienen diferente contexto y comportamiento agregado.
3. **Datos no especificados (NS):** el faltante podría ser selectivo y variar geográficamente, de modo que excluirlo del denominador no elimina sesgo.
4. **Territorio no homologado:** códigos/nombres iguales no garantizan límites poblacionales estables; se requieren catálogos y crosswalk oficiales por año.
5. **Sesgo de selección:** las observaciones excluidas pueden diferir sistemáticamente; reportar mapas y características de las exclusiones.
6. **Escalas y clusters:** la elección de features y normalización cambia la distancia entre grupos. Silhouette no mide verdad sociológica.
7. **Transversalidad:** grupos etarios en 2009 no son cohortes fijas en 2024.
8. **Categorías sexo:** 2024 agrega una categoría poco frecuente; no inferir características de individuos a partir de ella ni publicarla en celdas pequeñas.

## Límites para agentes / dashboard
- Material educativo neutro, informativo, verificable y no partidista.
- Agentes pueden citar cifras y producir borradores institucionales de comprensión de datos bajo revisión humana.
- No generar mensajes personalizados para influir en preferencias de voto basados en demografía o ubicación individual.
- No incorporar identificadores personales, padrones nominativos ni inferencias sobre intención de voto.
- Control de procedencia y aprobación humana antes de difusión.

## Calidad aún no validada
No se implementó aquí auditoría exhaustiva de duplicados de llave original `entidad-sección-sexo-edad`, cotejo estadístico por casilla con documentos externos, validación cartográfica certificada ni evaluación de error muestral. La auditoría realizada sí comprobó los conteos, rangos de edad, faltantes y columnas por archivo estatal.

## Datos de terceros / propiedad intelectual
Cada ZIP oficial es fuente del INE; conservar documentación y atribución, y respetar las condiciones y entrega del hackathon. Este repositorio es una propuesta académica/experimental y no representa posición institucional del INE.
''',encoding='utf8')

(R/'docs'/'05_siguiente_paso_vscode.md').write_text('''# 05 — ¿Continuar aquí o pasar a VS Code?

## Estado de cierre de fase

**Sí se puede pasar a VS Code** para ingeniería del MVP: ya existen datos raw versionados, ETL reproducible, matriz histórica, análisis, comparativa ML, artefacto de modelo, notebooks y pruebas. No conviene volver a investigar a ciegas desde cero.

**No se debe congelar aún el modelo final**: el matching geográfico es conservador y heurístico; los umbrales de NS y tamaño son experimentales; y el mejor silhouette es de k=4, no k=5. Falta revisión sustantiva de perfiles y ponderación.

## Próximas prioridades técnicas (orden)

1. Abrir carpeta raíz en VS Code, crear entorno virtual, instalar `requirements.txt`, ejecutar `pytest` y los notebooks para confirmar reproducibilidad.
2. Conseguir catálogos de cambios municipales y construir una tabla de equivalencias oficiales que reemplace `identidad_estable_conservadora` sin tocar crudos.
3. Evaluar tratamiento de NS, umbrales, pesos por población y características socio-territoriales; comparar k=4 frente a k=5 mediante interpretación y métricas.
4. Convertir resultados en **4–6 fichas** narrativas precisas, con diferencias presidenciales/intermedias, tendencias y límites.
5. Construir **dashboard mínimo** con: histórico nacional; filtros geográficos/edad; calidad/exclusiones; perfiles y exportación a PDF/PNG.
6. Añadir carga de datos agregados compatible y clasificación **solo de nuevas unidades con features requeridas**. Retraining no automático sin evaluación.
7. Como extensión, un asistente para fichas y materiales de **educación cívica neutra** sujetos a revisión humana y referencias a resultados.

## Definition of Done del MVP del hackathon

- Datos de seis elecciones inspeccionables, cifras y procesos replicables.
- Reglas de elegibilidad y exclusiones explícitas en el dashboard.
- 4–6 perfiles, evidencia de separación/estabilidad y fichas comprensibles.
- Documento técnico de 8–12 páginas y presentación ejecutiva <=10 diapositivas.
- Código o repositorio, fichas visuales, cartas de cesión/declaratoria y paquete completo, conforme a convocatoria.

## Distribución de trabajo sugerida

- **Data/ML:** validación territorial, análisis robustez y perfiles.
- **Backend/Data pipeline:** contratos de archivos procesados, API para consultas y asignación de unidades.
- **Frontend:** tablero con filtros y tarjetas de perfiles, exportación.
- **Documentación y presentación:** metodología, fichas y entregables del INE.

## Qué queda fuera del MVP
Usuarios identificables, campañas persuasivas dirigidas a personas, campañas publicitarias automatizadas, predicción individual de voto, reentrenamiento permanente y despliegue institucional con datos de producción.

## Recomendación de decisión
**Pasar a VS Code ahora para construir el MVP**, mientras dejamos documentadas como decisiones abiertas la equivalencia municipal, la elección k=4 frente a k=5 y la utilidad sustantiva de las fichas. Resolver esos riesgos en paralelo al prototipo evita repetir análisis y no bloquea toda la ingeniería.
''',encoding='utf8')

print('Docs regenerated',len(list((R/'docs').glob('*.md'))))
