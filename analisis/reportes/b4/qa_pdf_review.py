"""QA-only PDF extraction/render; real API and isolated SQLite, no production writes."""
from pathlib import Path
import json
import sys
import tempfile

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(tempfile.gettempdir()) / "ccpc-b4-pdfium-tools"))

from fastapi.testclient import TestClient
import pypdfium2 as pdfium
from src import dashboard_api as api


def main():
    out = ROOT / "analisis/reportes/b4"
    expected = json.loads((ROOT / "ml/resultados/b3/perfiles_candidato.json").read_text(encoding="utf-8"))
    results = []
    with tempfile.TemporaryDirectory(prefix="qa-b4-pdf-") as temporary:
        api.DB_PATH = Path(temporary) / "qa-reviews.sqlite3"
        api.package.cache_clear()
        with TestClient(api.app) as client:
            for profile in expected:
                pid = profile["perfil_id"]
                shown_response = client.get(f"/api/draft/{pid}")
                assert shown_response.status_code == 200
                shown = shown_response.json()
                payload = dict(profile_id=pid, reviewer="QA_B4_REVISOR_TEMPORAL", confirmed=True,
                               package_version=shown["package_version"], package_digest=shown["package_digest"],
                               draft_digest=shown["draft_digest"])
                approved = client.post("/api/approve", json=payload)
                assert approved.status_code == 200, approved.text
                download = client.get(approved.json()["download_url"])
                assert download.status_code == 200
                filename = f"qa_pdf_perfil_{pid}.pdf"
                (out / filename).write_bytes(download.content)
                document = pdfium.PdfDocument(download.content)
                texts, renders = [], []
                for page_number in range(len(document)):
                    page = document[page_number]
                    texts.append(page.get_textpage().get_text_range())
                    image_name = f"qa_pdf_perfil_{pid}_pagina_{page_number+1}.png"
                    page.render(scale=1.35).to_pil().save(out / image_name)
                    renders.append(image_name)
                text = " ".join(" ".join(texts).split())
                assert profile["nombre"] in text, (pid, "nombre", text)
                assert f"{profile['n_unidades']:,}" in text, (pid, "conteo", text)
                for field in ["media_presidencial", "media_intermedia"]:
                    assert f"{profile[field]:.1f}%" in text, (pid, field, text)
                for field in ["cambio_presidencial_pp", "cambio_intermedia_pp"]:
                    assert f"{profile[field]:+.1f}" in text, (pid, field, text)
                assert "ccpc-2009-2024-k4-v1" in text
                assert "QA_B4_REVISOR_TEMPORAL" in text
                assert "Revisión humana" in text
                assert "2024" in text and "2009" in text
                assert "no autoriza difusión automatizada" in text
                (out / f"qa_pdf_perfil_{pid}.txt").write_text("\n".join(texts), encoding="utf-8")
                results.append(dict(perfil_id=pid, paginas=len(document), pdf=filename, renders=renders,
                                    texto_y_cifras_verificados=True, revision_visual="Pendiente de inspección por qa_b4"))
    api.package.cache_clear()
    (out / "qa_pdf_resultados.json").write_text(json.dumps(results, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
