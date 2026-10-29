"""Export UNAPPROVED demonstrations from the active package, never train."""
from pathlib import Path
import pandas as pd
from .education import build_draft,pdf_for_draft
from .product_contract import load_active
import json
ROOT=Path(__file__).resolve().parents[1]
def main():
    package=load_active(ROOT)
    profiles=list(package['profiles'].values())
    fichas=ROOT/'entregables/fichas'/package['package_version'];fichas.mkdir(exist_ok=True,parents=True)
    for p in profiles:
        item=build_draft(p,package['package_digest'])
        # Not a human approval. Intended for print/layout QA only.
        pdf=pdf_for_draft(item,'BORRADOR DEMOSTRATIVO — NO REVISADO','Sin aprobación humana')
        (fichas/f'perfil_{p["perfil_id"]}_borrador_no_aprobado.pdf').write_bytes(pdf)
    years=(2009,2012,2015,2018,2021,2024)
    demo={'unidad_id':'MUESTRA_SINTETICA','grupo_edad':'25-34'}
    for yr,rate in zip(years,(44,61,48,63,51,60)):
        demo.update({f'tasa_{yr}':rate,f'observados_{yr}':300,f'ns_pct_{yr}':3})
    pd.DataFrame([demo]).to_csv(ROOT/'samples/plantilla_clasificacion_ejemplo_SINTETICO.csv',index=False)
    print(f"Generados {len(profiles)} borradores PDF sin aprobación: {package['package_version']}, y plantilla sintética.")
if __name__=='__main__':main()
