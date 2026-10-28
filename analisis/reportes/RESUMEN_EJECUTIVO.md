# Resumen ejecutivo — evidencia del análisis CCPC 2009–2024

## Qué se hizo
Se recorrieron 192 CSV alojados en seis ZIP oficiales, se calcularon controles de calidad y se agregaron los conteos por municipio y cinco grupos etarios. Se construyó un panel de seis elecciones y se compararon 9 configuraciones de clustering.

## Auditoría anual
| Año | Tipo | Filas | Municipios | Participación observada | NS / LN |
|---|---|---:|---:|---:|---:|
| 2009 | Intermedia | 8,706,843 | 2,458 | 44.06% | 2.41% |
| 2012 | Presidencial | 8,604,456 | 2,455 | 62.08% | 0.22% |
| 2015 | Intermedia | 9,106,059 | 2,458 | 47.07% | 6.13% |
| 2018 | Presidencial | 9,251,122 | 2,463 | 62.37% | 6.83% |
| 2021 | Intermedia | 9,430,502 | 2,468 | 51.84% | 4.32% |
| 2024 | Presidencial | 9,773,730 | 2,477 | 59.67% | 6.43% |

**Nota:** SV/(SV+NV) excluye NS; son tasas de *participación observada* en los cuadernillos, no porcentajes de cómputos oficiales. Las elecciones no son intercambiables: 2009, 2015 y 2021 son intermedias; 2012, 2018 y 2024 presidenciales.

## Matriz histórica y exclusiones

- Filas municipio × edad identificadas en al menos un año: **12,385**.
- Panel con tasa válida en seis años: **11,925**.
- Panel elegible del experimento: **8,541** (1,825 municipios; cobertura de LN 2024 83.1%).
- 38 códigos municipales muestran más de una grafía normalizada del nombre entre elecciones; sus 190 unidades municipio-edad quedan excluidas conservadoramente.
- Filtros: cobertura temporal completa, clave con nombre consistente, >=100 SV+NV por año, y NS/LN <=20% en cada año.

Motivos *superpuestos* (no sumar las filas):

| motivo                             |   n_unidades |
|:-----------------------------------|-------------:|
| Falta al menos una tasa            |          460 |
| Nombre municipal inconsistente     |          190 |
| <100 observados en alguna elección |          863 |
| NS >20% en alguna elección         |         3307 |

## Comparación de modelos
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

*Silhouette calculado con muestra aleatoria fijada de hasta 2,000 registros.* Escalado StandardScaler. k=4 maximiza esta métrica entre las alternativas probadas. La separación general es moderada: los perfiles **no** son clases inequívocas.

## Cinco perfiles exploratorios (no clases verdaderas)
| Perfil | Unidades | Municipios | Presidencial | Intermedia | Cambio presidencial | Cambio intermedio |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 1,366 | 655 | 46.6% | 34.6% | -9.8 pp | +3.4 pp |
| 2 | 1,872 | 900 | 59.0% | 45.0% | +0.3 pp | +18.7 pp |
| 3 | 1,964 | 897 | 64.3% | 57.0% | -9.0 pp | +0.2 pp |
| 4 | 1,259 | 482 | 68.7% | 52.7% | +11.4 pp | +33.5 pp |
| 5 | 2,080 | 949 | 77.6% | 69.1% | -1.4 pp | +14.9 pp |

**Interpretación:** la media presidencial refleja 2012/2018/2024 y la intermedia 2009/2015/2021. Los cambios miden la diferencia entre extremos dentro de cada categoría (2012→2024 y 2009→2021). Las medias no están ponderadas por población de las unidades; los tamaños LN se reportan separadamente.

## Robustez y prueba temporal descriptiva
- ARI entre semillas de KMeans: k=4: 0.966, k=5: 0.974, k=6: 0.801.
- Para k=5: ARI al cambiar StandardScaler por RobustScaler: 0.794; al reajustar con NS<=10%: 0.863.
- Clustering de cinco grupos ajustado **solo con 2009–2021**: la pertenencia a esos grupos explica descriptivamente un 54.4% de la variación entre las tasas 2024 (eta²). Este diagnóstico **no** constituye validación predictiva causal ni garantía de generalización.

## Qué no sabemos aún
1. No hay homologación geográfica certificada por INE. Nombres iguales no garantizan fronteras inmutables.
2. La tasa de NS varía considerablemente entre años, por lo que los observados pueden no ser una muestra aleatoria.
3. No hay variables de escolaridad, ingreso o intención de voto; no se infieren.
4. El modelo no usa microdatos ni permite etiquetar ciudadanos particulares.
5. La evaluación interna de clustering favorece ciertas geometrías; se requiere contrastar utilidad sustantiva con analistas.

## Decisión recomendada
**Avanzar a VS Code para convertir este pipeline en un prototipo reproducible y un dashboard**, sin cerrar aún el modelo ni presentar perfiles como definitivos. Mantener este análisis como línea base y priorizar tablas de homologación municipal verificadas, validación con expertos e interpretación de los clusters antes de automatizar contenidos.
