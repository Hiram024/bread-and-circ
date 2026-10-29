# Guía de entrega — decisión VS Code y siguiente fase

> Documento histórico anterior a la adopción B4. Se conserva como referencia; sus menciones a k5, rutas o aprobación no describen el activo actual. Consulte el [contrato vigente del README](../README.md#contrato-de-integración-para-rubén--b4), el descriptor activo y la [memoria de Hiram](00_memoria_tecnica_Hiram.md).

## Estado de la entrega

**Preparado y ejecutable:** lectura de resultados oficiales 2009–2024, notebooks originales (4) y de producto (2), agregaciones procesadas, cinco perfiles estadísticos exploratorios, comparación y estabilidad del clustering, modelo `joblib`, interfaz web, filtros, importador CSV válido, fichas PDF de demostración, flujo automatizado de validación y aprobación humana local, pruebas API.

**Pendiente para publicación institucional:** tabla oficial de cambios de fronteras 2009–2024, validar el modelo sobre geografía armonizada, revisión humana de todas las fichas, seguridad para internet, autenticación, persistencia de nuevos lotes, reentrenamiento versionado, integración institucional de comunicaciones (no incluida), entregables legales firmados.

## Cómo arrancar

1. Abrir `hackathon_ine_proyecto/` en VS Code.
2. Instalar Python 3.11. Opcional: extensiones Python/Jupyter.
3. Ejecutar `run.bat` (Windows) o `./run.sh` (Mac/Linux), o crear un entorno virtual manualmente y hacer `pip install -r requirements-app.txt`.
4. Abrir http://127.0.0.1:8501.
5. Probar 'Panorama', 'Perfiles', 'Explorador' y 'Auditoría'.
6. En 'Clasificar CSV', descargar plantilla, sustituir las cifras ficticias por agregados válidos y subir.
7. En 'Fichas', producir borrador, revisar con personas responsables y exportar PDF.
8. Ejecutar `python -m pytest -q tests` desde la raíz.

## Decisión de desarrollo

Es momento de pasar a VS Code para implementación y demos: las rutas principales ya son funcionales y los datos procesados están incluidos. Es posible completar el MVP sin requerir inicialmente los 54.8 millones de filas de origen, pero los seis ZIP originales se conservan para auditoría/reprocesamiento.

### Criterios de aceptación para el hackathon

- Aceptación documental Reto 1: 4–6 perfiles con metodología y estrategias educativas neutrales diferenciadas, fichas iconográficas y documento técnico de 8–12 páginas (revisar manualmente versión final).
- Reproducibilidad: misma versión del dataset, código y semillas; verificar hashes SHA-256.
- Elegibilidad: 100% de conteos no negativos, LN=SV+NV+NS, seis años completos, filtros documentados.
- Dashboard: lectura y segmentación de agregados, nunca identificación o predicción individual.
- Fichas: evidencia trazable, borrador no publicado, aprobación humana.

## No confundir

La calidad de clustering no es "accuracy" supervisada. K-Means k=4 tiene silhouette 0.247, k=5 0.232, k=6 0.222 en la evaluación disponible. La pérdida al escoger cinco es un compromiso de interpretación de perfiles con el reto, no optimización absoluta. La sensibilidad a RobustScaler es ARI 0.794 en k=5 y las fronteras municipales permanecen por verificar.
