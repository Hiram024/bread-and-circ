"""QA B4: independent B3 oracles, real inference and isolated approval history."""
import copy
import hashlib
import io
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tarfile

from fastapi.testclient import TestClient
import joblib
import numpy as np
import pandas as pd
import pytest
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from src import dashboard_api as api
from src import product_contract
from src.education import build_draft, verification_agent

ROOT = Path(__file__).resolve().parents[1]
VERSION = "ccpc-2009-2024-k4-v1"
KEY = ["EDOCVE", "MPIOCVE", "grupo_edad"]
FEATURES = ["media_presidencial", "media_intermedia", "cambio_presidencial_pp", "cambio_intermedia_pp"]
YEARS = [2009, 2012, 2015, 2018, 2021, 2024]
SIZES = {1: 1840, 2: 2155, 3: 2511, 4: 2035}


def canonical_keys(frame):
    result = frame.copy()
    for field, width in [("EDOCVE", 2), ("MPIOCVE", 3)]:
        result[field] = pd.to_numeric(result[field], errors="raise").astype(int).astype(str).str.zfill(width)
    return result


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(api, "DB_PATH", tmp_path / "reviews.sqlite3")
    api.package.cache_clear()
    with TestClient(api.app) as value:
        yield value
    api.package.cache_clear()


def approval(shown, **changes):
    payload = dict(profile_id=shown["perfil_id"], reviewer="Revisor QA independiente", confirmed=True,
                   package_version=shown["package_version"], package_digest=shown["package_digest"],
                   draft_digest=shown["draft_digest"])
    return {**payload, **changes}


def valid_input():
    row = {"unidad_id": "QA_AGREGADO", "grupo_edad": "25-34"}
    for year, rate in zip(YEARS, [45, 61, 43, 62, 50, 59]):
        row.update({f"tasa_{year}": rate, f"observados_{year}": 500, f"ns_pct_{year}": 4})
    return pd.DataFrame([row])


def upload(client, frame, filename="qa.csv"):
    return client.post("/api/classify", files={"file": (filename, frame.to_csv(index=False), "text/csv")})


def test_package_data_predictions_and_b2_b3_inputs_are_consistent(client):
    baseline = json.loads((ROOT / "analisis/reportes/b4/qa_baseline.json").read_text(encoding="utf-8"))
    frozen = {p: sha for p, sha in baseline["hashes_base"].items()
              if p.startswith("datos/processed/") or p.startswith("ml/resultados/b3/")
              or p == "ml/modelos/kmeans5_exploratorio.joblib"}
    for filename, digest in frozen.items():
        assert hashlib.sha256((ROOT / filename).read_bytes()).hexdigest() == digest, filename
    served = canonical_keys(api.data())
    expected = canonical_keys(pd.read_csv(ROOT / "ml/resultados/b3/asignaciones_candidato.csv"))
    assert len(served) == 8541 and not served.duplicated(KEY).any()
    joined = served.merge(expected, on=KEY, how="outer", suffixes=("_served", "_b3"),
                          indicator=True, validate="one_to_one")
    assert joined._merge.eq("both").all()
    assert joined.perfil_id_served.eq(joined.perfil_id_b3).all()
    assert served.perfil_id.value_counts().sort_index().to_dict() == SIZES
    assert served.LN_2024.sum() == 81666826
    assert served[KEY[:2]].value_counts().shape[0] == 1825
    active = api.artifact()
    assert active["k"] == active["model"].n_clusters == 4
    assert active["features"] == FEATURES
    raw = active["model"].predict(active["scaler"].transform(served[FEATURES].to_numpy(float)))
    expected_prediction = np.array([active["label_mapping"][int(label)] for label in raw])
    np.testing.assert_array_equal(expected_prediction, served.perfil_id.to_numpy())
    b3_profiles = json.loads((ROOT / "ml/resultados/b3/perfiles_candidato.json").read_text(encoding="utf-8"))
    profiles = api.profiles()
    assert set(profiles) == {1, 2, 3, 4}
    for prior in b3_profiles:
        actual = profiles[prior["perfil_id"]]
        assert actual["nombre"] == prior["nombre"]
        assert actual["n_unidades"] == prior["n_unidades"]
        assert actual["package_version"] == VERSION
        for feature in FEATURES:
            assert actual[feature] == pytest.approx(prior[feature], abs=1e-10, rel=0)


