#!/usr/bin/env bash
set -euo pipefail

PACKAGE="$1"

if [ -z "${PACKAGE:-}" ]; then
  echo "ERROR: Package name not provided."
  echo "Usage: ./tools/run_generate_docs.sh <PACKAGE_NAME>"
  exit 1
fi

echo "Running documentation generator for package: $PACKAGE"

python -m pip install --upgrade pip
python -m pip install requests python-docx

python tools/generate_iflow_docs.py --package "$PACKAGE"
