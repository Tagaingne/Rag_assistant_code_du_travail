#!/bin/sh
set -e

VECTOR_STORE_FILE="data/vector_store/chroma.sqlite3"

if [ ! -f "$VECTOR_STORE_FILE" ]; then
    echo "Base vectorielle absente : indexation initiale (peut prendre quelques minutes)..."
    python index.py
fi

exec uvicorn fastapi_app:app --host 0.0.0.0 --port 8000