def test_query_version_filters_and_nonexistent_profile(client):
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["observaciones"] == 8541 and health.json()["perfiles"] == 4
    assert health.json()["package_version"] == VERSION
    summary = client.get("/api/summary").json()
    assert summary["meta"]["package_version"] == VERSION
    assert len(summary["perfiles"]) == 4 and len(summary["historico"]) == 6
    sample = client.get("/api/observations", params={"perfil": 2, "edad": "25-34", "limit": 8}).json()
    assert sample["total"] > 0 and len(sample["items"]) == 8
    assert all(p["perfil_id"] == 2 and p["grupo_edad"] == "25-34" for p in sample["items"])
    assert sample["package_version"] == VERSION
    assert client.get("/api/draft/5").status_code == 404
    assert client.get("/api/observations", params={"perfil": 5}).status_code == 404


def test_csv_uses_real_candidate_without_training_and_rejects_invalid_input(client, monkeypatch):
    def no_fit(*args, **kwargs):
        raise AssertionError("CSV inference must not train")
    monkeypatch.setattr(KMeans, "fit", no_fit)
    monkeypatch.setattr(KMeans, "fit_predict", no_fit)
    monkeypatch.setattr(StandardScaler, "fit", no_fit)
    incoming = valid_input()
    response = upload(client, incoming)
    assert response.status_code == 200
    output = pd.read_csv(io.BytesIO(response.content))
    rates = incoming[[f"tasa_{y}" for y in YEARS]].to_numpy(float)
    independent_features = np.column_stack([rates[:, [1, 3, 5]].mean(axis=1), rates[:, [0, 2, 4]].mean(axis=1),
                                             rates[:, 5]-rates[:, 1], rates[:, 4]-rates[:, 0]])
    candidate = joblib.load(ROOT / "ml/resultados/b3/candidato_recomendado.joblib")
    raw = candidate["model"].predict(candidate["scaler"].transform(independent_features))
    assert output.perfil_id.tolist() == [candidate["label_mapping"][int(label)] for label in raw]
    assert output.package_version.eq(VERSION).all()
    assert output.perfil_nombre.iloc[0] == api.profiles()[int(output.perfil_id.iloc[0])]["nombre"]
    for field, value in [("tasa_2009", None), ("tasa_2012", np.inf), ("tasa_2015", -1),
                         ("tasa_2024", 101), ("observados_2018", 99), ("ns_pct_2021", -1), ("ns_pct_2024", 21)]:
        broken = incoming.copy()
        broken[field] = broken[field].astype(float)
        broken.loc[0, field] = value
        assert upload(client, broken).status_code == 422, (field, value)
    assert upload(client, incoming.drop(columns="tasa_2009")).status_code == 422
    assert upload(client, incoming, "qa.txt").status_code == 400
    assert upload(client, pd.concat([incoming]*5001, ignore_index=True)).status_code == 422
    boundary = upload(client, pd.concat([incoming]*5000, ignore_index=True))
    assert boundary.status_code == 200 and boundary.headers["X-Row-Count"] == "5000"
    oversized = client.post("/api/classify", files={"file": ("too-large.csv", b"a"*2000001, "text/csv")})
    assert oversized.status_code == 413


