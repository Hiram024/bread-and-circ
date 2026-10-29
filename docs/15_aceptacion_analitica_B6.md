# B6, camino B — aceptación analítica sistemática

Base efectiva `c3170d9d95d4eeeb7d22f9a62518f3010b4f28c4`, rama `feat/analysis-dashboard`, remoto Hiram024/bread-and-circ. B5 fue publicado con autorización de Hiram; el checkout estaba limpio al iniciar B6. Fecha/zona efectivas en los JSON:America/Tijuana. Las adiciones B6 permanecen locales sin commit/push y no se atribuyen únicamente al SHA base.

Esta aceptación comprueba fuente → cálculo → API → pantalla y sus universos; no valida científicamente el clustering ni atribuye aprobación a Rubén. El dictamen independiente y las ejecuciones finales están en [docs/16_QA_B6.md](16_QA_B6.md). La matriz numérica es `analisis/reportes/b6/matriz_trazabilidad.csv`; para interpretar capas de pantalla se lee junto con ese dictamen, que separa evidencia nueva de B5 reutilizada.

## Base, protocolo y brechas

Se comprobó el puntero activo, manifiesto, hashes y versión servida `ccpc-2009-2024-k4-v1`, digest `ae5243026dc27552abec02bafaba94819cb49b8dd6877416b79b188fccde1ed4`. Servidor conocido PID24988en127.0.0.1:8501al comprobar; no se detuvo ni reemplazó. Los bytes HTML/JS/CSS servidos se comparan por SHA256 con el checkout, evitando aceptar una caché o proceso distinto. SQLite real seguía ausente y no se crearon aprobaciones ficticias allí.

Al inicio coincidieron las263huellas de la pasada finalB5, incluidas fuentes, frontend y contratos. Esa cantidad es una referencia histórica de archivos, no una medida de calidad. Las nuevas adiciones de documentación no invalidan las cifras/controles B5 cuando código/datos correspondientes permanecen iguales. El inventario final distingue cambios documentales legítimos de insumos protegidos.

Brechas que justifican trabajo nuevo: reconciliar4820/4930desde panel, consolidar matriz por indicador y fórmula independiente, recorrer páginas completas sin pérdida/duplicación, teclado funcional ampliado y zoom real200%. Se reutilizan los controles B5 vigentes de respuesta antigua/error/nulos/HTML,fixture103filas,CSV/aprobación/PDF y anchos1440/390, identificando sus archivos/huellas y límites. La suite previa31tests se ejecutó nuevamente como línea base:31passed,1advertencia previa,exit0,49.30s (`qa_baseline_tests.txt`); no se copió su resultado anterior.

Ponytail full: un único script de aceptación de lectura, sin framework, dependencias nuevas, entrenamiento o nuevas pantallas. `verificar_trazabilidad.py` no importa helpers de `src.analytics`, pipeline ni reporting para fabricar sus esperados; usa pandas/NumPy y biblioteca estándar, suma los seis CSVanuales, reconstruye tasas/features de elegibles por clave y consulta HTTP de la aplicación real. No ejecuta B2/B3 completos ni recupera RAW. Su salida dentro del repo solo puede ser `analisis/reportes/b6`; otros directorios internos quedan protegidos. Temporales externos permiten negativos de QA.

## Reconciliación de incidencias: ambas cifras tienen contexto

Fuentes localizadas:

- `analisis/reportes/causas_exclusion_superpuestas.csv`, último cambio Git `081229d`:cuatro categorías, generado por `src/reporting.py` desde el panel guardado. La copia B2 `exclusiones_superpuestas.csv` mantiene esas cuatro para contrastar el reporte histórico.
- `analisis/reportes/b2/elegibilidad_y_causas.csv`, publicado en `a5794fd`:cinco indicadores por unidad, incluido `faltan_conteos_o_ns`. B2 reconstruye elegibilidad con los seis años explícitos, sin esconder ausencias por mínimos/máximos.
- `src/analytics.py`, publicado enB5`c3170d9`:expone los cinco indicadores B2 vinculados al paquete y sus combinaciones. B5 no cambió elegibilidad.

