"""B3 boundary checks and artifact roundtrip on small synthetic aggregates."""
import json
from pathlib import Path
from types import SimpleNamespace

import joblib
import numpy as np
import pandas as pd
import pytest
from threadpoolctl import threadpool_limits

from src import evaluate_clustering as b3


def synthetic(root):
    rng = np.random.RandomState(19)
    rates = rng.uniform(25, 85, (40, 6))
    frame = pd.DataFrame(dict(EDOCVE=["01"]*40, MPIOCVE=[f"{i:03}" for i in range(1, 41)],
                              grupo_edad=["18-24"]*40, apto_modelo=["True"]*39+["False"],
                              completo_6=["True"]*40, identidad_estable_conservadora=["True"]*40,
                              LN_2024=[1000]*40))
    for i, year in enumerate(b3.YEARS):
        frame[f"tasa_{year}"] = rates[:, i]
        frame[f"observados_{year}"] = 200
        frame[f"ns_pct_{year}"] = 5
    frame["media_presidencial"] = rates[:, [1, 3, 5]].mean(axis=1)
    frame["media_intermedia"] = rates[:, [0, 2, 4]].mean(axis=1)
    frame["cambio_presidencial_pp"] = rates[:, 5] - rates[:, 1]
    frame["cambio_intermedia_pp"] = rates[:, 4] - rates[:, 0]
    path = root / "datos/processed/matriz_modelo_6_anios.csv"
    path.parent.mkdir(parents=True)
    frame.to_csv(path, index=False)
    return path, frame


def test_features_flags_and_invalid_values(tmp_path):
    path, original = synthetic(tmp_path)
    # File column order is deliberately unrelated to the feature contract.
    original[list(reversed(original.columns))].to_csv(path, index=False)
    good, x = b3.load_data(tmp_path)
    assert len(good) == 39 and good.MPIOCVE.iloc[0] == "001"
    np.testing.assert_allclose(x, original.iloc[:39][b3.FEATS].to_numpy(float))
    for field, value in [("apto_modelo", "unknown"), ("apto_modelo", None),
                         ("media_presidencial", np.nan), ("media_intermedia", np.inf),
                         ("cambio_presidencial_pp", 999), ("ns_pct_2024", 21)]:
        broken = original.copy()
        broken.loc[0, field] = value
        broken.to_csv(path, index=False)
        with pytest.raises(ValueError):
            b3.load_data(tmp_path)
    duplicate = pd.concat([original, original.iloc[:1]])
    duplicate.to_csv(path, index=False)
    with pytest.raises(ValueError, match="duplicada"):
        b3.load_data(tmp_path)


def test_key_alignment_label_permutations_and_deterministic_ties():
    left = pd.DataFrame({"EDOCVE": ["01", "01"], "MPIOCVE": ["001", "002"], "grupo_edad": ["18-24"]*2,
                         "label": [1, 2]})
    joined = b3.align(left, left.iloc[::-1], ["label"])
    assert joined.label_left.equals(joined.label_right)
    with pytest.raises(ValueError, match="Universos"):
        b3.align(left, left.iloc[:1], ["label"])
    with pytest.raises(ValueError, match="Duplicados"):
        b3.align(left, pd.concat([left, left.iloc[:1]]), ["label"])
    scores, _ = b3.label_comparison([1, 1, 2, 2], [9, 9, 3, 3])
    assert scores["ARI"] == scores["fraccion_coincidente_emparejamiento_maximo"] == 1
    centers = np.array([[60, 40, 5, 9], [50, 50, 2, 8], [50, 50, 2, 8]])
    scaler = SimpleNamespace(inverse_transform=lambda x: x)
    mapping = b3.mapping_for(SimpleNamespace(cluster_centers_=centers), scaler)
    assert mapping == {1: 1, 2: 2, 0: 3}


def test_candidate_roundtrip_profiles_and_corruption(tmp_path, monkeypatch):
    synthetic(tmp_path)
    good, x = b3.load_data(tmp_path)
    out = b3.safe_output(tmp_path, tmp_path / b3.REL_OUT)
    with threadpool_limits(limits=1):
        bundle, _, _ = b3.fit(x, 4, 42, dict(n_init=3, init="k-means++", max_iter=300, tol=1e-4, algorithm="lloyd"))
        joblib.dump(bundle, out / "candidato_recomendado.joblib")
        prediction = b3.predict(b3.load_bundle(out / "candidato_recomendado.joblib"), good)
        profiles, _ = b3.profile_tables(good, prediction)
        assert sum(p["n_unidades"] for p in profiles) == len(good)
        assert sum(p["lista_nominal_2024"] for p in profiles) == good.LN_2024.sum()
        prediction.iloc[::-1].to_csv(out / "asignaciones_candidato.csv", index=False)
        b3.write_json(out / "perfiles_candidato.json", profiles)
        # This unit test isolates candidate validation from the separate real B2/hash gate.
        monkeypatch.setattr(b3, "environment", lambda root: {})
        monkeypatch.setattr(b3, "verified_b2", lambda root: {})
        monkeypatch.setattr(b3, "check_protected", lambda root, out: 0)
        b3.verify_candidate(tmp_path, out)
        profiles[0]["n_unidades"] += 1
        b3.write_json(out / "perfiles_candidato.json", profiles)
        with pytest.raises(ValueError, match="Resumen"):
            b3.verify_candidate(tmp_path, out)
        bundle["features"] = list(reversed(b3.FEATS))
        with pytest.raises(ValueError, match="Orden"):
            b3.predict(bundle, good)


def test_output_protection_and_environment_mismatch(tmp_path):
    for destination in ["ml/modelos", "ml/resultados", "datos/processed", "src", "."]:
        with pytest.raises(ValueError, match="protegida"):
            b3.safe_output(tmp_path, tmp_path / destination)
    assert b3.safe_output(tmp_path, tmp_path / b3.REL_OUT).is_dir()
    (tmp_path / "requirements-b3.txt").write_text("scikit-learn==0.0\n", encoding="utf-8")
    with pytest.raises(ValueError, match="incompatible"):
        b3.environment(tmp_path)
