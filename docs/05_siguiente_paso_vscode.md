# 05 — ¿Continuar aquí o pasar a VS Code?

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