def test_draft_content_confirmation_and_pdf_are_bound(client, monkeypatch):
    shown = client.get("/api/draft/1").json()
    repeated = client.get("/api/draft/1").json()
    assert shown["package_version"] == VERSION and shown["draft_digest"] == repeated["draft_digest"]
    assert shown["validation"]["passed"] and shown["requires_human_approval"]
    assert not shown["automated_publication"]
    assert "1,840" in shown["draft"]["resumen"]
    assert api.profiles()[1]["nombre"] == shown["draft"]["subtitulo"]
    assert VERSION in json.dumps(shown, ensure_ascii=False)
    corrupted = copy.deepcopy(shown["draft"])
    corrupted["resumen"] = "Cifras deliberadamente incompatibles"
    assert not verification_agent(shown["facts"], corrupted)["passed"]
    for changed in [dict(confirmed=False), dict(profile_id=2), dict(package_version="other-version"),
                    dict(package_digest="0"*64), dict(draft_digest="0"*64)]:
        result = client.post("/api/approve", json=approval(shown, **changed))
        assert result.status_code == (400 if "confirmed" in changed else 409), changed
    assert client.post("/api/approve", json=approval(shown, reviewer="   ")).status_code in [400, 422]
    result = client.post("/api/approve", json=approval(shown))
    assert result.status_code == 200
    download_url = result.json()["download_url"]
    pdf = client.get(download_url)
    assert pdf.status_code == 200 and pdf.headers["content-type"] == "application/pdf"
    original = api.build_draft
    def changed_text(profile, *args, **kwargs):
        changed = {**profile, "nombre": profile["nombre"] + " — texto cambiado después de revisar"}
        return original(changed, *args, **kwargs)
    monkeypatch.setattr(api, "build_draft", changed_text)
    assert client.post("/api/approve", json=approval(shown)).status_code == 409
    assert client.get(download_url).status_code == 409


def test_legacy_database_is_preserved_and_migration_is_idempotent(client):
    path = api.DB_PATH
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE approvals (id INTEGER PRIMARY KEY AUTOINCREMENT, perfil_id INTEGER NOT NULL, reviewer TEXT NOT NULL, reviewed_at TEXT NOT NULL, digest TEXT NOT NULL)")
        db.execute("INSERT INTO approvals VALUES (17,1,'Revisor anterior','2026-10-20','digest-heredado')")
    expected = (17, 1, "Revisor anterior", "2026-10-20", "digest-heredado")
    first = client.get("/api/approved-pdf/17")
    assert first.status_code == 409 and any(word in first.text.lower() for word in ["heredad", "versión", "version", "verific"])
    with api.db_conn() as db:
        assert db.execute("SELECT id,perfil_id,reviewer,reviewed_at,digest FROM approvals WHERE id=17").fetchone() == expected
        columns = {row[1] for row in db.execute("PRAGMA table_info(approvals)")}
        assert {"package_version", "package_digest"}.issubset(columns)
        assert db.execute("SELECT package_version,package_digest FROM approvals WHERE id=17").fetchone() == (None, None)
    backups = [p for p in path.parent.iterdir() if p != path and p.is_file() and "review" in p.name]
    assert backups, "Migration must preserve an appropriate backup"
    hashes = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in backups}
    with api.db_conn() as db:
        assert db.execute("SELECT COUNT(*) FROM approvals").fetchone()[0] == 1
    assert {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in backups} == hashes
    shown = client.get("/api/draft/2").json()
    assert client.post("/api/approve", json=approval(shown)).status_code == 200
    with api.db_conn() as db:
        assert db.execute("SELECT COUNT(*) FROM approvals").fetchone()[0] == 2
        assert db.execute("SELECT id,perfil_id,reviewer,reviewed_at,digest FROM approvals WHERE id=17").fetchone() == expected


