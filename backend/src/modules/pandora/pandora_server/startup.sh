#!/bin/bash

set -e

echo "Activating virtual environment..."
source .venv/bin/activate

echo "Setting up environment variables..."
export PYTHONIOENCODING=utf-8

echo "Running FastAPI app (main.py)..."
fastapi run main.py --host 0.0.0.0 --port 8000
