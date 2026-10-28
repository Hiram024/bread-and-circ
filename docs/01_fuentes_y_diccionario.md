# 01 — Fuentes, linaje y diccionario de datos

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
