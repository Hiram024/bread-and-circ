"""B6 final acceptance on a frozen checkout; isolated writes and real exit codes."""
from pathlib import Path
import datetime
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'analisis/reportes/b6'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def snapshot():
    names=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard'],cwd=ROOT,text=True).splitlines()
    result={}
    for name in sorted(set(names)):
        path=ROOT/name
        if not path.is_file() or name=='docs/16_QA_B6.md':continue
        if name.startswith('analisis/reportes/b6/qa_') and path.suffix not in ('.py','.cjs'):continue
        result[name]=sha(path)
    return result


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    before=snapshot()
    real_db=ROOT/'entregables/revision_local.sqlite3'
    db_before=sha(real_db) if real_db.exists() else None
    state={'fecha':datetime.datetime.now().astimezone().isoformat(),
           'base':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
           'status':subprocess.check_output(['git','status','--short','--branch'],cwd=ROOT,text=True),
           'hashes':before,'real_db_sha256':db_before,
           'excluded_from_snapshot':['docs/16_QA_B6.md','dynamic qa_* outputs except .py/.cjs scripts']}
    (OUT/'qa_final_state.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    stages=[]
    with tempfile.TemporaryDirectory(prefix='qa-b6-final-') as temporary:
        commands=[
            ('pytest',[sys.executable,'-B','-m','pytest','-q','-p','no:cacheprovider','--basetemp',str(Path(temporary)/'pytest'),'tests']),
            ('traceability',[sys.executable,'-B',str(OUT/'verificar_trazabilidad.py'),'--root',str(ROOT),'--out',str(Path(temporary)/'traceability'),'--base-url','http://127.0.0.1:8501']),
            ('browser',[sys.executable,'-B',str(OUT/'qa_browser_run.py')]),
            ('diff_check',['git','diff','--check','--','dashboard','src','tests','README.md','docs/00_memoria_tecnica_Hiram.md','docs/15_aceptacion_analitica_B6.md']),
        ]
        for label,command in commands:
            start=time.monotonic()
            result=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=360,
                                  env={**os.environ,'CCPC_REVIEW_DB':str(Path(temporary)/'reviews.sqlite3')})
            log='Command: '+subprocess.list2cmdline(command)+'\nExit: '+str(result.returncode)+'\n'+result.stdout+result.stderr
            (OUT/f'qa_final_{label}.txt').write_text(log,encoding='utf-8')
            stages.append({'control':label,'command':command,'exit':result.returncode,'seconds':round(time.monotonic()-start,3),
                           'log':f'analisis/reportes/b6/qa_final_{label}.txt'})
            print(json.dumps(stages[-1],ensure_ascii=False),flush=True)
        numerical=Path(temporary)/'traceability/resultados.json'
        if numerical.exists():
            value=json.loads(numerical.read_text(encoding='utf-8'))
            (OUT/'qa_final_numerical.json').write_text(json.dumps({'fecha':value['fecha'],'estados':value['estados'],
                'reconciliacion':value['reconciliacion'],'package_digest':value['package_digest'],
                'comparacion_claves_falsos_incluidos_excluidos':value['comparacion_claves_falsos_incluidos_excluidos']},
                ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    after=snapshot()
    changed=[name for name in sorted(set(before)|set(after)) if before.get(name)!=after.get(name)]
    db_after=sha(real_db) if real_db.exists() else None
    original=json.loads((OUT/'qa_baseline.json').read_text(encoding='utf-8'))['hashes']
    prefixes=('datos/processed/','ml/modelos/','ml/resultados/b3/','analisis/reportes/b2/','analisis/reportes/b4/','analisis/reportes/b5/')
    protected={name:h for name,h in original.items() if name.startswith(prefixes)}
    protected_changed=[name for name,h in protected.items() if sha(ROOT/name)!=h]
    result={'estado_automatizado':'PASA' if not changed and not protected_changed and db_before==db_after and all(s['exit']==0 for s in stages) else 'FALLA',
            'controles':stages,'archivos_cambiados_durante_pasada':changed,'historial_real_sin_cambios':db_before==db_after,
            'n_hashes':len(before),'protected_checked':len(protected),'protected_changed':protected_changed,
            'visual_review':'Separate manual inspection recorded in qa_visual_final.json, not asserted by this script'}
    (OUT/'qa_final_resultados.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False),flush=True)
    if result['estado_automatizado']!='PASA':raise SystemExit(1)


if __name__=='__main__':main()
