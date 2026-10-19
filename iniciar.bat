@echo off
REM Instala lo necesario la primera vez y abre el editor en el navegador (Windows).
cd /d "%~dp0"
where ffmpeg >nul 2>nul || (echo Falta ffmpeg. Instalalo con: winget install Gyan.FFmpeg & pause & exit /b 1)
where node >nul 2>nul || (echo Falta Node.js. Descargalo de https://nodejs.org & pause & exit /b 1)
if not exist .venv (python -m venv .venv || (echo Falta Python 3.10 o superior & pause & exit /b 1))
call .venv\Scripts\activate.bat
python -m pip install -q -r requirements.txt
if not exist node_modules (call npm install && call npx playwright install chromium)
python -m app
pause
