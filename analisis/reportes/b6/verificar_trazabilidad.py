"""B6 read-only acceptance: independent counts/panel -> live API -> UI contract.

Browser/zoom/keyboard acceptance belongs to qa_b6, not this numerical script.
"""
import argparse
from datetime import datetime
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import subprocess
import sys
from urllib.parse import urlencode
from urllib.request import urlopen
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

YEARS = [2009, 2012, 2015, 2018, 2021, 2024]
KEY = ['EDOCVE', 'MPIOCVE', 'grupo_edad']
FEATURES = ['media_presidencial', 'media_intermedia', 'cambio_presidencial_pp', 'cambio_intermedia_pp']
CAUSE_LABELS = {
    'faltan_tasas': 'Falta al menos una tasa',
    'identidad_inestable': 'Nombre municipal inconsistente',
    'observados_menor_100': '<100 observados en alguna elección',
    'ns_mayor_20': 'NS >20% en alguna elección',
    'faltan_conteos_o_ns': 'Faltan conteos o NS',
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def boolean(values):
    if not values.isin(['True', 'False']).all():
        raise ValueError(f'Booleano nulo/desconocido: {values.name}')
    return values.map({'True': True, 'False': False})


def exclusion_flags(panel):
    """Present low counts and missing years are different, overlapping causes."""
    rates = panel[[f'tasa_{year}' for year in YEARS]]
    observed = panel[[f'observados_{year}' for year in YEARS]]
    ns = panel[[f'ns_pct_{year}' for year in YEARS]]
    return pd.DataFrame({
        'faltan_tasas': ~(rates.notna() & np.isfinite(rates)).all(axis=1),
        'identidad_inestable': ~panel.identidad_estable_conservadora,
        'observados_menor_100': observed.lt(100).any(axis=1),
        'ns_mayor_20': ns.gt(20).any(axis=1),
        'faltan_conteos_o_ns': observed.isna().any(axis=1) | ns.isna().any(axis=1),
    })


def run(root, out, base_url):
    root, out = Path(root).resolve(), Path(out).resolve()
    if (out == root or root in out.parents) and out != root / 'analisis/reportes/b6':
        raise ValueError('Salida protegida; utiliza analisis/reportes/b6 o un temporal separado')
    out.mkdir(parents=True, exist_ok=True)
    used = set()

    def read(name):
        used.add(name)
        return json.loads((root / name).read_text(encoding='utf-8'))

    def csv(name, **kwargs):
        used.add(name)
        return pd.read_csv(root / name, **kwargs)

    def api(endpoint):
        with urlopen(base_url.rstrip('/') + endpoint, timeout=20) as response:
            return json.load(response)

    rows = []

    def check(identifier, screen, source, formula, unit, universe, field, component,
              expected, actual, decimals=1, tolerance=0, weighting='No aplica'):
        numeric = isinstance(expected, (int, float, np.number)) and not isinstance(expected, (bool, np.bool_))
        difference = float(actual) - float(expected) if numeric and actual is not None else None
        passed = abs(difference) <= tolerance if difference is not None else expected == actual
        shown = (f'{expected:.{decimals}f}' + ('%' if unit == '%' else ' pp' if unit == 'pp' else '')) if numeric and decimals else str(expected)
        rows.append(dict(id=identifier, pantalla=screen, fuente=source, version=manifest['package_version'],
                         clave_universo=universe, formula_denominador=formula, ponderacion=weighting,
                         unidad=unit, precision=f'{decimals} decimales' if decimals else 'entero/exacto',
                         endpoint_campo=field, componente=component, efecto_filtros=universe,
                         esperado=expected, observado=actual, diferencia=difference, tolerancia=tolerance,
                         presentacion_esperada=shown, estado='pasa' if passed else 'falla',
                         evidencia='resultados.json; revisión de pantalla: docs/16_QA_B6.md',
                         efecto_aceptacion='Sin bloqueo' if passed else 'Bloquea aceptación'))

    pointer = read('datos/processed/producto_activo.json')
    manifest = read(pointer['manifest'])
    if sha(root / pointer['manifest']) != pointer['sha256']:
        raise ValueError('Descriptor activo no corresponde al puntero')
    folder = str(Path(pointer['manifest']).parent).replace('\\', '/')
    for spec in manifest['files'].values():
        name = folder + '/' + spec['path']
        used.add(name)
        if sha(root / name) != spec['sha256']:
            raise ValueError(f'Hash de paquete incorrecto: {name}')
    obs = csv(folder + '/' + manifest['files']['observations']['path'])
    panel = csv('datos/processed/matriz_modelo_6_anios.csv',
                dtype={c: str for c in ['apto_modelo', 'completo_6', 'identidad_estable_conservadora']})
    for field in ['apto_modelo', 'completo_6', 'identidad_estable_conservadora']:
        panel[field] = boolean(panel[field])
    if panel.duplicated(KEY).any() or obs.duplicated(KEY).any():
        raise ValueError('Claves duplicadas; no se acepta alineación ambigua')
    flags = exclusion_flags(panel)
    eligible = ~flags.any(axis=1)
    check('elegibilidad', 'Auditoría', 'matriz_modelo_6_anios.csv', 'seis tasas finitas; identidad; observados>=100; NS<=20; sin faltantes',
          'diferencias', 'Panel de cinco edades', '/api/analysis-audit', '#coverageCards', 0, int(eligible.ne(panel.apto_modelo).sum()), decimals=0)
    check('claves_elegibles', 'Auditoría', 'Panel y observaciones del paquete', 'igualdad de conjuntos de claves compuestas',
          'claves', 'Elegibles', '/api/observations', '#obsRows',
          sorted(panel.loc[eligible, KEY].itertuples(index=False, name=None)),
          sorted(obs[KEY].itertuples(index=False, name=None)), decimals=0)
    # Keep a large set comparison compact in the matrix, with its exact result retained.
    rows[-1].update(esperado=len(obs), observado=int(eligible.sum()), presentacion_esperada=str(len(obs)))

    summary, audit = api('/api/summary'), api('/api/analysis-audit')
    for field, expected in [('total_unidades_panel', len(panel)), ('total_unidades_modeladas', len(obs)),
                            ('total_municipios_modelados', len(obs.groupby(KEY[:2])))]:
        check('panorama_' + field, 'Panorama', 'Panel B2 / observaciones activas', 'conteo por clave/unidad, según indicador',
              'conteos', 'Panel o elegibles, fijo', f'/api/summary meta.{field}', '#kpis', expected, summary['meta'][field], decimals=0)
    annual, history = [], []
    for year in YEARS:
        frame = csv(f'datos/processed/{year}/municipio_edad.csv')
        if frame.duplicated(KEY).any() or not frame.grupo_edad.isin(['18-24', '25-34', '35-44', '45-59', '60+']).all():
            raise ValueError(f'Claves/edades anuales inválidas: {year}')
        totals = frame[['LN', 'SV', 'NV', 'NS']].sum()
        observed = totals.SV + totals.NV
        rate = 100 * totals.SV / observed if observed else None
        ns_rate = 100 * totals.NS / totals.LN if totals.LN else None
        record = next(r for r in summary['historico'] if r['anio'] == year)
        for metric, value in [('participacion_pct', rate), ('ns_pct', ns_rate)]:
            check(f'nacional_{year}_{metric}', 'Panorama', f'datos/processed/{year}/municipio_edad.csv',
                  '100*sum(SV)/sum(SV+NV)' if metric == 'participacion_pct' else '100*sum(NS)/sum(LN)',
                  '%', 'Nacional procesado de cinco edades, fijo', f'/api/summary historico[{year}].{metric}',
                  '#nationalChart / #nationalRows' if metric == 'participacion_pct' else '#nationalRows',
                  value, record[metric], tolerance=1e-10, weighting='Razón de sumas, no media simple')
        annual.append(dict(anio=year, **{c: int(totals[c]) for c in totals.index}, participacion_pct=rate, ns_pct=ns_rate))
        rates = frame[KEY].copy()
        denominator = frame.SV + frame.NV
        rates[f'tasa_{year}'] = 100 * frame.SV / denominator.where(denominator.gt(0))
        rates[f'observados_{year}'] = denominator
        history.append(rates)
    indexed = {r['anio']: r for r in annual}
    for kind, first, last in [('intermedia', 2009, 2021), ('presidencial', 2012, 2024)]:
        current = {r['anio']: r for r in summary['historico']}
        check(f'cambio_{kind}', 'Panorama', f'Agregados {first}/{last}', f'tasa{last} - tasa{first}, sin redondear antes',
              'pp', 'Nacional procesado, fijo', '/api/summary historico', '#nationalInsights',
              indexed[last]['participacion_pct'] - indexed[first]['participacion_pct'],
              current[last]['participacion_pct'] - current[first]['participacion_pct'], decimals=2, tolerance=1e-10)
    reconstructed = obs[KEY + ['perfil_id']].copy()
    for rates in history:
        reconstructed = reconstructed.merge(rates, on=KEY, how='left', validate='one_to_one')
    for kind, years in [('presidencial', [2012, 2018, 2024]), ('intermedia', [2009, 2015, 2021])]:
        reconstructed[f'media_{kind}'] = reconstructed[[f'tasa_{y}' for y in years]].mean(axis=1, skipna=False)
        reconstructed[f'cambio_{kind}_pp'] = reconstructed[f'tasa_{years[-1]}'] - reconstructed[f'tasa_{years[0]}']
    if not np.isfinite(reconstructed[FEATURES].to_numpy()).all():
        raise ValueError('Features no finitas desde agregados anuales para elegibles')
    for profile in summary['perfiles']:
        pid = profile['perfil_id']
        group = reconstructed[reconstructed.perfil_id.eq(pid)]
        for field in ['n_unidades', 'porcentaje_unidades', *FEATURES]:
            value = len(group) if field == 'n_unidades' else 100 * len(group) / len(obs) if field == 'porcentaje_unidades' else group[field].mean()
            check(f'perfil_{pid}_{field}', 'Perfiles', 'Agregados anuales + asignaciones del paquete por clave',
                  'n' if field == 'n_unidades' else '100*n/n_elegibles' if field == 'porcentaje_unidades' else f'media entre unidades de {field}, desde tasas anuales',
                  'unidades' if field == 'n_unidades' else 'pp' if field.endswith('_pp') else '%', f'Perfil {pid}, fijo',
                  f'/api/summary perfiles[{pid}].{field}', '#profileCards / #profileChart / #changeChart / #profileComparison',
                  value, profile[field], decimals=0 if field == 'n_unidades' else 2 if field.endswith('_pp') else 1,
                  tolerance=0 if field == 'n_unidades' else 1e-10, weighting='Media simple entre unidades; sin pesos poblacionales')
    for field, expected in [('panel', len(panel)), ('elegibles', int(eligible.sum())), ('excluidas_unicas', int((~eligible).sum()))]:
        check(field, 'Auditoría', 'Panel aprobado B2', field, 'unidades', 'Panel, fijo', f'/api/analysis-audit {field}', '#coverageCards', expected, audit[field], decimals=0)
    coverage = {'unidades_panel': (int(eligible.sum()), len(panel)),
                'municipios_panel': (len(obs.groupby(KEY[:2])), len(panel.groupby(KEY[:2]))),
                'LN_2024_nacional_procesado': (int(panel.loc[eligible, 'LN_2024'].sum()), indexed[2024]['LN'])}
    for measure, (num, den) in coverage.items():
        actual = next(r for r in audit['cobertura'] if r['medida'] == measure)
        for field, expected in [('numerador', num), ('denominador', den), ('porcentaje', 100 * num / den)]:
            check(f'cobertura_{measure}_{field}', 'Auditoría/Panorama', 'Panel y agregado 2024 aprobado', f'100*{num}/{den}',
                  '%' if field == 'porcentaje' else 'conteos', measure + ', fijo', f'/api/analysis-audit cobertura.{measure}.{field}',
                  '#coverageRows / #kpis', expected, actual[field], decimals=1 if field == 'porcentaje' else 0,
                  tolerance=1e-10 if field == 'porcentaje' else 0)

    original = csv('analisis/reportes/causas_exclusion_superpuestas.csv').set_index('motivo').n_unidades
    cause_rows = []
    for code, label in CAUSE_LABELS.items():
        count = int(flags[code].sum())
        previous = int(original[label]) if label in original.index else None
        actual = next(r['unidades'] for r in audit['causas'] if r['codigo'] == code)
        check('causa_' + code, 'Auditoría', 'Panel aprobado, valores de seis años', code, 'incidencias', 'Panel, causas superpuestas',
              f'/api/analysis-audit causas.{code}', '#exclusionRows', count, actual, decimals=0)
        cause_rows.append(dict(causa=code, descripcion=label, anterior_4_categorias=previous, vigente_5_categorias=count,
                               diferencia=count - previous if previous is not None else None,
                               incidencias_adicionales_reportadas=count if previous is None else 0, universo=len(panel),
                               formula={'faltan_tasas':'no todas las seis tasas finitas', 'identidad_inestable':'no identidad nominal estable',
                                        'observados_menor_100':'existe valor presente <100; NaN no cumple <100',
                                        'ns_mayor_20':'existe NS presente >20',
                                        'faltan_conteos_o_ns':'existe observados o NS ausente en al menos un año'}[code],
                               contexto='Categoría diagnóstica añadida en B2; no cambia elegibilidad' if code == 'faltan_conteos_o_ns' else 'Misma categoría y conteo'))
    observed = panel[[f'observados_{year}' for year in YEARS]]
    missing = flags.faltan_conteos_o_ns
    details = panel.loc[missing, KEY].copy()
    details['anios_sin_observados'] = observed.loc[missing].apply(lambda row: '|'.join(str(y) for y in YEARS if pd.isna(row[f'observados_{y}'])), axis=1)
    details['tambien_alguno_menor_100'] = flags.loc[missing, 'observados_menor_100']
    details['faltan_tasas'] = flags.loc[missing, 'faltan_tasas']
    details['apto_guardado'] = panel.loc[missing, 'apto_modelo']
    check('union_4_5_causas', 'Auditoría', 'Panel aprobado', 'unión de primeras cuatro causas vs unión de cinco',
          'unidades', 'Excluidas únicas', '/api/analysis-audit excluidas_unicas', '#coverageCards',
          int(flags.iloc[:, :4].any(axis=1).sum()), int(flags.any(axis=1).sum()), decimals=0)

    # Representative interactions plus a full multi-page case, aligned by keys.
    cases = [('sin_filtros', {}, pd.Series(True, index=obs.index)),
             ('entidad', {'estado': 2}, obs.EDOCVE.eq(2)),
             ('perfil', {'perfil': 4}, obs.perfil_id.eq(4)),
             ('edad', {'edad': '60+'}, obs.grupo_edad.eq('60+')),
             ('combinado', {'estado': 2, 'edad': '18-24'}, obs.EDOCVE.eq(2) & obs.grupo_edad.eq('18-24')),
             ('busqueda', {'q': 'AGUAS'}, obs.MPIONOM.str.contains('AGUAS', case=False, regex=False)),
             ('literal', {'q': '.*'}, obs.MPIONOM.str.contains('.*', regex=False)),
             ('vacio', {'q': 'NO_EXISTE_B6_QA'}, obs.MPIONOM.eq('NO_EXISTE_B6_QA'))]
    page_evidence = []
    for name, params, mask in cases:
        selected = obs.loc[mask].sort_values(KEY)
        payload = api('/api/observations?' + urlencode({**params, 'limit': 100}))
        for field, expected in [('unidades', len(selected)), ('municipios', len(selected.groupby(KEY[:2]))), ('lista_nominal_2024', int(selected.LN_2024.sum()))]:
            check(f'seleccion_{name}_{field}', 'Explorador', 'Observaciones activas por clave', 'filtro AND literal antes de paginar',
                  'conteos', f'Selección completa {name}', f'/api/observations analytics.{field}', '#selectionSummary / #obsCount',
                  expected, payload['analytics'][field], decimals=0)
        for field in FEATURES:
            expected = float(selected[field].mean()) if len(selected) else None
            check(f'seleccion_{name}_{field}', 'Explorador', 'Observaciones activas por clave', 'media simple de todas las coincidencias',
                  'pp' if field.endswith('_pp') else '%', f'Selección completa {name}', f'/api/observations analytics.medias.{field}',
                  '#selectionSummary', expected, payload['analytics']['medias'][field], tolerance=1e-10,
                  weighting='Media simple entre unidades')
        if name in ('sin_filtros', 'combinado'):
            received = []
            for offset in range(0, len(selected), 100):
                page = payload if not offset else api('/api/observations?' + urlencode({**params, 'limit': 100, 'offset': offset}))
                received.extend((r['EDOCVE'], r['MPIOCVE'], r['grupo_edad']) for r in page['items'])
                if page['total'] != len(selected) or page['analytics'] != payload['analytics']:
                    raise ValueError(f'Total/resumen varía al paginar: {name}')
                page_evidence.append(dict(caso=name, offset=offset, visibles=len(page['items']), total=page['total'],
                                          rango=f'{offset+1}–{offset+len(page["items"])} de {len(selected)}'))
            check('paginacion_' + name, 'Explorador', 'Observaciones ordenadas por clave', 'concatenar páginas sin pérdidas ni duplicados',
                  'claves', f'Selección completa {name}', '/api/observations items,offset,total', '#pageRange / #obsRows',
                  list(selected[KEY].itertuples(index=False, name=None)), received, decimals=0)
            rows[-1].update(esperado=len(selected), observado=len(received), presentacion_esperada=str(len(selected)))
        if payload['items'] and name == 'combinado':
            item = payload['items'][0]
            key = tuple(item[k] for k in KEY)
            for year, rates in zip(YEARS, history):
                row = rates.set_index(KEY).loc[key]
                for field in [f'tasa_{year}', f'observados_{year}']:
                    check('detalle_' + field, 'Explorador', f'Agregado anual {year}, clave {key}', 'SV/(SV+NV) o SV+NV',
                          '%' if field.startswith('tasa') else 'conteos', f'Unidad {key}', f'/api/observations items.{field}',
                          '#detailTitle / #detailRows / #detailChart', float(row[field]), item[field],
                          decimals=1 if field.startswith('tasa') else 0, tolerance=1e-10 if field.startswith('tasa') else 0)

    frontend = {'/': 'dashboard/index.html', '/static/app.js': 'dashboard/static/app.js', '/static/app.css': 'dashboard/static/app.css'}
    for endpoint, name in frontend.items():
        used.add(name)
        with urlopen(base_url.rstrip('/') + endpoint, timeout=20) as response:
            served = hashlib.sha256(response.read()).hexdigest()
        check('servido_' + name, 'Integridad', name, 'SHA256 bytes servidos == checkout', 'SHA256', 'Versión efectiva', endpoint,
              name, sha(root / name), served, decimals=0)
    protected = read('analisis/reportes/b5/qa_final_state.json')['hashes']
    changed = [name for name, expected in protected.items()
               if name.startswith(('datos/', 'ml/modelos/', 'ml/resultados/b3/', 'analisis/reportes/b2/')) and sha(root / name) != expected]
    if changed:
        raise ValueError(f'Fuentes protegidas distintas de B5: {changed}')
    health = api('/health')
    check('paquete_servido', 'Integridad', 'producto_activo.json', 'digest activo == salud efectiva', 'SHA256', 'Paquete activo',
          '/health package_digest', '#packageVersion', pointer['sha256'], health['package_digest'], decimals=0)
    used.update(['src/analytics.py', 'src/dashboard_api.py', 'src/product_contract.py',
                 'src/reporting.py', 'src/validate_processed.py', 'src/pipeline.py',
                 'analisis/reportes/b2/elegibilidad_y_causas.csv', 'analisis/reportes/b5/fuentes_auditoria.json',
                 Path(__file__).resolve().relative_to(root).as_posix()])
    result = dict(fecha=datetime.now(ZoneInfo('America/Tijuana')).isoformat(), zona='America/Tijuana',
                  base=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip(),
                  rama=subprocess.check_output(['git', 'branch', '--show-current'], cwd=root, text=True).strip(),
                  git_status=subprocess.check_output(['git', 'status', '--short'], cwd=root, text=True),
                  comando=[sys.executable, *sys.argv], python=platform.python_version(),
                  versiones={n: importlib.metadata.version(n) for n in ['pandas', 'numpy', 'scikit-learn', 'scipy', 'joblib']},
                  package_version=manifest['package_version'], package_digest=pointer['sha256'],
                  versiones_reportes={name: subprocess.check_output(['git', 'log', '-1', '--format=%h', '--', name], cwd=root, text=True).strip()
                                      for name in ['analisis/reportes/causas_exclusion_superpuestas.csv',
                                                   'analisis/reportes/b2/elegibilidad_y_causas.csv', 'src/analytics.py']},
                  fuentes_sha256={name: sha(root / name) for name in sorted(used)},
                  estados=pd.Series([r['estado'] for r in rows]).value_counts().to_dict(), anual=annual,
                  reconciliacion=dict(incidencias_4=int(flags.iloc[:, :4].sum().sum()), incidencias_5=int(flags.sum().sum()),
                                      excluidas_4=int(flags.iloc[:, :4].any(axis=1).sum()), excluidas_5=int(flags.any(axis=1).sum()),
                                      causas={c: int(flags[c].sum()) for c in flags},
                                      missing_y_menor100=int((missing & flags.observados_menor_100).sum()),
                                      missing_sin_menor100=int((missing & ~flags.observados_menor_100).sum()),
                                      no_cumplen_seis_ge100=int((~observed.ge(100).all(axis=1)).sum()),
                                      celdas_anuales_observados_ausentes=int(observed.isna().sum().sum()),
                                      unidades_observados_ausentes=int(observed.isna().any(axis=1).sum()),
                                      unidades_ns_ausente=int(panel[[f'ns_pct_{y}' for y in YEARS]].isna().any(axis=1).sum()),
                                      faltantes_con_tasas_ausentes=int((missing & flags.faltan_tasas).sum()),
                                      filas_observados_cero=int(observed.eq(0).sum().sum()),
                                      unidades_observados_cero=int(observed.eq(0).any(axis=1).sum()),
                                      faltantes_y_observados_cero=int((missing & observed.eq(0).any(axis=1)).sum()),
                                      combinaciones_excluidas=len(flags.loc[~eligible].value_counts())),
                  comparacion_claves_falsos_incluidos_excluidos=int(eligible.ne(panel.apto_modelo).sum()),
                  paginas=page_evidence, limites='Matriz numérica API; pantalla/zoom/teclado en QA B6; RAW no revalidados')
    for filename, frame in [('matriz_trazabilidad.csv', pd.DataFrame(rows)), ('reconciliacion_causas.csv', pd.DataFrame(cause_rows)),
                            ('casos_faltantes.csv', details.sort_values(KEY))]:
        frame.to_csv(out / filename, index=False, encoding='utf-8', lineterminator='\n')
    (out / 'resultados.json').write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument('--out', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--base-url', default='http://127.0.0.1:8501')
    args = parser.parse_args()
    result = run(args.root, args.out, args.base_url)
    print(json.dumps({'estados': result['estados'], 'reconciliacion': result['reconciliacion']}, ensure_ascii=True))
    raise SystemExit(1 if result['estados'].get('falla', 0) else 0)
