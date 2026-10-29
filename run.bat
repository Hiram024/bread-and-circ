@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  where py >nul 2>nul
  if errorlevel 1 (
    if exist "%APPDATA%\uv\python\cpython-3.11-windows-x86_64-none\python.exe" (
      "%APPDATA%\uv\python\cpython-3.11-windows-x86_64-none\python.exe" -m venv .venv
    ) else (
      echo Se requiere CPython 3.11 para Windows. Consulta README.md.
      exit /b 1
    )
  ) else (
    py -3.11 -m venv .venv
  )
)
if not exist .venv\Scripts\python.exe exit /b 1
.venv\Scripts\python.exe -m pip install -r requirements-app.txt
if errorlevel 1 exit /b 1
echo Abre http://127.0.0.1:8501 en el navegador
.venv\Scripts\python.exe -B -m uvicorn src.dashboard_api:app --host 127.0.0.1 --port 8501
