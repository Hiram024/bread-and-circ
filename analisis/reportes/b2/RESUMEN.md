# B2 — APTO CON ADVERTENCIAS

Ejecución: 2026-10-28T20:18:15.780024-07:00 (America/Tijuana).
Base: `eee428ecf2bd3eb8a13b172e354e525d4de97b43`, rama `feat/analysis-dashboard`; código sin commit: True.

Auditoría independiente de todos los CSV procesados. No ejecuta pipeline, reporting ni modelado; no importa sus transformaciones.
Conteos y claves exactos; decimales de precisión completa con atol=1e-10 pp y rtol=0. Booleanos: solo True/False.

## Resultados

```json
{
  "n_panel": 12385,
  "n_completo6": 11925,
  "n_validas": 8541,
  "n_nombre_estable": 12195,
  "n_municipios": 1825,
  "LN_2024_validas": 81666826,
  "LN_2024_total_panel": 98330348,
  "cobertura_LN_2024_pct": 83.05353094041729,
  "excluidas_unicas": 3844,
  "municipios_panel": 2477,
  "filas_serie": 73895,
  "causas_superpuestas": {
    "faltan_tasas": 460,
    "identidad_inestable": 190,
    "observados_menor_100": 863,
    "ns_mayor_20": 3307,
    "faltan_conteos_o_ns": 110
  },
  "municipios_identidad_inestable": 38
}
```

Controles: {'pasa': 756, 'advertencia': 20, 'no comprobado': 7}; bloqueos: 0.

## Hallazgos y límites