|Causa sobre el mismo panel de12,385unidades|Reporte histórico,4causas|B2/B5 vigente,5causas|Diferencia comparable|Fórmula independiente|
|---|---:|---:|---:|---|
|Falta alguna tasa|460|460|0|Alguna tasa ausente/no finita entre los seis años|
|Identidad nominal inestable|190|190|0|Flag conservador nominal no estable, heredado de B2 aprobado|
|Observados menores de100|863|863|0|Existe un valor presente de observados<100; NaN no cumple esa comparación|
|NS mayor de20%|3307|3307|0|Existe NS presente>20%|
|Faltan conteos o NS|No desglosado|110|No comparable como cambio de conteo; añade110incidencias al desglose|Existe observados oNS ausente en algún año|
|Suma de incidencias reportadas|4820|4930|+110por categoría adicional|Suma de flags, con solapamientos|
|Unión de excluidas|3844|3844|0|Cada unidad cuenta una vez|

La categoría ausente del reporte histórico **no significa que antes hubiese cero unidades con faltantes**. El CSV comparativo conserva esa celda vacía, diferenciando ausencia de desglose de cero. Las cinco causas generan15combinaciones presentes entre excluidas; las combinaciones suman3844unidades, mientras los flags suman4930incidencias, nunca personas distintas.

La comprobación de faltantes es más precisa que una explicación verbal:

-110unidades tienen algún observado ausente y las mismas110algúnNSausente. Representan415celdas anuales ausentes.
-De esas110,21también tienen algún valor presente<100;89no tienen valores presentes bajos.
-Así, «existe algún valor<100» cuenta863; «no cumple seis valores>=100» cuenta863+110−21=952. No sustituimos una condición por la otra ni redefinimos la causa histórica para hacer coincidir cifras.
-Las110ya tienen al menos una tasa ausente:ya están en la unión de las cuatro causas. La unión de cuatro y cinco permanece3844;las8541elegibles coinciden exactamente por claves con el paquete. Falsos incluidos/excluidos:0.
-Los365ceros de SV+NV anuales pertenecen a355unidades;5también tienen años ausentes.110+355−5=460unidades sin seis tasas. La ausencia no se convierte en participación0.

`casos_faltantes.csv` identifica las110claves, años sin observados, solapamiento con<100 y condición excluida. `reconciliacion_causas.csv` registra fórmulas/conteos; `resultados.json` conserva versiones,hashes y resultados de unión/intersección. No se reescriben reportes históricos ni insumos B2 para borrar la diferencia; no cambia modelo/población/filtros/contrato.

## Matriz y resultados numéricos

`matriz_trazabilidad.csv` registra identificador,pantalla,fuente,versión,clave/universo,fórmula/denominador,ponderación,unidad,precisión,endpoint/campo,componente,efecto de filtros,esperado independiente,observado API,diferencia,tolerancia,estado y efecto de aceptación. El estado numérico no afirma por sí solo una interacción de navegador:su evidencia de pantalla es el informeQA y los artefactos referidos. No se usa coincidencia entre copias de un resumen como única validación de fórmula.

La ejecución numérica incluye135controles sobre todos los años/perfiles y casos representativos, sin convertir su cantidad en criterio autónomo de calidad. Conteos/conjuntos/huellas:igualdad exacta;tasas/medias/cambios:atol1e−10, sin redondear antes. Presentación actual:1decimal para porcentajes,2para cambiospp;hover2decimales,conteos con separadores. La matriz conserva precisión completa además de la representación esperada; el navegador revisa los valores efectivamente mostrados.

|Año/tipo|Participación nacional%|NS/LN%|
|---|---:|---:|
|2009Intermedia|44.0607831124|2.4081697295|
|2012Presidencial|62.0829638641|0.2204822578|
|2015Intermedia|47.0735597656|6.1258543836|
|2018Presidencial|62.3651034142|6.8328869945|
|2021Intermedia|51.8379755467|4.3229207656|
|2024Presidencial|59.6700294444|6.4330637780|

