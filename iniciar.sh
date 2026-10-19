#!/usr/bin/env bash
# Instala lo necesario la primera vez y abre el editor en el navegador (macOS / Linux).
set -e
cd "$(dirname "$0")"
command -v ffmpeg >/dev/null || { echo "Falta ffmpeg (macOS: brew install ffmpeg | Linux: sudo apt install ffmpeg)"; exit 1; }
command -v node >/dev/null || { echo "Falta Node.js 18+ (https://nodejs.org)"; exit 1; }
[ -d .venv ] || python3 -m venv .venv
source .venv/bin/activate
python -m pip install -q -r requirements.txt
[ -d node_modules ] || { npm install && npx playwright install chromium; }
python -m app
