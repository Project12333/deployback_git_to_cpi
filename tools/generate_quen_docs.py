#!/usr/bin/env python3

import os
import sys
import requests
import xml.etree.ElementTree as ET
from pathlib import Path

# ===============================
# Configuration
# ===============================

QUBRID_API_URL = "https://api.qubrid.com/v1/chat/completions"
MODEL_NAME = "qwen-instruct"
API_KEY = os.getenv("QUBRID_API_KEY")

if not API_KEY:
    print("❌ ERROR: QUBRID_API_KEY environment variable not set")
    sys.exit(1)

# ===============================
# Helpers
# ===============================

def read_iflow_xml(iflow_path: Path) -> str:
    try:
        return iflow_path.read_text(encoding="utf-8")
    except Exception as e:
        raise RuntimeError(f"Failed to read iFlow file: {e}")

def validate_xml(xml_text: str) -> None:
    try:
        ET.fromstring(xml_text)
    except Exception as e:
        raise RuntimeError(f"Invalid iFlow XML: {e}")

def build_prompt(iflow_name: str, xml_content: str) -> str:
    return (
        "You are a senior SAP CPI Technical Architect.\n\n"
        "Analyze the following SAP CPI iFlow XML and generate a professional "
        "technical documentation in Markdown format.\n\n"
        "STRICT STRUCTURE (do not add extra sections):\n"
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
        "max_tokens": 3000
    }

    response = requests.post(QUBRID_API_URL, headers=headers, json=payload, timeout=120)

    if response.status_code != 200:
        raise RuntimeError(
            f"Qubrid API error {response.status_code}: {response.text}"
        )

    data = response.json()
    return data["choices"][0]["message"]["content"]

# ===============================
# Main
# ===============================

def main():
    if len(sys.argv) != 2:
        print("Usage: python generate_quen_docs.py <path_to_iflw>")
        sys.exit(1)

    iflow_path = Path(sys.argv[1])

    if not iflow_path.exists():
        print(f"❌ iFlow file not found: {iflow_path}")
        sys.exit(1)

    print(f"📄 Reading iFlow: {iflow_path.name}")

    xml_content = read_iflow_xml(iflow_path)
    validate_xml(xml_content)

    prompt = build_prompt(iflow_path.stem, xml_content)

    print("Sending request to Qwen (Qubrid)...")
    doc_md = call_qwen(prompt)

    output_dir = Path("docs")
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / f"{iflow_path.stem}.md"
    output_file.write_text(doc_md, encoding="utf-8")

    print("Documentation generated successfully")
    print(f"📄 Output file: {output_file}")

if __name__ == "__main__":
    main()
