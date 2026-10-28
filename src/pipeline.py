"""Reproducible ETL for official INE CCPC ZIP archives (2009-2024).

Only aggregate counts. No personal data. Raw ZIPs are never edited.
Run: python -m src.pipeline --root .
"""
from __future__ import annotations
import argparse, hashlib, json, re, unicodedata, zipfile
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
import pandas as pd

YEARS=(2009,2012,2015,2018,2021,2024)
FIELDS=['AELEC','FELECCION','EDOCVE','EDONOM','MPIOCVE','MPIONOM','SECCION','TIPOSEC','DEF','DEL','SEXO','EDAD','LN','SV','NV','NS']
COUNTS=['LN','SV','NV','NS']
KEY=['EDOCVE','MPIOCVE','grupo_edad']
AGE_GROUPS=['18-24','25-34','35-44','45-59','60+']

def normalize_name(s):
    s=unicodedata.normalize('NFKD',str(s).upper())
    s=''.join(c for c in s if not unicodedata.combining(c))
    return re.sub(r'[^A-Z0-9]','',s)

def group_age(a):
    bins=[17,24,34,44,59,float('inf')]
    return pd.cut(a,bins=bins,labels=AGE_GROUPS,ordered=True)

def sha256(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for x in iter(lambda:f.read(2**20),b''):h.update(x)
    return h.hexdigest()

def scan_year(root:Path, year:int):
    folder=root/'datos'/'raw'/str(year)
    files=list(folder.glob('*.zip'))
    if len(files)!=1:raise ValueError(f'Expected one raw ZIP for {year}: {files}')
    zip_path=files[0]
    agg_frames=[]; sex_frames=[]; type_frames=[]; names=[]; per_file=[]
    rows=0; tallies=defaultdict(int); miss=Counter(); typ=Counter(); sex=Counter()
    ages_min=1e9;ages_max=-1e9
    with zipfile.ZipFile(zip_path) as z:
        inner=sorted([i for i in z.namelist() if i.lower().endswith('.csv')])
        if len(inner)!=32: raise ValueError(f'{year}: expected 32 state CSVs, found {len(inner)}')
        for j,name in enumerate(inner,1):
            # Each state is only ~15-80MB uncompressed. Read one at a time.
            with z.open(name) as fh:
                df=pd.read_csv(fh,encoding='utf-8-sig',low_memory=False,
                    dtype={'EDONOM':'string','MPIONOM':'string','TIPOSEC':'string'},
                    usecols=FIELDS)
            if set(df.columns)!=set(FIELDS):raise ValueError(f'{year} {name}: schema mismatch')
            n=len(df); rows+=n
            if df['AELEC'].nunique()!=1 or int(df['AELEC'].dropna().iloc[0])!=year:
                tallies['wrong_year']+=int((df.AELEC!=year).sum())
            for c in COUNTS:
                df[c]=pd.to_numeric(df[c],errors='coerce')
                tallies[c]+=int(df[c].sum())
            tallies['count_inconsistent']+=int((df.LN!=df.SV+df.NV+df.NS).sum())
            tallies['count_negative']+=int(df[COUNTS].lt(0).any(axis=1).sum())
            tallies['unobserved_rows']+=int((df.SV+df.NV==0).sum())
            tallies['LN_zero_rows']+=int((df.LN==0).sum())
            tallies['age_lt18_rows']+=int(df.EDAD.lt(18).sum())
            ages_min=min(ages_min,int(df.EDAD.min()));ages_max=max(ages_max,int(df.EDAD.max()))
            for c in FIELDS:
                if df[c].isna().any():miss[c]+=int(df[c].isna().sum())
            for label,value in df.groupby('SEXO',dropna=False)['LN'].sum().items():sex[str(label)]+=int(value)
            for label,value in df.groupby('TIPOSEC',dropna=False)['LN'].sum().items():typ[str(label)]+=int(value)
            df['grupo_edad']=group_age(df.EDAD)
            out_of_age=df.grupo_edad.isna()
            tallies['age_unclassified_rows']+=int(out_of_age.sum())
            if out_of_age.any():df=df.loc[~out_of_age]
            ag=df.groupby(KEY,observed=True,dropna=False)[COUNTS].sum().reset_index()
            ag['anio']=year
            agg_frames.append(ag)
            for dest,extra,store in [('sexo',['SEXO'],sex_frames),('tipo_seccion',['TIPOSEC'],type_frames)]:
                small=df.groupby(KEY+extra,observed=True,dropna=False)[COUNTS].sum().reset_index()
                small['anio']=year
                store.append(small)
            ns=df[['EDOCVE','MPIOCVE','EDONOM','MPIONOM']].drop_duplicates()
            names.append(ns)
            per_file.append(dict(file=name.split('/')[-1],rows=n,**{x:int(df[x].sum()) for x in COUNTS}))
            print(f'{year} {j:02}/32  {n:,} filas',flush=True)
    proc=root/'datos'/'processed'/str(year);proc.mkdir(parents=True,exist_ok=True)
    ag_all=pd.concat(agg_frames,ignore_index=True).groupby(KEY+['anio'],observed=True,dropna=False,as_index=False)[COUNTS].sum()
    ag_all.to_csv(proc/'municipio_edad.csv',index=False)
    pd.concat(sex_frames,ignore_index=True).groupby(KEY+['SEXO','anio'],observed=True,dropna=False,as_index=False)[COUNTS].sum().to_csv(proc/'municipio_edad_sexo.csv',index=False)
    pd.concat(type_frames,ignore_index=True).groupby(KEY+['TIPOSEC','anio'],observed=True,dropna=False,as_index=False)[COUNTS].sum().to_csv(proc/'municipio_edad_tipo_seccion.csv',index=False)
    nm=pd.concat(names,ignore_index=True).drop_duplicates().sort_values(['EDOCVE','MPIOCVE','MPIONOM'])
    nm['nombre_norm']=nm['MPIONOM'].map(normalize_name)
    nm.to_csv(proc/'municipios_nombres.csv',index=False)
    audit={'anio':year,'original_zip':str(zip_path.relative_to(root)),'sha256_zip':sha256(zip_path),'csv_estados':len(inner),'filas':rows,
           'municipios':int(ag_all[['EDOCVE','MPIOCVE']].drop_duplicates().shape[0]),
           'municipio_edad':len(ag_all),'edad_min':ages_min,'edad_max':ages_max,'conteos':{c:tallies[c] for c in COUNTS},
           'incidencias':{k:int(v) for k,v in tallies.items() if k not in COUNTS},'faltantes_por_columna':dict(miss),
           'LN_por_sexo':dict(sex),'LN_por_tipo_seccion':dict(typ),'estados':per_file}
    (proc/'auditoria.json').write_text(json.dumps(audit,indent=2,ensure_ascii=False),encoding='utf8')
    return audit

def panel(root:Path):
    p=root/'datos'/'processed'
    frames=[]; nameframes=[]
    for y in YEARS:
        a=pd.read_csv(p/str(y)/'municipio_edad.csv',dtype={'grupo_edad':'string'})
        a['observados']=a.SV+a.NV
        a['tasa']=np.where(a.observados>0,100*a.SV/a.observados,np.nan)
        a['ns_pct']=np.where(a.LN>0,100*a.NS/a.LN,np.nan)
        frames.append(a)
        n=pd.read_csv(p/str(y)/'municipios_nombres.csv')
        n=n[['EDOCVE','MPIOCVE','MPIONOM','nombre_norm']].drop_duplicates()
        n['anio']=y
        nameframes.append(n)
    names=pd.concat(nameframes,ignore_index=True)
    by_key=(names.groupby(['EDOCVE','MPIOCVE'])['nombre_norm'].nunique().rename('variantes_nombre').reset_index())
    # Strict exclusion of any key with >1 normalized municipal name across years.
    # This conservative approach excludes harmless renames alongside actual swaps;
    # it is NOT a substitute for official geographical crosswalks.
    by_key['identidad_estable_conservadora']=by_key.variantes_nombre.eq(1)
    by_key.to_csv(p/'municipios_auditoria_identidad.csv',index=False)
    names.to_csv(p/'municipios_nombres_historicos.csv',index=False)
    all_year=pd.concat(frames,ignore_index=True).merge(by_key,on=['EDOCVE','MPIOCVE'],how='left',validate='many_to_one')
    all_year.to_csv(p/'serie_municipio_edad_2009_2024.csv',index=False)
    wide=all_year.pivot_table(index=KEY,columns='anio',values=['tasa','ns_pct','observados','LN','SV','NV','NS'],aggfunc='first')
    wide.columns=[f'{field}_{year}' for field,year in wide.columns]
    wide=wide.reset_index().merge(by_key,on=['EDOCVE','MPIOCVE'],validate='many_to_one')
    pres=[2012,2018,2024]; mid=[2009,2015,2021]
    pr=[f'tasa_{y}' for y in pres];md=[f'tasa_{y}' for y in mid]
    wide['completo_6']=wide[pr+md].notna().all(axis=1)
    wide['max_ns_pct']=wide[[f'ns_pct_{y}' for y in YEARS]].max(axis=1)
    wide['min_observados']=wide[[f'observados_{y}' for y in YEARS]].min(axis=1)
    wide['apto_modelo']=wide.completo_6 & wide.identidad_estable_conservadora & wide.min_observados.ge(100) & wide.max_ns_pct.le(20)
    wide['media_presidencial']=wide[pr].mean(axis=1)
    wide['media_intermedia']=wide[md].mean(axis=1)
    wide['brecha_pres_intermedia']=wide.media_presidencial-wide.media_intermedia
    wide['cambio_presidencial_pp']=wide.tasa_2024-wide.tasa_2012
    wide['cambio_intermedia_pp']=wide.tasa_2021-wide.tasa_2009
    # 3-point series residual: center observation - linear interpolation of endpoints
    wide['curvatura_presidencial_pp']=wide.tasa_2018-(wide.tasa_2012+wide.tasa_2024)/2
    wide['curvatura_intermedia_pp']=wide.tasa_2015-(wide.tasa_2009+wide.tasa_2021)/2
    wide.to_csv(p/'matriz_modelo_6_anios.csv',index=False)
    return wide,all_year,by_key

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=Path('.'))
    parser.add_argument('--skip-extract',action='store_true');a=parser.parse_args();root=a.root.resolve()
    if not a.skip_extract:
        audits=[scan_year(root,y) for y in YEARS]
        pd.DataFrame([{**{k:v for k,v in a.items() if k not in ['conteos','incidencias','faltantes_por_columna','estados','LN_por_sexo','LN_por_tipo_seccion']},**a['conteos'],**a['incidencias']} for a in audits]).to_csv(root/'analisis'/'reportes'/'auditoria_resumen.csv',index=False)
    wide,series,keys=panel(root)
    print('PANEL',len(wide),'completos6',int(wide.completo_6.sum()),'aptos',int(wide.apto_modelo.sum()),'keys_ambiguous',int((~keys.identidad_estable_conservadora).sum()),flush=True)
if __name__=='__main__':main()