Nación significa los cinco grupos de edad de los procesados, no certificación RAW nueva. Participación=100*sum(SV)/(sum(SV)+sum(NV));NS=100*sum(NS)/sum(LN). No se promedian tasas municipales. Intermedias2021−2009=+7.7771924343pp;presidenciales2024−2012=−2.4129344197pp. Se calcularon con valores completos y se muestran+7.78/−2.41pp.

Los cuatro perfiles se verifican sobre las asignaciones activas alineadas por entidad+municipio+edad y features recalculadas desde los conteos anuales, no copiadas de perfiles.json. Tamaños1840/2155/2511/2035suman8541. Proporciones21.5431/25.2312/29.3994/23.8262%usan8541como denominador. Las medias/cambios son simples entre unidades;no se incorpora peso poblacional. Los municipios por perfil se superponen por edades y no se suman como únicos nacionales. Los nombres aprobados B4 permanecen intactos.

|Cobertura|Numerador|Denominador explícito|Porcentaje|
|---|---:|---:|---:|
|Unidades elegibles/panel|8541|12385unidades municipio×edad|68.9624545822%|
|Municipios representados/panel|1825|2477claves municipales|73.6778360920%|
|LN2024elegible/nacional procesado|81666826|98330348registrosLN2024de cinco edades|83.0535309404%|

Los denominadores LNdel panel y nacional coinciden en esta base, no por definición general. La cobertura de LN no mide precisión del modelo. Se mantiene la restricción de extrapolar a excluidas, cortes transversales y geografía histórica no certificada.

El script recorre las86páginas de100sin filtros:8541claves en orden,sin pérdidas/duplicación y mismo total/resumen completo en todas. Comprueba entidad,perfil,edad,combinado,búsqueda literal AGUAS,regex literal `.*`,vacío y detalle de seis tasas/observados de una clave. Ejemploestado2/edad18-24:5unidades/5municipios,LN446745;limit100o2no redefine el universo. La fixture manual B5de103filas detecta el error de resumir solo la primera página;la de19/110detecta confundir tasa agregada con media simple50%. Su vigencia y nueva ejecución quedan enQA.

## Navegador, teclado y zoom: alcance

El control nativo de captura se detuvo porque no pudo determinar con suficiente confianza la URL de Chrome para aplicar su política; no se volvió a utilizar. QA registró la limitación y probó una vía legítima con ChromeQAen perfil temporal propio,URLconocida y preferencias del navegador, sin tocar el perfil del usuario ni simular zoom medianteviewport,CSSzoom,DSF oCDPpageScale.

La prueba preliminar de zoom real usa preferencia Chromium `partition.default_zoom_level` con nivel log(2)/log(1.2)=3.8017840169:misma ventana física1442×978,al100%innerWidth1427/DPR1.25;al200%innerWidth713/DPR2.5,visualViewport.scale=1yCSSzoom=1enambos. Es zoom del navegador, distinto de los anchos emulados B5. El recorrido completo,teclado puro,estados,capturas y fuentes oficiales del mecanismo se registran enQA;la prueba preliminar sola no certifica aceptación visual completa.

No se declara conformidadWCAG ni uso de lector de pantalla si no se ejecutó. No se instalan herramientas adicionales de accesibilidad por completar una lista. Las afirmaciones normativas o límites están delimitadas en el informe independiente.

## Repetir y límites por bloque

Desde la raíz del proyecto con el servidor local actual y .venv:

```powershell
& .\.venv\Scripts\python.exe -B analisis\reportes\b6\verificar_trazabilidad.py --root . --out analisis/reportes/b6 --base-url http://127.0.0.1:8501
$qaB6Temp = Join-Path $env:TEMP ('ccpc-b6-tests-' + [guid]::NewGuid().ToString('N'))
& .\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider --basetemp $qaB6Temp tests
```

