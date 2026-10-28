"""Reproducible, aggregate-level exploratory unsupervised segmentation."""
from __future__ import annotations
import argparse,json,joblib
from pathlib import Path
import numpy as np,pandas as pd
from sklearn.preprocessing import StandardScaler,RobustScaler
from sklearn.cluster import KMeans,Birch
from sklearn.mixture import GaussianMixture
from sklearn.metrics import silhouette_score,davies_bouldin_score,calinski_harabasz_score,adjusted_rand_score

FEATS=['media_presidencial','media_intermedia','cambio_presidencial_pp','cambio_intermedia_pp']

def fit_algorithm(name,k,z,seed=42):
    if name=='KMeans': model=KMeans(n_clusters=k,n_init=20,random_state=seed)
    elif name=='GaussianMixture':model=GaussianMixture(n_components=k,covariance_type='full',n_init=3,reg_covar=1e-4,random_state=seed)
    elif name=='Birch':model=Birch(n_clusters=k,threshold=0.35)
    else:raise ValueError(name)
    lab=model.fit_predict(z)
    return model,lab

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=Path('.'));args=ap.parse_args()
    root=args.root.resolve();src=root/'datos'/'processed'/'matriz_modelo_6_anios.csv'
    dataset=pd.read_csv(src)
    good=dataset.loc[dataset.apto_modelo].copy().reset_index(drop=True)
    if good.empty:raise RuntimeError('No valid six-election observations')
    x=good[FEATS].to_numpy(dtype=float)
    if not np.isfinite(x).all():raise ValueError('Nonfinite features present')
    scaler=StandardScaler().fit(x);z=scaler.transform(x)
    result=[];label_store={}
    for name in ['KMeans','GaussianMixture','Birch']:
        for k in [4,5,6]:
            model,lab=fit_algorithm(name,k,z)
            cnt=np.bincount(lab)
            if len(cnt)<k or not cnt.min(): continue
            result.append({'algoritmo':name,'k':k,'silhouette_muestra_2000':float(silhouette_score(z,lab,sample_size=min(2000,len(z)),random_state=64)),
               'davies_bouldin':float(davies_bouldin_score(z,lab)),
               'calinski_harabasz':float(calinski_harabasz_score(z,lab)),
               'min_fraccion':float(cnt.min()/len(z)),'max_fraccion':float(cnt.max()/len(z)),
               'BIC':float(model.bic(z)) if name=='GaussianMixture' else None})
            label_store[(name,k)]=lab
            print('MODEL',name,k,'silhouette',round(result[-1]['silhouette_muestra_2000'],4),flush=True)
    out=root/'ml'/'resultados';out.mkdir(parents=True,exist_ok=True)
    comp=pd.DataFrame(result).sort_values(['silhouette_muestra_2000'],ascending=False)
    comp.to_csv(out/'comparacion_modelos.csv',index=False)
    stability=[]
    for k in [4,5,6]:
        labs=[fit_algorithm('KMeans',k,z,seed)[1] for seed in [7,42,98]]
        stability.append({'algoritmo':'KMeans','k':k,'ARI_semillas_media':float(np.mean([adjusted_rand_score(labs[i],labs[j]) for i,j in [(0,1),(0,2),(1,2)]]))})
    pd.DataFrame(stability).to_csv(out/'estabilidad_semillas.csv',index=False)
    # Sensitivity of assignments for k=5 to scaling choices and stricter NS filter.
    stable=[]
    for k in [4,5,6]:
        base=label_store[('KMeans',k)]
        robust=RobustScaler().fit_transform(x)
        lab_robust=KMeans(n_clusters=k,n_init=20,random_state=42).fit_predict(robust)
        stricter=good.max_ns_pct.le(10).to_numpy()
        if stricter.sum()>k*10:
            lab_strict=KMeans(n_clusters=k,n_init=20,random_state=42).fit_predict(z[stricter])
            ari_strict=adjusted_rand_score(base[stricter],lab_strict)
        else:ari_strict=np.nan
        stable.append({'k':k,'ARI_escalador_robusto_vs_estandar':float(adjusted_rand_score(base,lab_robust)),
             'ARI_NS_hasta_10_por_ciento':float(ari_strict),'unidades_NS_10pct':int(stricter.sum())})
    pd.DataFrame(stable).to_csv(out/'sensibilidad.csv',index=False)
    # k=5 is a demonstration aligned with contest deliverable, not objectively optimal.
    chosen_k=5
    model=KMeans(n_clusters=chosen_k,n_init=30,random_state=42).fit(z)
    lab=model.labels_
    centroids=pd.DataFrame(scaler.inverse_transform(model.cluster_centers_),columns=FEATS)
    # deterministic identifiers sorted by participation mean across two election types
    sorted_ids=centroids.assign(media_total=centroids[['media_presidencial','media_intermedia']].mean(axis=1)).sort_values('media_total').index.to_list()
    mapping={int(old):i+1 for i,old in enumerate(sorted_ids)}
    good['perfil_id']=pd.Series(lab).map(mapping).to_numpy()
    good['municipio_identificador']=good.EDOCVE.astype(str).str.zfill(2)+'-'+good.MPIOCVE.astype(str).str.zfill(3)
    good['distancia_centroide']=np.linalg.norm(z-model.cluster_centers_[lab],axis=1)
    good.to_csv(out/'observaciones_segmentadas.csv',index=False)
    profiles=(good.groupby('perfil_id',as_index=False).agg(n_unidades=('perfil_id','size'),
      municipios=('municipio_identificador','nunique'),media_presidencial=('media_presidencial','mean'),
      media_intermedia=('media_intermedia','mean'),brecha_pp=('brecha_pres_intermedia','mean'),
      cambio_presidencial_pp=('cambio_presidencial_pp','mean'),cambio_intermedia_pp=('cambio_intermedia_pp','mean'),
      mediana_distancia=('distancia_centroide','median'), LN_2024=('LN_2024','sum')))
    profiles['fraccion_unidades']=profiles.n_unidades/len(good)
    profiles.to_csv(out/'fichas_perfiles_exploratorias.csv',index=False)
    age=pd.crosstab(good.grupo_edad,good.perfil_id).reindex(['18-24','25-34','35-44','45-59','60+'])
    age.to_csv(out/'perfiles_por_edad.csv')
    # Holdout diagnostic: train 2009-2021 only, inspect 2024 outcome.
    past=good[['tasa_2009','tasa_2012','tasa_2015','tasa_2018','tasa_2021']].copy()
    prior=np.column_stack([(past.tasa_2012+past.tasa_2018)/2,
                            (past.tasa_2009+past.tasa_2015+past.tasa_2021)/3,
                            past.tasa_2018-past.tasa_2012,
                            past.tasa_2021-past.tasa_2009])
    past_scaler=StandardScaler().fit(prior)
    labels_prior=KMeans(n_clusters=5,random_state=42,n_init=20).fit_predict(past_scaler.transform(prior))
    # eta^2 = variation in 2024 rates explained by past-group membership descriptively.
    y=good.tasa_2024.to_numpy(); grand=y.mean();ss_tot=((y-grand)**2).sum()
    ss_between=sum(((y[labels_prior==c].mean()-grand)**2)*(labels_prior==c).sum() for c in range(5))
    hold={'metodo':'Clustering solo con 2009-2021; tasa de 2024 NO usada en ajuste','n':len(y),
        'eta_cuadrada_tasa_2024':float(ss_between/ss_tot),
        '2024_media_por_cluster_previo':{str(c):float(y[labels_prior==c].mean()) for c in range(5)}}
    (out/'validacion_temporal_descriptiva.json').write_text(json.dumps(hold,indent=2,ensure_ascii=False),encoding='utf-8')
    # Saved joblib is trusted local output; never load arbitrary external joblib files.
    artifact={'model':model,'scaler':scaler,'features':FEATS,'k':chosen_k,'label_mapping':mapping,
       'scope':'Grupos estadísticos agregados municipio x edad; entrenamiento 2009-2024','filters':{'min_observados_por_anio':100,'max_ns_pct':20,'6_years':True,'nombre_municipal_estable':True}}
    joblib.dump(artifact,root/'ml'/'modelos'/'kmeans5_exploratorio.joblib')
    meta={'n_validas':len(good),'n_municipios':good[['EDOCVE','MPIOCVE']].drop_duplicates().shape[0],
          'n_panel':len(dataset),'n_completo6':int(dataset.completo_6.sum()),'n_nombre_estable':int(dataset.identidad_estable_conservadora.sum()),
          'LN_2024_validas':int(good.LN_2024.sum()),'LN_2024_total_panel':int(dataset.LN_2024.sum()),
          'cobertura_LN_2024_pct':float(100*good.LN_2024.sum()/dataset.LN_2024.sum()),
          'features':FEATS,'filtros':'completo 6 + nombres municipales estables + observados >= 100 por año + NS <=20% todos los años',
          'k_demo':chosen_k,'best_silhouette':comp.iloc[0][['algoritmo','k','silhouette_muestra_2000']].to_dict()}
    (out/'resumen_modelado.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf8')
    print('MODEL_DONE',meta,flush=True)
if __name__=='__main__':main()
