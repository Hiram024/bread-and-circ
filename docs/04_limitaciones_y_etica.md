# 04 — Limitaciones, ética y control de calidad

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