El primero solo haceGETy lecturas de fuentes;genera matriz/comparativa/casos/resultados,retorna1si hay discrepancias y0si pasan. QAregistra sus comandos de navegador/zoom y pasada final en `docs/16_QA_B6.md`. No ejecutar entrenamiento,reporting o pipeline para esta aceptación.

B7:revisión/aceptación conjunta deRubén y recorrido coordinado, no recibida. B8/B10:documento técnico y revisión visual final. Reproducibilidad/cierre:notebook completo y otros entornos requeridos;Linux/macOS/Docker/otros navegadores no comprobados aquí. B9:preparación/ensayo de presentación. B6no cierra ninguno por asociación, ni añade mapas,nuevasfeatures,LLM,autenticación o publicación.

Hay dos correcciones funcionales acotadas de presentación:los títulos de ejes Plotly utilizan `title.text` y el menú permite desplazamiento vertical propio al zoom200%;no cambia el contrato B4/B5. El resto del diff principal contiene herramienta/evidencia/documentación de aceptación. El resultado final y cualquier corrección posterior deben coincidir con el dictamen independiente, no interpretarse a partir de conteos de pruebas. Propuesta de commit,no ejecutado:`fix: complete analytical acceptance and restore chart and zoom accessibility`.

## Defecto de presentación detectado durante B6

QAsemántico en Chrome156 comprobó que Plotlylocal3.3.1ignoraba `yaxis.title`/`xaxis.title` como cadenas:el layout resuelto devolvía «Click to enter Y axis title», y las unidades no aparecían como título de eje. Las cifras/tablas eran correctas,pero el control de unidad del gráfico fallaba. Evidencia de reproducción:`analisis/reportes/b6/qa_axis_probe.txt`. No se rebajó la aserción para aprobarlo.

