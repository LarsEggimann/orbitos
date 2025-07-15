#!/bin/bash

set -e

echo "🔄 Updating system..."
sudo apt update && sudo apt upgrade -y

echo "📦 Installing required APT packages..."
sudo apt install -y python3 python3-pip python3-venv i2c-tools python3-smbus

echo "🧪 Creating virtual environment in .venv..."
python3 -m venv .venv

echo "✅ Activating virtual environment and installing pip packages..."
source .venv/bin/activate
pip install --upgrade pip
pip install "fastapi[standard]"


echo "🚀 Running FastAPI app (main.py)..."
fastapi run main.py --host 0.0.0.0 --port 8000
