"""Controlled B3 evaluation; never writes production data, models or contracts.

Compare: python -m src.evaluate_clustering --root .
Export a reviewed decision: python -m src.evaluate_clustering --root . --select
Verify in a fresh process: python -m src.evaluate_clustering --root . --verify
"""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import importlib.metadata
from itertools import combinations
import json
from pathlib import Path
import platform
import subprocess
import sys
from time import perf_counter
import warnings
from zoneinfo import ZoneInfo

import joblib
import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment
from sklearn.cluster import KMeans
from sklearn.exceptions import InconsistentVersionWarning
from sklearn.metrics import (adjusted_rand_score, calinski_harabasz_score,
                             davies_bouldin_score, pairwise_distances, silhouette_samples)
from sklearn.preprocessing import RobustScaler, StandardScaler
from threadpoolctl import threadpool_info, threadpool_limits

from .modeling import FEATS
from .validate_processed import ATOL, KEY, YEARS, clean_json, fingerprint, git, parse_bool

REL_OUT = Path("ml/resultados/b3")
ACTIVE = Path("ml/modelos/kmeans5_exploratorio.joblib")
VERSIONS = ["numpy", "pandas", "scipy", "scikit-learn", "joblib", "threadpoolctl"]


def write_json(path, value):
    path.write_text(json.dumps(clean_json(value), ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def save(frame, out, filename):
    frame.to_csv(out / filename, index=False, lineterminator="\n")


def safe_output(root, out):
    root, out = root.resolve(), out.resolve()
    allowed = root / REL_OUT
    if out != allowed and allowed not in out.parents:
        raise ValueError("La salida debe quedar dentro de ml/resultados/b3; producción está protegida")
    out.mkdir(parents=True, exist_ok=True)
    return out


def environment(root):
    actual = {p: importlib.metadata.version(p) for p in VERSIONS}
    for line in (root / "requirements-b3.txt").read_text(encoding="utf-8").splitlines():
        if "==" in line and not line.startswith("#"):
            package, expected = line.strip().split("==")
            if importlib.metadata.version(package) != expected:
                raise ValueError(f"Entorno B3 incompatible: {package} debe ser {expected}")
    return dict(python=platform.python_version(), plataforma=platform.platform(), paquetes=actual,
                ejecutable=sys.executable, librerias_nativas=threadpool_info())


def verified_b2(root):
    path = root / "analisis/reportes/b2/resultados.json"
    report = json.loads(path.read_text(encoding="utf-8"))
    if report["bloqueos"] or report["decision"] not in ["APTO PARA B3", "APTO CON ADVERTENCIAS"]:
        raise ValueError("B2 no habilita B3")
    hashes = report["trazabilidad"]["sha256_entradas_y_codigo"]
    changed = [p for p, sha in hashes.items() if not (root / p).is_file() or fingerprint(root / p) != sha]
    if changed:
        raise ValueError(f"Entradas B2 cambiaron; requiere control pertinente: {changed}")
    return dict(resultado_sha256=fingerprint(path), huellas_comprobadas=len(hashes), resumen=report["resumen"])


def load_data(root):
    data = pd.read_csv(root / "datos/processed/matriz_modelo_6_anios.csv",
                       dtype={c: "string" for c in KEY + ["apto_modelo", "completo_6", "identidad_estable_conservadora"]})
    required = KEY + FEATS + ["apto_modelo", "completo_6", "identidad_estable_conservadora", "LN_2024"]
    required += [f"{field}_{year}" for field in ["tasa", "ns_pct", "observados"] for year in YEARS]
    if not set(required).issubset(data):
        raise ValueError(f"Faltan columnas: {sorted(set(required) - set(data))}")
    for field in ["apto_modelo", "completo_6", "identidad_estable_conservadora"]:
        data[field] = parse_bool(data[field])
    for field, width in [("EDOCVE", 2), ("MPIOCVE", 3)]:
        if not data[field].str.fullmatch(r"[0-9]+", na=False).all():
            raise ValueError(f"Clave inválida: {field}")
        data[field] = data[field].str.zfill(width)
    if data[KEY].isna().any().any() or data.duplicated(KEY).any():
        raise ValueError("Clave de unidad nula o duplicada")
    good = data.loc[data.apto_modelo].sort_values(KEY).reset_index(drop=True)
    if good.empty:
        raise ValueError("No hay unidades elegibles")
    numbers = [c for c in required if c not in KEY + ["apto_modelo", "completo_6", "identidad_estable_conservadora"]]
    good[numbers] = good[numbers].apply(pd.to_numeric, errors="raise")
    if not np.isfinite(good[numbers].to_numpy(float)).all():
        raise ValueError("Features/calidad no finitos: no se imputan ceros")
    if not (good.completo_6 & good.identidad_estable_conservadora).all():
        raise ValueError("Elegibilidad incompatible con flags de B2")
    if not good[[f"observados_{y}" for y in YEARS]].ge(100).all().all():
        raise ValueError("Elegible con menos de 100 observados")
    if not good[[f"ns_pct_{y}" for y in YEARS]].apply(lambda s: s.between(0, 20)).all().all():
        raise ValueError("NS fuera de contrato B2")
    if not good[[f"tasa_{y}" for y in YEARS]].apply(lambda s: s.between(0, 100)).all().all():
        raise ValueError("Tasa fuera de 0-100")
    formula = np.column_stack([
        (good.tasa_2012 + good.tasa_2018 + good.tasa_2024) / 3,
        (good.tasa_2009 + good.tasa_2015 + good.tasa_2021) / 3,
        good.tasa_2024 - good.tasa_2012, good.tasa_2021 - good.tasa_2009])
    x = good[FEATS].to_numpy(float)
    if not np.allclose(formula, x, atol=ATOL, rtol=0):
        raise ValueError("Las cuatro fórmulas no coinciden con las tasas")
    return good, x


def align(left, right, fields):
    if left[KEY].isna().any().any() or right[KEY].isna().any().any():
        raise ValueError("Clave nula al comparar")
    if left.duplicated(KEY).any() or right.duplicated(KEY).any():
        raise ValueError("Duplicados: comparación por clave ambigua")
    joined = left.merge(right[KEY + fields], on=KEY, how="outer", validate="one_to_one",
                        suffixes=("_left", "_right"), indicator=True)
    if not joined._merge.eq("both").all():
        raise ValueError("Universos de claves diferentes")
    return joined.drop(columns="_merge")


def label_comparison(left, right):
    table = pd.crosstab(pd.Series(np.asarray(left), name="origen"), pd.Series(np.asarray(right), name="destino"))
    row, col = linear_sum_assignment(-table.to_numpy())
    return dict(ARI=float(adjusted_rand_score(left, right)),
                fraccion_coincidente_emparejamiento_maximo=float(table.to_numpy()[row, col].sum() / len(left))), table


def mapping_for(model, scaler):
    centers = scaler.inverse_transform(model.cluster_centers_)
    ordered = sorted(range(len(centers)), key=lambda i: ((centers[i, 0] + centers[i, 1]) / 2, *centers[i], i))
    return {int(raw): int(rank + 1) for rank, raw in enumerate(ordered)}


def predict(bundle, data):
    if bundle["features"] != FEATS:
        raise ValueError("Orden de features incompatible")
    raw = bundle["model"].predict(bundle["scaler"].transform(data[FEATS].to_numpy(float)))
    labels = np.array([bundle["label_mapping"][int(label)] for label in raw], dtype=int)
    return data[KEY].assign(perfil_id=labels)


def load_bundle(path):
    # A mismatch is fatal, not suppressed because unpickling happened to work.
    with warnings.catch_warnings():
        warnings.simplefilter("error", InconsistentVersionWarning)
        return joblib.load(path)  # Only trusted project or locally generated artifacts.


def bundle_for(model, scaler):
    return dict(model=model, scaler=scaler, features=FEATS.copy(), k=model.n_clusters,
                label_mapping=mapping_for(model, scaler),
                filters=dict(min_observados_por_anio=100, max_ns_pct=20, **{"6_years": True}, nombre_municipal_estable=True),
                scope="Candidato B3; agregado municipio × edad, seis elecciones, sin adopción de producto")


def fit(x, k, seed, params, robust=False):
    scaler = (RobustScaler() if robust else StandardScaler()).fit(x)
    z = scaler.transform(x)
    model = KMeans(n_clusters=k, random_state=seed, **params)
    started = perf_counter()
    model.fit(z)
    elapsed = perf_counter() - started
    if len(np.unique(model.labels_)) != k or not np.isfinite(model.cluster_centers_).all():
        raise ValueError("Ajuste degenerado o centroides no finitos")
    return bundle_for(model, scaler), z, elapsed


def profile_tables(data, assignments, names=None):
    labelled = align(data, assignments, ["perfil_id"])
    rows, profiles = [], []
    for label, group in labelled.groupby("perfil_id", sort=True):
        means = group[FEATS].mean()
        name = (names or {}).get(str(int(label)), f"Presidencial {means.iloc[0]:.1f}%; intermedia {means.iloc[1]:.1f}%")
        ages = group.grupo_edad.value_counts()
        predominant = sorted(ages.index[ages.eq(ages.max())])[0]
        profiles.append(dict(perfil_id=int(label), nombre=name, n_unidades=len(group),
                             municipios=len(group.groupby(KEY[:2])), porcentaje_unidades=100 * len(group) / len(data),
                             lista_nominal_2024=int(group.LN_2024.sum()), edad_predominante=predominant,
                             **means.to_dict(), brecha_pres_intermedia=float((group.media_presidencial - group.media_intermedia).mean()),
                             notas=["Candidato B3 pendiente de B4", "Medias simples de unidades agregadas, no personas", "Geografía histórica no certificada"]))
        for field in FEATS + [f"tasa_{year}" for year in YEARS]:
            rows.append(dict(perfil_id=int(label), variable=field, n=len(group), media=float(group[field].mean()),
                             p25=float(group[field].quantile(.25)), mediana=float(group[field].median()),
                             p75=float(group[field].quantile(.75)), minimo=float(group[field].min()), maximo=float(group[field].max())))
    return profiles, pd.DataFrame(rows)


def samples_for(n, protocol):
    return {int(seed): np.random.RandomState(seed).permutation(n)[:min(protocol["n_muestra"], n)]
            for seed in protocol["semillas_muestra"]}


def metrics(z, raw_labels, mapping, indices, distances):
    sizes = np.bincount(raw_labels)
    row = dict(davies_bouldin=float(davies_bouldin_score(z, raw_labels)),
               calinski_harabasz=float(calinski_harabasz_score(z, raw_labels)),
               min_fraccion=float(sizes.min()/len(z)), max_fraccion=float(sizes.max()/len(z)))
    grouped = []
    for seed, idx in indices.items():
        values = silhouette_samples(distances[seed], raw_labels[idx], metric="precomputed")
        row[f"silhouette_{seed}"] = float(values.mean())
        for cluster in sorted(mapping):
            mask = raw_labels[idx] == cluster
            grouped.append(dict(muestra_semilla=seed, perfil_id=mapping[cluster], n_muestra=int(mask.sum()),
                                silhouette_media=float(values[mask].mean()) if mask.any() else None,
                                fraccion_negativa=float((values[mask] < 0).mean()) if mask.any() else None))
    return row, grouped


def check_protected(root, out):
    baseline = json.loads((out / "preparacion.json").read_text(encoding="utf-8"))
    changed = [p for p, sha in baseline["hashes_base_protegida"].items()
               if not (root / p).exists() or fingerprint(root / p) != sha]
    if changed:
        raise ValueError(f"Base de producción/B2 cambió: {changed}")
    return len(baseline["hashes_base_protegida"])


def compare(root, out):
    protocol_path = out / "protocolo.json"
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    baseline = json.loads((out / "preparacion.json").read_text(encoding="utf-8"))
    if fingerprint(protocol_path) != baseline["protocolo_sha256"]:
        raise ValueError("El protocolo cambió después de registrarse")
    if protocol["features"] != FEATS:
        raise ValueError("Features del protocolo distintas de producción")
    env, b2 = environment(root), verified_b2(root)
    good, x = load_data(root)
    if len(good) != b2["resumen"]["n_validas"]:
        raise ValueError("Conjunto diferente al aprobado en B2")
    reference = load_bundle(root / ACTIVE)
    old_predictions = predict(reference, good)
    old_saved = pd.read_csv(root / "ml/resultados/observaciones_segmentadas.csv", dtype={c: "string" for c in KEY})
    for col, width in [("EDOCVE", 2), ("MPIOCVE", 3)]:
        old_saved[col] = old_saved[col].str.zfill(width)
    joined = align(old_predictions, old_saved, ["perfil_id"])
    differences = int(joined.perfil_id_left.ne(joined.perfil_id_right).sum())
    if differences:
        raise ValueError(f"Referencia activa no reproduce {differences} asignaciones guardadas")
    output_models = out / "candidatos"
    output_models.mkdir(exist_ok=True)
    assignments = good[KEY].copy()
    assignments["activo_k5"] = old_predictions.perfil_id.to_numpy()
    index = samples_for(len(good), protocol["evaluacion"])
    sample_rows = [good.iloc[idx][KEY].assign(muestra_semilla=seed, posicion_muestra=np.arange(len(idx))) for seed, idx in index.items()]
    save(pd.concat(sample_rows), out, "muestras_evaluacion.csv")
    z_main = StandardScaler().fit_transform(x)
    distances = {seed: pairwise_distances(z_main[idx]) for seed, idx in index.items()}
    results, stability, group_silhouette, group_stats, group_sizes = [], [], [], [], []
    fitted = {}
    for k in protocol["k"]:
        for seed in protocol["semillas"]:
            bundle, z, elapsed = fit(x, k, seed, protocol["kmeans"])
            model = bundle["model"]
            row, diagnostics = metrics(z, model.labels_, bundle["label_mapping"], index, distances)
            results.append(dict(k=k, semilla=seed, n=len(good), n_init=model.n_init, segundos_ajuste=elapsed,
                                iteraciones=model.n_iter_, inertia=float(model.inertia_), **row))
            assignments[f"k{k}_s{seed}"] = predict(bundle, good).perfil_id.to_numpy()
            for label, group in good.assign(perfil_id=assignments[f"k{k}_s{seed}"]).groupby("perfil_id"):
                group_sizes.append(dict(k=k, semilla=seed, perfil_id=int(label), n=len(group),
                                        fraccion=len(group)/len(good), **group[FEATS].mean().to_dict()))
            group_silhouette.extend(dict(k=k, semilla=seed, **d) for d in diagnostics)
            if seed == protocol["semilla_referencia"]:
                fitted[k] = bundle
                joblib.dump(bundle, output_models / f"k{k}_seed42.joblib")
                restored = load_bundle(output_models / f"k{k}_seed42.joblib")
                if not predict(restored, good).perfil_id.equals(predict(bundle, good).perfil_id):
                    raise ValueError("La recarga cambió asignaciones del candidato")
                profiles, stats = profile_tables(good, predict(bundle, good))
                write_json(output_models / f"perfiles_k{k}.json", profiles)
                group_stats.append(stats.assign(k=k))
            print(f"principal k={k} seed={seed} silhouette64={row['silhouette_64']:.6f} DB={row['davies_bouldin']:.6f}", flush=True)
        for left, right in combinations(protocol["semillas"], 2):
            comparison, _ = label_comparison(assignments[f"k{k}_s{left}"], assignments[f"k{k}_s{right}"])
            stability.append(dict(k=k, semilla_a=left, semilla_b=right, **comparison))
    save(pd.DataFrame(results).sort_values(["k", "semilla"]), out, "comparacion.csv")
    stability = pd.DataFrame(stability).sort_values(["k", "semilla_a", "semilla_b"])
    save(stability, out, "estabilidad_pares.csv")
    save(stability.groupby("k").ARI.agg(["mean", "median", "min", "max"]).reset_index(), out, "estabilidad_resumen.csv")
    save(pd.DataFrame(group_silhouette).sort_values(["k", "semilla", "muestra_semilla", "perfil_id"]), out, "silhouette_grupos.csv")
    save(pd.DataFrame(group_sizes).sort_values(["k", "semilla", "perfil_id"]), out, "tamanos_grupos.csv")
    save(pd.concat(group_stats).sort_values(["k", "perfil_id", "variable"]), out, "estadisticas_grupos.csv")
    sensitivity, overlaps, cross_metrics, sensitivity_stats, sensitivity_profiles = [], [], [], [], []
    ns_mask = good[[f"ns_pct_{year}" for year in YEARS]].le(10).all(axis=1)
    for scenario, data, values, robust in [("RobustScaler", good, x, True), ("NS10", good.loc[ns_mask].reset_index(drop=True), x[ns_mask], False)]:
        idx = samples_for(len(data), protocol["evaluacion"])
        transformed = (RobustScaler() if robust else StandardScaler()).fit_transform(values)
        dists = {seed: pairwise_distances(transformed[rows]) for seed, rows in idx.items()}
        if scenario == "NS10":
            save(pd.concat([data.iloc[rows][KEY].assign(muestra_semilla=seed, posicion_muestra=np.arange(len(rows))) for seed, rows in idx.items()]), out, "muestras_NS10.csv")
        for k in protocol["k"]:
            bundle, z, elapsed = fit(values, k, 42, protocol["kmeans"], robust=robust)
            predicted = predict(bundle, data)
            scenario_profiles, scenario_stats = profile_tables(data, predicted)
            sensitivity_stats.append(scenario_stats.assign(escenario=scenario, k=k))
            sensitivity_profiles.extend(dict(escenario=scenario, k=k, **{key: value for key, value in profile.items() if key != "notas"}) for profile in scenario_profiles)
            principal = assignments[KEY + [f"k{k}_s42"]]
            common = predicted.merge(principal, on=KEY, validate="one_to_one")
            comparison, contingency = label_comparison(common[f"k{k}_s42"], common.perfil_id)
            row, _ = metrics(z, bundle["model"].labels_, bundle["label_mapping"], idx, dists)
            sensitivity.append(dict(escenario=scenario, k=k, semilla=42, n=len(data),
                                    municipios=len(data.groupby(KEY[:2])), LN_2024=int(data.LN_2024.sum()),
                                    cobertura_LN2024_nacional_pct=100 * data.LN_2024.sum()/b2["resumen"]["LN_2024_total_panel"],
                                    segundos_ajuste=elapsed, **comparison, **row))
            name = f"{scenario}_k{k}"
            merged = assignments.merge(predicted.rename(columns={"perfil_id": name}), on=KEY, how="left", validate="one_to_one")
            assignments[name] = merged[name].astype("Int64")
            overlaps.append(contingency.rename_axis(index="perfil_origen", columns="perfil_destino").stack().rename("unidades").reset_index().assign(comparacion=name))
            print(f"sensibilidad {scenario} k={k} n={len(data)} ARI={comparison['ARI']:.6f}", flush=True)
    for left, right in [("k4_s42", "k5_s42"), ("k5_s42", "k6_s42"), ("activo_k5", "k5_s42"), ("activo_k5", "k4_s42"), ("activo_k5", "k6_s42")]:
        comparison, contingency = label_comparison(assignments[left], assignments[right])
        name = f"{left}__{right}"
        cross_metrics.append(dict(comparacion=name, **comparison))
        overlaps.append(contingency.rename_axis(index="perfil_origen", columns="perfil_destino").stack().rename("unidades").reset_index().assign(comparacion=name))
    save(pd.DataFrame(sensitivity).sort_values(["escenario", "k"]), out, "sensibilidad.csv")
    save(pd.concat(sensitivity_stats).sort_values(["escenario", "k", "perfil_id", "variable"]), out, "sensibilidad_distribuciones.csv")
    save(pd.DataFrame(sensitivity_profiles).sort_values(["escenario", "k", "perfil_id"]), out, "sensibilidad_perfiles.csv")
    save(pd.concat(overlaps).sort_values(["comparacion", "perfil_origen", "perfil_destino"]), out, "cruces.csv")
    save(pd.DataFrame(cross_metrics), out, "comparacion_particiones.csv")
    save(assignments.sort_values(KEY), out, "asignaciones_experimentos.csv")
    same_recipe, _ = label_comparison(assignments.activo_k5, assignments.k5_s42)
    old_centers = reference["model"].cluster_centers_
    new_centers = fitted[5]["model"].cluster_centers_
    center_cost = pairwise_distances(old_centers, new_centers)
    center_rows, center_cols = linear_sum_assignment(center_cost)
    write_json(out / "referencia.json", dict(artefacto_activo_sha256=fingerprint(root / ACTIVE),
               sklearn_serializado_documentado="1.8.0 (diagnóstico B2)", entorno_carga=env,
               carga_sin_advertencia_de_version=True, predicciones_verificadas_por_clave=len(good),
               diferencias_vs_guardado=differences, receta_reproducida_n_init30=same_recipe,
               parametros_activos=reference["model"].get_params(),
               orden_features=reference["features"],
               centroides_activos=reference["scaler"].inverse_transform(reference["model"].cluster_centers_).tolist(),
               max_delta_centroides_escalados_emparejados=float(np.abs(old_centers[center_rows] - new_centers[center_cols]).max()),
               max_delta_media_escalador=float(np.abs(reference["scaler"].mean_ - fitted[5]["scaler"].mean_).max()),
               max_delta_escala_escalador=float(np.abs(reference["scaler"].scale_ - fitted[5]["scaler"].scale_).max())))
    code_paths = ["src/evaluate_clustering.py", "src/modeling.py", "src/pipeline.py", "src/validate_processed.py",
                  "tests/test_evaluate_clustering.py", "requirements-b3.txt"]
    metadata = dict(fecha=datetime.now(ZoneInfo("America/Tijuana")).isoformat(), zona="America/Tijuana",
                    commit_base=git(root, "rev-parse", "HEAD"), rama=git(root, "branch", "--show-current"),
                    git_status=git(root, "status", "--porcelain=v1"), entorno=env, B2=b2,
                    parametros=protocol, protocolo_sha256=fingerprint(protocol_path),
                    datos_entrenamiento_sha256=fingerprint(root / "datos/processed/matriz_modelo_6_anios.csv"),
                    features_ordenadas_sha256=hashlib.sha256(np.ascontiguousarray(x, dtype="<f8").tobytes()).hexdigest(),
                    claves_ordenadas_sha256=hashlib.sha256(good[KEY].to_csv(index=False, lineterminator="\n").encode("utf-8")).hexdigest(),
                    codigo_sha256={p: fingerprint(root / p) for p in code_paths},
                    candidatos_sha256={f"k{k}_seed42.joblib": fingerprint(output_models / f"k{k}_seed42.joblib") for k in protocol["k"]},
                    archivos_base_sin_cambios=check_protected(root, out), ponderacion="Unidades, sin pesos poblacionales",
                    etapa="Comparación ejecutada; selección aún pendiente")
    write_json(out / "ejecucion.json", metadata)
    (out / "environment.lock.txt").write_text(subprocess.check_output([sys.executable, "-m", "pip", "freeze"], text=True), encoding="utf-8")
    print("Comparación completa. Revisar tablas y registrar seleccion.json antes de --select.", flush=True)


def verify_candidate(root, out):
    environment(root)
    verified_b2(root)
    good, _ = load_data(root)
    bundle = load_bundle(out / "candidato_recomendado.joblib")
    predicted = predict(bundle, good)
    saved = pd.read_csv(out / "asignaciones_candidato.csv", dtype={c: "string" for c in KEY})
    joined = align(predicted, saved, ["perfil_id"])
    if not joined.perfil_id_left.eq(joined.perfil_id_right).all():
        raise ValueError("Asignaciones recargadas distintas del CSV candidato")
    recorded = json.loads((out / "perfiles_candidato.json").read_text(encoding="utf-8"))
    names = {str(p["perfil_id"]): p["nombre"] for p in recorded}
    recomputed, _ = profile_tables(good, predicted, names)
    for expected, actual in zip(recomputed, recorded, strict=True):
        if expected.keys() != actual.keys():
            raise ValueError("Esquema de perfiles inconsistente")
        for field, value in expected.items():
            same = np.isclose(value, actual[field], atol=ATOL, rtol=0) if isinstance(value, float) else value == actual[field]
            if not same:
                raise ValueError(f"Resumen de perfil inconsistente: {field}")
    if len(recorded) != bundle["k"] or sum(p["n_unidades"] for p in recorded) != len(good):
        raise ValueError("Tamaños de perfiles inconsistentes")
    if sum(p["lista_nominal_2024"] for p in recorded) != int(good.LN_2024.sum()):
        raise ValueError("Suma LN de perfiles inconsistente")
    result = dict(estado="APTO PARA B4 CON ADVERTENCIAS", claves_verificadas=len(good),
                  coincidencia_asignaciones_por_clave=True, perfiles_recalculados_coherentes=True,
                  k=bundle["k"], candidato_sha256=fingerprint(out / "candidato_recomendado.joblib"),
                  archivos_base_sin_cambios=check_protected(root, out),
                  fecha=datetime.now(ZoneInfo("America/Tijuana")).isoformat())
    write_json(out / "verificacion_candidato.json", result)
    print(json.dumps(result, ensure_ascii=False), flush=True)


def select(root, out):
    environment(root)
    verified_b2(root)
    good, _ = load_data(root)
    decision = json.loads((out / "seleccion.json").read_text(encoding="utf-8"))
    k = decision["k_recomendado"]
    if k not in [4, 5, 6] or not decision["razones"] or set(decision["nombres"]) != {str(i) for i in range(1, k+1)}:
        raise ValueError("Decisión incompleta o k fuera del protocolo")
    experiment = json.loads((out / "ejecucion.json").read_text(encoding="utf-8"))
    candidate_path = out / "candidatos" / f"k{k}_seed42.joblib"
    if fingerprint(candidate_path) != experiment["candidatos_sha256"][candidate_path.name]:
        raise ValueError("El candidato cambió después de la comparación")
    bundle = load_bundle(candidate_path)
    bundle["metadata"] = dict(decision=decision, ejecucion=experiment)
    joblib.dump(bundle, out / "candidato_recomendado.joblib")
    assignments = predict(bundle, good)
    save(assignments.sort_values(KEY), out, "asignaciones_candidato.csv")
    profiles, stats = profile_tables(good, assignments, decision["nombres"])
    write_json(out / "perfiles_candidato.json", profiles)
    save(stats.sort_values(["perfil_id", "variable"]), out, "estadisticas_candidato.csv")
    labelled = align(good, assignments, ["perfil_id"])
    experiments = pd.read_csv(out / "asignaciones_experimentos.csv", dtype={c: "string" for c in KEY})
    joined = align(assignments, experiments, ["activo_k5"])
    comparison, table = label_comparison(joined.activo_k5, joined.perfil_id)
    cross = table.rename_axis(index="perfil_activo", columns="perfil_candidato").stack().rename("unidades").reset_index()
    cross["pct_dentro_activo"] = 100 * cross.unidades / cross.groupby("perfil_activo").unidades.transform("sum")
    cross["pct_dentro_candidato"] = 100 * cross.unidades / cross.groupby("perfil_candidato").unidades.transform("sum")
    active_names = {p["perfil_id"]: p["nombre"] for p in json.loads((root / "datos/processed/producto/perfiles.json").read_text(encoding="utf-8"))}
    cross["nombre_activo"] = cross.perfil_activo.map(active_names)
    cross["nombre_candidato"] = cross.perfil_candidato.astype(str).map(decision["nombres"])
    save(cross.sort_values(["perfil_activo", "perfil_candidato"]), out, "correspondencia_activo_candidato.csv")
    write_json(out / "impacto_particion.json", dict(k_activo=5, k_candidato=k, n=len(good), **comparison,
                                                  equivalencia_de_IDs=False, adopcion_producto=False))
    for field in ["EDOCVE", "grupo_edad"]:
        table = labelled.groupby([field, "perfil_id"], as_index=False).size().rename(columns={"size": "unidades"})
        table["porcentaje_dentro_grupo"] = 100 * table.unidades / table.groupby(field).unidades.transform("sum")
        save(table.sort_values([field, "perfil_id"]), out, f"candidato_por_{field}.csv")
    verify_candidate(root, out)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--out", type=Path, default=REL_OUT)
    stage = parser.add_mutually_exclusive_group()
    stage.add_argument("--select", action="store_true")
    stage.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    out = safe_output(root, args.out if args.out.is_absolute() else root / args.out)
    with threadpool_limits(limits=1):
        (verify_candidate if args.verify else select if args.select else compare)(root, out)


if __name__ == "__main__":
    main()
