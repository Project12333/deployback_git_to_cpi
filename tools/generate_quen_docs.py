#!/usr/bin/env python3

import os
import sys
import requests
import xml.etree.ElementTree as ET
from pathlib import Path
from docx import Document

# =====================================================
# Qubrid Configuration (STABLE)
# =====================================================

QUBRID_API_URL = "https://platform.qubrid.com/api/v1/qubridai/chat/completions"
QUBRID_MODEL = "Qwen/Qwen2.5-7B-Instruct"  # ✅ stable on Qubrid
API_KEY = os.getenv("QUBRID_API_KEY")

BASE_ARTIFACTS_DIR = Path("cpi-artifacts")
BASE_DOCS_DIR = Path("docs")

MAX_XML_CHARS = 4000   # 🔑 hard safety limit

if not API_KEY:
    print("❌ QUBRID_API_KEY not set")
    sys.exit(1)

# =====================================================
# LLM Call (SAFE)
# =====================================================

def call_llm(prompt):
    response = requests.post(
        QUBRID_API_URL,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": QUBRID_MODEL,
            "messages": [
                {"role": "system", "content": "You are a senior SAP CPI Technical Architect."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "max_tokens": 1000,   # 🔑 safe
            "stream": False
        },
        timeout=120
    )

    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]

# =====================================================
# Prompt
# =====================================================

def build_prompt(iflow_name, xml):
    return f"""
Generate a professional SAP CPI Technical Specification document
using EXACTLY this structure:

1. Introduction
1.1 Purpose
1.2 Scope
2. Integration Overview
2.1 Integration Architecture
2.2 Integration Components
3. Integration Scenarios
3.1 Scenario Description
3.2 Data Flow
3.3 Security Requirements
4. Error Handling and Logging
5. Testing and Validation

iFlow Name: {iflow_name}

iFlow XML (trimmed):
{xml}
"""

# =====================================================
# DOCX Writer
# =====================================================

def save_doc(text, path):
    doc = Document()
    for line in text.split("\n"):
        doc.add_paragraph(line)
    doc.save(path)

# =====================================================
# Main
# =====================================================

def main():
    if len(sys.argv) != 2:
        print("Usage: python generate_quen_docs.py <PACKAGE_NAME>")
        sys.exit(1)

    package = sys.argv[1]
    package_path = BASE_ARTIFACTS_DIR / package

    if not package_path.exists():
        print(f"❌ Package not found: {package}")
        sys.exit(1)

    flows = list(package_path.rglob("*.iflw"))
    if not flows:
        print("⚠️ No iFlows found")
        return

    out_dir = BASE_DOCS_DIR / package
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n🚀 Generating docs for package: {package}\n")

    success = False

    for f in flows:
        try:
            print(f"➡ Processing {f.name}")

            raw_xml = f.read_text(encoding="utf-8")
            ET.fromstring(raw_xml)  # validate XML

            safe_xml = raw_xml[:MAX_XML_CHARS]
            prompt = build_prompt(f.stem, safe_xml)

            doc_text = call_llm(prompt)

            output = out_dir / f"{f.stem}.docx"
            save_doc(doc_text, output)

            print(f"✅ Generated {output}")
            success = True

        except Exception as e:
            print(f"⚠️ Skipped {f.name}: {e}")

    if success:
        print("\n🎉 Documentation generation completed")
    else:
        print("\n⚠️ No documents generated (all flows skipped)")

if __name__ == "__main__":
    main()
