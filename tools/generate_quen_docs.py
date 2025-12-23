#!/usr/bin/env python3

import os
import sys
import requests
import xml.etree.ElementTree as ET
from pathlib import Path
from docx import Document

QUBRID_API_URL = "https://platform.qubrid.com/api/v1/qubridai/chat/completions"
QUBRID_MODEL = "Qwen/Qwen2.5-14B-Instruct"
API_KEY = os.getenv("QUBRID_API_KEY")

BASE_ARTIFACTS_DIR = Path("cpi-artifacts")
BASE_DOCS_DIR = Path("docs")

if not API_KEY:
    raise RuntimeError("QUBRID_API_KEY not set")

def call_llm(prompt):
    r = requests.post(
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
            "max_tokens": 1200,
            "stream": False
        },
        timeout=120
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

def build_prompt(name, xml):
    xml = xml[:5000]  # hard safety limit
    return f"""
Generate SAP CPI Technical Specification using this structure:

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

iFlow Name: {name}

iFlow XML:
{xml}
"""

def save_doc(text, path):
    doc = Document()
    for line in text.split("\n"):
        doc.add_paragraph(line)
    doc.save(path)

def main():
    if len(sys.argv) != 2:
        print("Usage: python generate_quen_docs.py <PACKAGE_NAME>")
        sys.exit(1)

    package = sys.argv[1]
    pkg_path = BASE_ARTIFACTS_DIR / package
    flows = list(pkg_path.rglob("*.iflw"))

    out_dir = BASE_DOCS_DIR / package
    out_dir.mkdir(parents=True, exist_ok=True)

    for f in flows:
        xml = f.read_text(encoding="utf-8")
        ET.fromstring(xml)
        doc_text = call_llm(build_prompt(f.stem, xml))
        save_doc(doc_text, out_dir / f"{f.stem}.docx")

    print("✅ DOCX files generated")

if __name__ == "__main__":
    main()
