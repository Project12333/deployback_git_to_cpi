#!/bin/bash
set -e

PKG_ID=$1
PKG_DIR="cpi-artifacts/$PKG_ID"
OUTPUT_FILE="$PKG_DIR/Package_Summary.md"

export PATH="$HOME/.ollama/bin:$PATH"

if [ ! -d "$PKG_DIR" ]; then
  echo "Package not found: $PKG_DIR"
  exit 1
fi

FILES=$(find "$PKG_DIR" -type f \( -name "*.iflw" -o -name "*.xml" -o -name "*.groovy" -o -name "*.xslt" -o -name "iFlowContent.xml" \))

if [ -z "$FILES" ]; then
  echo "No artifacts found"
  exit 2
fi

FULL_CONTENT=""

for file in $FILES; do
  CONTENT=$(cat "$file")
  FULL_CONTENT+="

--- START ARTIFACT: $file ---
$CONTENT
--- END ARTIFACT: $file ---
"
done

SYSTEM_PROMPT=$(cat << 'EOF'
You are a senior SAP CPI Architect. Produce one consolidated Markdown documentation with EXACTLY the following sections:

1. High-level architecture
2. Purpose of each iFlow
3. Sender/Receiver systems
4. Adapter types used
5. Step-by-step flow explanation
6. Mapping logic summary
7. Groovy script explanations
8. Error handling
9. Security/authentication
10. Deployment notes
EOF
)

USER_PROMPT="Use the following artifacts to generate documentation: $FULL_CONTENT"

echo "$SYSTEM_PROMPT
$USER_PROMPT" > prompt.txt

RESULT=$(ollama run mistral < prompt.txt)

echo "$RESULT" > "$OUTPUT_FILE"
echo "Generated document: $OUTPUT_FILE"
