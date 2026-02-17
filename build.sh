#!/usr/bin/env bash
set -euo pipefail

echo "Installing build deps (PyInstaller)"
python -m pip install --upgrade pip
pip install pyinstaller

echo "Building CyberOS (one-file)"
pyinstaller --noconfirm --onefile --name CyberOS src/cyberos/main.py --add-data "icons:icons" --clean

echo "Build finished. See dist/CyberOS"