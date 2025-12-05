#!/bin/bash
set -e

PACKAGE="$1"
PKG_DIR="cpi-artifacts/$PACKAGE"

echo "📦 Package ID: $PACKAGE"

if [ ! -d "$PKG_DIR" ]; then
  echo "❌ ERROR: Package folder not found: $PKG_DIR"
  exit 1
fi

# Search for all .iflw files in the package
IFLOWS=$(find "$PKG_DIR" -type f -name "*.iflw")

if [ -z "$IFLOWS" ]; then
  echo "❌ No .iflw files found in $PKG_DIR"
  exit 1
fi

echo "📝 Found iFlows:"
echo "$IFLOWS"

# Process each iFlow file
for f in $IFLOWS; do
  echo "🚀 Generating documentation for: $f"
  python3 tools/ollama_generate_docs.py "$f"
done

echo "✅ Completed documentation generation."
