# 03 — Model card: K-Means 5 (exploratorio)

> Documento histórico anterior a la adopción B4. Se conserva como referencia; sus menciones a k5, rutas o aprobación no describen el activo actual. Consulte el [contrato vigente del README](../README.md#contrato-de-integración-para-rubén--b4), el descriptor activo y la [memoria de Hiram](00_memoria_tecnica_Hiram.md).

**Propósito:** particionar 8,541 grupos agregados municipio × edad según tendencias de participación en elecciones federales. **NO** es clasificación de personas. **NO** recomendado para uso institucional sin revisión geográfica y sustantiva.

## Entradas y features
Cuatro features continuas: `media_presidencial`, `media_intermedia`, `cambio_presidencial_pp`, `cambio_intermedia_pp`, en puntos porcentuales, usando exclusivamente observaciones elegibles con seis tasas y filtros de cobertura.

Transformación `StandardScaler` y `KMeans(n_clusters=5, n_init=30, random_state=42)`. Modelo y escalador guardados en `ml/modelos/kmeans5_exploratorio.joblib`. Etiquetas arbitrarias reordenadas 1–5 según promedio conjunto de participación, **no** ranking de ciudadanía.

## Rendimiento y comparación
| Algoritmo | k | Silhouette* | Davies-Bouldin | Cluster mínimo |
|---|---:|---:|---:|---:|
| Birch | 4 | 0.164 | 1.382 | 6.1% |
| Birch | 5 | 0.183 | 1.381 | 6.1% |
| Birch | 6 | 0.185 | 1.226 | 0.1% |
| GaussianMixture | 4 | 0.146 | 1.633 | 15.7% |
| GaussianMixture | 5 | 0.153 | 1.686 | 12.1% |
| GaussianMixture | 6 | 0.125 | 2.121 | 4.0% |
| KMeans | 4 | 0.247 | 1.187 | 21.5% |
| KMeans | 5 | 0.232 | 1.218 | 14.7% |
| KMeans | 6 | 0.222 | 1.211 | 8.9% |

La métrica que favorece k=4 no respalda afirmar que k=5 es óptimo. Varias particiones alternativas se superponen. ARI semilla k=5: 0.974; ARI escalador robusto: 0.794. El clustering no tiene accuracy frente a etiquetas reales (no existen).

## Descripción numérica de perfiles exploratorios
| Perfil | Unidades | Municipios | Presidencial | Intermedia | Cambio presidencial | Cambio intermedio |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 1,366 | 655 | 46.6% | 34.6% | -9.8 pp | +3.4 pp |
| 2 | 1,872 | 900 | 59.0% | 45.0% | +0.3 pp | +18.7 pp |
| 3 | 1,964 | 897 | 64.3% | 57.0% | -9.0 pp | +0.2 pp |
| 4 | 1,259 | 482 | 68.7% | 52.7% | +11.4 pp | +33.5 pp |
| 5 | 2,080 | 949 | 77.6% | 69.1% | -1.4 pp | +14.9 pp |

**Importante:** descripción de centroides/promedios agregados, no tipos esenciales de persona ni relación causal. El nombre puede definirse solo después de revisión de gráficos y evidencia.

## Generalización y evaluación temporal
Para comprobar utilidad descriptiva fuera de la ventana de entrenamiento, un segundo modelo k=5 **ajustado solo con datos 2009–2021** generó grupos con diferencias de tasa 2024 (eta²=0.544). Esta prueba no valida predicción de voto individual ni causalidad.

## Límites
- Excluye unidades sin panel completo, nombre municipal inconsistente, observados <100 o NS>20% cualquier año.
- Cobertura LN 2024: 83.1%. Los excluidos pueden tener un perfil distinto; no extrapolar sin comprobar sesgo.
- Cambios de claves municipales y fronteras pendientes de homologación institucional.
- Mezcla de poblaciones transversales, no trayectorias individuales.
- Variación de NS no aleatoria potencial y cambios de condiciones electorales.
- No usar como guía para dirigir campañas partidistas o persuasión demográfica individualizada.

## Uso seguro
Exploración institucional, comparación territorial de agregados, materiales neutrales de educación cívica con verificación humana y publicación de supuestos. Para inferencia sobre individuos se requerirían otros datos, otra pregunta de investigación y garantías especiales: **fuera del proyecto**.
