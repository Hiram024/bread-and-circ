"""Small adversarial cases for the B2 audit, independent of the real CSV totals."""
import json

import numpy as np
import pandas as pd
import pytest

from src.validate_processed import (
    AGES, COUNTS, KEY, YEARS, audit, canonical_keys, clean_json, compare_frames,
    exclusions, parse_bool, reconstruct, validate_aggregate,
)


def synthetic_panel():
    annual, checks = [], []
    names = []
    for year in YEARS:
        frame = pd.DataFrame([
            dict(EDOCVE="01", MPIOCVE="001", grupo_edad="18-24", anio=year, LN=120, SV=60, NV=40, NS=20),
            # Both quality criteria fail, but this is one excluded unit.
            dict(EDOCVE="01", MPIOCVE="002", grupo_edad="18-24", anio=year, LN=100, SV=30, NV=30, NS=40),
        ])
        annual.append(validate_aggregate(frame, checks, "synthetic", year))
        names.extend([dict(EDOCVE="01", MPIOCVE=f"{m:03}", MPIONOM=f"Municipio {m}",
                           nombre_norm=f"MUNICIPIO{m}", EDONOM="Entidad", anio=year) for m in [1, 2]])
    assert not any(c["estado"] == "falla" for c in checks)
    return annual, pd.DataFrame(names)


def test_valid_selection_overlap_missing_year_and_boolean_parsing():
    annual, names = synthetic_panel()
    series, wide, _ = reconstruct(annual, names)
    assert len(series) == 12
    assert wide.apto_modelo.tolist() == [True, False]
    causes = exclusions(wide)
    assert causes.observados_menor_100.sum() == causes.ns_mayor_20.sum() == 1
    assert causes.loc[~causes.apto_modelo].shape[0] == 1
    assert causes.loc[1, "causas"] == "observados_menor_100 | ns_mayor_20"
    assert np.isclose(wide.loc[0, "media_presidencial"], 60)
    assert parse_bool(pd.Series(["True", "False", True, False])).tolist() == [True, False, True, False]
    for invalid in [["false"], ["yes"], ["1"], [None]]:
        with pytest.raises(ValueError, match="Booleanos inválidos"):
            parse_bool(pd.Series(invalid))
    annual[0] = annual[0].loc[annual[0].MPIOCVE.ne("001")]
    _, missing, _ = reconstruct(annual, names)
    assert not missing.loc[0, "completo_6"] and not missing.loc[0, "apto_modelo"]
    assert pd.isna(missing.loc[0, "tasa_2009"])
    # Skip-NaN min/max would look acceptable: completeness must still exclude it.
    assert missing.loc[0, "min_observados"] == 100
    assert missing.loc[0, "max_ns_pct"] < 20


def test_invalid_counts_zero_denominators_and_key_collisions():
    records = []
    counts = [(0, 0, 0, 0), (20, 0, 0, 20), (10, 3, 3, 3),
              (10, -1, 10, 1), (10, "bad", 4, 6), (10, np.inf, 0, 0),
              (10, 2.5, 3.5, 4), (10, None, 4, 6)]
    for m, row in enumerate(counts, 1):
        records.append(dict(EDOCVE="01", MPIOCVE=f"{m:03}", grupo_edad=AGES[0], anio=2009,
                            **dict(zip(COUNTS, row))))
    checks = []
    validated = validate_aggregate(pd.DataFrame(records), checks, "invalid", 2009)
    assert pd.isna(validated.loc[0, "tasa"]) and pd.isna(validated.loc[0, "ns_pct"])
    assert pd.isna(validated.loc[1, "tasa"]) and validated.loc[1, "ns_pct"] == 100
    sv = next(c for c in checks if c["control"] == "conteo_SV")
    assert sv["estado"] == "falla" and sv["discrepancias"] == 5
    assert next(c for c in checks if c["control"] == "LN_igual_SV_NV_NS")["estado"] == "falla"
    text = json.dumps(clean_json(checks), allow_nan=False)
    assert "Infinity" not in text and "NaN" not in text
    keys = canonical_keys(pd.DataFrame({"EDOCVE": ["1", "01", "x"], "MPIOCVE": ["1", "001", "0"]}), [], "keys")
    assert keys.EDOCVE[:2].tolist() == ["01", "01"]
    assert keys.MPIOCVE[:2].tolist() == ["001", "001"]
    checks = []
    assert not compare_frames(keys.iloc[:1], keys.iloc[:2], ["EDOCVE", "MPIOCVE"], [], checks, "collision")
    assert any(c["control"] == "comparacion_suspendida" for c in checks)
    boundary = pd.DataFrame([dict(EDOCVE="01", MPIOCVE="001", grupo_edad=AGES[0], anio="2009",
                                   LN=str(2**53), SV=str(2**53), NV="1", NS="0")], dtype="string")
    checks = []
    validate_aggregate(boundary, checks, "integer-boundary", 2009)
    assert next(c for c in checks if c["control"] == "LN_igual_SV_NV_NS")["estado"] == "falla"
    boundary = boundary.astype("string")
    boundary.loc[0, "SV"] = str(2**53 + 1)
    checks = []
    validate_aggregate(boundary, checks, "too-large", 2009)
    assert next(c for c in checks if c["control"] == "conteo_SV")["estado"] == "falla"
    boundary.loc[0, "anio"] = pd.NA
    checks = []
    validate_aggregate(boundary, checks, "missing-year-value", 2009)
    assert next(c for c in checks if c["control"] == "anio")["estado"] == "falla"


def test_duplicate_rejected_and_saved_panel_corruption_detected():
    annual, names = synthetic_panel()
    _, wide, _ = reconstruct(annual, names)
    saved = wide.astype("string")
    checks = []
    assert compare_frames(wide, saved, KEY, ["tasa_2024", "LN_2024", "apto_modelo"], checks, "valid")
    assert compare_frames(wide, saved.iloc[::-1], KEY, ["tasa_2024"], [], "shuffled")
    saved.loc[0, "tasa_2024"] = "61"
    saved.loc[1, "apto_modelo"] = "True"
    checks = []
    assert not compare_frames(wide, saved, KEY, ["tasa_2024", "apto_modelo"], checks, "corrupted")
    assert {c["control"] for c in checks if c["estado"] == "falla"} == {"valor_tasa_2024", "valor_apto_modelo"}
    saved = wide.astype("string").iloc[:1]
    assert not compare_frames(wide, saved, KEY, ["tasa_2024"], [], "missing-key")
    saved = wide.astype("string")
    saved.loc[0, "LN_2024"] = "120.00000000001"
    assert not compare_frames(wide, saved, KEY, ["LN_2024"], [], "exact-count")
    annual[0] = pd.concat([annual[0], annual[0].iloc[:1]])
    with pytest.raises(ValueError, match="duplicados"):
        reconstruct(annual, names)


def test_missing_inputs_block_and_protected_output_is_rejected(tmp_path):
    assert audit(tmp_path, tmp_path / "audit") == 1
    result = json.loads((tmp_path / "audit/resultados.json").read_text(encoding="utf-8"))
    assert result["decision"] == "BLOQUEADO"
    assert any(c["control"] == "reconstruccion_panel" and c["estado"] == "no comprobado" for c in result["controles"])
    with pytest.raises(ValueError, match="separado"):
        audit(tmp_path, tmp_path / "datos/processed")
