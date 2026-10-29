"""QA-only stable-state orchestration, full suite and real-browser checks."""
from pathlib import Path
import datetime
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'analisis/reportes/b5'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot():
    names = subprocess.check_output(['git', 'ls-files', '--cached', '--others', '--exclude-standard'], cwd=ROOT, text=True).splitlines()
    result = {}
    for name in sorted(set(names)):
        path = ROOT / name
        if not path.is_file() or name == 'docs/14_QA_B5.md':
            continue
        if name.startswith('analisis/reportes/b5/qa_') and path.suffix not in ('.py', '.cjs'):
            continue
        result[name] = sha(path)
    return result


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    before = snapshot()
    real_db = ROOT / 'entregables/revision_local.sqlite3'
    db_before = sha(real_db) if real_db.exists() else None
    state = {'fecha':datetime.datetime.now().astimezone().isoformat(),
             'base':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
             'status':subprocess.check_output(['git','status','--short','--branch'],cwd=ROOT,text=True),
             'hashes':before,'real_db_sha256':db_before,
             'excluded_from_snapshot':['docs/14_QA_B5.md','dynamic qa_* outputs except .py/.cjs scripts']}
    (OUT/'qa_final_state.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    stages=[]
    with tempfile.TemporaryDirectory(prefix='qa-b5-final-') as temporary:
        commands=[
            ('pytest',[sys.executable,'-B','-m','pytest','-q','-p','no:cacheprovider','--basetemp',str(Path(temporary)/'pytest'),'tests']),
            ('browser',[sys.executable,'-B',str(OUT/'qa_browser_run.py')]),
            ('diff_check',['git','diff','--check','--','src','dashboard','tests','README.md','docs/00_memoria_tecnica_Hiram.md','docs/13_dashboard_analitico_B5.md']),
        ]
        for label,command in commands:
            start=time.monotonic()
            completed=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=300,
                                     env={**os.environ,'CCPC_REVIEW_DB':str(Path(temporary)/'reviews.sqlite3')})
            log='Command: '+subprocess.list2cmdline(command)+'\nExit: '+str(completed.returncode)+'\n'+completed.stdout+completed.stderr
            (OUT/f'qa_final_{label}.txt').write_text(log,encoding='utf-8')
            stages.append({'control':label,'command':command,'exit':completed.returncode,'seconds':round(time.monotonic()-start,3),
                           'log':f'analisis/reportes/b5/qa_final_{label}.txt'})
            print(json.dumps(stages[-1],ensure_ascii=False))
    after=snapshot()
    changed=[name for name in sorted(set(before)|set(after)) if before.get(name)!=after.get(name)]
    db_after=sha(real_db) if real_db.exists() else None
    result={'estado_automatizado':'PASA' if not changed and db_before==db_after and all(s['exit']==0 for s in stages) else 'FALLA',
            'controles':stages,'archivos_cambiados_durante_pasada':changed,'historial_real_sin_cambios':db_before==db_after,
            'n_hashes':len(before),'visual_review':'pending separate agent inspection; not asserted by this script'}
    (OUT/'qa_final_resultados.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))
    if result['estado_automatizado']!='PASA':
        raise SystemExit(1)


if __name__=='__main__':
    main()
