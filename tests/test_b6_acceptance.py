"""B6 regression: missing years are not observed low counts or extra exclusions."""
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('b6_traceability', ROOT / 'analisis/reportes/b6/verificar_trazabilidad.py')
acceptance = importlib.util.module_from_spec(spec)
spec.loader.exec_module(acceptance)
YEARS = [2009, 2012, 2015, 2018, 2021, 2024]


def test_missing_vs_low_counts_reconcile_manual_fixture_and_audited_panel():
    fixture = pd.DataFrame({'identidad_estable_conservadora':[True, True, True]})
    for year in YEARS:
        fixture[f'tasa_{year}'] = 50.
        fixture[f'observados_{year}'] = 200.
        fixture[f'ns_pct_{year}'] = 5.
    for stem in ['tasa', 'observados', 'ns_pct']:
        fixture.loc[[1,2],f'{stem}_2009'] = np.nan
    fixture.loc[2,'observados_2012'] = 10.
    flags = acceptance.exclusion_flags(fixture)
    assert flags.to_dict('list') == {
        'faltan_tasas':[False,True,True],
        'identidad_inestable':[False,False,False],
        'observados_menor_100':[False,False,True],
        'ns_mayor_20':[False,False,False],
        'faltan_conteos_o_ns':[False,True,True],
    }
    assert flags.any(axis=1).sum() == 2
    assert flags.sum().sum() == 5
    assert flags.drop(columns='faltan_conteos_o_ns').any(axis=1).equals(flags.any(axis=1))
    assert acceptance.boolean(pd.Series(['True','False'])).tolist() == [True,False]
    with pytest.raises(ValueError, match='Booleano'):
        acceptance.boolean(pd.Series(['True','false']))
    with pytest.raises(ValueError, match='Booleano'):
        acceptance.boolean(pd.Series(['False',None]))

    panel = pd.read_csv(ROOT / 'datos/processed/matriz_modelo_6_anios.csv',
                        dtype={'identidad_estable_conservadora':str,'apto_modelo':str})
    panel['identidad_estable_conservadora'] = acceptance.boolean(panel.identidad_estable_conservadora)
    saved = acceptance.boolean(panel.apto_modelo)
    flags = acceptance.exclusion_flags(panel)
    assert flags.sum().to_dict() == {'faltan_tasas':460,'identidad_inestable':190,
        'observados_menor_100':863,'ns_mayor_20':3307,'faltan_conteos_o_ns':110}
    missing = panel[[f'observados_{year}' for year in YEARS]].isna().any(axis=1)
    low = panel[[f'observados_{year}' for year in YEARS]].lt(100).any(axis=1)
    assert int(missing.sum()) == 110
    assert int((missing & low).sum()) == 21
    assert int((missing & ~low).sum()) == 89
    assert int((~panel[[f'observados_{year}' for year in YEARS]].ge(100).all(axis=1)).sum()) == 952
    old = flags.drop(columns='faltan_conteos_o_ns')
    assert int(old.sum().sum()) == 4820
    assert int(flags.sum().sum()) == 4930
    assert int(old.any(axis=1).sum()) == int(flags.any(axis=1).sum()) == 3844
    assert (~flags.any(axis=1)).equals(saved)
