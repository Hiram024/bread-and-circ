"""Produce the contest's 8-12-page technical document from verified project results."""
from pathlib import Path
import pandas as pd
from .product_contract import load_active
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,Image
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT=Path(__file__).resolve().parents[1]
font='/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf'
bold='/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf'
if Path(font).exists():
    pdfmetrics.registerFont(TTFont('IneArial',font));pdfmetrics.registerFont(TTFont('IneArialBold',bold))
FONT='IneArial' if Path(font).exists() else 'Helvetica'; BOLD='IneArialBold' if Path(bold).exists() else 'Helvetica-Bold'
INK=colors.HexColor('#31264f');PURPLE=colors.HexColor('#6f479f')
base=ParagraphStyle('base',fontName=FONT,fontSize=11,leading=16.5,spaceAfter=11,textColor=INK)
heading=ParagraphStyle('heading',parent=base,fontName=BOLD,fontSize=17,leading=21,spaceAfter=16,textColor=PURPLE)
sub=ParagraphStyle('sub',parent=base,fontName=BOLD,fontSize=11,leading=17,spaceBefore=7,spaceAfter=8)
small=ParagraphStyle('small',parent=base,fontSize=9,leading=12)
TITLE=ParagraphStyle('title',parent=heading,fontSize=25,leading=30,spaceAfter=30)
P=lambda x:Paragraph(x,base)
S=lambda x:Paragraph(x,sub)
SM=lambda x:Paragraph(x,small)
story=[]
def section(num,title):
    if story:story.append(PageBreak())
    story.append(Paragraph(f'{num}. {title}',heading))
def txt(*paragraphs):
    for s in paragraphs:story.append(P(s))