- **advertencia** `denominador_cero_tasa` — datos/processed/2009/municipio_edad.csv: 35. No bloquea si se conserva nulo y la unidad no se considera completa.
- **no comprobado** `exclusion_etaria_heredada` — datos/processed/2009/auditoria.json: {'age_lt18_rows': 0, 'age_unclassified_rows': 0}. No bloquea: metadatos heredados; totales CSV/JSON se contrastan por separado.
- **advertencia** `denominador_cero_tasa` — datos/processed/2009/municipio_edad_sexo.csv: 70. No bloquea si se conserva nulo y la unidad no se considera completa.
- **advertencia** `denominador_cero_tasa` — datos/processed/2009/municipio_edad_tipo_seccion.csv: 130. No bloquea si se conserva nulo y la unidad no se considera completa.
- **advertencia** `denominador_cero_tasa` — datos/processed/2012/municipio_edad.csv: 5. No bloquea si se conserva nulo y la unidad no se considera completa.
- **no comprobado** `exclusion_etaria_heredada` — datos/processed/2012/auditoria.json: {'age_lt18_rows': 0, 'age_unclassified_rows': 0}. No bloquea: metadatos heredados; totales CSV/JSON se contrastan por separado.
- **advertencia** `denominador_cero_tasa` — datos/processed/2012/municipio_edad_sexo.csv: 10. No bloquea si se conserva nulo y la unidad no se considera completa.
- **advertencia** `denominador_cero_tasa` — datos/processed/2012/municipio_edad_tipo_seccion.csv: 30. No bloquea si se conserva nulo y la unidad no se considera completa.
- **advertencia** `denominador_cero_tasa` — datos/processed/2015/municipio_edad.csv: 150. No bloquea si se conserva nulo y la unidad no se considera completa.
- **no comprobado** `exclusion_etaria_heredada` — datos/processed/2015/auditoria.json: {'age_lt18_rows': 0, 'age_unclassified_rows': 0}. No bloquea: metadatos heredados; totales CSV/JSON se contrastan por separado.
- **advertencia** `denominador_cero_tasa` — datos/processed/2015/municipio_edad_sexo.csv: 300. No bloquea si se conserva nulo y la unidad no se considera completa.
- **advertencia** `denominador_cero_tasa` — datos/processed/2015/municipio_edad_tipo_seccion.csv: 474. No bloquea si se conserva nulo y la unidad no se considera completa.
- **advertencia** `denominador_cero_tasa` — datos/processed/2018/municipio_edad.csv: 65. No bloquea si se conserva nulo y la unidad no se considera completa.
- **no comprobado** `exclusion_etaria_heredada` — datos/processed/2018/auditoria.json: {'age_lt18_rows': 0, 'age_unclassified_rows': 0}. No bloquea: metadatos heredados; totales CSV/JSON se contrastan por separado.
- **advertencia** `denominador_cero_tasa` — datos/processed/2018/municipio_edad_sexo.csv: 130. No bloquea si se conserva nulo y la unidad no se considera completa.
- **advertencia** `denominador_cero_tasa` — datos/processed/2018/municipio_edad_tipo_seccion.csv: 300. No bloquea si se conserva nulo y la unidad no se considera completa.
- **advertencia** `denominador_cero_tasa` — datos/processed/2021/municipio_edad.csv: 50. No bloquea si se conserva nulo y la unidad no se considera completa.
- **no comprobado** `exclusion_etaria_heredada` — datos/processed/2021/auditoria.json: {'age_lt18_rows': 0, 'age_unclassified_rows': 0}. No bloquea: metadatos heredados; totales CSV/JSON se contrastan por separado.
- **advertencia** `denominador_cero_tasa` — datos/processed/2021/municipio_edad_sexo.csv: 100. No bloquea si se conserva nulo y la unidad no se considera completa.
- **advertencia** `denominador_cero_tasa` — datos/processed/2021/municipio_edad_tipo_seccion.csv: 250. No bloquea si se conserva nulo y la unidad no se considera completa.
- **advertencia** `denominador_cero_tasa` — datos/processed/2024/municipio_edad.csv: 60. No bloquea si se conserva nulo y la unidad no se considera completa.
- **no comprobado** `exclusion_etaria_heredada` — datos/processed/2024/auditoria.json: {'age_lt18_rows': 0, 'age_unclassified_rows': 0}. No bloquea: metadatos heredados; totales CSV/JSON se contrastan por separado.
- **advertencia** `denominador_cero_tasa` — datos/processed/2024/municipio_edad_sexo.csv: 120. No bloquea si se conserva nulo y la unidad no se considera completa.
- **advertencia** `denominador_cero_tasa` — datos/processed/2024/municipio_edad_tipo_seccion.csv: 275. No bloquea si se conserva nulo y la unidad no se considera completa.
- **advertencia** `variantes_nominales` — municipios procesados: 38. No bloquea; nombres iguales no certifican fronteras históricas.
- **no comprobado** `origen_RAW` — seis elecciones: No se abrieron ni recuperaron RAW. No bloquea CAMINO B; no certifica origen oficial ni extracción.
- **advertencia** `limites_territoriales_y_seleccion` — panel: Identidad nominal no prueba geometría; grupos etarios son cortes transversales; cobertura desigual no implica ausencia de sesgo. No bloquea B3 exploratorio; limita representatividad e interpretación.

## Lectura de tablas

- `totales_anuales.csv`: filas agregadas verificadas separadas de microfilas RAW documentadas, sin verificarlas.
- `serie_control.csv`, `panel_control.csv`: reconstrucciones por claves, sin reemplazar originales.
- `controles.csv`, `resultados.json`: esperado/observado, discrepancias, ejemplos, efecto y SHA-256.
- `elegibilidad_y_causas.csv`, `combinaciones_exclusion.csv`: causas superpuestas y excluidos únicos.
- `tasas_ausentes.csv`: distingue unidad ausente de observados cero; no rellena con cero.
- `cobertura.csv`: numeradores, denominadores y universos explícitos. Nacional significa el agregado procesado de cinco edades.
- `seleccion_entidad.csv`, `seleccion_edad.csv`, `seleccion_entidad_edad.csv`: porcentajes con denominador dentro de cada grupo.
- `seleccion_anual.csv`: medias simples separadas de tasas ponderadas por observados y NS ponderado por LN.
- `identidad_nominal.csv`, `nombres_anuales_control.csv`: variantes, años y claves; no homologación geométrica.

Los controles de datos no validan el modelo. B3 decide entrenamiento/k; B4 cierra perfiles. Agentes/API/PDF siguen bajo responsabilidad de Rubén.
La extracción confiable es una premisa del equipo. Las huellas identifican esta ejecución, no prueban origen oficial.
