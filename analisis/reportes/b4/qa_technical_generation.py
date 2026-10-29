"""QA-only execution of the technical report generator in an isolated root."""
from pathlib import Path
import json
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "analisis/reportes/b4"
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(tempfile.gettempdir()) / "ccpc-b4-pdfium-tools"))
import pypdfium2 as pdfium

with tempfile.TemporaryDirectory(prefix="qa-b4-technical-") as folder:
    isolated = Path(folder)
    for file in (ROOT / "src").glob("*.py"):
        target = isolated / "src" / file.name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file, target)
    pointer = json.loads((ROOT / "datos/processed/producto_activo.json").read_text(encoding="utf-8"))
    package_folder = Path(pointer["manifest"]).parent
    shutil.copytree(ROOT / package_folder, isolated / package_folder)
    for relative in ["datos/processed/producto_activo.json", "ml/resultados/comparacion_modelos.csv",
                     "analisis/reportes/resumen_nacional.csv", "analisis/figuras/no_especificados.png"]:
        target = isolated / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)
    command = [sys.executable, "-B", "-m", "src.technical_report"]
    run = subprocess.run(command, cwd=isolated, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         text=True, encoding="utf-8", errors="replace")
    (OUT / "qa_technical_generation.txt").write_text("Command: " + subprocess.list2cmdline(command) +
        f"\nIsolated cwd: {isolated}\nExit: {run.returncode}\n" + run.stdout, encoding="utf-8")
    assert run.returncode == 0, run.stdout
    generated = isolated / "entregables/reportes/ccpc-2009-2024-k4-v1/documento_tecnico_reto1.pdf"
    payload = generated.read_bytes()
    (OUT / "qa_technical_generated.pdf").write_bytes(payload)
    document = pdfium.PdfDocument(payload)
    texts = [document[i].get_textpage().get_text_range() for i in range(len(document))]
    joined = " ".join(" ".join(texts).split())
    assert "ccpc-2009-2024-k4-v1" in joined
    assert "8. 4 perfiles" in joined
    assert "Cinco perfiles y su caracterización" not in joined
    assert "el 5 muestra niveles altos" not in joined
    expected = json.loads((ROOT / "ml/resultados/b3/perfiles_candidato.json").read_text(encoding="utf-8"))
    for p in expected:
        assert p["nombre"] in joined and f"{p['n_unidades']:,}" in joined
    (OUT / "qa_technical_generated.txt").write_text("\n\n".join(texts), encoding="utf-8")
    pages = [i for i, text in enumerate(texts) if "8. 4 perfiles" in " ".join(text.split())]
    assert pages
    renders = []
    for i in pages:
        name = f"qa_technical_section8_page{i+1}.png"
        document[i].render(scale=1.35).to_pil().save(OUT / name)
        renders.append(name)
    result = dict(exit=run.returncode, paginas=len(document), version_y_cuatro_perfiles_verificados=True,
                  renders=renders, alcance_visual="Sección8; informe técnico completo aún requiere QA editorial antes de entrega")
    (OUT / "qa_technical_generation_resultados.json").write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