El principal cambió cuatro configuraciones a `title:{text:...}`;la función `historyLayout` cubre tanto nacional como detalle. Fuente primaria:[Plotly ejeY title.text](https://plotly.com/javascript/reference/layout/yaxis/#layout-yaxis-title-text) y [ejeX](https://plotly.com/javascript/reference/layout/xaxis/#layout-xaxis-title-text). No se cambió biblioteca,datos,modelo,features,nombres,umbrales,API ni editorial de fichas. QA vuelve a comprobar ejes resueltos/renderizados,zoom,teclado y regresión JScon SQLite temporal. La evidencia visual B5 anterior se conserva como histórica;los gráficos afectados necesitan aceptación nueva sobre JSactual.

Incidencia de implementación del verificador (no de la aplicación):su primer comando devolvióexit1por `SyntaxError: unmatched ')'` en la función que añade filas a la matriz. Se corrigió el paréntesis antes de producir evidencia válida y se repitió el comando completo:verificacion.txtregistraexit0y135controlespasa. No se cambió una expectativa para ocultar ese fallo. Las ejecuciones iniciales132y135fueron de integración;la salida vigente corresponde al script/hash y fecha de resultados.json, no a la primera versión escrita.

## Reanudación del29/10/2026 y segundo defecto corregido

Al retomar el checkout seguía en c3170d9con las ediciones locales B6 conservadas. El servidor anterior ya no escuchaba en8501;la primera comprobación devolvióConnectionRefused/WinError10061. Confirmado el puerto libre,se inició `.\.venv\Scripts\python.exe -B -m uvicorn src.dashboard_api:app --host 127.0.0.1 --port 8501`,PID32428al comprobar,sin detener servicios desconocidos. `analisis/reportes/b6/reanudacion.json` registra fecha/zona,salud,mismo paquete/digest y hashes de los bytes servidos HTML/JS/CSS. Se comprobaron170archivos de los prefijos protegidos allí indicados,sin cambios;ese número no sustituye el inventario final QA ni mide calidad. SQLite real sigue ausente.

El último defecto QA anterior era distinto del overflow global:alzoomreal200%el menú sticky de100vhcarecía de scrollvertical propio. Aunque el DOMrecibía foco,Auditoría quedaba entre459.8y527.4conviewportCSSde414dealto;la persona no veía el control. Evidencia original `qa_nav_zoom_probe.json`/PNG. El principal añadió una regla `.sidebar{overflow-y:auto}`;QA exigió que cada uno de los seis botones al recibir foco quede dentro de la vista. Integración posterior:Auditoría200%top173/bottom240.6,dentro414. No se rediseñó navegación ni cambió contrato/modelo/datos.

El navegador volvió a recorrer cuatro pantallas100/200con teclado y títulos/unidades de ejes efectivos. CapturasCDPde sololectura representan el viewportreal;las primeras capturasPlaywrightfullPagecortadas por coordinación de zoom se conservan como fallo del harness,no como imagen válida de aceptación. QA inspeccionó conview_imagelas cuatro vistas finales200%. El rechazo anterior de control nativo se conserva y no se volvió a usar esa vía.

La regresión nueva reutiliza el harness B5 sin modificarlo mediante un wrapper que escribe únicamente enB6:CSVválido/inválido,asincronía/error/nulos/HTML,aprobación/PDF/tokensobsoletos y anchos1440/390pasaron en integración. La suite completa/pasada estable y dictamen formal corresponden aQA16,distintos de estas ejecuciones intermedias. No se declara aprobación deRubén,B7uotrosbloques.

## Cierre B6 — aceptación con advertencias

**B6: COMPLETADO CON ADVERTENCIAS. qa_b6:APROBADO CON ADVERTENCIAS no bloqueantes en integración.** La suite completa posterior a las dos correcciones ejecutó **32passed,1advertencia previa Starlette/httpx,exit0**, sin cambiar los31tests anteriores y con un grupo nuevo B6justificado. La matriz numérica ejecutada devuelve135pasa,0fallas;no cambia elegibilidad ni contrato. Los registros `qa_integration_tests.txt`/`qa_integration_state.json` distinguen este resultado de la pasada final formal posterior al cierre documental.

Navegador real Chrome156:cuatro vistas100/200con zoom real de navegador,teclado,filtros,paginación/detalle,títulos/unidades de ejes y los seis botones del menú enfocados dentro deviewport. Regresión del harness B5contra código actual con salida B6:CSVválido/inválido,asincronía/error/nulos/HTML,revisión/aprobación/PDFy rechazo de versión obsoleta,anchos1440/390,exit0. CeroerroresJS y cero solicitudesexternas durante esos recorridos. Las capturas finales de zoom utilizan CDPsololectura,no una imagen recortada del harness. Datos/modelo/paquete/historial permanecen intactos;no se creóSQLite real.

La pasada formal final se ejecuta después de este cierre documental,con todos los archivos del principal congelados. Sus resultados,comandos,tiempos,huellas del estado exacto y revisión visual autoritativa están en `docs/16_QA_B6.md` y `analisis/reportes/b6/qa_final_resultados.json`, `qa_final_state.json`, `qa_final_pytest.txt`, `qa_final_browser.txt` y `qa_visual_final.json`. El informe QA se excluye de autorreferencia,pero incluye el estado de documentación del principal. Cualquier fallo de esa pasada exige corrección y comprobación correspondiente;no se transforma en éxito por este texto.

Límites no bloqueantes:lector de pantalla no ejecutado,otros navegadores/sistemas no probados,deprecación previa Starlette/httpx y favicon404heredado. Las respuestas422delCSVinválido son negativos esperados. No se afirma conformidadWCAG ni certificación científica del clustering. B7mantiene revisión conjunta conRubén;B8/B10documento técnico/QAvisual final;B9ensayo;reproducibilidad/cierre para notebook y otros entornos requeridos. No se declara su aceptación por asociación.

No se hizo commit,push,merge,PR ni publicación. Propuesta en inglés Conventional Commits:`fix: complete analytical acceptance and restore chart and zoom accessibility`.
