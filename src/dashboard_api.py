"""FastAPI dashboard for aggregate CCPC profiles. Start: uvicorn src.dashboard_api:app --port 8501"""
from __future__ import annotations
import io,os,sqlite3
from contextlib import asynccontextmanager,closing
from datetime import datetime,timezone
from functools import lru_cache
from pathlib import Path
from typing import Optional
from threading import Lock
import numpy as np,pandas as pd
from fastapi import FastAPI,UploadFile,File,HTTPException,Query
from fastapi.responses import FileResponse,JSONResponse,Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel,Field
from .education import build_draft,pdf_for_draft
from .product_contract import load_active, FEATS, YEARS
from .analytics import AGES, filter_observations, selection_summary, audit_evidence, national_history

ROOT=Path(__file__).resolve().parents[1]
PRODUCT=ROOT/'datos/processed/producto'
DB_PATH=Path(os.environ.get('CCPC_REVIEW_DB',str(ROOT/'entregables/revision_local.sqlite3')))
DB_SCHEMA_LOCK=Lock()

@asynccontextmanager
async def lifespan(app):
    package()
    yield

app=FastAPI(title='Hackathon INE — Perfiles estadísticos',version='1.1.0',lifespan=lifespan)
app.mount('/static',StaticFiles(directory=str(ROOT/'dashboard/static')),name='static')

@lru_cache(maxsize=1)
def package():return load_active(ROOT)

def data():return package()['data']
def profiles():return package()['profiles']
def metadata():return package()['metadata']
def artifact():return package()['artifact']

