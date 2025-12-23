#!/usr/bin/env python3

import os
import sys
import requests
import xml.etree.ElementTree as ET
from pathlib import Path
from docx import Document

# =====================================================
# Qubrid Configuration (OpenAI-compatible API)
# =====================================================

QUBRID_API_URL = "https://platform.qubrid.com/api/v1/qubridai/chat/completions"
QUBRID_MODEL = "Qwen/Qwen3-Coder-30B-A3B-Instruct"
API_KEY = os.getenv("QUBRID_API_KEY")

BASE_ARTIFACTS_DIR = Path("cpi-artifacts")
BASE_DOCS_DIR = Path("docs")

MAX_XML_CHARS = 12000  # 🔑 critical to avoid 500 errors

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
# XML Safety
# =====================================================

def shrink_xml(xml: str) -> str:
    if len(xml) <= MAX_XML_CHARS:
        return xml
    return xml[:MAX_XML_CHARS] + "\n<!-- XML truncated to avoid payload overflow -->"

# =====================================================
# Prompt
# =====================================================

def build_prompt(iflow_name, xml):
    return (
        "You are a senior SAP CPI Technical Architect.\n\n"
        "Generate a professional SAP CPI Technical Specification document "
        "STRICTLY based on the information available in the iFlow XML.\n\n"
        "Use EXACTLY this structure:\n\n"
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
        "SAP CPI iFlow XML (trimmed if required):\n"
        f"{xml}"
    )

# =====================================================
# Qubrid API Call
# =====================================================

def call_qwen(prompt):
    response = requests.post(
        QUBRID_API_URL,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": QUBRID_MODEL,
            "messages": [
                {"role": "system", "content": "You are an SAP CPI expert."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "max_tokens": 2500,  # 🔑 reduced to stay safe
            "stream": False
        },
        timeout=180,
    )

    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]

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

    for flow in flows:
        try:
            print(f"➡ Processing {flow.name}")

            raw_xml = flow.read_text(encoding="utf-8")
            ET.fromstring(raw_xml)  # validate XML

            safe_xml = shrink_xml(raw_xml)
            doc_text = call_qwen(build_prompt(flow.stem, safe_xml))

            output_file = out_dir / f"{flow.stem}.docx"
            save_docx(doc_text, output_file)

            print(f"✅ Generated {output_file}")

        except Exception as e:
            print(f"❌ {flow.name}: {e}")

    print("\n🎉 Documentation generation completed")

if __name__ == "__main__":
    main()
