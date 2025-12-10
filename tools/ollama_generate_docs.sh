#!/bin/bash
set -e

PACKAGE="$1"
PKG_DIR="cpi-artifacts/$PACKAGE"

echo "Package: $PACKAGE"
echo "Checking for reference template..."

if [ ! -f tools/reference.docx ]; then
  echo "❌ ERROR: tools/reference.docx not found!"
  exit 1
else
  echo "✔ reference.docx found"
fi

IFLOWS=$(find "$PKG_DIR" -type f -name "*.iflw")

if [ -z "$IFLOWS" ]; then
  echo "❌ No iFlows found in package."
  exit 1
fi

echo "Found iFlows:"
echo "$IFLOWS"

printf "%s\n" $IFLOWS | xargs -P 4 -I {} python3 tools/ollama_generate_docs.py "{}"

echo "✔ Documentation generation completed."
