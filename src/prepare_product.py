"""Build a clean dashboard data mart and conservative municipal audit.

Official geometrical equivalence is NOT claimed. Codes and names are only a
proxy; `requiere_revision_territorial` is explicit in all output products.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd

YEARS = [2009,2012,2015,2018,2021,2024]
LABELS = {
 1:'Participación baja; descenso presidencial',
 2:'Participación media-baja; aumento intermedio',
 3:'Participación media-alta; descenso presidencial',
 4:'Participación media-alta; crecimiento intermedio',
 5:'Participación alta; comportamiento sostenido',
}

def build(root: Path):
    root=Path(root)
    out=root/'datos/processed/producto';out.mkdir(parents=True,exist_ok=True)
    names=pd.read_csv(root/'datos/processed/municipios_nombres_historicos.csv')
    names24=pd.read_csv(root/'datos/processed/2024/municipios_nombres.csv')
    name_index=names24[['EDOCVE','MPIOCVE','EDONOM','MPIONOM']].drop_duplicates(['EDOCVE','MPIOCVE'])
    key=['EDOCVE','MPIOCVE']
    status=(names.groupby(key).agg(anios_observados=('anio','nunique'),variantes_normalizadas=('nombre_norm','nunique'),
          nombres=('MPIONOM',lambda s:' | '.join(sorted(set(map(str,s)))))).reset_index())
    status=status.merge(name_index,on=key,how='left',validate='one_to_one')
    status['clave_municipal']=status.EDOCVE.map('{:02d}'.format)+'-'+status.MPIOCVE.map('{:03d}'.format)
    status['estatus_administrativo']=np.select([status.anios_observados.lt(6),status.variantes_normalizadas.gt(1)],
        ['incompleto_en_serie','revisar_identidad_nominal'],default='estable_por_nombre_y_clave')
    status['requiere_revision_territorial']=True
    status['justificacion']='La identidad nominal no demuestra igualdad de límites históricos; falta una correspondencia cartográfica con fechas de vigencia.'
    status.sort_values(key).to_csv(out/'homologacion_municipal_auditoria.csv',index=False)
    raw=pd.read_csv(root/'ml/resultados/observaciones_segmentadas.csv')
    raw=raw.merge(name_index,on=key,how='left',validate='many_to_one')
    raw['clave_municipal']=raw.EDOCVE.map('{:02d}'.format)+'-'+raw.MPIOCVE.map('{:03d}'.format)
    raw['perfil_nombre']=raw.perfil_id.map(LABELS)
    raw['restriccion_geografica']='Comparabilidad por clave y nombre; límites territoriales no certificados'
    wanted=['EDOCVE','MPIOCVE','clave_municipal','EDONOM','MPIONOM','grupo_edad','perfil_id','perfil_nombre',
            'media_presidencial','media_intermedia','cambio_presidencial_pp','cambio_intermedia_pp',
            'brecha_pres_intermedia','distancia_centroide','LN_2024','max_ns_pct',
            *[f'tasa_{y}' for y in YEARS],*[f'observados_{y}' for y in YEARS]]
    raw[wanted].sort_values(['EDOCVE','MPIOCVE','grupo_edad']).to_csv(out/'observaciones_dashboard.csv',index=False)
    summaries=[]
    for pid,d in raw.groupby('perfil_id'):
        means={k:round(float(d[k].mean()),2) for k in ['media_presidencial','media_intermedia','brecha_pres_intermedia',
                  'cambio_presidencial_pp','cambio_intermedia_pp']}
        summaries.append({'perfil_id':int(pid),'nombre':LABELS[int(pid)],'n_unidades':len(d),'municipios':int(d.clave_municipal.nunique()),
             'porcentaje_unidades':round(100*len(d)/len(raw),2),'lista_nominal_2024':int(d.LN_2024.sum()),
             'edad_predominante':str(d.grupo_edad.value_counts().index[0]),**means,
             'notas':['Perfiles estadísticos de unidades agregadas municipio × edad.',
                      'Las medias son no ponderadas por población y no representan individuos.',
                      'La comparabilidad territorial histórica no está certificada.']})
    (out/'perfiles.json').write_text(json.dumps(summaries,ensure_ascii=False,indent=2),encoding='utf8')
    national=pd.read_csv(root/'analisis/reportes/resumen_nacional.csv')
    national.to_csv(out/'historico_nacional.csv',index=False)
    stats={'anios':YEARS,'total_unidades_modeladas':len(raw),'total_municipios_modelados':int(raw.clave_municipal.nunique()),
           'total_unidades_panel':int(len(pd.read_csv(root/'datos/processed/matriz_modelo_6_anios.csv',usecols=['EDOCVE']))),
           'modelo':'KMeans k=5 exploratorio','origen':'CCPC INE 2009–2024; agregación municipio × edad',
           'advertencia_territorial':'No se dispone de crosswalk cartográfico oficial multianual verificado; se utiliza un filtro conservador de estabilidad nominal.','perfiles':summaries}
    (out/'metadatos_dashboard.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2),encoding='utf8')
    return stats
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path('.'));a=p.parse_args()
    print(json.dumps(build(a.root),ensure_ascii=False)[:600])
