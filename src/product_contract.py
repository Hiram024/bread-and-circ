"""One active, integrity-checked product snapshot; no selector or training."""
from __future__ import annotations
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import warnings
import joblib
import numpy as np
import pandas as pd
from sklearn.exceptions import InconsistentVersionWarning
from threadpoolctl import threadpool_limits
from .modeling import FEATS

ROOT = Path(__file__).resolve().parents[1]
POINTER = Path("datos/processed/producto_activo.json")
YEARS = (2009, 2012, 2015, 2018, 2021, 2024)


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"),
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"JSON no finito: {value}")))


def contained(base, relative):
    base = Path(base).resolve()
    path = (base / relative).resolve()
    if Path(relative).is_absolute() or base not in path.parents:
        raise ValueError(f"Ruta fuera del paquete/proyecto: {relative}")
    return path


def check_environment(compatibility):
    if ".".join(platform.python_version_tuple()[:2]) != compatibility["python_major_minor"]:
        raise ValueError("Python incompatible con el paquete activo")
    for package, expected in compatibility["packages"].items():
        if importlib.metadata.version(package) != expected:
            raise ValueError(f"Paquete incompatible: {package} requiere {expected}; instala requirements-app.txt")


def load_package(root, manifest_path, expected_digest=None):
    """Reject incoherence before exposing any file from a product snapshot."""
    root = Path(root).resolve()
    manifest_path = Path(manifest_path)
    manifest_path = contained(root, manifest_path.relative_to(root) if manifest_path.is_absolute() else manifest_path)
    package_digest = sha256(manifest_path)
    if expected_digest is not None and package_digest != expected_digest:
        raise ValueError("Integridad del descriptor de paquete inválida")
    manifest = read_json(manifest_path)
    required = {"package_version", "k", "features", "years", "filters", "compatibility", "files"}
    if not required.issubset(manifest) or manifest["features"] != FEATS or manifest["years"] != list(YEARS):
        raise ValueError("Contrato de features/años/descriptor incompatible")
    if not isinstance(manifest["k"], int) or manifest["k"] < 1 or not manifest["package_version"]:
        raise ValueError("Versión/k de paquete inválidos")
    if manifest["filters"] != {"min_observados_por_anio": 100, "max_ns_pct": 20,
                                "6_years": True, "nombre_municipal_estable": True}:
        raise ValueError("Filtros del paquete fuera del contrato vigente")
    check_environment(manifest["compatibility"])
    paths = {}
    for name in ["artifact", "profiles", "observations", "metadata", "national", "territory_audit"]:
        spec = manifest["files"][name]
        paths[name] = contained(manifest_path.parent, spec["path"])
        if sha256(paths[name]) != spec["sha256"]:
            raise ValueError(f"Integridad de archivo de paquete inválida: {name}")
    with warnings.catch_warnings():
        warnings.simplefilter("error", InconsistentVersionWarning)
        bundle = joblib.load(paths["artifact"])  # Trusted, locally generated project artifacts only.
    if bundle["features"] != manifest["features"] or bundle["k"] != manifest["k"] or bundle["filters"] != manifest["filters"]:
        raise ValueError("Modelo y descriptor no corresponden")
    if bundle["model"].n_clusters != manifest["k"] or bundle["model"].n_features_in_ != len(FEATS):
        raise ValueError("Dimensiones del modelo incompatibles")
    profiles_list = read_json(paths["profiles"])
    profiles = {p["perfil_id"]: p for p in profiles_list}
    ids = set(range(1, manifest["k"] + 1))
    if len(profiles_list) != len(profiles) or set(profiles) != ids or set(bundle["label_mapping"].values()) != ids:
        raise ValueError("IDs de perfiles/modelo no corresponden")
    data = pd.read_csv(paths["observations"], dtype={"grupo_edad": "string", "clave_municipal": "string"})
    key = ["EDOCVE", "MPIOCVE", "grupo_edad"]
    if data[key].isna().any().any() or data.duplicated(key).any() or set(data.perfil_id) != ids:
        raise ValueError("Observaciones con claves/perfiles incompatibles")
    if not data.package_version.eq(manifest["package_version"]).all() or not np.isfinite(data[FEATS].to_numpy(float)).all():
        raise ValueError("Versión o features de observaciones inválidas")
    with threadpool_limits(limits=1):
        raw = bundle["model"].predict(bundle["scaler"].transform(data[FEATS].to_numpy(float)))
    predicted = np.array([bundle["label_mapping"][int(label)] for label in raw])
    if not np.array_equal(predicted, data.perfil_id.to_numpy()):
        raise ValueError("Asignaciones del paquete no reproducidas por su artefacto")
    for pid, group in data.groupby("perfil_id"):
        profile = profiles[pid]
        if profile["package_version"] != manifest["package_version"] or profile["k"] != manifest["k"]:
            raise ValueError("Perfil con versión/k incompatibles")
        if profile["n_unidades"] != len(group) or profile["municipios"] != len(group.groupby(key[:2])):
            raise ValueError("Tamaños de perfiles incoherentes")
        if profile["lista_nominal_2024"] != int(group.LN_2024.sum()):
            raise ValueError("LN de perfiles incoherente")
        if not group.perfil_nombre.eq(profile["nombre"]).all():
            raise ValueError("Nombres de perfiles incoherentes")
        for field in FEATS + ["brecha_pres_intermedia"]:
            if not np.isclose(profile[field], group[field].mean(), rtol=0, atol=1e-10):
                raise ValueError(f"Estadística de perfil incoherente: {field}")
    metadata = read_json(paths["metadata"])
    if (metadata["package_version"] != manifest["package_version"] or metadata["k"] != manifest["k"] or
            metadata["features"] != manifest["features"] or metadata["perfiles"] != profiles_list or
            metadata["total_unidades_modeladas"] != len(data) or
            metadata["total_municipios_modelados"] != len(data.groupby(key[:2]))):
        raise ValueError("Metadatos no corresponden al paquete")
    return dict(manifest=manifest, manifest_path=manifest_path, package_version=manifest["package_version"],
                package_digest=package_digest, artifact=bundle, profiles=profiles, data=data,
                metadata={**metadata, "package_digest": package_digest},
                national=pd.read_csv(paths["national"]), territory_audit=pd.read_csv(paths["territory_audit"]))


def load_active(root=ROOT):
    pointer = read_json(Path(root) / POINTER)
    return load_package(root, pointer["manifest"], pointer["sha256"])


def activate(root, manifest_path):
    """Validate first; replace only the pointer. Restart the local process next."""
    root = Path(root).resolve()
    package = load_package(root, manifest_path)
    pointer_path = root / POINTER
    if pointer_path.exists():
        previous = load_active(root)
        if previous["package_version"] == package["package_version"] and previous["package_digest"] != package["package_digest"]:
            raise ValueError("No se puede reutilizar una versión para contenido diferente")
    value = {"manifest": package["manifest_path"].relative_to(root).as_posix(), "sha256": package["package_digest"]}
    temp = pointer_path.with_suffix(".pending.json")
    temp.write_text(canonical(value) + "\n", encoding="utf-8")
    os.replace(temp, pointer_path)
    return package
