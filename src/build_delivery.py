"""Export five clearly marked UNAPPROVED demonstration PDFs and CSV template."""
from pathlib import Path
import pandas as pd
from .education import build_draft,pdf_for_draft
from .prepare_product import build
import json
ROOT=Path(__file__).resolve().parents[1]
def main():
    build(ROOT)
    profiles=json.loads((ROOT/'datos/processed/producto/perfiles.json').read_text())
    fichas=ROOT/'entregables/fichas';fichas.mkdir(exist_ok=True,parents=True)
    for p in profiles:
        item=build_draft(p)
        # Not a human approval. Intended for print/layout QA only.
        pdf=pdf_for_draft(item,'BORRADOR DEMOSTRATIVO — NO REVISADO','Sin aprobación humana')
        (fichas/f'perfil_{p["perfil_id"]}_borrador_no_aprobado.pdf').write_bytes(pdf)
    years=(2009,2012,2015,2018,2021,2024)
    demo={'unidad_id':'MUESTRA_SINTETICA','grupo_edad':'25-34'}
    for yr,rate in zip(years,(44,61,48,63,51,60)):
        demo.update({f'tasa_{yr}':rate,f'observados_{yr}':300,f'ns_pct_{yr}':3})
    pd.DataFrame([demo]).to_csv(ROOT/'samples/plantilla_clasificacion_ejemplo_SINTETICO.csv',index=False)
    print('Generados 5 borradores PDF sin aprobación y plantilla sintética.')
if __name__=='__main__':main()
