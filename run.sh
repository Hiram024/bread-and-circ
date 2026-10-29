#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [ ! -d .venv ]; then python3.11 -m venv .venv; fi
.venv/bin/python -m pip install -r requirements-app.txt
printf '\nAbre http://127.0.0.1:8501 en el navegador. Para detener: Ctrl+C\n'
.venv/bin/python -B -m uvicorn src.dashboard_api:app --host 127.0.0.1 --port 8501
