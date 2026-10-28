# Dashboard funcional — alcance y endpoints

## Visión

Aplicación FastAPI con interfaz HTML/CSS/JavaScript y gráficos Plotly distribuidos localmente. Funciona en `localhost:8501` sin cuenta, internet o clave API. Incluye exploración de participación nacional y perfiles, filtros de entidad/municipio/edad, clasificador de nuevos **agregados compatibles**, auditoría territorial, generación y aprobación local de fichas PDF.

### Entradas y salidas

- `GET /`: interfaz principal.
- `GET /health`: diagnóstico rápido.
- `GET /api/summary`, `/api/profiles`, `/api/states`: datos agregados y catálogos.
- `GET /api/observations?estado=&perfil=&edad=&q=&limit=&offset=`: observaciones filtradas.
- `GET /api/territory-audit`: estados de identidad municipal observados, no equivalencia geométrica certificada.
- `GET /api/template`: plantilla CSV con datos ficticios.
- `POST /api/classify` (multipart con campo `file`): valida CSV, normaliza 4 features y devuelve asignación de perfil como CSV, hasta 2MB/5000 filas.
- `GET /api/draft/{profile_id}`: roles automatizados de datos, narrativa y validación.
- `POST /api/approve`: revisión humana afirmativa y registro SQLite local (no publica contenido).
- `GET /api/approved-pdf/{approval_id}`: PDF aprobado con información de quien revisó.

### Reglas del clasificador

Entradas requeridas: `tasa_YYYY`, `observados_YYYY` y `ns_pct_YYYY` para cada `YYYY = 2009, 2012, 2015, 2018, 2021, 2024`. Las tasas son porcentajes [0,100]; `observados` >=100 por año; NS [0,20]% por año; no se aceptan valores faltantes. La observación debe representar datos **agregados**, no personas. Se reutilizan el escalador y centroides sin reentrenar.

**Limitación:** un registro solo de 2024 o de 2027 no es compatible; requerirá rediseño de features y reentrenamiento de todo el modelo. Ningún cambio automático en modelos preexistentes.

### Operación y riesgos

- Para uso local o demo. No hay autenticación, controles multiusuario ni hardening para Internet pública.
- No se almacenan los CSV enviados; se procesan en memoria y la respuesta es un nuevo CSV. Los aprobados se registran en SQLite local.
- El "flujo de agentes" no llama a modelos generativos: son módulos deterministas auditables, listos para un reemplazo posterior por LLM bajo controles y revisión humana.
- No clasifica a ciudadanos ni genera propaganda focalizada; solo fichas estadísticas/educativas neutrales.
