# Auditoría de homologación territorial — evidencia y límite

La unidad del experimento es `(EDOCVE, MPIOCVE, grupo_edad)` por seis elecciones. Una coincidencia de nombre y clave es una comprobación **administrativa**, **no** una correspondencia geométrica certificada.

## Resultado operativo

La tabla `datos/processed/producto/homologacion_municipal_auditoria.csv` contiene todas las 2,477 claves, sus nombres observados, los años observados y una categoría:

- `estable_por_nombre_y_clave`: seis años observados, normalización de nombres idéntica.
- `revisar_identidad_nominal`: seis años observados pero nombre divergente, incluidos cambios ortográficos o legales.
- `incompleto_en_serie`: clave no presente los seis años (puede ser nuevo municipio, municipio dividido o reasignación).

Las 8,541 unidades del modelo proceden del filtro conservador previo sobre 6 años y nombre normalizado estable, observados >=100 y NS <=20% por año. **No** se añadieron automáticamente unidades descartadas por parecido ortográfico. Para datos históricos, esta es una precaución contra equivalencias falsas.

La columna `requiere_revision_territorial` se mantiene **True para todas las claves** porque coincidencia administrativa no demuestra límites municipales constantes entre 2009 y 2024. Por ejemplo, la clave Chiapas 07-120 muestra nombres incompatibles en la serie histórica y no se une.

## Qué es necesario para cerrar la equivalencia

1. Obtener los catálogos o polígonos municipales históricos para los seis cortes, con fecha de vigencia, de la Dirección de Cartografía Electoral del INE, evitando usar únicamente el catálogo vigente.
2. Construir un cruce explícito: clave antigua, clave nueva, periodo, tipo de cambio (renombre, fusión, escisión, desplazamiento de límites), porcentaje espacial/poblacional cubierto y fuente.
3. Para escisiones, exigir correspondencia a sección o cartografía: no prorratear votos por nombre o población sin evidencia.
4. Recalcular el panel y el clustering sobre una geografía homologada; comparar ARI, cobertura, perfiles y sesgo por municipio excluido.
5. Solo entonces declarar el análisis longitudinal territorial verificado.

## Referencias institucionales

- INE SIGE, corte cartográfico vigente y catálogos: https://cartografia.ine.mx/sige8/
- INE, productos cartográficos especializados: https://ine.mx/voto-y-elecciones/especializados/
- INE, modificaciones del marco geográfico para elecciones 2024: https://centralelectoral.ine.mx/2023/08/25/aprueba-ine-cambios-en-la-cartografia-electoral-del-pais-rumbo-al-proceso-electoral-del-2024/
- INEGI, catálogo de claves y tablas de equivalencia: https://www.inegi.org.mx/app/ageeml/

**La homologación nominal y auditoría quedan implementadas. La homologación geométrica oficial multianual queda pendiente**, y no se presenta como completada.