def db_conn():
    path=Path(DB_PATH);path.parent.mkdir(parents=True,exist_ok=True)
    with DB_SCHEMA_LOCK:
        db=sqlite3.connect(path)
        try:
            columns={row[1] for row in db.execute('PRAGMA table_info(approvals)')}
            additions=['package_version','package_digest']
            if columns and any(c not in columns for c in additions):
                backup=path.with_name(path.name+'.pre-b4-'+datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')+'.bak')
                with closing(sqlite3.connect(backup)) as target:db.backup(target)
            with db:
                db.execute('''CREATE TABLE IF NOT EXISTS approvals
                  (id INTEGER PRIMARY KEY AUTOINCREMENT, perfil_id INTEGER NOT NULL, reviewer TEXT NOT NULL,
                   reviewed_at TEXT NOT NULL, digest TEXT NOT NULL, package_version TEXT, package_digest TEXT)''')
                if columns:
                    for column in additions:
                        if column not in columns:db.execute(f'ALTER TABLE approvals ADD COLUMN {column} TEXT')
            return db
        except (sqlite3.Error,OSError):
            db.close()
            raise

@app.get('/')
def home():return FileResponse(ROOT/'dashboard/index.html',media_type='text/html')
@app.get('/health')
def health():return {'status':'ok','observaciones':len(data()),'perfiles':len(profiles()),
                    'package_version':package()['package_version'],'package_digest':package()['package_digest'],'k':package()['manifest']['k']}
@app.get('/api/summary')
def summary():
    national=package()['national']
    return {'meta':metadata(),'historico':national_history(national),'perfiles':list(profiles().values())}
@app.get('/api/profiles')
def get_profiles():return list(profiles().values())
@app.get('/api/observations')
def observations(estado:Optional[int]=Query(None,ge=1,le=32),perfil:Optional[int]=None,edad:Optional[str]=None,
                 q:str=Query('',max_length=120),limit:int=Query(100,ge=1,le=500),offset:int=Query(0,ge=0)):
    if perfil is not None and perfil not in profiles():raise HTTPException(404,'Perfil no existe en el paquete activo')
    if edad is not None and edad not in AGES:raise HTTPException(422,'Grupo de edad desconocido')
    frame=filter_observations(data(),estado,perfil,edad,q)
    out=frame.iloc[offset:offset+limit].copy()
    fields=['EDOCVE','MPIOCVE','clave_municipal','EDONOM','MPIONOM','grupo_edad','perfil_id','perfil_nombre','package_version','media_presidencial',
            'media_intermedia','cambio_presidencial_pp','cambio_intermedia_pp','LN_2024','max_ns_pct',
            *[f'tasa_{y}' for y in YEARS],*[f'observados_{y}' for y in YEARS]]
    return {'total':len(frame),'package_version':package()['package_version'],'offset':offset,'limit':limit,
            'analytics':selection_summary(frame),
            'items':out[fields].replace({np.nan:None}).to_dict('records')}

@lru_cache(maxsize=1)
def analysis_audit():
    return audit_evidence(ROOT,package())

@app.get('/api/analysis-audit')
def get_analysis_audit():
    try:return analysis_audit()
    except (OSError,ValueError,KeyError) as exc:
        raise HTTPException(503,f'Auditoría analítica no disponible: {exc}')

@app.get('/api/documentation/{name}')
def documentation(name:str):
    allowed={'metodologia':'docs/02_decisiones_metodologicas.md','b2':'docs/10_auditoria_procesados_B2.md',
             'b3':'docs/11_evaluacion_modelo_B3.md','memoria':'docs/00_memoria_tecnica_Hiram.md',
             'contrato':'README.md'}
    if name not in allowed:raise HTTPException(404,'Documento no disponible')
    return FileResponse(ROOT/allowed[name],media_type='text/plain; charset=utf-8')
@app.get('/api/states')
def states():
    return data()[['EDOCVE','EDONOM']].drop_duplicates().sort_values('EDONOM').to_dict('records')
@app.get('/api/territory-audit')
def territory_audit():
    frame=package()['territory_audit']
    return {'total':len(frame),'estados':frame.estatus_administrativo.value_counts().to_dict(),
            'examples':frame[frame.estatus_administrativo.ne('estable_por_nombre_y_clave')][
              ['clave_municipal','MPIONOM','estatus_administrativo','nombres']].head(50).to_dict('records'),
            'advertencia':'Coincidir por nombre y clave no certifica equivalencia de fronteras históricas.'}

@app.get('/api/template')
def template():
    columns=['unidad_id','grupo_edad',*[f'tasa_{y}' for y in YEARS],
             *[f'observados_{y}' for y in YEARS],*[f'ns_pct_{y}' for y in YEARS]]
    demo={'unidad_id':'EJEMPLO_AGREGADO','grupo_edad':'25-34'}
    demo.update({f'tasa_{y}':v for y,v in zip(YEARS,[43.5,61.0,45.5,63.0,52.0,60.0])})
    demo.update({f'observados_{y}':300 for y in YEARS})
    demo.update({f'ns_pct_{y}':5 for y in YEARS})
    return Response(pd.DataFrame([demo])[columns].to_csv(index=False),media_type='text/csv',
       headers={'Content-Disposition':'attachment; filename=plantilla_datos_agregados.csv'})

def classify_dataframe(incoming:pd.DataFrame):
    req=[f'tasa_{y}' for y in YEARS]+[f'observados_{y}' for y in YEARS]+[f'ns_pct_{y}' for y in YEARS]
    missing=[k for k in req if k not in incoming]
    if missing:raise ValueError('Columnas faltantes: '+', '.join(missing))
    if len(incoming)==0 or len(incoming)>5000:raise ValueError('El archivo debe tener de 1 a 5,000 filas')
    x=incoming.copy()
    for c in req:
        x[c]=pd.to_numeric(x[c],errors='coerce')
        if x[c].isna().any() or not np.isfinite(x[c].to_numpy()).all():
            raise ValueError(f'Valores faltantes/no numéricos en {c}')
    t=x[[f'tasa_{y}' for y in YEARS]]
    if (t.lt(0)|t.gt(100)).any().any():raise ValueError('Tasas fuera del rango 0–100')
    observed=x[[f'observados_{y}' for y in YEARS]]
    filters=package()['manifest']['filters']
    if observed.lt(filters['min_observados_por_anio']).any().any() or observed.mod(1).ne(0).any().any():
        raise ValueError('Los observados deben ser conteos enteros de al menos 100 por elección')
    ns=x[[f'ns_pct_{y}' for y in YEARS]]
    if (ns.lt(0)|ns.gt(filters['max_ns_pct'])).any().any():raise ValueError('NS debe estar en [0,20]% por elección')
    # Exactly the same feature engineering used in the model, unweighted by population.
    x['media_presidencial']=x[['tasa_2012','tasa_2018','tasa_2024']].mean(axis=1)
    x['media_intermedia']=x[['tasa_2009','tasa_2015','tasa_2021']].mean(axis=1)
    x['cambio_presidencial_pp']=x['tasa_2024']-x['tasa_2012']
    x['cambio_intermedia_pp']=x['tasa_2021']-x['tasa_2009']
    bundle=artifact()
    z=bundle['scaler'].transform(x[FEATS].to_numpy(float))
    ids=bundle['model'].predict(z)
    x['perfil_id']=[bundle['label_mapping'][int(i)] for i in ids]
    x['perfil_nombre']=x.perfil_id.map({pid:p['nombre'] for pid,p in profiles().items()})
    x['package_version']=package()['package_version']
    x['package_digest']=package()['package_digest']
    x['distancia_centroide']=np.linalg.norm(z-bundle['model'].cluster_centers_[ids],axis=1)
    x['nota']='Asignación estadística exploratoria de unidad agregada; no clasificación individual'
    return x

@app.post('/api/classify')
async def classify(file:UploadFile=File(...)):
    if not file.filename or not file.filename.lower().endswith('.csv'):raise HTTPException(400,'Se requiere CSV')
    content=await file.read(2_000_001)
    if len(content)>2_000_000:raise HTTPException(413,'Máximo 2 MB por archivo')
    try:
        df=pd.read_csv(io.BytesIO(content));x=classify_dataframe(df)
    except (ValueError,pd.errors.ParserError,UnicodeDecodeError) as e:raise HTTPException(422,str(e))
    # Avoid spreadsheet formula injection when exporting user-provided text.
    for col in x.select_dtypes(include=['object','string']).columns:
        x[col]=x[col].astype(str).map(lambda v: "'"+v if v.startswith(('=','+','-','@')) else v)
    return Response(x.to_csv(index=False),media_type='text/csv',headers={
        'Content-Disposition':'attachment; filename=clasificacion_agregada.csv',
        'X-Row-Count':str(len(x)),'X-Package-Version':package()['package_version']})

@app.get('/api/draft/{profile_id}')
def draft(profile_id:int):
    profile=profiles().get(profile_id)
    if profile is None:raise HTTPException(404,'Perfil no existe')
    return build_draft(profile,package()['package_digest'])

class ApprovalRequest(BaseModel):
    profile_id:int=Field(ge=1)
    reviewer:str=Field(min_length=3,max_length=100)
    confirmed:bool
    package_version:str=Field(min_length=1,max_length=120)
    package_digest:str=Field(pattern=r'^[0-9a-f]{64}$')
    draft_digest:str=Field(pattern=r'^[0-9a-f]{64}$')

@app.post('/api/approve')
def approve(payload:ApprovalRequest):
    if not payload.confirmed:raise HTTPException(400,'Debe confirmar la revisión manual')
    if len(payload.reviewer.strip())<3:raise HTTPException(400,'Revisor requerido: mínimo 3 caracteres no vacíos')
    profile=profiles().get(payload.profile_id)
    if profile is None:raise HTTPException(404,'Perfil no existe')
    bundle=build_draft(profile,package()['package_digest'])
    if (payload.package_version!=bundle['package_version'] or payload.package_digest!=bundle['package_digest'] or
            payload.draft_digest!=bundle['draft_digest']):
        raise HTTPException(409,'El borrador, perfil o versión cambió; genere la ficha y vuelva a revisarla')
    ts=datetime.now(timezone.utc).isoformat()
    with closing(db_conn()) as db,db:
        cur=db.execute('INSERT INTO approvals (perfil_id,reviewer,reviewed_at,digest,package_version,package_digest) VALUES (?,?,?,?,?,?)',
                       (payload.profile_id,payload.reviewer.strip(),ts,bundle['draft_digest'],bundle['package_version'],bundle['package_digest']))
        aid=cur.lastrowid
    return {'approval_id':aid,'profile_id':payload.profile_id,'reviewer':payload.reviewer.strip(),
            'reviewed_at':ts,'download_url':f'/api/approved-pdf/{aid}',
            'package_version':bundle['package_version'],'draft_digest':bundle['draft_digest'],
            'note':'Aprobación local de ficha, sin envío ni publicación.'}

@app.get('/api/approved-pdf/{approval_id}')
def approved_pdf(approval_id:int):
    with closing(db_conn()) as db:
        row=db.execute('SELECT perfil_id,reviewer,reviewed_at,digest,package_version,package_digest FROM approvals WHERE id=?',(approval_id,)).fetchone()
    if row is None:raise HTTPException(404,'Aprobación no existe')
    if not row[4] or not row[5]:
        raise HTTPException(409,'Aprobación heredada sin versión verificable; registro conservado, requiere revisión nueva')
    if row[4]!=package()['package_version'] or row[5]!=package()['package_digest']:
        raise HTTPException(409,'La aprobación pertenece a otro paquete; registro conservado, requiere revisión nueva')
    profile=profiles().get(row[0])
    if profile is None:raise HTTPException(409,'El perfil aprobado no existe en este paquete')
    item=build_draft(profile,package()['package_digest'])
    if item['draft_digest']!=row[3]:raise HTTPException(409,'El contenido cambió; requiere revisión nueva')
    payload=pdf_for_draft(item,row[1],row[2])
    return Response(payload,media_type='application/pdf',headers={
        'Content-Disposition':f'attachment; filename=ficha_perfil_{row[0]}.pdf'})
