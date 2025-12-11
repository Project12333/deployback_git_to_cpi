#!/usr/bin/env bash
set -e

echo "Installing dependencies..."
python -m pip install --upgrade pip
python -m pip install requests python-docx

echo "Running generator..."
python tools/generate_iflow_docs.py

echo "Documentation generated."
