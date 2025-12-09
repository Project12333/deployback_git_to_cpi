#!/bin/bash
set -e

MMD_FILE="$1"
PNG_FILE="${MMD_FILE%.mmd}.png"

echo "Converting Mermaid to PNG:"
echo "Input: $MMD_FILE"
echo "Output: $PNG_FILE"

mmdc -i "$MMD_FILE" -o "$PNG_FILE" --backgroundColor "#ffffff"
