#!/usr/bin/env python3

import os
import sys
import requests
import xml.etree.ElementTree as ET
from pathlib import Path
from docx import Document

# =========================================================
# Configuration
# =========================================================

QUBRID_API_URL = "https://api.qubrid.com/v1/chat/completions"
MODEL_NAME = "qwen-instruct"
API_KEY = os.getenv("QUBRID_API_KEY")

BASE_ARTIFACTS_DIR = Path("cpi-artifacts")
BASE_DOCS_DIR = Path("docs")

if not API_KEY:
    print("❌ ERROR: QUBRID_API_KEY environment variable not set")
    sys.exit(1)

# =========================================================
# Helpers
# =========================================================

def list_packages():
    return [p.name for p in BASE_ARTIFACTS_DIR.iterdir() if p.is_dir()]

def ask_package(packages):
    print("\n📦 Available CPI Packages:\n")
    for idx, pkg in enumerate(packages, start=1):
        print(f"{idx}. {pkg}")

    choice = input("\nEnter package number: ").strip()

    if not choice.isdigit() or int(choice) not in range(1, len(packages) + 1):
        raise ValueError("Invalid package selection")

    return packages[int(choice) - 1]

def read_iflow_xml(iflow_path: Path) -> str:
    return iflow_path.read_text(encoding="utf-8")

def validate_xml(xml_text: str):
    ET.fromstring(xml_text)

def build_prompt(iflow_name: str, xml_content: str) -> str:
    return (
        "You are a senior SAP CPI Technical Architect.\n\n"
        "Generate a professional SAP CPI Technical Specification document.\n\n"
        "STRICT STRUCTURE:\n"
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
        f"iFlow Name: {iflow_name}\n\n"
        "iFlow XML:\n"
        f"{xml_content}"
    )

def call_qwen(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": "You are an SAP CPI expert."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,
        "max_tokens": 3500
    }

    response = requests.post(QUBRID_API_URL, headers=headers, json=payload, timeout=120)

    if response.status_code != 200:
        raise RuntimeError(response.text)

    return response.json()["choices"][0]["message"]["content"]

def save_docx(content: str, output_file: Path):
    doc = Document()
    for line in content.split("\n"):
        doc.add_paragraph(line)
    doc.save(output_file)

# =========================================================
# Main
# =========================================================

def main():
    if not BASE_ARTIFACTS_DIR.exists():
        print("❌ cpi-artifacts folder not found")
        sys.exit(1)

    packages = list_packages()

    if not packages:
        print("❌ No packages found")
        sys.exit(1)

    try:
        package_name = ask_package(packages)
    except Exception as e:
        print(f"❌ {e}")
        sys.exit(1)

    package_path = BASE_ARTIFACTS_DIR / package_name
    iflow_files = list(package_path.rglob("*.iflw"))

    if not iflow_files:
        print(f"⚠️ No iFlows found in {package_name}")
        sys.exit(0)

    output_dir = BASE_DOCS_DIR / package_name
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n🚀 Generating documentation for package: {package_name}\n")

    for iflow in iflow_files:
        try:
            print(f"➡ Processing {iflow.name}")

            xml = read_iflow_xml(iflow)
            validate_xml(xml)

            prompt = build_prompt(iflow.stem, xml)
            doc_text = call_qwen(prompt)

            output_file = output_dir / f"{iflow.stem}.docx"
            save_docx(doc_text, output_file)

            print(f"✅ Generated {output_file}")

        except Exception as e:
            print(f"❌ Failed {iflow.name}: {e}")

    print("\n🎉 All documents generated successfully")

if __name__ == "__main__":
    main()
