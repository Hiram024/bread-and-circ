"""Create and execute self-contained notebooks (executed outputs kept in .ipynb)."""
from pathlib import Path
import nbformat as nbf
from nbclient import NotebookClient

ROOT=Path(__file__).resolve().parents[1]
common="""from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display
ROOT = Path.cwd().resolve()
if not (ROOT/'datos').exists():
    ROOT = ROOT.parent.parent
assert (ROOT/'datos'/'processed').exists(), f'Abra el proyecto raíz, no otro directorio: {ROOT}'
plt.rcParams.update({'figure.figsize':(9,4.3),'figure.dpi':110})
"""

def make(title,overview,cells,relative):
    nb=nbf.v4.new_notebook()
    nb.metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},
                 'language_info':{'name':'python'},'title':title}
    nb.cells=[nbf.v4.new_markdown_cell(f'# {title}\n\n{overview}\n\nFuente: ZIPs CCPC del INE conservados en `datos/raw/`. Se trabaja sobre sus agregaciones verificables en `datos/processed/`. Los resultados representan **grupos estadísticos, no personas individuales**.'),nbf.v4.new_code_cell(common)]
    for intro,code in cells:
        nb.cells.append(nbf.v4.new_markdown_cell(intro))
        nb.cells.append(nbf.v4.new_code_cell(code))
    p=ROOT/relative;p.parent.mkdir(parents=True,exist_ok=True)
    print('Executing',relative,flush=True)
    client=NotebookClient(nb,timeout=180,kernel_name='python3',resources={'metadata':{'path':str(ROOT)}})
    client.execute()
    nbf.write(nb,p)
    print('Wrote',relative, 'cells',len(nb.cells),flush=True)

make('01 · Auditoría de las seis bases',
     'Auditoría de origen, tamaños, consistencia y datos no especificados. Este notebook lee los reportes creados mediante `python -m src.pipeline`; la auditoría original de los 192 archivos estatales se implementa en `src/pipeline.py`.',[
('## Inventario 2009–2024 y aritmética de los conteos',"""a = pd.read_csv(ROOT/'analisis/reportes/auditoria_resumen.csv')
cols=['anio','filas','municipios','LN','SV','NV','NS','count_inconsistent','count_negative','unobserved_rows']
display(a[cols]); print('TOTAL FILAS:',f'{a.filas.sum():,}'); print('Errores aritméticos:',a.count_inconsistent.sum())"""),
('## Fuentes, hash SHA-256 y campos faltantes',"""import json
for year in a.anio:
    d=json.loads((ROOT/f'datos/processed/{year}/auditoria.json').read_text())
    print(year,' | zip=',d['original_zip'].split('/')[-1], '| SHA256=',d['sha256_zip'][:16], '| faltantes=',d['faltantes_por_columna'])"""),
('## Proporción de registros sin marca conocida',"""n=pd.read_csv(ROOT/'analisis/reportes/resumen_nacional.csv')
ax=n.plot.bar(x='anio',y='ns_pct',legend=False);ax.set(title='NS/LN según elección',ylabel='% LN',xlabel='Año')
plt.tight_layout();plt.show()
print('NS significa no especificado: no debe contarse como abstención.')"""),
('## Comparaciones cuidadosas entre tipos de elección',"""display(n[['anio','tipo','participacion_pct','ns_pct']].round(2))
print('No comparar 2012→2015 como tendencia directa: elecciones de naturaleza distinta.')""")], 'analisis/notebooks/01_auditoria.ipynb')

make('02 · Análisis exploratorio histórico',
     'EDA ponderado de participación por elección, por grupos de edad y contraste descriptivo por sexo/tipo de sección. No se realiza inferencia individual.',[
('## Evolución de participación nacional (ponderada por observados)',"""n=pd.read_csv(ROOT/'analisis/reportes/resumen_nacional.csv')
plt.plot(n.anio,n.participacion_pct,marker='o')
for _,r in n.iterrows():plt.annotate(f'{r.participacion_pct:.1f}%',(r.anio,r.participacion_pct),xytext=(0,8),textcoords='offset points',ha='center')
plt.title('Participación observada nacional CCPC');plt.xlabel('Año');plt.ylabel('% SV / (SV + NV)');plt.grid(alpha=.2);plt.show()
display(n[['anio','tipo','participacion_pct','ns_pct']].round(2))"""),
('## Trayectorias transversales por edades (no son cohortes individuales)',"""age=pd.read_csv(ROOT/'analisis/reportes/participacion_por_edad_y_anio.csv')
a=age.pivot(index='anio',columns='grupo_edad',values='participacion_pct')
ax=a[['18-24','25-34','35-44','45-59','60+']].plot(marker='o')
ax.set(title='Tasas agregadas por grupo de edad',ylabel='Participación observada (%)',xlabel='Año');plt.tight_layout();plt.show()
display(a.round(2))"""),
('## Sexo: comparación descriptiva agregada (2024 incluye la categoría 2)',"""s=pd.read_csv(ROOT/'analisis/reportes/participacion_por_sexo_y_anio.csv')
display(s[['anio','SEXO','LN','participacion_pct']].round(2))
print('No inferir comportamiento de personas; evitar divulgar granularidad de categorías con base pequeña.')"""),
('## Secciones U/M/R (composición, no causalidad)',"""t=pd.read_csv(ROOT/'analisis/reportes/participacion_por_tipo_seccion_y_anio.csv')
ax=t.pivot(index='anio',columns='TIPOSEC',values='participacion_pct').plot(marker='o')
ax.set(title='Descriptivo por tipo de sección',ylabel='% observados',xlabel='Año');plt.tight_layout();plt.show()""")], 'analisis/notebooks/02_historico.ipynb')

