# B3 — APTO PARA B4 CON ADVERTENCIAS

Recomendado: **K-Means k=4, StandardScaler, n_init=30, semilla 42**. No adoptado por el producto.

Informe y comandos: [`docs/11_evaluacion_modelo_B3.md`](../../../docs/11_evaluacion_modelo_B3.md).

| k | Silhouette muestras 64 / 2026, seed42 | Davies-Bouldin | ARI semillas, media [mínimo, máximo] |
|---|---|---|---|
| 4 | 0.247070 / 0.251644 | 1.186598 | 0.963304 [0.928580, 0.987496] |
| 5 | 0.232284 / 0.238248 | 1.217939 | 0.970438 [0.953057, 0.985856] |
| 6 | 0.222114 / 0.228712 | 1.210639 | 0.822530 [0.704082, 0.996685] |

Dos muestras comunes de 2,000 unidades, ajuste en las 8,541 elegibles; no son intervalos de confianza. Sensibilidad k4: ARI RobustScaler 0.869001 en 8,541; NS10 0.842758 en 5,671 comunes (LN 2024 nacional procesada cubierta 57.8616%).

Referencia activa k5 examinada con sklearn1.8.0 y reproducida: predicciones coincidentes en 8,541 claves, ARI=1 y escalador/centros sin diferencias. Las 89 huellas B2 coinciden; 131 archivos originales permanecen intactos. No se repitió B2 ni se sobrescribió el artefacto activo.

Candidato: `candidato_recomendado.joblib`; SHA-256 `246da2f60bf2d951be8c52368a9ea9730b37e5a1d2a028f07b05b9d3801b3865`. Recarga en proceso nuevo: 8,541 asignaciones por clave reproducidas; estadísticas y sumas de perfiles coherentes (LN 81,666,826). Ver `verificacion_candidato.json`.

Perfiles nuevos: n=1,840 / 2,155 / 2,511 / 2,035; propuestas de nombres y medias en `perfiles_candidato.json`, IQR en `estadisticas_candidato.csv`. Los IDs no equivalen a los activos. Cruce 5×4 y nombres en `correspondencia_activo_candidato.csv`; ARI=0.636450. Revisión/adopción del contrato pendiente de B4 con Rubén.

Pruebas: **16 aprobadas**, una deprecación previa Starlette/httpx; sin advertencias sklearn de versiones. Transcript real: `pruebas.txt`. Entorno reproducible: Python3.11.15 y `environment.lock.txt`; intención de dependencias en `requirements-b3.txt` de la raíz.

Límites: separación moderada, sensibilidad a calidad/escalado, cobertura desigual, geografía nominal, evaluación temporal previa retrospectiva condicionada. No se hizo remuestreo municipal ni auditoría RAW. No se alteraron agentes/API/PDF/app ni se hizo commit/push/merge/PR.
