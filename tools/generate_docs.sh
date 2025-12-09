#!/bin/bash
set -e

PACKAGE="$1"
PKG_DIR="cpi-artifacts/$PACKAGE"

echo "Package: $PACKAGE"

# Find all .iflw files inside the package
IFLOWS=$(find "$PKG_DIR" -type f -name "*.iflw")

if [ -z "$IFLOWS" ]; then
  echo "No iFlows found in package."
  exit 1
fi

echo "Found iFlows:"
echo "$IFLOWS"

# Run documentation generator for each iFlow in parallel (4 at a time)
printf "%s\n" $IFLOWS | xargs -P 4 -I {} python3 tools/generate_docs.py "{}"

echo "Documentation and Mermaid diagram generation completed."
