"""Deterministic, auditable educational content workflow (no external LLM).

DataAgent -> WriterAgent -> ValidatorAgent -> explicit HumanReview. Does not
produce targeted persuasion, personalized political messages or publication.
"""
from __future__ import annotations
import io
from datetime import datetime, timezone
from html import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pathlib import Path

FONT_PATH=Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
if FONT_PATH.exists():
    try: pdfmetrics.registerFont(TTFont('DejaVuINE',str(FONT_PATH)))
    except Exception: pass
FONT='DejaVuINE' if 'DejaVuINE' in pdfmetrics.getRegisteredFontNames() else 'Helvetica'

def data_agent(profile:dict)->dict:
    required=('perfil_id','nombre','n_unidades','media_presidencial','media_intermedia',
        'cambio_presidencial_pp','cambio_intermedia_pp')
    if not all(k in profile for k in required):raise ValueError('Perfil incompleto')
    return {'perfil_id':int(profile['perfil_id']),'nombre':str(profile['nombre']),
            'unidades':int(profile['n_unidades']),
            'participacion_presidencial':round(float(profile['media_presidencial']),1),
            'participacion_intermedia':round(float(profile['media_intermedia']),1),
            'cambio_presidencial':round(float(profile['cambio_presidencial_pp']),1),
            'cambio_intermedia':round(float(profile['cambio_intermedia_pp']),1),
            'fuente':'Conteos Censales de Participación Ciudadana, INE, elecciones 2009–2024',
            'granularidad':'Municipio × grupo de edad (agregados, sin datos personales)'}

def narrative_agent(facts:dict)->dict:
    p=facts
    return {'titulo':f'Ficha descriptiva · Perfil {p["perfil_id"]}',
            'subtitulo':p['nombre'],
            'resumen':(f'Este grupo estadístico comprende {p["unidades"]:,} unidades municipio × edad. '
                 f'En las elecciones presidenciales presenta una participación media de {p["participacion_presidencial"]:.1f}%, '
                 f'mientras que en las intermedias la media es de {p["participacion_intermedia"]:.1f}%.'),
            'evolucion':(f'Entre 2012 y 2024 el cambio presidencial es de {p["cambio_presidencial"]:+.1f} puntos porcentuales; '
                 f'entre 2009 y 2021 el cambio de elecciones intermedias es de {p["cambio_intermedia"]:+.1f} puntos.'),
            'contenido_educativo':('La participación electoral es un indicador colectivo que puede consultarse '
                 'en los datos públicos del INE. Las cifras cambian entre elecciones y territorios. '
                 'Para interpretar una tendencia es necesario distinguir elecciones presidenciales e intermedias.'),
            'metodologia':('Agrupación estadística exploratoria mediante K-Means con cinco clusters, basada en '
                 'tasas agregadas y su evolución entre tipos de elección. Las medias mostradas son no ponderadas.'),
            'limitaciones':('No permite identificar, predecir ni describir el voto de una persona. '
                 'Los grupos de edad son cortes transversales, no cohortes de ciudadanos rastreados. '
                 'No se ha acreditado la equivalencia cartográfica histórica mediante un crosswalk oficial.'),
            'fuente':p['fuente'],'estado':'BORRADOR_PENDIENTE_REVISION'}

def verification_agent(facts:dict,draft:dict)->dict:
    check=(f'{facts["unidades"]:,}' in draft['resumen'] and
           f'{facts["participacion_presidencial"]:.1f}%' in draft['resumen'] and
           f'{facts["participacion_intermedia"]:.1f}%' in draft['resumen'] and
           f'{facts["cambio_presidencial"]:+.1f}' in draft['evolucion'] and
           f'{facts["cambio_intermedia"]:+.1f}' in draft['evolucion'])
    text=' '.join(str(v) for v in draft.values()).lower()
    forbidden=('vota por','voten por','apoya al partido','apoye al partido','convencer al elector')
    if any(x in text for x in forbidden):check=False
    return {'passed':bool(check),'checks':['cifras respaldadas por perfil',
             'sin afirmaciones sobre comportamiento individual',
             'sin exhortación partidista o persuasión demográfica'],
            'checked_at':datetime.now(timezone.utc).isoformat()}

def build_draft(profile:dict)->dict:
    facts=data_agent(profile);draft=narrative_agent(facts);v=verification_agent(facts,draft)
    if not v['passed']:raise ValueError('Error en validación interna de la ficha')
    return {'perfil_id':facts['perfil_id'],'facts':facts,'draft':draft,'validation':v,
            'requires_human_approval':True,'automated_publication':False,
            'agent_steps':['data_agent','narrative_agent','verification_agent','human_review']}

def pdf_for_draft(item:dict, reviewer:str, when:str)->bytes:
    if not reviewer.strip():raise ValueError('Revisor requerido')
    out=io.BytesIO()
    pdf=SimpleDocTemplate(out,pagesize=A4,rightMargin=2*cm,leftMargin=2*cm,
                          topMargin=1.8*cm,bottomMargin=1.8*cm)
    styles=getSampleStyleSheet();styles.add(ParagraphStyle(name='INE_H',parent=styles['Heading1'],fontName=FONT,fontSize=17,
       leading=22,textColor=colors.HexColor('#33235b'),spaceAfter=14))
    styles.add(ParagraphStyle(name='INE_P',parent=styles['BodyText'],fontName=FONT,fontSize=9,leading=14,spaceAfter=12))
    styles.add(ParagraphStyle(name='INE_sub',parent=styles['Heading2'],fontName=FONT,fontSize=11,leading=16,
       textColor=colors.HexColor('#623cad'),spaceBefore=10,spaceAfter=6))
    d=item['draft']; f=item['facts']
    story=[Paragraph(escape(d['titulo']),styles['INE_H']),Paragraph(escape(d['subtitulo']),styles['INE_sub'])]
    for heading,key in [('Descripción estadística','resumen'),('Evolución electoral','evolucion'),
                        ('Material educativo neutral','contenido_educativo'),('Método','metodologia'),('Limitaciones','limitaciones')]:
        story.extend([Paragraph(heading,styles['INE_sub']),Paragraph(escape(d[key]),styles['INE_P'])])
    story.append(Spacer(1,0.3*cm))
    for msg in [f'Fuente: {f["fuente"]}',f'Revisión humana: {reviewer} · {when}',
                'La aprobación de esta ficha no autoriza difusión automatizada.']:
        story.append(Paragraph(escape(msg),styles['INE_P']))
    pdf.build(story)
    return out.getvalue()
