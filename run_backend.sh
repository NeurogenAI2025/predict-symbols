#!/bin/bash

# Calea absolută către virtualenv-ul tău
VENV_PATH="/home/NRG_Live/tfenv310"

# Directorul aplicației
APP_DIR="/home/NRG_Live/NRG"

# Numele fișierului FastAPI (ex: main.py)
APP_FILE="main.py"

echo "🔄 Activare mediu virtual Python..."
source "$VENV_PATH/bin/activate"

cd "$APP_DIR" || exit 1

echo "🚀 Pornire FastAPI din $APP_FILE ..."
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

