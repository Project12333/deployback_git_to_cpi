#!/bin/bash
set -e

PACKAGE="$1"
PKG_DIR="cpi-artifacts/$PACKAGE"

echo "📦 Processing package: $PACKAGE"

if [ ! -d "$PKG_DIR" ]; then
  echo "❌ ERROR: Package folder not found: $PKG_DIR"
  exit 1
fi

# Find all iFlow XML files
IFLOWS=$(find "$PKG_DIR" -type f -name "*.iflw")

if [ -z "$IFLOWS" ]; then
  echo "❌ No .iflw files found inside package."
  exit 1
fi

echo "🔍 Found iFlows:"
echo "$IFLOWS"

# Run Python generator for EACH iFlow
for f in $IFLOWS; do
  echo "➡ Generating documentation for: $f"
  python3 tools/ollama_generate_docs.py "$f"
done

echo "✔ Documentation generation completed."
