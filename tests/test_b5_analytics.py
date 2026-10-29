"""Independent B5 oracles: CSV totals, all-match aggregation and invalid inputs."""
import copy
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from src import dashboard_api as api
from src import analytics

ROOT = Path(__file__).resolve().parents[1]
YEARS = [2009, 2012, 2015, 2018, 2021, 2024]
FEATURES = ['media_presidencial', 'media_intermedia', 'cambio_presidencial_pp', 'cambio_intermedia_pp']
KEY = ['EDOCVE', 'MPIOCVE', 'grupo_edad']


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(api, 'DB_PATH', tmp_path / 'reviews.sqlite3')
    with TestClient(api.app) as value:
        yield value


def test_national_and_profiles_reconcile_independently_with_annual_csv(client):
    result = client.get('/api/summary').json()
    assert [row['anio'] for row in result['historico']] == YEARS
    for row in result['historico']:
        annual = pd.read_csv(ROOT / f'datos/processed/{row["anio"]}/municipio_edad.csv')
        votes = annual[['LN', 'SV', 'NV', 'NS']].sum()
        assert row['participacion_pct'] == pytest.approx(100 * votes.SV / (votes.SV + votes.NV), abs=1e-10)
        assert row['ns_pct'] == pytest.approx(100 * votes.NS / votes.LN, abs=1e-10)
    frame = pd.read_csv(ROOT / 'datos/processed/producto/ccpc-2009-2024-k4-v1/observaciones_dashboard.csv')
    authoritative = json.loads((ROOT / 'ml/resultados/b3/perfiles_candidato.json').read_text(encoding='utf-8'))
    assert len(result['perfiles']) == 4
    for profile, expected in zip(result['perfiles'], authoritative):
        assert profile['perfil_id'] == expected['perfil_id']
        assert profile['nombre'] == expected['nombre']
        selected = frame[frame.perfil_id.eq(profile['perfil_id'])]
        assert profile['n_unidades'] == len(selected)
        for field in FEATURES:
            assert profile[field] == pytest.approx(selected[field].mean(), abs=1e-10)


def test_national_ratio_uses_counts_instead_of_stored_or_simple_mean_and_keeps_null():
    # Units 9/10 and 10/100 have simple mean50%, national19/110, not50%.
    fixture = pd.DataFrame([
        {'anio':2009, 'SV':19, 'NV':91, 'NS':10, 'LN':120, 'participacion_pct':50., 'ns_pct':0.},
        {'anio':2012, 'SV':0, 'NV':0, 'NS':0, 'LN':0, 'participacion_pct':0., 'ns_pct':0.},
    ])
    records = analytics.national_history(fixture)
    assert records[0]['participacion_pct'] == pytest.approx(100 * 19 / 110)
    assert records[0]['ns_pct'] == pytest.approx(100 * 10 / 120)
    assert records[0]['participacion_pct'] != 50.
    assert records[1]['participacion_pct'] is None and records[1]['ns_pct'] is None


def test_all_match_analytics_pagination_and_nullable_values(client, monkeypatch):
    # Three final rows deliberately change every mean, beyond the first page.
    fixture = pd.concat([api.data().iloc[[0]].copy()] * 103, ignore_index=True)
    fixture['MPIOCVE'] = np.arange(1, 104)
    fixture['clave_municipal'] = ['01' + str(i).zfill(3) for i in range(1, 104)]
    fixture['EDOCVE'] = 1
    fixture['EDONOM'] = 'Entidad QA'
    fixture['MPIONOM'] = ['Municipio QA ' + str(i) for i in range(103)]
    fixture['grupo_edad'] = '18-24'
    fixture['perfil_id'] = 1
    fixture['LN_2024'] = 10
    for field in FEATURES + [f'tasa_{year}' for year in YEARS]:
        fixture[field] = [0.] * 100 + [100.] * 3
    monkeypatch.setattr(api, 'data', lambda: fixture)
    first = client.get('/api/observations', params={'limit':100}).json()
    second = client.get('/api/observations', params={'limit':100, 'offset':100}).json()
    assert first['total'] == second['total'] == 103
    assert len(first['items']) == 100 and len(second['items']) == 3
    assert first['offset'] == 0 and second['offset'] == 100
    assert first['analytics'] == second['analytics']
    aggregate = first['analytics']
    assert aggregate['unidades'] == aggregate['municipios'] == 103
    assert aggregate['lista_nominal_2024'] == 1030
    assert aggregate['perfil_conteos'] == [{'perfil_id':1, 'unidades':103}]
    for mean in aggregate['medias'].values():
        assert mean == pytest.approx(300 / 103)
    for year in aggregate['historico']:
        assert year['media_tasa_pct'] == pytest.approx(300 / 103)
        assert year['unidades_con_tasa'] == 103
    a = {(x['EDOCVE'], x['MPIOCVE'], x['grupo_edad']) for x in first['items']}
    b = {(x['EDOCVE'], x['MPIOCVE'], x['grupo_edad']) for x in second['items']}
    assert not a & b and len(a | b) == 103
    fixture.loc[:, 'tasa_2009'] = np.nan
    missing = client.get('/api/observations', params={'limit':1}).json()
    assert missing['items'][0]['tasa_2009'] is None
    assert missing['analytics']['historico'][0]['media_tasa_pct'] is None
    assert missing['analytics']['historico'][0]['unidades_con_tasa'] == 0
    empty = client.get('/api/observations', params={'q':'NO COINCIDE'}).json()
    assert empty['total'] == empty['analytics']['unidades'] == 0 and empty['items'] == []
    assert all(x['media_tasa_pct'] is None for x in empty['analytics']['historico'])


