# 02 — Metodología, decisiones y análisis exploratorio

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
