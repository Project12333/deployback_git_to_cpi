#!/bin/bash
set -e

PACKAGE_ID="$1"

echo "📦 Package ID received: $PACKAGE_ID"

# Locate the package folder
PKG_DIR="cpi-artifacts/$PACKAGE_ID"

if [ ! -d "$PKG_DIR" ]; then
  echo "❌ ERROR: Package folder not found: $PKG_DIR"
  exit 1
fi

echo "📂 Package folder found: $PKG_DIR"

# Find all iFlow files inside the package
IFLWS=$(find "$PKG_DIR" -type f -name "*.iflw")

if [ -z "$IFLWS" ]; then
  echo "❌ ERROR: No .iflw files found inside $PKG_DIR"
  exit 1
fi

echo "📝 Found iFlow files:"
echo "$IFLWS"

# Generate documentation for every iFlow
for f in $IFLWS; do
  echo "🚀 Generating documentation for: $f"
  python3 tools/ollama_generate_docs.py "$f"
done

echo "✅ Documentation generation completed."
