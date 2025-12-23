#!/usr/bin/env python3

import os
import sys
import requests
import xml.etree.ElementTree as ET
from pathlib import Path
from docx import Document

# =====================================================
# Qubrid Configuration (Qwen3-Max)
# =====================================================

QUBRID_API_URL = "https://platform.qubrid.com/api/v1/inference/qwen3-max"
API_KEY = os.getenv("QUBRID_API_KEY")

BASE_ARTIFACTS_DIR = Path("cpi-artifacts")
BASE_DOCS_DIR = Path("docs")

if not API_KEY:
    print("❌ QUBRID_API_KEY not set")
    sys.exit(1)

# =====================================================
# Package Handling
# =====================================================

def list_packages():
    return [p.name for p in BASE_ARTIFACTS_DIR.iterdir() if p.is_dir()]

def get_package_name():
    # CI mode → argument
    if len(sys.argv) == 2:
        return sys.argv[1]

    # Local interactive mode
    packages = list_packages()
    if not packages:
        raise RuntimeError("No CPI packages found")

    print("\n📦 Available CPI Packages:\n")
    for i, pkg in enumerate(packages, 1):
        print(f"{i}. {pkg}")

    choice = input("\nEnter package number: ").strip()
    if not choice.isdigit() or int(choice) not in range(1, len(packages) + 1):
        raise ValueError("Invalid package selection")

    return packages[int(choice) - 1]

# =====================================================
# Prompt
# =====================================================

def build_prompt(name, xml):
    return (
        "You are a senior SAP CPI Technical Architect.\n\n"
        "Generate a SAP CPI Technical Specification document "
        "in professional language with the following STRICT structure:\n\n"
        "1. Introduction\n"
        "   1.1 Purpose\n"
        "   1.2 Scope\n"
        "2. Integration Overview\n"
        "   2.1 Integration Architecture\n"
        "   2.2 Integration Components\n"
        "3. Integration Scenarios\n"
        "   3.1 Scenario Description\n"
        "   3.2 Data Flow\n"
        "   3.3 Security Requirements\n"
        "4. Error Handling and Logging\n"
        "5. Testing and Validation\n\n"
        f"iFlow Name: {name}\n\n"
        "SAP CPI iFlow XML:\n"
        f"{xml}"
    )

# =====================================================
# Qubrid Inference Call (CORRECT)
# =====================================================

def call_qwen(prompt):
    response = requests.post(
        QUBRID_API_URL,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "input": prompt,
            "parameters": {
                "temperature": 0.2,
                "max_new_tokens": 3500
            }
        },
        timeout=180,
    )

    response.raise_for_status()
    data = response.json()

    if "output" not in data:
        raise RuntimeError(f"Unexpected response: {data}")

    return data["output"]

# =====================================================
# DOCX Writer
# =====================================================

def save_docx(text, path):
    doc = Document()
    for line in text.split("\n"):
        doc.add_paragraph(line)
    doc.save(path)

# =====================================================
# Main
# =====================================================

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
            print(f"➡ Processing {f.name}")

            xml = f.read_text(encoding="utf-8")
            ET.fromstring(xml)  # validate XML

            doc_text = call_qwen(build_prompt(f.stem, xml))
            out = out_dir / f"{f.stem}.docx"
            save_docx(doc_text, out)

            print(f"✅ Generated {out}")

        except Exception as e:
            print(f"❌ {f.name}: {e}")

    print("\n🎉 Documentation generation completed")

if __name__ == "__main__":
    main()
