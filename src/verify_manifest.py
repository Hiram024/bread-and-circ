"""Verify all files against SHA256 manifest after extracting project + raw packs."""
import hashlib,json,sys
from pathlib import Path
root=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
m=json.loads((root/'MANIFEST_SHA256.json').read_text())
missing=[];wrong=[]
for f in m['files']:
 p=root/f['path']
 if not p.exists():missing.append(f['path']);continue
 h=hashlib.sha256()
 with p.open('rb') as src:
  for b in iter(lambda:src.read(1024*1024),b''):h.update(b)
 if h.hexdigest()!=f['sha256']:wrong.append(f['path'])
print('Verificados:',len(m['files'])-len(missing)-len(wrong),'| faltantes:',len(missing),'| errores:',len(wrong))
if missing:print('Faltantes:',missing[:20])
if wrong:print('Errores SHA:',wrong[:20])
sys.exit(1 if missing or wrong else 0)
