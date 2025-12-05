#!/bin/bash
set -e

BASE="cpi-artifacts"
PACKAGES=()

# Search for folders containing .iflw
while IFS= read -r iflw; do
    pkg=$(dirname "$iflw" | sed "s|$BASE/||")
    PACKAGES+=("\"$pkg\"")
done < <(find "$BASE" -type f -name "*.iflw")

# Remove duplicates
UNIQUE=$(printf "%s\n" "${PACKAGES[@]}" | sort -u | paste -sd "," -)

echo "[$UNIQUE]"
