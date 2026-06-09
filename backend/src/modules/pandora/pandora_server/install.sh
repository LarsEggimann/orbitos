#!/bin/bash

set -e

echo "Updating system..."
sudo apt update && sudo apt upgrade -y

echo "Installing required APT packages..."
sudo apt install -y python3 python3-pip python3-venv i2c-tools python3-smbus

echo "Creating virtual environment in .venv with system packages access..."
python3 -m venv .venv --system-site-packages

echo "Activating virtual environment and installing pip packages..."
source .venv/bin/activate
pip install --upgrade pip
pip install "fastapi[standard]"
pip install sqlmodel # sql, also installs sqlalchemy and pydantic
pip install orjson numpy pyserial pytrinamic pylablib-lightweight

# done, set finish message
echo "Setup complete!"