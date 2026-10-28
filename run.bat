@echo off
cd /d "%~dp0"
if not exist .venv (py -3 -m venv .venv)
.venv\Scripts\python.exe -m pip install -r requirements-app.txt
if errorlevel 1 exit /b 1
echo Abre http://127.0.0.1:8501 en el navegador
.venv\Scripts\python.exe -m uvicorn src.dashboard_api:app --host 127.0.0.1 --port 8501