def table(data,widths=None):
    t=Table([[Paragraph(str(v),small) for v in row] for row in data],colWidths=widths,repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#efe7f9')),('LINEBELOW',(0,0),(-1,-1),.35,colors.HexColor('#e8e0f0')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),6)]))
    story.append(t);story.append(Spacer(1,9))

def img(path,maxw=15.0,maxh=7.2):
    im=Image(str(ROOT/path));w,h=im.imageWidth,im.imageHeight
    sc=min(maxw*cm/w,maxh*cm/h);im.drawWidth=w*sc;im.drawHeight=h*sc;story.append(im)

package=load_active(ROOT)
profiles=list(package['profiles'].values())
OUT=ROOT/'entregables/reportes'/package['package_version']/'documento_tecnico_reto1.pdf'
comparison=pd.read_csv(ROOT/'ml/resultados/comparacion_modelos.csv')
summary=pd.read_csv(ROOT/'analisis/reportes/resumen_nacional.csv')
section('1','Objetivo y síntesis ejecutiva')
txt('<b>HackINE / Reto 1: Perfiles ciudadanos de participación.</b> Propuesta técnica de segmentación estadística no supervisada a partir de los Conteos Censales de Participación Ciudadana (CCPC) de 2009, 2012, 2015, 2018, 2021 y 2024.',
    f'El producto integra análisis descriptivo de datos electorales agregados, {package["manifest"]["k"]} perfiles exploratorios de la versión {package["package_version"]} sobre unidades <b>municipio × grupo de edad</b>, un dashboard local interactivo, un clasificador de nuevas observaciones compatibles y fichas educativas neutrales sometidas a revisión humana.',
    '<b>Alcance:</b> los perfiles representan agrupaciones de estadísticas poblacionales, no tipos de personas observadas individualmente. El proyecto no utiliza información personal ni estima el comportamiento de voto individual.')
story.append(S('Conclusión del análisis'))
txt('La extracción anterior documentó 54,872,712 registros RAW. B2 comprobó los procesados y confirmó un panel de 12,385 unidades, de las cuales 8,541 cumplen los filtros de elegibilidad. B3 comparó k=4/5/6 bajo protocolo común; B4 adopta localmente el candidato de cuatro perfiles, con silhouette 0.247/0.252 en dos muestras fijadas.',
    'La correspondencia histórica de límites municipales todavía no está certificada. El modelo debe considerarse demostración metodológica, no clasificación institucional lista para aplicación operacional.')
section('2','Fuentes, unidades y variables')
txt('La extracción anterior del equipo documentó seis bases federales y 32 CSV estatales originales por año, con hashes de ZIP. B2 comprobó los CSV procesados, sin revalidar RAW. Las columnas compartidas incluyen entidad y municipio, sección, sexo, edad, lista nominal (LN), sufragó (SV), no votó (NV) y no especificado (NS).')
table([['Año','Tipo','Microfilas documentadas','Participación']]+[[r.anio,r.tipo,f'{r.filas:,}',f'{r.participacion_pct:.1f}%'] for r in summary.itertuples()], [2*cm,3*cm,4*cm,4*cm])
txt('Se construyeron cinco intervalos de edad (18–24, 25–34, 35–44, 45–59, 60+). Cada fila analítica representa una agrupación de conteos en un municipio, grupo etario y año. No es un panel de seguimiento de individuos a lo largo del tiempo.')
section('3','Controles de calidad y tasas')
txt('El barrido total verificó <b>LN = SV + NV + NS</b> y ausencia de conteos negativos para los seis años. La proporción NS y la cobertura electoral cambian entre procesos; por eso se reportan separadamente los registros con estado conocido y los no especificados.',
    'La tasa empleada es <b>100 × SV / (SV + NV)</b>. NS no se trata como abstención y se conserva para estimar la calidad de cobertura. Cuando SV + NV es cero, la tasa se considera ausente, no cero.',
    'Para evitar que unos pocos registros muy pequeños dominen las estimaciones, el conjunto de entrenamiento requiere al menos 100 registros observados por elección y un máximo del 20% de NS en cada año. Se rechazan tasas faltantes de cualquiera de los seis procesos.')
img('analisis/figuras/no_especificados.png',14.5,7)
section('4','Comparabilidad histórica y cartografía')
txt('La identidad geográfica se revisó mediante clave de entidad y municipio, presencia anual y variantes normalizadas de nombre. El producto documenta 2,477 claves municipales: 2,423 estables nominalmente en los seis años; 32 con variaciones nominales y 22 incompletas en la serie.',
    '<b>Advertencia crucial:</b> estabilidad de nombre y clave no demuestra que un polígono municipal conserve idénticos límites. La experiencia con cambios de municipalización y reasignación de claves, especialmente en Chiapas, obliga a no imputar equivalencias cartográficas.',
    'La solución implementa una <b>auditoría conservadora y exclusión de unidades nominalmente ambiguas</b>. Para demostrar equivalencia espacial real se necesitan catálogos históricos por corte, polígonos o correspondencias de secciones aprobadas por el INE; no se sustituyen por aproximaciones inventadas.')
story.append(S('Decisión operativa'))
txt('El dashboard señala explícitamente esta limitación. La aplicación debe evaluarse como prototipo y recalcularse una vez disponible la homologación geográfica oficial de la serie 2009–2024.')
section('5','Selección de muestra y cobertura')
txt('De las 12,385 unidades del panel derivado, 11,925 disponen de una tasa observada en los seis procesos. Después de aplicar elegibilidad temporal, calidad NS, mínimo de observaciones e identidad nominal conservadora, permanecen 8,541 unidades, correspondientes a 1,825 municipios.',
    'Su cobertura equivale a cerca del 83.1% de la lista nominal de 2024 incluida en el panel. Esta reducción de cobertura puede introducir sesgo territorial y demográfico: las unidades pequeñas, nuevas o geográficamente complejas están potencialmente infrarrepresentadas.',
    'No se interpreta el 83.1% como precisión del modelo. Se trata de cobertura de población agregada en el corte más reciente, y debe ser auditada para evaluar representatividad, diferencias de inclusión y posible sesgo por entidad federativa.')
story.append(S('Datos y resultados reproducibles'))
txt('El ZIP entrega el panel largo, una matriz ancha de seis años, los flags de elegibilidad, la tabla de auditoría municipal, observaciones segmentadas y los reportes de sensibilidad. Se preservan las fuentes originales para rehacer cálculos y verificar su procedencia.')
section('6','Ingeniería de features y algoritmo')
txt('Se comparan los procesos presidenciales (2012, 2018, 2024) con las elecciones intermedias (2009, 2015, 2021), debido a sus distintos niveles históricos de participación.',
    'El vector de features tiene cuatro componentes: media presidencial, media intermedia, cambio presidencial 2024–2012 y cambio intermedio 2021–2009, calculados en puntos porcentuales. Las cuatro variables se normalizan mediante StandardScaler antes de aplicar K-Means.',
    'La distancia euclidiana entre centroides agrupa unidades que muestran niveles y trayectorias relativamente similares. El número de clusters se prueba en k = 4, 5 y 6. También se comparan Gaussian Mixture y Birch como familias alternativas.',
    'No se emplean la entidad, el sexo o la edad como variables para inferir afinidades individuales; se conservan solo como descriptores agregados para investigar distribución y cobertura. El modelo no posee una exactitud supervisada.')
section('7','Comparación y robustez del modelo')
table([['Modelo','k','Silhouette','Davies–Bouldin']]+[[r.algoritmo,r.k,f'{r.silhouette_muestra_2000:.3f}',f'{r.davies_bouldin:.3f}'] for r in comparison.sort_values('silhouette_muestra_2000',ascending=False).head(7).itertuples()], [5*cm,1.2*cm,3.2*cm,4*cm])
txt('La comparación histórica de la tabla anterior usa n_init=20 y no se mezcla con B3. B3 fijó n_init=30 y seleccionó cuatro perfiles: mejor separación observada en ambas muestras y tamaños equilibrados. Cinco tuvo ligeramente mayor estabilidad entre semillas; no se afirma que cuatro gane todos los criterios ni sea el número verdadero de grupos.',
    'En B3, k4 obtuvo ARI medio entre semillas 0.9633; sensibilidad RobustScaler 0.8690 y NS10 0.8428 sobre 5,671 unidades comunes. El diagnóstico temporal anterior ajustó features 2009–2021, pero seleccionó unidades por elegibilidad de seis años incluida 2024: es retrospectivo condicionado, no validación temporal independiente.')
section('8',f'{package["manifest"]["k"]} perfiles activos y su caracterización')
table([['Perfil','Unidades','Presidencial','Intermedia']]+[[f'{p["perfil_id"]}. {p["nombre"]}',f'{p["n_unidades"]:,}',f'{p["media_presidencial"]:.1f}%',f'{p["media_intermedia"]:.1f}%'] for p in profiles],[6.7*cm,2.0*cm,2.6*cm,2.6*cm])
txt('Las tasas se expresan como <b>medias no ponderadas de las unidades</b>; una unidad rural pequeña y una urbana grande cuentan igual en la media del perfil. No deben interpretarse como porcentajes representativos de todas las personas que integran el cluster.',
    f'Los nombres y estadísticas de la tabla proceden del paquete {package["package_version"]}. Sus IDs son locales a esa entrega y no se interpretan como equivalencias por posición con la referencia histórica de B3. La comparación entre versiones requiere el cruce de asignaciones por clave.',
    'Las fichas de perfil incluyen magnitudes, fuente, definición metodológica y limitaciones. Cualquier interpretación causal requiere estudios adicionales, no solo clustering de conteos agregados.')
section('9','Interfaz, fichas y trabajo institucional')
txt('El dashboard local ofrece gráficos de evolución nacional, distribución y comparación de los perfiles, filtros de entidad/municipio/grupo de edad, inspección de la auditoría territorial y clasificación de nuevos CSV con la misma estructura temporal de seis elecciones.',
    'El proceso de redacción de fichas usa cuatro etapas: 1) extracción de estadísticas verificadas, 2) narrativa educativa neutral, 3) comprobación mecánica de cifras y expresiones y 4) revisión humana con aprobación explícita antes de descargar el PDF. En el MVP, los módulos operan determinísticamente sin claves de servicios externos.',
    'Las fichas informan sobre variación electoral y transparencia de los datos; no hacen persuasión personalizada ni generan recomendaciones de publicidad política basadas en grupos sociodemográficos. No existe envío de mensajes, autenticación institucional ni publicación en redes.')
story.append(S('Qué requiere un despliegue real'))
txt('Control de usuarios y roles, auditorías de modificaciones, cifrado, alojamiento institucional, estrategia de actualización de datos, validación del modelo sobre cartografía oficial y evaluación de accesibilidad y seguridad. El prototipo está diseñado para localhost.')
section('10','Limitaciones, conclusiones y bibliografía')
txt('<b>Limitaciones:</b> la homogeneidad territorial no está certificada; las tasas no son historiales de las mismas personas; seis eventos son pocos puntos temporales; el clustering no demuestra causas, preferencias electorales ni propensiones individuales; el modelo no puede procesar un año futuro aislado sin cambiar features y reentrenar.',
    '<b>Recomendación:</b> presentar la versión activa de perfiles como descripción estadística exploratoria y registrar incertidumbre. La certificación cartográfica y revisión de sesgo siguen pendientes; no se infiere causalidad ni comportamiento individual.',
    '<b>Reproducibilidad:</b> B4 conserva los procesados auditados y la evidencia histórica, y enlaza modelo, observaciones, perfiles y metadatos mediante su descriptor y hashes. El notebook de producto fue adaptado sin atribuirle una reejecución completa en B4. La documentación anterior de RAW no equivale a una verificación nueva de sus ZIP.')
story.append(S('Referencias principales'))
for r in [
'INE, Conteos Censales de Participación Ciudadana 2009–2024: ine.mx/transparencia/datos-abiertos/visualizacion-datos/conteos-censales-participacion/',
'INE, SIGE 8 y catálogos cartográficos: cartografia.ine.mx/sige8/',
'INE, Marco Geográfico Electoral, actualización 2023: centralelectoral.ine.mx/2023/08/25/aprueba-ine-cambios-en-la-cartografia-electoral-del-pais-rumbo-al-proceso-electoral-del-2024/',
'Scikit-learn, clustering y métricas: scikit-learn.org/stable/modules/clustering.html',
'Convocatoria Hackea la Participación 2026, Reto 1; copia proporcionada por el equipo.',
]:story.append(SM(r))

def footer(canvas,doc):
    canvas.saveState();w,h=A4
    canvas.setStrokeColor(colors.HexColor('#ddd5e7'));canvas.line(1.8*cm,1.35*cm,w-1.8*cm,1.35*cm)
    canvas.setFont(FONT,8);canvas.setFillColor(colors.HexColor('#83768f'))
    canvas.drawString(1.9*cm,1.12*cm,'HackINE · Reto 1 · Documento técnico, versión exploratoria')
    canvas.drawRightString(w-1.9*cm,1.12*cm,f'Página {doc.page}')
    canvas.restoreState()

if __name__=='__main__':
    OUT.parent.mkdir(exist_ok=True,parents=True)
    SimpleDocTemplate(str(OUT),pagesize=A4,leftMargin=1.9*cm,rightMargin=1.9*cm,
       topMargin=1.7*cm,bottomMargin=1.75*cm,title='Documento técnico | HackINE Reto 1').build(story,onFirstPage=footer,onLaterPages=footer)
    print('DOCUMENTO',OUT,OUT.stat().st_size)