def test_controlled_corrupt_package_is_detected_in_temporary_root(tmp_path, monkeypatch):
    pointer = json.loads((ROOT / "datos/processed/producto_activo.json").read_text(encoding="utf-8"))
    manifest_path = ROOT / pointer["manifest"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    destination = tmp_path / "isolated"
    target_manifest = destination / pointer["manifest"]
    target_manifest.parent.mkdir(parents=True)
    shutil.copy2(manifest_path, target_manifest)
    for entry in manifest["files"].values():
        source = (manifest_path.parent / entry["path"]).resolve()
        target = (target_manifest.parent / entry["path"]).resolve()
        assert destination.resolve() in target.parents
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    target_pointer = destination / "datos/processed/producto_activo.json"
    target_pointer.write_bytes((ROOT / "datos/processed/producto_activo.json").read_bytes())
    restored = product_contract.load_active(destination)
    assert restored["package_version"] == VERSION and restored["artifact"]["k"] == 4
    target_profiles = target_manifest.parent / manifest["files"]["profiles"]["path"]
    original = target_profiles.read_bytes()
    target_profiles.write_bytes(original + b"\n")
    with pytest.raises(ValueError):
        product_contract.load_active(destination)
    target_profiles.write_bytes(original)
    assert product_contract.load_active(destination)["package_version"] == VERSION
    # Rehashing tampered files must not hide statistical incoherence.
    wrong_profiles = json.loads(original)
    wrong_profiles[0]["n_unidades"] += 1
    target_profiles.write_text(json.dumps(wrong_profiles, ensure_ascii=False), encoding="utf-8")
    altered_manifest = copy.deepcopy(manifest)
    altered_manifest["files"]["profiles"]["sha256"] = hashlib.sha256(target_profiles.read_bytes()).hexdigest()
    target_manifest.write_text(json.dumps(altered_manifest, ensure_ascii=False), encoding="utf-8")
    altered_pointer = {**pointer, "sha256": hashlib.sha256(target_manifest.read_bytes()).hexdigest()}
    target_pointer.write_text(json.dumps(altered_pointer), encoding="utf-8")
    with pytest.raises(ValueError, match="Tamaños"):
        product_contract.load_active(destination)
    target_profiles.write_bytes(original)
    target_manifest.write_bytes(manifest_path.read_bytes())
    target_pointer.write_bytes((ROOT / "datos/processed/producto_activo.json").read_bytes())
    assert product_contract.load_active(destination)["artifact"]["k"] == 4
    monkeypatch.setattr(api, "ROOT", destination)
    api.package.cache_clear()
    try:
        cached = api.package()
        target_profiles.write_bytes(original + b"\n")
        # Existing process retains one coherent snapshot; a reload validates the whole package.
        assert api.package() is cached and len(api.data()) == 8541 and len(api.profiles()) == 4
        api.package.cache_clear()
        with pytest.raises(ValueError):
            api.package()
        target_profiles.write_bytes(original)
        api.package.cache_clear()
        assert api.package()["package_digest"] == cached["package_digest"]
        assert api.package() is not cached
    finally:
        api.package.cache_clear()


def test_previous_k5_reference_runs_from_git_in_isolated_root(tmp_path):
    baseline = json.loads((ROOT / "analisis/reportes/b4/qa_baseline.json").read_text(encoding="utf-8"))
    archive = subprocess.check_output(["git", "archive", baseline["base"], "src/dashboard_api.py", "src/education.py",
                                       "dashboard", "datos/processed/producto", "ml/modelos/kmeans5_exploratorio.joblib"], cwd=ROOT)
    isolated = tmp_path / "previous-reference"
    isolated.mkdir()
    with tarfile.open(fileobj=io.BytesIO(archive)) as bundle:
        for entry in bundle:
            if not entry.isfile():
                continue
            target = (isolated / entry.name).resolve()
            assert isolated.resolve() in target.parents
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(bundle.extractfile(entry).read())
    command = """from fastapi.testclient import TestClient
import json,numpy as np
from src.dashboard_api import app,data,profiles,artifact,FEATS
client=TestClient(app)
assert client.get('/health').json()=={'status':'ok','observaciones':8541,'perfiles':5}
assert {k:p['n_unidades'] for k,p in profiles().items()}=={1:1366,2:1872,3:1964,4:1259,5:2080}
frame=data();bundle=artifact()
raw=bundle['model'].predict(bundle['scaler'].transform(frame[FEATS].to_numpy(float)))
pred=np.array([bundle['label_mapping'][int(label)] for label in raw])
assert np.array_equal(pred,frame.perfil_id.to_numpy())
print(json.dumps({'recovered_k':5,'observations':len(frame),'all_assignments_reproduced':True}))
"""
    result = subprocess.run([sys.executable, "-B", "-c", command], cwd=isolated,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
    assert result.returncode == 0, result.stdout
    assert '"recovered_k": 5' in result.stdout


def test_duplicate_profile_names_rejected_before_activation(tmp_path):
    isolated = tmp_path / "isolated-build"
    b2_path = "analisis/reportes/b2/resultados.json"
    b2 = json.loads((ROOT / b2_path).read_text(encoding="utf-8"))
    relative_files = [p for p in b2["trazabilidad"]["sha256_entradas_y_codigo"] if p.startswith("datos/processed/")]
    relative_files += [b2_path] + [f"ml/resultados/b3/{name}" for name in [
        "verificacion_candidato.json", "candidato_recomendado.joblib", "asignaciones_candidato.csv",
        "perfiles_candidato.json", "ejecucion.json"]]
    for relative in relative_files:
        target = isolated / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)
    pointer = isolated / "datos/processed/producto_activo.json"
    pointer.write_bytes((ROOT / "datos/processed/producto_activo.json").read_bytes())
    active_manifest_relative = Path(json.loads(pointer.read_text(encoding="utf-8"))["manifest"])
    shutil.copytree(ROOT / active_manifest_relative.parent, isolated / active_manifest_relative.parent, dirs_exist_ok=True)
    original_pointer = pointer.read_bytes()
    names = json.loads((ROOT / "ml/resultados/b3/perfiles_candidato.json").read_text(encoding="utf-8"))
    names.append(copy.deepcopy(names[0]))
    names_path = tmp_path / "duplicate-names.json"
    names_path.write_text(json.dumps(names, ensure_ascii=False), encoding="utf-8")
    invalid_version = "ccpc-qa-duplicate-names-v1"
    command = [sys.executable, "-B", "-m", "src.prepare_product", "--root", str(isolated),
               "--version", invalid_version, "--names", str(names_path), "--activate"]
    result = subprocess.run(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, encoding="utf-8", errors="replace")
    assert result.returncode != 0, result.stdout
    assert "nombres" in result.stdout.lower() or "duplicad" in result.stdout.lower(), result.stdout
    assert pointer.read_bytes() == original_pointer
    assert not (isolated / "datos/processed/producto" / invalid_version).exists()
    valid_names = names[:-1]
    valid_names[0]["nombre"] += " — cambio que exige nueva versión"
    names_path.write_text(json.dumps(valid_names, ensure_ascii=False), encoding="utf-8")
    command[command.index(invalid_version)] = VERSION
    reused = subprocess.run(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, encoding="utf-8", errors="replace")
    assert reused.returncode != 0 and "contenido" in reused.stdout.lower(), reused.stdout
    assert pointer.read_bytes() == original_pointer
    assert product_contract.load_active(isolated)["profiles"][1]["nombre"] != valid_names[0]["nombre"]


def test_git_checkout_roundtrip_preserves_package_hashes_with_autocrlf(tmp_path):
    repository = tmp_path / "index-fixture"
    checkout = tmp_path / "checkout"
    repository.mkdir()
    checkout.mkdir()
    baseline = json.loads((ROOT / "analisis/reportes/b4/qa_baseline.json").read_text(encoding="utf-8"))
    relatives = {p for p in baseline["hashes_base"] if p.startswith("datos/processed/")
                 or p.startswith("ml/resultados/b3/") or p == "ml/modelos/kmeans5_exploratorio.joblib"}
    relatives |= {".gitattributes", "datos/processed/producto_activo.json"}
    pointer = json.loads((ROOT / "datos/processed/producto_activo.json").read_text(encoding="utf-8"))
    manifest_path = ROOT / pointer["manifest"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    relatives.add(pointer["manifest"])
    relatives |= {(manifest_path.parent / f["path"]).relative_to(ROOT).as_posix() for f in manifest["files"].values()}
    before = {}
    for relative in sorted(relatives):
        content = (ROOT / relative).read_bytes()
        target = repository / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        before[relative] = hashlib.sha256(content).hexdigest()
    for command in [["init"], ["config", "core.autocrlf", "true"], ["add", "--", "."], ["write-tree"],
                    ["checkout-index", "--all", f"--prefix={checkout.as_posix()}/"]]:
        result = subprocess.run(["git", "-C", str(repository), *command], stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
        assert result.returncode == 0, result.stdout
    for relative, digest in before.items():
        assert hashlib.sha256((checkout / relative).read_bytes()).hexdigest() == digest, relative
    recovered = product_contract.load_active(checkout)
    assert recovered["package_version"] == VERSION and recovered["artifact"]["k"] == 4
    assert len(recovered["data"]) == 8541
