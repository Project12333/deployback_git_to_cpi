#!/usr/bin/env python3

import os
import sys
import requests
import xml.etree.ElementTree as ET
from pathlib import Path
from docx import Document

QUBRID_API_URL = "https://platform.qubrid.com/api/v1/chat/completions"
MODEL_NAME = "qwen-instruct"
API_KEY = os.getenv("QUBRID_API_KEY")

BASE_ARTIFACTS_DIR = Path("cpi-artifacts")
BASE_DOCS_DIR = Path("docs")

if not API_KEY:
    print("❌ QUBRID_API_KEY not set")
    sys.exit(1)

def list_packages():
    return [p.name for p in BASE_ARTIFACTS_DIR.iterdir() if p.is_dir()]

def get_package_name():
    # CI mode → argument
    if len(sys.argv) == 2:
        return sys.argv[1]

    # Local mode → interactive
    packages = list_packages()
    print("\n📦 Available CPI Packages:\n")
    for i, pkg in enumerate(packages, 1):
        print(f"{i}. {pkg}")

    choice = input("\nEnter package number: ").strip()
    if not choice.isdigit():
        raise ValueError("Invalid selection")

    return packages[int(choice) - 1]

def build_prompt(name, xml):
    return (
        "You are a senior SAP CPI Technical Architect.\n\n"
        "Generate a SAP CPI Technical Specification document with this structure:\n"
        "1. Introduction\n"
        "1.1 Purpose\n"
        "1.2 Scope\n"
        "2. Integration Overview\n"
        "2.1 Integration Architecture\n"
        "2.2 Integration Components\n"
        "3. Integration Scenarios\n"
        "3.1 Scenario Description\n"
        "3.2 Data Flow\n"
        "3.3 Security Requirements\n"
        "4. Error Handling and Logging\n"
        "5. Testing and Validation\n\n"
        f"iFlow Name: {name}\n\n"
        f"iFlow XML:\n{xml}"
    )

def call_qwen(prompt):
    r = requests.post(
        QUBRID_API_URL,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": MODEL_NAME,
            "messages": [
                {"role": "system", "content": "You are an SAP CPI expert."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 3500,
        },
        timeout=120,
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

def save_docx(text, path):
    doc = Document()
    for line in text.split("\n"):
        doc.add_paragraph(line)
    doc.save(path)

def main():
    package = get_package_name()
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

    for f in flows:
        try:
            xml = f.read_text(encoding="utf-8")
            ET.fromstring(xml)

            doc_text = call_qwen(build_prompt(f.stem, xml))
            out = out_dir / f"{f.stem}.docx"
            save_docx(doc_text, out)

            print(f"✅ {out}")
        except Exception as e:
            print(f"❌ {f.name}: {e}")

if __name__ == "__main__":
    main()
