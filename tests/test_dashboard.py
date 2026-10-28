import io
import pandas as pd
from fastapi.testclient import TestClient
from src.dashboard_api import app, data,profiles,classify_dataframe
from src.education import build_draft,pdf_for_draft

client=TestClient(app)
def test_status_and_summary():
    assert client.get('/health').json()['observaciones']==8541
    s=client.get('/api/summary').json()
    assert len(s['perfiles'])==5 and len(s['historico'])==6

def test_territory_and_filters():
    r=client.get('/api/observations',params={'perfil':1,'limit':5}).json()
    assert r['total']>0 and len(r['items'])<=5 and all(x['perfil_id']==1 for x in r['items'])
    a=client.get('/api/territory-audit').json()
    assert a['total']==2477

def test_input_validation_and_classification():
    years=[2009,2012,2015,2018,2021,2024]
    one={'unidad_id':'solo_agregados'}
    for y,v in zip(years,[45,61,43,62,50,59]):
        one.update({f'tasa_{y}':v,f'observados_{y}':500,f'ns_pct_{y}':4})
    x=classify_dataframe(pd.DataFrame([one]));assert int(x.perfil_id.iloc[0]) in range(1,6)
    r=client.post('/api/classify',files={'file':('example.csv',pd.DataFrame([one]).to_csv(index=False),'text/csv')})
    assert r.status_code==200 and b'perfil_nombre' in r.content
    one['tasa_2009']=101
    r=client.post('/api/classify',files={'file':('bad.csv',pd.DataFrame([one]).to_csv(index=False),'text/csv')})
    assert r.status_code==422

def test_education_validation_and_pdf():
    for pid, p in profiles().items():
        d=build_draft(p)
        assert d['validation']['passed']
        assert d['requires_human_approval']
        b=pdf_for_draft(d,'Revisor de prueba','2026-10-27')
        assert b.startswith(b'%PDF-')
    assert client.post('/api/approve',json={'profile_id':1,'reviewer':'Test Reviewer','confirmed':False}).status_code==400

def test_home():
    assert client.get('/').status_code==200
    assert 'Perfilado estadístico' in client.get('/').text