make('03 · Homologación territorial y cobertura',
     'Auditoría del panel municipio×edad. Los 38 códigos con nombre distinto se excluyen como precaución, sin afirmar que los demás códigos garantizan geografía constante.',[
('## Panel de seis elecciones y elegibilidad',"""d=pd.read_csv(ROOT/'datos/processed/matriz_modelo_6_anios.csv')
print('Unidades distintas:',len(d),'| Seis elecciones:',d.completo_6.sum(),'| Aptas:',d.apto_modelo.sum())
display(pd.read_csv(ROOT/'analisis/reportes/cobertura_panel.csv'))
print('LN 2024 cubierto (%):',round(d.loc[d.apto_modelo,'LN_2024'].sum()/d.LN_2024.sum()*100,2))"""),
('## Exclusiones superpuestas: no se suman',"""e=pd.read_csv(ROOT/'analisis/reportes/causas_exclusion_superpuestas.csv')
display(e)
ax=e.plot.barh(x='motivo',y='n_unidades',legend=False)
ax.set(xlabel='Unidades afectadas',ylabel='');plt.tight_layout();plt.show()"""),
('## Identidad territorial: casos pendientes de correspondencia oficial',"""m=pd.read_csv(ROOT/'datos/processed/municipios_auditoria_identidad.csv')
issues=m.query('variantes_nombre > 1')
print('Códigos con nombres normalizados incompatibles:',len(issues))
name=pd.read_csv(ROOT/'datos/processed/municipios_nombres_historicos.csv')
display(issues.head(8).merge(name,on=['EDOCVE','MPIOCVE'],how='left')[['EDOCVE','MPIOCVE','anio','MPIONOM']].drop_duplicates().head(25))"""),
('## Control de sensibilidad a NS y mínimo observado',"""valid=d.apto_modelo
print('NS máxima (%) entre elegibles: ',d.loc[valid,'max_ns_pct'].describe().round(2).to_string())
print('Observados mínimos entre elegibles:',d.loc[valid,'min_observados'].describe().round(1).to_string())
print('Nota: un umbral de corte es una decisión experimental y debe probarse contra exclusiones.')""")], 'analisis/notebooks/03_territorios.ipynb')

make('04 · Clustering y validación 2009–2024',
     'Reproducción del clustering exploratorio, comparación de modelos, estabilidad, sensibilidad y validación temporal descriptiva. El modelo final del hackathon no está congelado.',[
('## Preparación de los features sin usar identificadores demográficos como predictores',"""from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from src.modeling import FEATS
D=pd.read_csv(ROOT/'datos/processed/matriz_modelo_6_anios.csv')
D=D.loc[D.apto_modelo].reset_index(drop=True)
X=D[FEATS].to_numpy()
scale=StandardScaler().fit(X);Z=scale.transform(X)
print('n=',len(D),'features=',FEATS)
display(D[FEATS].describe().round(2))"""),
('## Comparación de nueve variantes, con métricas reproducibles',"""c=pd.read_csv(ROOT/'ml/resultados/comparacion_modelos.csv')
display(c.sort_values('silhouette_muestra_2000',ascending=False)[['algoritmo','k','silhouette_muestra_2000','davies_bouldin','min_fraccion']].round(3))
for algo,grupo in c.groupby('algoritmo'):
    plt.plot(grupo.k,grupo.silhouette_muestra_2000,marker='o',label=algo)
plt.xticks([4,5,6]);plt.xlabel('k');plt.ylabel('Silhouette');plt.title('Separación de clusters: más alto es mejor');plt.legend();plt.grid(alpha=.2);plt.show()"""),
('## Reentrenamiento independiente y verificación de resultados k=4 vs k=5',"""for k in [4,5]:
    kmodel=KMeans(n_clusters=k,n_init=20,random_state=42)
    labels=kmodel.fit_predict(Z)
    score=silhouette_score(Z,labels,sample_size=min(2000,len(Z)),random_state=64)
    print(f'KMeans k={k}, silhouette={score:.4f}, tamaños={np.bincount(labels).tolist()}')
print('Son puntuaciones de clustering, NO exactitud de predicción individual.')"""),
('## Fichas de los cinco grupos exploratorios, distribuciones y limitaciones',"""p=pd.read_csv(ROOT/'ml/resultados/fichas_perfiles_exploratorias.csv')
display(p[['perfil_id','n_unidades','municipios','media_presidencial','media_intermedia','cambio_presidencial_pp','cambio_intermedia_pp']].round(2))
ax=p.plot.scatter(x='media_intermedia',y='media_presidencial',s=p.n_unidades/10)
for _,r in p.iterrows():ax.annotate(f'P{int(r.perfil_id)}',(r.media_intermedia,r.media_presidencial),xytext=(6,0),textcoords='offset points')
ax.set(title='Centros aproximados de grupos',xlabel='Intermedias (%)',ylabel='Presidenciales (%)');plt.show()"""),
('## Estabilidad y temporalidad sin filtrar 2024 al entrenamiento de evaluación',"""import json
st=pd.read_csv(ROOT/'ml/resultados/estabilidad_semillas.csv')
sens=pd.read_csv(ROOT/'ml/resultados/sensibilidad.csv')
display(st.round(3));display(sens.round(3))
h=json.loads((ROOT/'ml/resultados/validacion_temporal_descriptiva.json').read_text())
print('Holdout descriptivo: entrenamiento 2009–2021; tasa 2024 retenida.')
print('Eta² 2024:',round(h['eta_cuadrada_tasa_2024'],3))
print('Esto NO demuestra capacidad de predicción causal ni resultados individuales.')""")], 'ml/notebooks/04_modelado.ipynb')
