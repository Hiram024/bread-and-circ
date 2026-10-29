"""B6 browser acceptance: own local server, temporary SQLite, Chrome profiles."""
from pathlib import Path
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'analisis/reportes/b6'


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    with tempfile.TemporaryDirectory(prefix='qa-b6-browser-') as temporary:
        with socket.socket() as candidate:
            candidate.bind(('127.0.0.1',0))
            port=candidate.getsockname()[1]
        base=f'http://127.0.0.1:{port}/'
        env={**os.environ,'CCPC_REVIEW_DB':str(Path(temporary)/'reviews.sqlite3')}
        server_command=[sys.executable,'-B','-m','uvicorn','src.dashboard_api:app','--host','127.0.0.1','--port',str(port)]
        with (OUT/'qa_browser_server.txt').open('w',encoding='utf-8') as log:
            process=subprocess.Popen(server_command,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,
                                     creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            try:
                deadline=time.monotonic()+30
                while True:
                    if process.poll() is not None:raise RuntimeError('QA server stopped before readiness')
                    try:
                        with urlopen(base+'health',timeout=1) as response:health=json.load(response)
                        assert health['package_version']=='ccpc-2009-2024-k4-v1'
                        break
                    except (OSError,TimeoutError):
                        if time.monotonic()>=deadline:raise RuntimeError('QA server readiness timed out')
                        time.sleep(.1)
                node=Path(os.environ['LOCALAPPDATA'])/'ms-playwright-go/1.57.0/node.exe'
                for label,script in [('zoom','qa_browser.cjs'),('regression','qa_b5_regression.cjs')]:
                    command=[str(node),str(OUT/script),base]
                    result=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,text=True,
                                          encoding='utf-8',errors='replace',timeout=180)
                    transcript='Server: '+subprocess.list2cmdline(server_command)+'\nCommand: '+subprocess.list2cmdline(command)+'\nExit: '+str(result.returncode)+'\n'+result.stdout+result.stderr
                    (OUT/f'qa_{label}_transcript.txt').write_text(transcript,encoding='utf-8')
                    print(f'{label}: exit {result.returncode}; '+str(OUT/f'qa_{label}_transcript.txt'))
                    if result.returncode:raise SystemExit(result.returncode)
            finally:
                process.terminate()
                try:process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill();process.wait(timeout=5)


if __name__=='__main__':main()
