"""B2: independent, read-only audit of processed CCPC inputs (no RAW or training).

Run: python -m src.validate_processed --root . --out analisis/reportes/b2
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import importlib.util
import json
import re
import subprocess
import sys
import unicodedata
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

YEARS = (2009, 2012, 2015, 2018, 2021, 2024)
AGES = ("18-24", "25-34", "35-44", "45-59", "60+")
MUNICIPALITY = ["EDOCVE", "MPIOCVE"]
KEY = MUNICIPALITY + ["grupo_edad"]
COUNTS = ["LN", "SV", "NV", "NS"]
MEASURES = COUNTS + ["observados", "tasa", "ns_pct"]
ATOL = 1e-10  # Full-precision CSV rates/features, in percentage points; rtol=0.
CAUSES = ["faltan_tasas", "identidad_inestable", "observados_menor_100", "ns_mayor_20", "faltan_conteos_o_ns"]


def clean_json(value):
    """Keep evidence JSON standard, including missing values in anomaly examples."""
    if isinstance(value, dict):
        return {str(k): clean_json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean_json(v) for v in value]
    if isinstance(value, np.generic):
        value = value.item()
    if value is None or value is pd.NA or (isinstance(value, float) and not np.isfinite(value)):
        return None
    return value


def record(checks, control, source, expected, observed, discrepancies=0, examples=None,
           status=None, impact="Bloquea B3 si falla"):
    status = status or ("falla" if discrepancies else "pasa")
    checks.append(clean_json(dict(control=control, archivo_universo=source, esperado=expected,
                                  observado=observed, estado=status, discrepancias=int(discrepancies),
                                  ejemplos=examples or [], efecto_B3=impact)))
    return status == "pasa"


def examples(frame, mask, columns=None):
    return frame.loc[mask, columns or list(frame.columns)].head(5).to_dict("records")


def parse_bool(values):
    """Only explicit CSV booleans; never bool('False'). Unknown/null is an error."""
    text = values.astype("string")
    invalid = ~text.isin(["True", "False"])
    if invalid.any():
        raise ValueError(f"Booleanos inválidos: {text[invalid].head(5).tolist()}")
    return text.eq("True").astype(bool)


def canonical_keys(frame, checks, label):
    for col, width, upper in [("EDOCVE", 2, 32), ("MPIOCVE", 3, 999)]:
        if col not in frame:
            continue
        raw = frame[col].astype("string")
        number = pd.to_numeric(raw, errors="coerce")
        bad = (~raw.str.fullmatch(r"[0-9]+", na=False) | ~number.between(1, upper)).fillna(True)
        record(checks, f"clave_{col}", label, f"Entero 1..{upper}, representación de ancho {width}",
               int(bad.sum()), bad.sum(), examples(frame, bad))
        # No coercion of malformed keys into an apparently valid municipality.
        frame[col] = raw.str.zfill(width)
    return frame


def read_csv(root, rel, checks, required):
    try:
        frame = pd.read_csv(root / rel, dtype="string", keep_default_na=False)
        frame = frame.mask(frame.eq(""))
    except (OSError, ValueError, pd.errors.ParserError) as exc:
        record(checks, "insumo_legible", rel, "CSV disponible", str(exc), 1, status="no comprobado")
        return None
    missing = sorted(set(required) - set(frame))
    record(checks, "esquema", rel, list(required), list(frame), len(missing), missing)
    if missing:
        return None
    return canonical_keys(frame, checks, rel)


def read_json(root, rel, checks, expected_type=dict):
    try:
        value = json.loads((root / rel).read_text(encoding="utf-8"))
        if not isinstance(value, expected_type):
            raise ValueError(f"Se esperaba {expected_type.__name__}; se encontró {type(value).__name__}")
        return value
    except (OSError, ValueError) as exc:
        record(checks, "insumo_legible", rel, "JSON disponible", str(exc), 1, status="no comprobado")
        return None


def unique(frame, keys, checks, label):
    bad = frame[keys].isna().any(axis=1) | frame.duplicated(keys, keep=False)
    return record(checks, "unicidad", label, {"clave": keys, "duplicados_o_nulos": 0},
                  {"filas": len(frame), "duplicados_o_nulos": int(bad.sum())}, bad.sum(),
                  examples(frame, bad, keys))


def validate_aggregate(frame, checks, label, year, extra=()):
    """Validate every count before deriving rates, without zero imputation."""
    for field in COUNTS:
        original = frame[field].copy()
        number = pd.to_numeric(original, errors="coerce")
        bad = (~np.isfinite(number) | number.lt(0) | number.mod(1).ne(0) | number.gt(2**53)).fillna(True)
        record(checks, f"conteo_{field}", label, "Finito, entero, no negativo, <=2**53", int(bad.sum()),
               bad.sum(), examples(frame, bad, KEY + ["anio", field]))
        frame[field] = number.astype(float if bad.any() else "int64")
    bad_year = pd.to_numeric(frame.anio, errors="coerce").ne(year).fillna(True)
    record(checks, "anio", label, year, sorted(frame.anio.dropna().astype(str).unique()), bad_year.sum(),
           examples(frame, bad_year, KEY + ["anio"]))
    frame["anio"] = year
    bad_age = ~frame.grupo_edad.isin(AGES)
    record(checks, "categorias_edad", label, AGES, sorted(frame.grupo_edad.dropna().unique()),
           bad_age.sum(), examples(frame, bad_age, KEY))
    unique(frame, ["anio"] + KEY + list(extra), checks, label)
    bad = frame.LN.ne(frame.SV + frame.NV + frame.NS)
    record(checks, "LN_igual_SV_NV_NS", label, "Igualdad exacta en todas las filas", int(bad.sum()),
           bad.sum(), examples(frame, bad, KEY + COUNTS))
    frame["observados"] = frame.SV + frame.NV
    frame["tasa"] = 100 * frame.SV.div(frame.observados.where(frame.observados.gt(0)))
    frame["ns_pct"] = 100 * frame.NS.div(frame.LN.where(frame.LN.gt(0)))
    for field, denominator in [("tasa", "observados"), ("ns_pct", "LN")]:
        undefined = frame[denominator].eq(0)
        record(checks, f"denominador_cero_{field}", label, "Indefinido (nulo), nunca tasa cero",
               int(undefined.sum()), examples=examples(frame, undefined, KEY + COUNTS + [field]),
               status="advertencia" if undefined.any() else "pasa",
               impact="No bloquea si se conserva nulo y la unidad no se considera completa")
        bad = (frame[field].notna() & ~frame[field].between(0, 100)) | (undefined & frame[field].notna())
        record(checks, f"rango_{field}", label, "[0,100] cuando está definido", int(bad.sum()), bad.sum(),
               examples(frame, bad, KEY + [field]))
    return frame


def compare_frames(expected, actual, keys, fields, checks, label, atol=ATOL):
    """Outer alignment detects missing/extra keys; no positional comparisons or dedup."""
    if actual is None:
        return False
    missing = sorted(set(keys + fields) - set(actual))
    if missing:
        record(checks, "columnas_comparacion", label, keys + fields, list(actual), len(missing), missing)
        return False
    valid = [unique(frame, keys, checks, f"{label}:{side}")
             for side, frame in [("recalculado", expected), ("guardado", actual)]]
    if not all(valid):
        record(checks, "comparacion_suspendida", label, "Join one_to_one", "Clave ambigua", 1,
               status="no comprobado")
        return False
    joined = expected[keys + fields].merge(actual[keys + fields], on=keys, how="outer",
                                           suffixes=("_esperado", "_guardado"), indicator=True,
                                           validate="one_to_one")
    bad_keys = joined._merge.ne("both")
    ok = record(checks, "universo", label, len(expected), len(actual), bad_keys.sum(),
                examples(joined, bad_keys, keys + ["_merge"]))
    both = joined.loc[~bad_keys]
    for field in fields:
        left, right = both[f"{field}_esperado"], both[f"{field}_guardado"]
        numeric = pd.api.types.is_numeric_dtype(expected[field])
        boolean = pd.api.types.is_bool_dtype(expected[field])
        max_delta = None
        if boolean:
            try:
                right = parse_bool(right)
                equal = left.eq(right)
            except ValueError as exc:
                record(checks, f"booleano_{field}", label, "True/False explícitos", str(exc), 1)
                ok = False
                continue
        elif numeric:
            converted = pd.to_numeric(right, errors="coerce").astype(float)
            left_num = left.astype(float)
            integer = field.split("_")[0] in COUNTS + ["observados"] or field.startswith(("n_", "total_")) or field in [
                "anio", "municipios", "municipio_edad", "filas_agregadas", "variantes_nombre",
                "anios_observados", "variantes_normalizadas", "n", "n_unidades", "min_observados", "lista_nominal_2024",
                "filas_RAW_documentadas_no_verificadas"]
            tolerance = 0 if integer else atol
            equal = pd.Series(np.isclose(left_num, converted, rtol=0, atol=tolerance, equal_nan=True), index=both.index)
            # A nonnumeric token is not equivalent to a structural missing value.
            equal &= ~(right.notna() & (converted.isna() | ~np.isfinite(converted)))
            delta = (left_num - converted).abs()
            max_delta = float(delta.max()) if delta.notna().any() else None
        else:
            equal = left.astype("string").eq(right.astype("string")).fillna(False) | (left.isna() & right.isna())
        bad = ~equal
        passed = record(checks, f"valor_{field}", label,
                        {"coincidencia": "por clave", "atol": (0 if boolean or not numeric else tolerance), "rtol": 0},
                        {"diferencias": int(bad.sum()), "max_diferencia_absoluta": max_delta}, bad.sum(),
                        examples(both, bad, keys + [f"{field}_esperado", f"{field}_guardado"]))
        ok = passed and ok
    return ok


def normalize_nominal(value):
    # Independent implementation of the documented accent/punctuation-insensitive rule.
    letters = unicodedata.normalize("NFKD", value.upper())
    return re.sub("[^A-Z0-9]", "", "".join(c for c in letters if not unicodedata.combining(c)))


def reconstruct(annual, names):
    """No calls to pipeline.panel; year-by-year 1:1 merges cannot conceal duplicates."""
    series = pd.concat(annual, ignore_index=True).sort_values(["anio"] + KEY).reset_index(drop=True)
    if series.duplicated(["anio"] + KEY).any():
        raise ValueError("Serie ambigua: duplicados antes de reconstruir el panel")
    identity = names.groupby(MUNICIPALITY, as_index=False).agg(
        variantes_nombre=("nombre_norm", "nunique"))
    identity["identidad_estable_conservadora"] = identity.variantes_nombre.eq(1)
    series = series.merge(identity, on=MUNICIPALITY, how="left", validate="many_to_one")
    if series.variantes_nombre.isna().any():
        raise ValueError("Unidades sin identidad nominal; no se puede determinar elegibilidad")
    units = series.groupby(KEY, as_index=False).size()[KEY]
    wide = units
    for year in YEARS:
        values = series.loc[series.anio.eq(year), KEY + MEASURES]
        wide = wide.merge(values.rename(columns={c: f"{c}_{year}" for c in MEASURES}),
                          on=KEY, how="left", validate="one_to_one")
    wide = wide.merge(identity, on=MUNICIPALITY, how="left", validate="many_to_one")
    rates = wide[[f"tasa_{y}" for y in YEARS]]
    observed = wide[[f"observados_{y}" for y in YEARS]]
    ns = wide[[f"ns_pct_{y}" for y in YEARS]]
    wide["completo_6"] = rates.notna().all(axis=1) & np.isfinite(rates).all(axis=1)
    # Saved descriptive extrema skip missing years; eligibility below never does.
    wide["min_observados"] = observed.min(axis=1)
    wide["max_ns_pct"] = ns.max(axis=1)
    wide["apto_modelo"] = (wide.completo_6 & wide.identidad_estable_conservadora &
                           observed.ge(100).all(axis=1) & ns.le(20).all(axis=1) &
                           observed.notna().all(axis=1) & ns.notna().all(axis=1))
    for kind, years in [("presidencial", (2012, 2018, 2024)), ("intermedia", (2009, 2015, 2021))]:
        first, middle, last = [wide[f"tasa_{y}"] for y in years]
        # Existing descriptive means use available rates; the complete flag gates training.
        wide[f"media_{kind}"] = pd.concat([first, middle, last], axis=1).mean(axis=1)
        wide[f"cambio_{kind}_pp"] = last - first
        wide[f"curvatura_{kind}_pp"] = middle - (first + last) / 2
    wide["brecha_pres_intermedia"] = wide.media_presidencial - wide.media_intermedia
    return series.sort_values(["anio"] + KEY), wide.sort_values(KEY), identity.sort_values(MUNICIPALITY)


def exclusions(wide):
    result = wide[KEY + ["completo_6", "apto_modelo"]].copy()
    result["faltan_tasas"] = ~wide.completo_6
    result["identidad_inestable"] = ~wide.identidad_estable_conservadora
    result["observados_menor_100"] = wide[[f"observados_{y}" for y in YEARS]].lt(100).any(axis=1)
    result["ns_mayor_20"] = wide[[f"ns_pct_{y}" for y in YEARS]].gt(20).any(axis=1)
    result["faltan_conteos_o_ns"] = wide[[f"{c}_{y}" for c in ["observados", "ns_pct"] for y in YEARS]].isna().any(axis=1)
    result["causas"] = result[CAUSES].apply(lambda row: " | ".join(row.index[row]) or "incluida", axis=1)
    return result


def national(annual):
    rows = []
    for frame in annual:
        totals = {c: int(frame[c].sum()) for c in COUNTS}
        obs = totals["SV"] + totals["NV"]
        rows.append(dict(anio=int(frame.anio.iloc[0]), filas_agregadas=len(frame),
                         municipios=len(frame.groupby(MUNICIPALITY)), **totals,
                         observados=obs, participacion_pct=100 * totals["SV"] / obs if obs else np.nan,
                         ns_pct=100 * totals["NS"] / totals["LN"] if totals["LN"] else np.nan))
    return pd.DataFrame(rows).sort_values("anio")


def save_csv(frame, out, name):
    frame.to_csv(out / name, index=False, lineterminator="\n")


def selection_tables(series, wide, names, out):
    flags = wide[KEY + ["apto_modelo"]]
    labelled = series.merge(flags, on=KEY, validate="many_to_one")
    names24 = names.loc[names.anio.eq(2024)].groupby(MUNICIPALITY).EDONOM.agg(
        lambda s: " | ".join(sorted(set(s)))).rename("EDONOM")
    selection = wide.merge(names24, on=MUNICIPALITY, how="left", validate="many_to_one")
    for fields, filename in [(["EDOCVE", "EDONOM"], "seleccion_entidad.csv"),
                             (["grupo_edad"], "seleccion_edad.csv"),
                             (["EDOCVE", "EDONOM", "grupo_edad"], "seleccion_entidad_edad.csv")]:
        table = selection.groupby(fields, dropna=False).apto_modelo.agg(unidades="size", incluidas="sum").reset_index()
        table["excluidas"] = table.unidades - table.incluidas
        table["incluidas_pct_del_grupo"] = 100 * table.incluidas / table.unidades
        table["excluidas_pct_del_grupo"] = 100 * table.excluidas / table.unidades
        save_csv(table.sort_values(fields), out, filename)
    summary = labelled.groupby(["anio", "apto_modelo"], as_index=False).agg(
        unidades_presentes=("LN", "size"), tasas_definidas=("tasa", "count"),
        LN=("LN", "sum"), SV=("SV", "sum"), NV=("NV", "sum"), NS=("NS", "sum"),
        tasa_media_simple_unidades=("tasa", "mean"), ns_media_simple_unidades=("ns_pct", "mean"))
    summary["participacion_ponderada_observados_pct"] = 100 * summary.SV / (summary.SV + summary.NV)
    summary["ns_ponderado_LN_pct"] = 100 * summary.NS / summary.LN
    annual_totals = labelled.groupby("anio")[COUNTS].sum()
    summary["cobertura_LN_anual_pct"] = 100 * summary.LN / summary.anio.map(annual_totals.LN)
    summary["cobertura_unidades_anual_pct"] = 100 * summary.unidades_presentes / summary.anio.map(labelled.groupby("anio").size())
    summary["universo_unidades_grupo"] = summary.apto_modelo.map(wide.apto_modelo.value_counts())
    summary["presencia_pct_del_grupo"] = 100 * summary.unidades_presentes / summary.universo_unidades_grupo
    save_csv(summary.sort_values(["anio", "apto_modelo"]), out, "seleccion_anual.csv")
    missing_frames = []
    for year in YEARS:
        present = series.loc[series.anio.eq(year), KEY].assign(presente=True)
        part = wide[KEY + [f"tasa_{year}", f"observados_{year}", f"ns_pct_{year}"]].merge(
            present, on=KEY, how="left", validate="one_to_one")
        part["anio"] = year
        part["motivo"] = np.where(part.presente.isna(), "unidad_ausente", "sin_observados")
        missing_frames.append(part.loc[part[f"tasa_{year}"].isna(), KEY + ["anio", "motivo"]])
    missing = pd.concat(missing_frames, ignore_index=True)
    save_csv(missing.sort_values(["anio"] + KEY), out, "tasas_ausentes.csv")
    return summary


def git(root, *args):
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, encoding="utf-8")
    return result.stdout.strip() if result.returncode == 0 else f"NO DISPONIBLE: {result.stderr.strip()}"


def fingerprint(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def reconcile(root, totals, secondary, checks):
    reports = "analisis/reportes/"
    for rel in [reports + "auditoria_resumen.csv", reports + "resumen_nacional.csv",
                "datos/processed/producto/historico_nacional.csv"]:
        saved = read_csv(root, rel, checks, ["anio"] + COUNTS + ["municipios"])
        if saved is not None:
            saved["anio"] = pd.to_numeric(saved.anio, errors="coerce")
            fields = COUNTS + ["municipios"]
            saved = saved.rename(columns={"filas": "filas_RAW_documentadas_no_verificadas"})
            fields += ["filas_RAW_documentadas_no_verificadas"]
            if "participacion_pct" in saved:
                fields += ["participacion_pct", "ns_pct"]
            else:
                saved = saved.rename(columns={"municipio_edad": "filas_agregadas"})
                fields += ["filas_agregadas"]
            compare_frames(totals, saved, ["anio"], fields, checks, rel)
    for variable, name in [("grupo_edad", "participacion_por_edad_y_anio.csv"),
                           ("SEXO", "participacion_por_sexo_y_anio.csv"),
                           ("TIPOSEC", "participacion_por_tipo_seccion_y_anio.csv")]:
        source = secondary.get(variable, [])
        if not source:
            continue
        values = pd.concat(source).groupby(["anio", variable], as_index=False)[COUNTS].sum()
        values["participacion_pct"] = 100 * values.SV / (values.SV + values.NV).where((values.SV + values.NV).gt(0))
        values["ns_pct"] = 100 * values.NS / values.LN.where(values.LN.gt(0))
        rel = reports + name
        actual = read_csv(root, rel, checks, ["anio", variable] + COUNTS + ["participacion_pct"])
        if actual is not None:
            actual["anio"] = pd.to_numeric(actual.anio, errors="coerce")
            fields = COUNTS + ["participacion_pct"] + (["ns_pct"] if variable == "grupo_edad" else [])
            compare_frames(values, actual, ["anio", variable], fields, checks, rel)


def reconcile_panel(root, wide, series, identity, names, totals, checks, out):
    proc = "datos/processed/"
    for expected, rel, keys in [(series, proc + "serie_municipio_edad_2009_2024.csv", ["anio"] + KEY),
                                (wide, proc + "matriz_modelo_6_anios.csv", KEY),
                                (identity, proc + "municipios_auditoria_identidad.csv", MUNICIPALITY),
                                (names[[*MUNICIPALITY, "MPIONOM", "nombre_norm", "anio"]],
                                 proc + "municipios_nombres_historicos.csv", MUNICIPALITY + ["anio", "MPIONOM", "nombre_norm"])]:
        actual = read_csv(root, rel, checks, keys)
        if actual is not None and "anio" in keys:
            actual["anio"] = pd.to_numeric(actual.anio, errors="coerce")
        compare_frames(expected, actual, keys, [c for c in expected if c not in keys], checks, rel)
        if rel.endswith("matriz_modelo_6_anios.csv") and actual is not None and not actual.duplicated(KEY).any():
            try:
                saved_flag = actual[KEY].assign(apto_guardado=parse_bool(actual.apto_modelo))
                joined = wide[KEY + ["apto_modelo"]].merge(saved_flag, on=KEY, how="outer", validate="one_to_one")
                save_csv(joined.loc[joined.apto_modelo.ne(joined.apto_guardado)].sort_values(KEY), out,
                         "diferencias_elegibilidad.csv")
            except (ValueError, AttributeError) as exc:
                record(checks, "elegibilidad_guardada", rel, "Booleano válido", str(exc), 1)
    excluded = exclusions(wide)
    save_csv(excluded.sort_values(KEY), out, "elegibilidad_y_causas.csv")
    combinations = excluded.groupby(CAUSES, as_index=False, dropna=False).size().rename(columns={"size": "unidades"})
    combinations["excluidas"] = combinations[CAUSES].any(axis=1)
    save_csv(combinations.sort_values(CAUSES), out, "combinaciones_exclusion.csv")
    record(checks, "union_exclusiones", "panel reconstruido", int((~wide.apto_modelo).sum()),
           int(excluded[CAUSES].any(axis=1).sum()),
           int((excluded[CAUSES].any(axis=1) != ~wide.apto_modelo).sum()))
    saved_coverage = read_csv(root, "analisis/reportes/cobertura_panel.csv", checks, ["grupo", "n"])
    coverage = pd.DataFrame({"grupo": ["Todas las unidades distintas", "Con tasa en seis elecciones",
                                      "Con nombre municipal estable", "Aptas para clustering"],
                             "n": [len(wide), int(wide.completo_6.sum()),
                                   int(wide.identidad_estable_conservadora.sum()), int(wide.apto_modelo.sum())]})
    compare_frames(coverage, saved_coverage, ["grupo"], ["n"], checks, "cobertura_panel.csv")
    causes = pd.DataFrame({"motivo": ["Falta al menos una tasa", "Nombre municipal inconsistente",
                                      "<100 observados en alguna elección", "NS >20% en alguna elección"],
                           "n_unidades": [int(excluded[c].sum()) for c in CAUSES[:4]]})
    compare_frames(causes, read_csv(root, "analisis/reportes/causas_exclusion_superpuestas.csv", checks,
                                   ["motivo", "n_unidades"]), ["motivo"], ["n_unidades"], checks, "causas_exclusion_superpuestas.csv")
    save_csv(causes, out, "exclusiones_superpuestas.csv")
    eligible = wide.loc[wide.apto_modelo]
    stats = dict(n_panel=len(wide), n_completo6=int(wide.completo_6.sum()), n_validas=len(eligible),
                 n_nombre_estable=int(wide.identidad_estable_conservadora.sum()),
                 n_municipios=len(eligible.groupby(MUNICIPALITY)),
                 LN_2024_validas=int(eligible.LN_2024.sum()), LN_2024_total_panel=int(wide.LN_2024.sum()))
    stats["cobertura_LN_2024_pct"] = 100 * stats["LN_2024_validas"] / stats["LN_2024_total_panel"]
    meta = read_json(root, "ml/resultados/resumen_modelado.json", checks)
    if meta is not None:
        compare_frames(pd.DataFrame([dict(universo="panel", **stats)]), pd.DataFrame([dict(universo="panel", **meta)]),
                       ["universo"], list(stats), checks, "resumen_modelado.json", atol=ATOL)
    product_meta = read_json(root, proc + "producto/metadatos_dashboard.json", checks)
    if product_meta is not None:
        expected = pd.DataFrame([dict(universo="producto", total_unidades_modeladas=stats["n_validas"],
                                      total_municipios_modelados=stats["n_municipios"], total_unidades_panel=stats["n_panel"])])
        compare_frames(expected, pd.DataFrame([dict(universo="producto", **product_meta)]), ["universo"],
                       ["total_unidades_modeladas", "total_municipios_modelados", "total_unidades_panel"], checks, "metadatos_dashboard.json", atol=0)
    profiles = read_json(root, proc + "producto/perfiles.json", checks, expected_type=list)
    if profiles is not None:
        profile_frame = pd.DataFrame(profiles)
        required = ["perfil_id", "n_unidades", "lista_nominal_2024"]
        if set(required).issubset(profile_frame):
            unique(profile_frame, ["perfil_id"], checks, "perfiles.json")
            for field, expected in [("n_unidades", stats["n_validas"]), ("lista_nominal_2024", stats["LN_2024_validas"])]:
                values = pd.to_numeric(profile_frame[field], errors="coerce")
                bad = ~np.isfinite(values) | values.lt(0) | values.mod(1).ne(0)
                record(checks, f"total_perfiles_{field}", "perfiles.json", expected, values.sum(),
                       int(bad.sum()) + int(values.sum() != expected))
            if product_meta is not None:
                compare_frames(profile_frame, pd.DataFrame(product_meta.get("perfiles", [])), ["perfil_id"],
                               ["n_unidades", "lista_nominal_2024"], checks, "perfiles.json vs copia metadatos", atol=0)
        else:
            record(checks, "esquema_perfiles", "perfiles.json", required, list(profile_frame), 1)
    for rel in ["ml/resultados/observaciones_segmentadas.csv", proc + "producto/observaciones_dashboard.csv"]:
        actual = read_csv(root, rel, checks, KEY)
        fields = ["media_presidencial", "media_intermedia", "cambio_presidencial_pp", "cambio_intermedia_pp",
                  "brecha_pres_intermedia", "LN_2024", "max_ns_pct"] + [f"{v}_{y}" for v in ["tasa", "observados"] for y in YEARS]
        compare_frames(eligible, actual, KEY, fields, checks, rel)
    territorial = names.groupby(MUNICIPALITY, as_index=False).agg(
        anios_observados=("anio", "nunique"), variantes_normalizadas=("nombre_norm", "nunique"),
        nombres=("MPIONOM", lambda s: " | ".join(sorted(set(s)))))
    territorial["estatus_administrativo"] = np.where(territorial.anios_observados.lt(6), "incompleto_en_serie",
        np.where(territorial.variantes_normalizadas.gt(1), "revisar_identidad_nominal", "estable_por_nombre_y_clave"))
    territorial["requiere_revision_territorial"] = True
    compare_frames(territorial, read_csv(root, proc + "producto/homologacion_municipal_auditoria.csv", checks, MUNICIPALITY),
                   MUNICIPALITY, [c for c in territorial if c not in MUNICIPALITY], checks, "homologacion_municipal_auditoria.csv")
    save_csv(territorial.sort_values(MUNICIPALITY), out, "identidad_nominal.csv")
    save_csv(names.sort_values(["anio"] + MUNICIPALITY + ["MPIONOM"]), out, "nombres_anuales_control.csv")
    record(checks, "variantes_nominales", "municipios procesados", "Exclusión conservadora sin fuzzy matching",
           int(territorial.variantes_normalizadas.gt(1).sum()), status="advertencia",
           examples=territorial.loc[territorial.variantes_normalizadas.gt(1)].head(5).to_dict("records"),
           impact="No bloquea; nombres iguales no certifican fronteras históricas")
    ln_national = int(totals.loc[totals.anio.eq(2024), "LN"].iloc[0])
    municipal_total = len(wide.groupby(MUNICIPALITY))
    rows = []
    for measure, num, den, universe in [
        ("unidades_panel", len(eligible), len(wide), "Unión de municipio × edad observada en los seis CSV"),
        ("municipios_panel", stats["n_municipios"], municipal_total, "Unión de claves municipales en los seis CSV"),
        ("LN_2024_panel", stats["LN_2024_validas"], stats["LN_2024_total_panel"], "LN 2024 de unidades del panel"),
        ("LN_2024_nacional_procesado", stats["LN_2024_validas"], ln_national, "LN del agregado nacional procesado 2024 (cinco edades)"),
        ("municipios_2024", stats["n_municipios"], int(totals.loc[totals.anio.eq(2024), "municipios"].iloc[0]), "Municipios presentes en agregado 2024")]:
        rows.append(dict(medida=measure, numerador=num, denominador=den, porcentaje=100*num/den, universo=universe))
    save_csv(pd.DataFrame(rows), out, "cobertura.csv")
    record(checks, "denominador_LN_2024", "panel vs agregado 2024", ln_national, stats["LN_2024_total_panel"],
           int(ln_national != stats["LN_2024_total_panel"]))
    selection_tables(series, wide, names, out)
    stats.update(excluidas_unicas=int((~wide.apto_modelo).sum()), municipios_panel=municipal_total,
                 filas_serie=len(series), causas_superpuestas={c: int(excluded[c].sum()) for c in CAUSES},
                 municipios_identidad_inestable=int(territorial.variantes_normalizadas.gt(1).sum()))
    return stats


def audit(root, out):
    root, out = root.resolve(), out.resolve()
    protected = [root / p for p in ["datos", "ml", "src", "tests", "docs"]]
    if out == root or any(out == p or p in out.parents or out in p.parents for p in protected):
        raise ValueError("--out debe estar separado de insumos/código; recomendado analisis/reportes/b2")
    out.mkdir(parents=True, exist_ok=True)
    checks, annual, nameframes = [], [], []
    secondary = {"grupo_edad": [], "SEXO": [], "TIPOSEC": []}
    # Fingerprint all protected baseline files, including consumers that must remain intact.
    inputs = sorted(p for folder in ["datos/processed", "ml", "src", "tests", "docs", "analisis/reportes"]
                    for p in (root / folder).rglob("*") if p.is_file() and out not in p.parents
                    and "__pycache__" not in p.parts)
    inputs += [root / p for p in ["requirements.txt", "requirements-app.txt", "README.md"] if (root / p).exists()]
    before = {p.relative_to(root).as_posix(): fingerprint(p) for p in inputs}
    metadata = dict(fecha=datetime.now(ZoneInfo("America/Tijuana")).isoformat(), zona="America/Tijuana",
                    commit_base=git(root, "rev-parse", "HEAD"), rama=git(root, "branch", "--show-current"),
                    git_status_inicio=git(root, "status", "--porcelain=v1"), python=sys.version,
                    versiones={p: importlib.metadata.version(p) for p in ["pandas", "numpy", "scikit-learn", "joblib", "pytest", "httpx"]
                               if importlib.util.find_spec(p.replace("scikit-learn", "sklearn")) is not None},
                    parametros=dict(anios=YEARS, minimo_observados=100, maximo_ns_pct=20,
                                    atol_pp=ATOL, rtol=0, conteos_tolerancia=0),
                    origen_RAW="Extracción confiable confirmada por Hiram; RAW no leídos ni verificados en B2",
                    sha256_entradas_y_codigo=before)
    for year in YEARS:
        base = f"datos/processed/{year}/"
        start = len(checks)
        frame = read_csv(root, base + "municipio_edad.csv", checks, [*KEY, "anio", *COUNTS])
        if frame is None:
            continue
        frame = validate_aggregate(frame, checks, base + "municipio_edad.csv", year)
        age_sizes = frame.groupby(MUNICIPALITY).grupo_edad.nunique()
        record(checks, "cinco_edades_por_municipio", base, 5, sorted(age_sizes.unique()),
               int(age_sizes.ne(5).sum()), age_sizes[age_sizes.ne(5)].head(5).reset_index().to_dict("records"))
        main_valid = not any(c["estado"] in ["falla", "no comprobado"] for c in checks[start:])
        if main_valid:
            annual.append(frame)
            secondary["grupo_edad"].append(frame)
        names = read_csv(root, base + "municipios_nombres.csv", checks, MUNICIPALITY + ["EDONOM", "MPIONOM", "nombre_norm"])
        if names is not None:
            missing_name = names[["EDONOM", "MPIONOM", "nombre_norm"]].isna().any(axis=1)
            record(checks, "nombres_no_nulos", base, 0, int(missing_name.sum()), missing_name.sum(), examples(names, missing_name))
            if not missing_name.any():
                derived = names.MPIONOM.map(normalize_nominal)
                bad = derived.ne(names.nombre_norm) | derived.eq("")
                record(checks, "normalizacion_independiente", base, "NFKD, sin acentos ni caracteres fuera A-Z0-9",
                       int(bad.sum()), bad.sum(), examples(names, bad))
                names = names.assign(nombre_norm=derived, anio=year)
                unique(names, MUNICIPALITY + ["MPIONOM", "nombre_norm"], checks, base + "municipios_nombres.csv")
                expected_keys = frame.groupby(MUNICIPALITY).size().reset_index()[MUNICIPALITY]
                actual_keys = names.groupby(MUNICIPALITY).size().reset_index()[MUNICIPALITY]
                compare_frames(expected_keys, actual_keys, MUNICIPALITY, [], checks, base + "nombres_vs_agregados")
                nameframes.append(names)
        audit_json = read_json(root, base + "auditoria.json", checks)
        if audit_json is not None and main_valid:
            computed = national([frame])
            saved = pd.DataFrame([dict(anio=audit_json.get("anio"), **audit_json.get("conteos", {}),
                                       municipios=audit_json.get("municipios"), filas_agregadas=audit_json.get("municipio_edad"))])
            compare_frames(computed, saved, ["anio"], COUNTS + ["municipios", "filas_agregadas"], checks, base + "auditoria.json")
            frame.attrs["raw_documented"] = audit_json.get("filas")
            incidences = audit_json.get("incidencias", {})
            record(checks, "exclusion_etaria_heredada", base + "auditoria.json", "No deducir microfilas desde agregados",
                   {k: incidences.get(k) for k in ["age_lt18_rows", "age_unclassified_rows"]},
                   status="no comprobado", impact="No bloquea: metadatos heredados; totales CSV/JSON se contrastan por separado")
            # Verify internal consistency of documented state records, without calling it a RAW audit.
            states = pd.DataFrame(audit_json.get("estados", []))
            if set(COUNTS + ["rows"]).issubset(states):
                for field in COUNTS + ["rows"]:
                    documented = audit_json["conteos"].get(field) if field in COUNTS else audit_json.get("filas")
                    value = pd.to_numeric(states[field], errors="coerce")
                    bad = value.isna().any() or value.sum() != documented
                    record(checks, f"metadato_estatal_{field}", base + "auditoria.json", documented, value.sum(), int(bad))
        for variable, filename, categories in [("SEXO", "municipio_edad_sexo.csv", ["0", "1", "2"] if year == 2024 else ["0", "1"]),
                                               ("TIPOSEC", "municipio_edad_tipo_seccion.csv", ["U", "M", "R"])]:
            secondary_start = len(checks)
            small = read_csv(root, base + filename, checks, KEY + ["anio", variable] + COUNTS)
            if small is None:
                continue
            small = validate_aggregate(small, checks, base + filename, year, [variable])
            bad = ~small[variable].isin(categories)
            record(checks, f"categorias_{variable}", base + filename, categories, sorted(small[variable].dropna().unique()),
                   bad.sum(), examples(small, bad))
            if main_valid and not any(c["estado"] in ["falla", "no comprobado"] for c in checks[secondary_start:]):
                collapsed = small.groupby(["anio"] + KEY, as_index=False)[COUNTS].sum()
                compare_frames(frame, collapsed, ["anio"] + KEY, COUNTS, checks, base + filename + ":marginal_principal", atol=0)
                secondary[variable].append(small)
                if audit_json is not None:
                    key = "LN_por_sexo" if variable == "SEXO" else "LN_por_tipo_seccion"
                    inherited = audit_json.get(key, {})
                    actual_ln = small.groupby(variable).LN.sum().to_dict()
                    record(checks, key, base + "auditoria.json", inherited, actual_ln, int(inherited != actual_ln))
    stats = {}
    if annual:
        totals = national(annual)
        totals["filas_RAW_documentadas_no_verificadas"] = [f.attrs.get("raw_documented") for f in annual]
        save_csv(totals, out, "totales_anuales.csv")
        reconcile(root, totals, secondary, checks)
    if len(annual) == len(YEARS) and len(nameframes) == len(YEARS):
        try:
            names = pd.concat(nameframes, ignore_index=True)
            series, wide, identity = reconstruct(annual, names)
            save_csv(series, out, "serie_control.csv")
            save_csv(wide, out, "panel_control.csv")
            stats = reconcile_panel(root, wide, series, identity, names, totals, checks, out)
        except (ValueError, KeyError, TypeError) as exc:
            record(checks, "reconstruccion_panel", "seis agregados/nombres", "Join inequívoco y esquema válido", str(exc), 1)
    else:
        record(checks, "reconstruccion_panel", "seis agregados/nombres", "6 años válidos con nombres",
               {"agregados_validos": len(annual), "nombres_disponibles": len(nameframes)}, 1, status="no comprobado")
    after = {name: fingerprint(root / name) if (root / name).exists() else None for name in before}
    changed = [name for name in before if before[name] != after[name]]
    record(checks, "insumos_y_consumidores_intactos", "SHA-256 antes/después", "Sin cambios durante auditoría", changed, len(changed), changed[:5])
    record(checks, "origen_RAW", "seis elecciones", "Premisa aportada por Hiram", "No se abrieron ni recuperaron RAW",
           status="no comprobado", impact="No bloquea CAMINO B; no certifica origen oficial ni extracción")
    record(checks, "limites_territoriales_y_seleccion", "panel", "Interpretación descriptiva agregada",
           "Identidad nominal no prueba geometría; grupos etarios son cortes transversales; cobertura desigual no implica ausencia de sesgo",
           status="advertencia", impact="No bloquea B3 exploratorio; limita representatividad e interpretación")
    blockers = [c for c in checks if c["estado"] == "falla" or
                (c["estado"] == "no comprobado" and not c["efecto_B3"].startswith("No bloquea"))]
    decision = "BLOQUEADO" if blockers else "APTO CON ADVERTENCIAS"
    metadata["git_status_fin"] = git(root, "status", "--porcelain=v1")
    metadata["codigo_sin_commit"] = bool(metadata["git_status_inicio"] or metadata["git_status_fin"])
    result = clean_json(dict(decision=decision, resumen=stats, bloqueos=len(blockers),
                             estados=pd.Series([c["estado"] for c in checks]).value_counts().to_dict(),
                             trazabilidad=metadata, controles=checks))
    (out / "resultados.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    flat = pd.DataFrame(checks)
    for field in ["esperado", "observado", "ejemplos"]:
        flat[field] = flat[field].map(lambda x: json.dumps(x, ensure_ascii=False, allow_nan=False))
    save_csv(flat, out, "controles.csv")
    summary = [f"# B2 — {decision}", "", f"Ejecución: {metadata['fecha']} ({metadata['zona']}).",
               f"Base: `{metadata['commit_base']}`, rama `{metadata['rama']}`; código sin commit: {metadata['codigo_sin_commit']}.",
               "", "Auditoría independiente de todos los CSV procesados. No ejecuta pipeline, reporting ni modelado; no importa sus transformaciones.",
               "Conteos y claves exactos; decimales de precisión completa con atol=1e-10 pp y rtol=0. Booleanos: solo True/False.",
               "", "## Resultados", "", "```json", json.dumps(clean_json(stats), ensure_ascii=False, indent=2, allow_nan=False), "```", "",
               f"Controles: {result['estados']}; bloqueos: {len(blockers)}.", "", "## Hallazgos y límites", ""]
    for c in checks:
        if c["estado"] != "pasa":
            summary.append(f"- **{c['estado']}** `{c['control']}` — {c['archivo_universo']}: {c['observado']}. {c['efecto_B3']}.")
    summary += ["", "## Lectura de tablas", "",
                "- `totales_anuales.csv`: filas agregadas verificadas separadas de microfilas RAW documentadas, sin verificarlas.",
                "- `serie_control.csv`, `panel_control.csv`: reconstrucciones por claves, sin reemplazar originales.",
                "- `controles.csv`, `resultados.json`: esperado/observado, discrepancias, ejemplos, efecto y SHA-256.",
                "- `elegibilidad_y_causas.csv`, `combinaciones_exclusion.csv`: causas superpuestas y excluidos únicos.",
                "- `tasas_ausentes.csv`: distingue unidad ausente de observados cero; no rellena con cero.",
                "- `cobertura.csv`: numeradores, denominadores y universos explícitos. Nacional significa el agregado procesado de cinco edades.",
                "- `seleccion_entidad.csv`, `seleccion_edad.csv`, `seleccion_entidad_edad.csv`: porcentajes con denominador dentro de cada grupo.",
                "- `seleccion_anual.csv`: medias simples separadas de tasas ponderadas por observados y NS ponderado por LN.",
                "- `identidad_nominal.csv`, `nombres_anuales_control.csv`: variantes, años y claves; no homologación geométrica.",
                "", "Los controles de datos no validan el modelo. B3 decide entrenamiento/k; B4 cierra perfiles. Agentes/API/PDF siguen bajo responsabilidad de Rubén.",
                "La extracción confiable es una premisa del equipo. Las huellas identifican esta ejecución, no prueban origen oficial."]
    (out / "RESUMEN.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    print(f"B2: {decision} | {result['estados']} | bloqueos={len(blockers)}")
    print(json.dumps(clean_json(stats), ensure_ascii=False, allow_nan=False))
    print(f"Evidencia: {out}")
    return 1 if blockers else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--out", type=Path, default=Path("analisis/reportes/b2"))
    args = parser.parse_args()
    return audit(args.root, args.out if args.out.is_absolute() else args.root / args.out)


if __name__ == "__main__":
    sys.exit(main())
