"""Read-only analytical views of the active snapshot and matched B2 evidence."""
from pathlib import Path

import numpy as np
import pandas as pd

from .product_contract import FEATS, YEARS, read_json, sha256

AGES = ('18-24', '25-34', '35-44', '45-59', '60+')
KEY = ['EDOCVE', 'MPIOCVE', 'grupo_edad']
CAUSES = {
    'faltan_tasas': 'Falta alguna tasa',
    'identidad_inestable': 'Identidad nominal inestable',
    'observados_menor_100': 'Menos de 100 observados en alguna elección',
    'ns_mayor_20': 'NS mayor de 20% en alguna elección',
    'faltan_conteos_o_ns': 'Faltan conteos o NS',
}


def national_history(frame):
    """National ratios use summed counts; an undefined rate stays null."""
    result = frame.sort_values('anio').copy()
    observed = result.SV + result.NV
    result['participacion_pct'] = 100 * result.SV / observed.where(observed.gt(0))
    result['ns_pct'] = 100 * result.NS / result.LN.where(result.LN.gt(0))
    return result.replace({np.nan: None}).to_dict('records')


def filter_observations(frame, estado=None, perfil=None, edad=None, q=''):
    if estado is not None:
        frame = frame[frame.EDOCVE.eq(estado)]
    if perfil is not None:
        frame = frame[frame.perfil_id.eq(perfil)]
    if edad:
        frame = frame[frame.grupo_edad.eq(edad)]
    if q:
        frame = frame[frame.MPIONOM.str.contains(q, case=False, na=False, regex=False)]
    return frame.sort_values(KEY, kind='stable')


def selection_summary(frame):
    """Simple unit means over every matching row, before pagination."""
    def mean(column):
        value = frame[column].mean()
        return float(value) if pd.notna(value) else None

    return {
        'unidades': len(frame),
        'municipios': len(frame.groupby(KEY[:2])),
        'lista_nominal_2024': int(frame.LN_2024.sum()),
        'medias': {field: mean(field) for field in FEATS},
        'perfil_conteos': [{'perfil_id': int(pid), 'unidades': int(count)}
                          for pid, count in frame.perfil_id.value_counts().sort_index().items()],
        'historico': [{'anio': year, 'tipo': 'Presidencial' if year in (2012, 2018, 2024) else 'Intermedia',
                       'media_tasa_pct': mean(f'tasa_{year}'),
                       'unidades_con_tasa': int(frame[f'tasa_{year}'].notna().sum())} for year in YEARS],
    }


def audit_evidence(root, package):
    """Fail closed for this view if supplemental B2 evidence no longer matches."""
    root = Path(root)
    binding = read_json(root / 'analisis/reportes/b5/fuentes_auditoria.json')
    if binding['package_digest'] != package['package_digest']:
        raise ValueError('La evidencia B2 no corresponde al paquete activo')
    for name, expected in binding['files'].items():
        if sha256(root / name) != expected:
            raise ValueError(f'Evidencia B2 modificada: {name}')
    evidence = read_json(root / 'analisis/reportes/b2/resultados.json')
    for name, expected in evidence['trazabilidad']['sha256_entradas_y_codigo'].items():
        # B4 legitimately changed code/docs; only the audited data are inherited.
        if name.startswith('datos/processed/') and sha256(root / name) != expected:
            raise ValueError(f'Entrada auditada modificada: {name}')
    folder = root / 'analisis/reportes/b2'
    flags = pd.read_csv(folder / 'elegibilidad_y_causas.csv', dtype={c: str for c in ['apto_modelo', *CAUSES]})
    for column in ['apto_modelo', *CAUSES]:
        if not flags[column].isin(['True', 'False']).all():
            raise ValueError(f'Booleano desconocido en evidencia B2: {column}')
        flags[column] = flags[column].map({'True': True, 'False': False})
    if flags.duplicated(KEY).any() or flags[KEY].isna().any().any():
        raise ValueError('Claves ambiguas en evidencia B2')
    if not flags.apto_modelo.eq(~flags[list(CAUSES)].any(axis=1)).all():
        raise ValueError('Elegibilidad y causas B2 no corresponden')
    keys = lambda frame: set(frame[KEY].itertuples(index=False, name=None))
    if keys(flags[flags.apto_modelo]) != keys(package['data']):
        raise ValueError('Las unidades B2 no corresponden al paquete activo')
    national = pd.read_csv(folder / 'totales_anuales.csv').set_index('anio').sort_index()
    active = package['national'].set_index('anio').sort_index()
    if list(national.index) != list(YEARS) or list(active.index) != list(YEARS):
        raise ValueError('Años nacionales incompletos')
    for field in ['LN', 'SV', 'NV', 'NS']:
        if not national[field].equals(active[field]):
            raise ValueError(f'Total nacional no coincide con B2: {field}')
    rates = 100 * national.SV / (national.SV + national.NV)
    if not np.allclose(rates, active.participacion_pct, rtol=0, atol=1e-10):
        raise ValueError('La tasa nacional no coincide con la razón de sumas B2')
    summary = evidence['resumen']
    if len(flags) != summary['n_panel'] or int(flags.apto_modelo.sum()) != summary['n_validas']:
        raise ValueError('Tamaño del panel B2 incoherente')
    coverage = pd.read_csv(folder / 'cobertura.csv')
    ln = package['metadata']['cobertura_LN_2024']
    checks = {
        'unidades_panel': (len(package['data']), len(flags)),
        'municipios_panel': (len(package['data'].groupby(KEY[:2])), len(flags.groupby(KEY[:2]))),
        'LN_2024_nacional_procesado': (int(package['data'].LN_2024.sum()), int(national.loc[2024, 'LN'])),
    }
    for measure, (numerator, denominator) in checks.items():
        row = coverage.loc[coverage.medida.eq(measure)]
        if (len(row) != 1 or int(row.iloc[0].numerador) != numerator or int(row.iloc[0].denominador) != denominator
                or not np.isclose(row.iloc[0].porcentaje, 100 * numerator / denominator, rtol=0, atol=1e-10)):
            raise ValueError(f'Cobertura B2 incoherente: {measure}')
    if ln['numerador'] != checks['LN_2024_nacional_procesado'][0] or ln['denominador'] != checks['LN_2024_nacional_procesado'][1]:
        raise ValueError('Denominador LN del paquete incoherente')
    combinations = flags.groupby(list(CAUSES), sort=True).size()
    return {
        'package_version': package['package_version'], 'package_digest': package['package_digest'],
        'fuentes': binding['files'], 'decision_B2': evidence['decision'],
        'panel': len(flags), 'elegibles': int(flags.apto_modelo.sum()),
        'excluidas_unicas': int((~flags.apto_modelo).sum()),
        'cobertura': coverage.to_dict('records'),
        'causas': [{'codigo': code, 'motivo': label, 'unidades': int(flags[code].sum())} for code, label in CAUSES.items()],
        'combinaciones_excluidas': [{'causas': [code for code, value in zip(CAUSES, combination) if value],
                                    'unidades': int(count)} for combination, count in combinations.items() if any(combination)],
        'seleccion_edad': pd.read_csv(folder / 'seleccion_edad.csv').to_dict('records'),
        'seleccion_entidad': pd.read_csv(folder / 'seleccion_entidad.csv').to_dict('records'),
    }
