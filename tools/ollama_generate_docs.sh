#!/bin/bash
set -e

PACKAGE="$1"
PKG_DIR="cpi-artifacts/$PACKAGE"

echo "📦 Package: $PACKAGE"

IFLOWS=$(find "$PKG_DIR" -type f -name "*.iflw")

if [ -z "$IFLOWS" ]; then
  echo "❌ No iFlows found"
  exit 1
fi

echo "📝 Found iFlows:"
echo "$IFLOWS"

export -f

# ⚡ Run 4 in parallel
echo "$IFLOWS" | xargs -n 1 -P 4 -I {} python3 tools/ollama_generate_docs.py "{}"

echo "✅ FAST generation complete"
