"""Run existing Playwright against a QA-owned server, port and temporary database."""
from pathlib import Path
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "analisis/reportes/b5"


def main():
    with tempfile.TemporaryDirectory(prefix="qa-b5-baseline-browser-") as temporary:
        with socket.socket() as candidate:
            candidate.bind(("127.0.0.1", 0))
            port = candidate.getsockname()[1]
        base = f"http://127.0.0.1:{port}/"
        env = {**os.environ, "CCPC_REVIEW_DB": str(Path(temporary) / "browser-reviews.sqlite3")}
        server_command = [sys.executable, "-B", "-m", "uvicorn", "src.dashboard_api:app", "--host", "127.0.0.1", "--port", str(port)]
        with (OUT / "qa_baseline_browser_server.txt").open("w", encoding="utf-8") as log:
            process = subprocess.Popen(server_command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT,
                                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            try:
                deadline = time.monotonic() + 25
                while True:
                    if process.poll() is not None:
                        raise RuntimeError("QA server stopped before readiness")
                    try:
                        with urllib.request.urlopen(base + "health", timeout=1) as response:
                            health = json.load(response)
                        assert health["package_version"] == "ccpc-2009-2024-k4-v1"
                        break
                    except (OSError, TimeoutError):
                        if time.monotonic() >= deadline:
                            raise RuntimeError("QA server readiness timed out")
                        time.sleep(.1)
                node = Path(os.environ["LOCALAPPDATA"]) / "ms-playwright-go/1.57.0/node.exe"
                command = [str(node), str(OUT / "qa_baseline_browser.cjs"), base]
                result = subprocess.run(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                        text=True, encoding="utf-8", errors="replace", timeout=90)
                transcript = "Server command: " + subprocess.list2cmdline(server_command) + "\n"
                transcript += "Browser command: " + subprocess.list2cmdline(command) + f"\nExit: {result.returncode}\n" + result.stdout
                (OUT / "qa_baseline_browser_transcript.txt").write_text(transcript, encoding="utf-8")
                print(transcript)
                if result.returncode:
                    raise SystemExit(result.returncode)
            finally:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)


if __name__ == "__main__":
    main()
