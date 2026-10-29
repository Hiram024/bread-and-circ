"""Prepare an immutable B4 product from B3, without training or implicit activation."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import shutil
import tempfile
import numpy as np
import pandas as pd
from .evaluate_clustering import align, load_bundle, load_data, predict, profile_tables
from .product_contract import FEATS, YEARS, activate, canonical, load_package, read_json, sha256

VERSION = "ccpc-2009-2024-k4-v1"
B3 = Path("ml/resultados/b3")


def build(root: Path, version=VERSION, names_path=None):
    root = Path(root).resolve()
    if not re.fullmatch(r"[a-z0-9][a-z0-9.-]*", version):
        raise ValueError("Identificación de versión inválida")
    evidence = read_json(root / B3 / "verificacion_candidato.json")
    source = root / B3 / "candidato_recomendado.joblib"
    if sha256(source) != evidence["candidato_sha256"] or evidence["k"] != 4:
        raise ValueError("Candidato distinto al comprobado en B3")
    recorded_b2 = read_json(root / "analisis/reportes/b2/resultados.json")
    inputs = {p: h for p, h in recorded_b2["trazabilidad"]["sha256_entradas_y_codigo"].items()
              if p.startswith("datos/processed/")}
    for path, expected in inputs.items():
        if sha256(root / path) != expected:
            raise ValueError(f"Insumo procesado auditado cambió: {path}")
    good, _ = load_data(root)
    bundle = load_bundle(source)
    assignments = predict(bundle, good)
    saved = pd.read_csv(root / B3 / "asignaciones_candidato.csv",
                        dtype={c: "string" for c in ["EDOCVE", "MPIOCVE", "grupo_edad"]})
    compared = align(assignments, saved, ["perfil_id"])
    if not compared.perfil_id_left.eq(compared.perfil_id_right).all() or len(good) != evidence["claves_verificadas"]:
        raise ValueError("Las asignaciones no corresponden a B3")
    names_source = Path(names_path).resolve() if names_path else root / B3 / "perfiles_candidato.json"
    supplied_names = read_json(names_source)
    names = {str(p["perfil_id"]): p["nombre"] for p in supplied_names}
    if len(supplied_names) != len(names) or set(names) != {str(i) for i in range(1, bundle["k"]+1)} or not all(isinstance(n, str) and n.strip() for n in names.values()):
        raise ValueError("Nombres/IDs incompletos")
    profiles, _ = profile_tables(good, assignments, names)
    for profile in profiles:
        profile.update(package_version=version, k=bundle["k"], notas=[
            "Paquete local adoptado por Hiram en B4; aprobación de Rubén no asumida.",
            "Medias simples de unidades agregadas; no describen personas.",
            "Correspondencia territorial nominal; límites históricos no certificados."])
    if names_path is None:
        for old, new in zip(read_json(root / B3 / "perfiles_candidato.json"), profiles, strict=True):
            for field in ["n_unidades", "municipios", "lista_nominal_2024", *FEATS, "brecha_pres_intermedia"]:
                if not np.isclose(old[field], new[field], rtol=0, atol=1e-10):
                    raise ValueError(f"Resumen de B3 distinto: {field}")
    raw = good.merge(assignments, on=["EDOCVE", "MPIOCVE", "grupo_edad"], validate="one_to_one")
    names24 = pd.read_csv(root / "datos/processed/2024/municipios_nombres.csv",
                          dtype={"EDOCVE": "string", "MPIOCVE": "string"})
    for col, width in [("EDOCVE", 2), ("MPIOCVE", 3)]:
        names24[col] = names24[col].str.zfill(width)
    if names24.duplicated(["EDOCVE", "MPIOCVE"]).any():
        raise ValueError("Nombres 2024 ambiguos; no resolver con first/drop_duplicates")
    raw = raw.merge(names24[["EDOCVE", "MPIOCVE", "EDONOM", "MPIONOM"]],
                    on=["EDOCVE", "MPIOCVE"], how="left", validate="many_to_one")
    if raw[["EDONOM", "MPIONOM"]].isna().any().any():
        raise ValueError("Nombres faltantes en producto")
    raw["clave_municipal"] = raw.EDOCVE + "-" + raw.MPIOCVE
    raw["perfil_nombre"] = raw.perfil_id.map({p["perfil_id"]: p["nombre"] for p in profiles})
    raw["package_version"] = version
    z = bundle["scaler"].transform(raw[FEATS].to_numpy(float))
    labels = bundle["model"].predict(z)
    raw["distancia_centroide"] = np.linalg.norm(z - bundle["model"].cluster_centers_[labels], axis=1)
    raw["restriccion_geografica"] = "Comparabilidad por clave y nombre; límites territoriales no certificados"
    for col in ["EDOCVE", "MPIOCVE"]:
        raw[col] = raw[col].astype(int)
    fields = ["EDOCVE", "MPIOCVE", "clave_municipal", "EDONOM", "MPIONOM", "grupo_edad",
              "perfil_id", "perfil_nombre", "package_version", *FEATS, "brecha_pres_intermedia",
              "distancia_centroide", "LN_2024", "max_ns_pct", "restriccion_geografica",
              *[f"tasa_{y}" for y in YEARS], *[f"observados_{y}" for y in YEARS]]
    b2 = recorded_b2["resumen"]
    metadata = dict(package_version=version, k=bundle["k"], features=FEATS, filters=bundle["filters"],
                    anios=list(YEARS), total_unidades_modeladas=len(raw),
                    total_municipios_modelados=len(raw.groupby(["EDOCVE", "MPIOCVE"])),
                    total_unidades_panel=b2["n_panel"], modelo=f"KMeans k={bundle['k']} exploratorio",
                    origen="CCPC INE 2009–2024; agregación municipio × edad", perfiles=profiles,
                    advertencia_territorial="Correspondencia nominal; no hay crosswalk cartográfico histórico certificado.",
                    cobertura_LN_2024=dict(numerador=int(raw.LN_2024.sum()), denominador=b2["LN_2024_total_panel"],
                                          porcentaje=100 * raw.LN_2024.sum()/b2["LN_2024_total_panel"],
                                          universo="Agregado nacional procesado 2024 de cinco edades"))
    parent = root / "datos/processed/producto"
    parent.mkdir(parents=True, exist_ok=True)
    destination = parent / version
    with tempfile.TemporaryDirectory(prefix=".preparar-", dir=parent) as folder:
        stage = Path(folder)
        shutil.copyfile(source, stage / "modelo.joblib")
        raw[fields].sort_values(["EDOCVE", "MPIOCVE", "grupo_edad"]).to_csv(
            stage / "observaciones_dashboard.csv", index=False, lineterminator="\n")
        (stage / "perfiles.json").write_text(canonical(profiles) + "\n", encoding="utf-8")
        (stage / "metadatos_dashboard.json").write_text(canonical(metadata) + "\n", encoding="utf-8")
        for filename in ["historico_nacional.csv", "homologacion_municipal_auditoria.csv"]:
            shutil.copyfile(parent / filename, stage / filename)
        files = {name: {"path": filename, "sha256": sha256(stage / filename)} for name, filename in [
            ("artifact", "modelo.joblib"), ("profiles", "perfiles.json"), ("observations", "observaciones_dashboard.csv"),
            ("metadata", "metadatos_dashboard.json"), ("national", "historico_nacional.csv"),
            ("territory_audit", "homologacion_municipal_auditoria.csv")]}
        env = read_json(root / B3 / "ejecucion.json")["entorno"]
        manifest = dict(package_version=version, k=bundle["k"], features=FEATS, years=list(YEARS),
                        filters=bundle["filters"], compatibility={
                            "python_major_minor": ".".join(env["python"].split(".")[:2]),
                            "python_tested": env["python"], "packages": env["paquetes"]}, files=files,
                        evidence=dict(B3_candidate_sha256=sha256(source), B3_report="docs/11_evaluacion_modelo_B3.md",
                                      names_source_sha256=sha256(names_source), processed_inputs_sha256=inputs,
                                      decision="Adopción local por Hiram; revisión de Rubén no asumida"))
        (stage / "manifest.json").write_text(canonical(manifest) + "\n", encoding="utf-8")
        load_package(root, stage / "manifest.json")
        if destination.exists():
            if sha256(destination / "manifest.json") != sha256(stage / "manifest.json"):
                raise ValueError("Versión existente con otro contenido; utiliza una identidad nueva")
            load_package(root, destination / "manifest.json")
        else:
            stage.rename(destination)
    return load_package(root, destination / "manifest.json")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--version", default=VERSION)
    parser.add_argument("--names", type=Path)
    parser.add_argument("--activate", action="store_true")
    args = parser.parse_args()
    package = build(args.root, args.version, args.names)
    if args.activate:
        package = activate(args.root, package["manifest_path"])
    print(json.dumps({"estado": "activado" if args.activate else "preparado",
                      "package_version": package["package_version"], "package_digest": package["package_digest"],
                      "unidades": len(package["data"]), "perfiles": len(package["profiles"]),
                      "reiniciar_servidor": bool(args.activate)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
