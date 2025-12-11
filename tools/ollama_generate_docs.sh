#!/bin/bash
set -e

PACKAGE="$1"
PKG_DIR="cpi-artifacts/$PACKAGE"

echo "📦 Processing package: $PACKAGE"

IFLOWS=$(find "$PKG_DIR" -type f -name "*.iflw")

if [ -z "$IFLOWS" ]; then
  echo "❌ No iFlows found in: $PKG_DIR"
  exit 1
fi

echo "🔍 Found iFlows:"
echo "$IFLOWS"

for IFLOW in $IFLOWS; do
  echo "➡ Generating documentation for: $IFLOW"
  python3 tools/ollama_generate_docs.py "$IFLOW"
done

echo "✔ Documentation generation completed."
