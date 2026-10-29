"""Create executed add-on notebooks without re-running the heavy original ingestion."""
from pathlib import Path
import nbformat as nbf
from nbclient import NotebookClient
ROOT=Path(__file__).resolve().parents[1]

def make(title, cells, path):
    nb=nbf.v4.new_notebook()
    nb.cells=[nbf.v4.new_markdown_cell(f'# {title}\n\n**Fuente:** INE CCPC 2009–2024, bases adjuntas. No hay datos personales.')]
    for kind,body in cells:
        nb.cells.append(nbf.v4.new_markdown_cell(body) if kind=='md' else nbf.v4.new_code_cell(body))
    nb.metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python'}}
    client=NotebookClient(nb,timeout=120,kernel_name='python3',resources={'metadata':{'path':str(ROOT)}})
    executed=client.execute()
    path.parent.mkdir(parents=True,exist_ok=True)
    nbf.write(executed,path)
    print('NOTEBOOK',path,len(executed.cells))

make('05 · Auditoría de identidad municipal',[
('md','## Pregunta de investigación\n¿Podemos afirmar que la identidad de cada municipio es comparable a lo largo de las seis elecciones? **No**: la coincidencia de clave y nombre no valida límites geográficos. Aquí se documenta una aproximación conservadora.'),
('code','''from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from src.product_contract import load_active
package=load_active(Path('.'))
a=package['territory_audit']
a.estatus_administrativo.value_counts()'''),
('code','''counts=a.estatus_administrativo.value_counts().sort_values()
fig,ax=plt.subplots(figsize=(9,4));counts.plot.barh(ax=ax);ax.set_title('Claves municipales según auditoría administrativa');ax.set_xlabel('Municipios');ax.grid(axis='x',alpha=.2);plt.tight_layout();plt.show()'''),
('md','## Casos delicados\nSe muestran claves cuyo nombre y/o presencia histórica difieren. Esto NO autoriza a unir claves distintas ni a interpolar municipios nuevos.'),
('code','''a[a.estatus_administrativo.ne('estable_por_nombre_y_clave')][['clave_municipal','EDONOM','MPIONOM','anios_observados','nombres','estatus_administrativo']].head(15)'''),
('md','## Tasa de inclusión del clustering\nEste filtro no elimina el riesgo de cambios en límites. La cobertura y el sesgo deben evaluarse antes de usar resultados institucionalmente.'),
('code','''panel=pd.read_csv('datos/processed/matriz_modelo_6_anios.csv')
print('unidades panel',len(panel),'aptas',int(panel.apto_modelo.sum()))
print('porcentaje aptas',round(100*panel.apto_modelo.mean(),1),'%')
print('nombres no estables',len(a[a.variantes_normalizadas.gt(1)]))'''),
('md','## Conclusión\nLa homologación administrativa queda auditable y reproducible. **La equivalencia cartográfica histórica continúa pendiente**; ver `docs/07_homologacion_territorial.md`.')], ROOT/'analisis/notebooks/05_auditoria_homologacion_producto.ipynb')

make('06 · Consolidación de perfiles y fichas',[
('md','## Propósito\nValidar los resultados visibles por el dashboard y probar el flujo de creación de una ficha educativa sin datos personales ni difusión automatizada.'),
('code','''import json
import pandas as pd
from pathlib import Path
from src.product_contract import load_active
package=load_active(Path('.'))
profiles=pd.DataFrame(package['profiles'].values())
profiles[['perfil_id','nombre','n_unidades','media_presidencial','media_intermedia','cambio_presidencial_pp','cambio_intermedia_pp']]'''),
('md','## Distribución y medidas descriptivas\nLos promedios son **no ponderados**. La versión activa, cantidad y nombres se leen del paquete; B3 documenta la comparación histórica 4/5/6.'),
('code','''import matplotlib.pyplot as plt
fig,ax=plt.subplots(figsize=(9,4));
x=profiles.perfil_id.to_numpy();ax.bar(x-.16,profiles.media_presidencial,width=.32,label='Presidenciales');ax.bar(x+.16,profiles.media_intermedia,width=.32,label='Intermedias');ax.set_xticks(x);ax.set_xlabel('Perfil estadístico');ax.set_ylabel('Participación media (%)');ax.legend();plt.tight_layout();plt.show()'''),
('md','## Inferencia en CSV agregado\nSolo observaciones con tasas, observados y NS para los **seis años**. Datos futuros aislados no son compatibles con este modelo.'),
('code','''from src.dashboard_api import classify_dataframe
sample=pd.read_csv('samples/plantilla_clasificacion_ejemplo_SINTETICO.csv')
classified=classify_dataframe(sample)
classified[['unidad_id','perfil_id','perfil_nombre','distancia_centroide']]'''),
('md','## Flujo editorial asistido (determinista)\nLos módulos funcionan como agentes especializados de datos, redacción y verificación; la aprobación humana se realiza aparte en la interfaz. No hay IA generativa externa en esta versión.'),
('code','''from src.education import build_draft,pdf_for_draft
item=build_draft(profiles.iloc[0].to_dict(),package['package_digest'])
print('validación:',item['validation'])
print('requiere aprobación humana:',item['requires_human_approval'])
print(item['draft']['resumen'])
print('bytes PDF de muestra:',len(pdf_for_draft(item,'BORRADOR — NO APROBADO','Sin revisión')))'''),
('md','## Conclusión\nPanel, modelo y generación de borradores se pueden operar en VS Code. La homologación geométrica y el despliegue público quedan expresamente fuera del MVP.')], ROOT/'ml/notebooks/06_producto_inferencia_y_fichas.ipynb')
