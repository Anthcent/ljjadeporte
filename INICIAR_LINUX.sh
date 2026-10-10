#!/usr/bin/env sh
set -e
cd "$(dirname "$0")"
python3 app.py init
printf '\nAbre http://127.0.0.1:8000 en tu navegador\n'
python3 app.py
