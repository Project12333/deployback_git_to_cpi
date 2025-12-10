#!/bin/bash
set -e

PACKAGE="$1"
PKG_DIR="cpi-artifacts/$PACKAGE"

echo "Package: $PACKAGE"

IFLOWS=$(find "$PKG_DIR" -type f -name "*.iflw")

if [ -z "$IFLOWS" ]; then
  echo "❌ No iFlows found."
  exit 1
fi

echo "Found iFlows:"
echo "$IFLOWS"

# Use 70B model
MODEL="deepseek-r1:70b"

# Process iFlows in parallel
printf "%s\n" $IFLOWS | xargs -P 4 -I {} python3 tools/ollama_generate_docs.py "{}"

echo "✅ Documentation generation completed using model: $MODEL"
