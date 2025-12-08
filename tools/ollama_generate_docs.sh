#!/bin/bash
set -e

PACKAGE="$1"
PKG_DIR="cpi-artifacts/$PACKAGE"

echo "Package: $PACKAGE"

IFLOWS=$(find "$PKG_DIR" -type f -name "*.iflw")

if [ -z "$IFLOWS" ]; then
  echo "No iFlows found in package."
  exit 1
fi

echo "Found iFlows:"
echo "$IFLOWS"

# Correct xargs parallel execution
printf "%s\n" $IFLOWS | xargs -P 4 -I {} python3 tools/ollama_generate_docs.py "{}"

echo "Documentation generation completed."