def test_filters_match_direct_frame_selection_and_reject_invalid_parameters(client):
    frame = pd.read_csv(ROOT / 'datos/processed/producto/ccpc-2009-2024-k4-v1/observaciones_dashboard.csv')
    cases = [
        ({'estado':1}, frame.EDOCVE.eq(1)),
        ({'perfil':4}, frame.perfil_id.eq(4)),
        ({'edad':'60+'}, frame.grupo_edad.eq('60+')),
        ({'q':'AGUAS'}, frame.MPIONOM.str.contains('AGUAS', case=False, regex=False)),
        ({'estado':1, 'perfil':4, 'edad':'60+', 'q':'AGUAS'}, frame.EDOCVE.eq(1) & frame.perfil_id.eq(4) & frame.grupo_edad.eq('60+') & frame.MPIONOM.str.contains('AGUAS',case=False,regex=False)),
        ({'q':'.*'}, frame.MPIONOM.str.contains('.*',regex=False)),
    ]
    for params, mask in cases:
        response = client.get('/api/observations', params={**params, 'limit':500})
        assert response.status_code == 200
        payload = response.json()
        assert payload['total'] == payload['analytics']['unidades'] == int(mask.sum())
        expected = frame.loc[mask].sort_values(KEY,kind='stable').iloc[:500]
        assert {(x['EDOCVE'],x['MPIOCVE'],x['grupo_edad']) for x in payload['items']} == set(expected[KEY].itertuples(index=False,name=None))
    for params in [{'estado':0},{'estado':33},{'estado':'bad'},{'edad':'17-'},{'limit':0},{'limit':501},{'offset':-1},{'q':'x'*121}]:
        assert client.get('/api/observations',params=params).status_code == 422, params
    assert client.get('/api/observations',params={'perfil':5}).status_code == 404
    cleared = client.get('/api/observations').json()
    assert cleared['total'] == 8541 and len(cleared['items']) == 100


def test_package_and_data_hashes_remain_unchanged(client):
    baseline = json.loads((ROOT / 'analisis/reportes/b5/qa_baseline.json').read_text(encoding='utf-8'))
    for filename, digest in baseline['hashes'].items():
        if filename.startswith(('datos/processed/', 'ml/modelos/', 'ml/resultados/b3/', 'analisis/reportes/b2/')):
            assert hashlib.sha256((ROOT/filename).read_bytes()).hexdigest() == digest, filename
    assert client.get('/health').json()['package_digest'] == 'ae5243026dc27552abec02bafaba94819cb49b8dd6877416b79b188fccde1ed4'


def test_audit_unique_exclusions_denominators_and_controlled_defects(client, monkeypatch):
    api.analysis_audit.cache_clear()
    response = client.get('/api/analysis-audit')
    assert response.status_code == 200, response.text
    report = response.json()
    assert (report['panel'],report['elegibles'],report['excluidas_unicas']) == (12385,8541,3844)
    assert sum(row['unidades'] for row in report['combinaciones_excluidas']) == 3844
    assert sum(row['unidades'] for row in report['causas']) > 3844
    expected = {'unidades_panel':(8541,12385),'municipios_panel':(1825,2477),'LN_2024_nacional_procesado':(81666826,98330348)}
    for row in report['cobertura']:
        if row['medida'] in expected:
            numerator,denominator = expected[row['medida']]
            assert (row['numerador'],row['denominador']) == (numerator,denominator)
            assert row['porcentaje'] == pytest.approx(100*numerator/denominator,abs=1e-10)
    broken = copy.copy(api.package())
    broken['data'] = broken['data'].iloc[:-1]
    with pytest.raises(ValueError,match='unidades B2'):
        analytics.audit_evidence(ROOT,broken)
    broken = copy.copy(api.package())
    broken['national'] = broken['national'].copy()
    broken['national'].loc[0,'participacion_pct'] += 1
    with pytest.raises(ValueError,match='tasa nacional'):
        analytics.audit_evidence(ROOT,broken)
    def unavailable(*args):
        raise ValueError('QA: evidencia no corresponde')
    monkeypatch.setattr(api,'audit_evidence',unavailable)
    api.analysis_audit.cache_clear()
    assert client.get('/api/analysis-audit').status_code == 503
    api.analysis_audit.cache_clear()
    for name in ['b2','b3','metodologia','memoria','contrato']:
        document = client.get('/api/documentation/'+name)
        assert document.status_code == 200 and len(document.content)>100
    assert client.get('/api/documentation/secreto').status_code == 404
