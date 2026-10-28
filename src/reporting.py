"""Summary datasets and figures for the INE CCPC historical audit."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

YRS=[2009,2012,2015,2018,2021,2024]

def summarize(root:Path):
    root=root.resolve();r=root/'analisis'/'reportes';r.mkdir(parents=True,exist_ok=True)
    fig=root/'analisis'/'figuras';fig.mkdir(parents=True,exist_ok=True)
    audit=[json.load(open(root/'datos'/'processed'/str(y)/'auditoria.json')) for y in YRS]
    a=[]
    for d in audit:
        c=d['conteos'];den=c['SV']+c['NV'];a.append({'anio':d['anio'],'tipo':'Presidencial' if d['anio'] in (2012,2018,2024) else 'Intermedia',
        'filas':d['filas'],'municipios':d['municipios'],'LN':c['LN'],'SV':c['SV'],'NV':c['NV'],'NS':c['NS'],
        'participacion_pct':100*c['SV']/den,'ns_pct':100*c['NS']/c['LN'],
        'faltantes_DEL':d['faltantes_por_columna'].get('DEL',0)})
    nat=pd.DataFrame(a);nat.to_csv(r/'resumen_nacional.csv',index=False)
    series=pd.read_csv(root/'datos'/'processed'/'serie_municipio_edad_2009_2024.csv')
    age=series.groupby(['anio','grupo_edad'],as_index=False)[['LN','SV','NV','NS']].sum()
    age['participacion_pct']=age.SV/(age.SV+age.NV)*100
    age['ns_pct']=age.NS/age.LN*100
    age.to_csv(r/'participacion_por_edad_y_anio.csv',index=False)
    # Aggregates from original data; sex and section type are DESCRIPTIVE, not model features.
    for variable,source,outname in [('SEXO','municipio_edad_sexo.csv','participacion_por_sexo_y_anio.csv'),
                                 ('TIPOSEC','municipio_edad_tipo_seccion.csv','participacion_por_tipo_seccion_y_anio.csv')]:
        frames=[]
        for y in YRS:
            p=pd.read_csv(root/'datos'/'processed'/str(y)/source)
            g=p.groupby(['anio',variable],dropna=False,as_index=False)[['LN','SV','NV','NS']].sum()
            g['participacion_pct']=g.SV/(g.SV+g.NV)*100
            frames.append(g)
        pd.concat(frames,ignore_index=True).to_csv(r/outname,index=False)
    panel=pd.read_csv(root/'datos'/'processed'/'matriz_modelo_6_anios.csv')
    status=pd.DataFrame([
        {'grupo':'Todas las unidades distintas','n':len(panel)},
        {'grupo':'Con tasa en seis elecciones','n':int(panel.completo_6.sum())},
        {'grupo':'Con nombre municipal estable','n':int(panel.identidad_estable_conservadora.sum())},
        {'grupo':'Aptas para clustering','n':int(panel.apto_modelo.sum())},
    ]);status.to_csv(r/'cobertura_panel.csv',index=False)
    # Exclusion categories overlap: not an additive breakdown.
    ex=pd.DataFrame([{'motivo':'Falta al menos una tasa','n_unidades':int((~panel.completo_6).sum())},
      {'motivo':'Nombre municipal inconsistente','n_unidades':int((~panel.identidad_estable_conservadora).sum())},
      {'motivo':'<100 observados en alguna elección','n_unidades':int((panel.min_observados<100).sum())},
      {'motivo':'NS >20% en alguna elección','n_unidades':int((panel.max_ns_pct>20).sum())}])
    ex.to_csv(r/'causas_exclusion_superpuestas.csv',index=False)
    plt.figure(figsize=(9,4.5));plt.plot(nat.anio,nat.participacion_pct,marker='o')
    for _,v in nat.iterrows():plt.annotate(f"{v.participacion_pct:.1f}%",(v.anio,v.participacion_pct),xytext=(0,9),textcoords='offset points',ha='center')
    plt.xlabel('Año de elección');plt.ylabel('Participación observada (%)');plt.ylim(35,72)
    plt.title('Participación nacional registrada en CCPC (2009–2024)');plt.grid(alpha=.2);plt.tight_layout();plt.savefig(fig/'participacion_nacional.png',dpi=150);plt.close()
    ageplot=age.pivot(index='anio',columns='grupo_edad',values='participacion_pct').reindex(YRS)
    plt.figure(figsize=(9,5.2));
    for c in ['18-24','25-34','35-44','45-59','60+']:plt.plot(ageplot.index,ageplot[c],marker='.',label=c)
    plt.xlabel('Año');plt.ylabel('Participación observada (%)');plt.title('Participación por edad: panel transversal');plt.legend(title='Grupo de edad',ncol=5,fontsize=8);plt.grid(alpha=.2);plt.tight_layout();plt.savefig(fig/'participacion_grupos_edad.png',dpi=150);plt.close()
    plt.figure(figsize=(9,4.3));plt.bar(nat.anio.astype(str),nat.ns_pct)
    plt.ylabel('% LN con estado no especificado');plt.xlabel('Año');plt.title('Cobertura de marcas de participación: NS / LN');plt.tight_layout();plt.savefig(fig/'no_especificados.png',dpi=150);plt.close()
    comp=pd.read_csv(root/'ml'/'resultados'/'comparacion_modelos.csv')
    plt.figure(figsize=(9,4.8));
    for name,g in comp.groupby('algoritmo'):
        g=g.sort_values('k');plt.plot(g.k,g.silhouette_muestra_2000,marker='o',label=name)
    plt.xlabel('Número de clusters (k)');plt.ylabel('Silhouette (muestra 2,000)');plt.title('Comparación de modelos 2009–2024');plt.xticks([4,5,6]);plt.legend();plt.grid(alpha=.2);plt.tight_layout();plt.savefig(fig/'comparacion_clustering.png',dpi=150);plt.close()
    prof=pd.read_csv(root/'ml'/'resultados'/'fichas_perfiles_exploratorias.csv')
    plt.figure(figsize=(8.5,5.0));
    for _,rr in prof.iterrows():
        plt.scatter(rr.media_intermedia,rr.media_presidencial,s=np.sqrt(rr.n_unidades)*22,alpha=.7)
        plt.annotate(f"Perfil {int(rr.perfil_id)}",(rr.media_intermedia,rr.media_presidencial),xytext=(7,0),textcoords='offset points')
    plt.xlabel('Participación media intermedia (%)');plt.ylabel('Participación media presidencial (%)');plt.title('Centros de los 5 perfiles exploratorios (tamaño ≈ unidades)');plt.grid(alpha=.2);plt.tight_layout();plt.savefig(fig/'centros_perfiles.png',dpi=150);plt.close()
    return nat,age,status,ex
if __name__=='__main__':
    import sys
    root=Path(sys.argv[1] if len(sys.argv)>1 else '.')
    nat,age,status,ex=summarize(root)
    print(nat[['anio','participacion_pct','ns_pct']].round(2).to_string(index=False));print(status.to_string(index=False));print(ex.to_string(index=False))
