"""QA final on a frozen checkout: full suite, PDF text/render and real browser."""
from pathlib import Path
from datetime import datetime
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import uuid
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "analisis/reportes/b4"
sys.stdout.reconfigure(encoding="utf-8")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    names = subprocess.check_output(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=ROOT).decode().split("\0")
    paths = [p for p in names if p and p != "docs/12_QA_B4.md" and
             (not p.startswith("analisis/reportes/b4/qa_") or Path(p).suffix in [".py", ".cjs"] or p.endswith("qa_baseline.json"))]
    before = {p: sha(ROOT / p) for p in sorted(set(paths))}
    actual_db = ROOT / "entregables/revision_local.sqlite3"
    history_before = sha(actual_db) if actual_db.exists() else None
    state = dict(fecha=datetime.now(ZoneInfo("America/Tijuana")).isoformat(),
                 base=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip(),
                 git_status=subprocess.check_output(["git", "status", "--short", "--branch"], cwd=ROOT).decode(),
                 hashes=before, historial_real_sha256=history_before)
    (OUT / "qa_final_state.json").write_text(json.dumps(state, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    temporary = str(Path(tempfile.gettempdir()) / ("qa-b4-final-" + uuid.uuid4().hex))
    steps = [("pytest", [sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", "--basetemp", temporary, "tests"]),
             ("pdf", [sys.executable, "-B", str(OUT / "qa_pdf_review.py")]),
             ("browser", [sys.executable, "-B", str(OUT / "qa_browser_run.py")])]
    evidence = []
    for label, command in steps:
        result = subprocess.run(command, cwd=ROOT, env={**os.environ, "PYTHONIOENCODING": "utf-8"},
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                encoding="utf-8", errors="strict", timeout=180)
        transcript = "Command: " + subprocess.list2cmdline(command) + f"\nExit: {result.returncode}\n" + result.stdout
        (OUT / f"qa_final_{label}.txt").write_text(transcript, encoding="utf-8")
        evidence.append(dict(control=label, comando=command, exit=result.returncode))
        print(transcript, flush=True)
        if result.returncode:
            break
    changed = [p for p, digest in before.items() if not (ROOT / p).exists() or sha(ROOT / p) != digest]
    history_after = sha(actual_db) if actual_db.exists() else None
    result = dict(controles=evidence, archivos_cambiados_durante_pasada=changed,
                  historial_real_sin_cambios=history_before == history_after,
                  revision_visual="Pendiente de inspección qa_b4 de los renders finales",
                  estado_automatizado="PASA" if len(evidence) == 3 and all(e["exit"] == 0 for e in evidence)
                  and not changed and history_before == history_after else "FALLA")
    (OUT / "qa_final_resultados.json").write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    if result["estado_automatizado"] != "PASA":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
