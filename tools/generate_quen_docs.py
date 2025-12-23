#!/usr/bin/env python3

import os
import sys
import time
import requests
import xml.etree.ElementTree as ET
from pathlib import Path
from docx import Document

# =====================================================
# Qubrid Configuration
# =====================================================

QUBRID_API_URL = "https://platform.qubrid.com/api/v1/qubridai/chat/completions"
QUBRID_MODEL = "Qwen/Qwen3-Coder-30B-A3B-Instruct"
API_KEY = os.getenv("QUBRID_API_KEY")

BASE_ARTIFACTS_DIR = Path("cpi-artifacts")
BASE_DOCS_DIR = Path("docs")

if not API_KEY:
    print("❌ QUBRID_API_KEY not set")
    sys.exit(1)

# =====================================================
# Helpers
# =====================================================

def call_llm(messages, max_tokens=800, retries=3):
    for attempt in range(retries):
        try:
            r = requests.post(
                QUBRID_API_URL,
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": QUBRID_MODEL,
                    "messages": messages,
                    "temperature": 0.2,
                    "max_tokens": max_tokens,
                    "stream": False
                },
                timeout=120,
            )
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
        except Exception as e:
            if attempt == retries - 1:
                raise
            time.sleep(3)

# =====================================================
# Step 1: XML → Technical Summary
# =====================================================

def summarize_iflow(iflow_name, xml):
    # VERY aggressive trim – this is intentional
    xml = xml[:6000]

    messages = [
        {
            "role": "system",
            "content": "You are an SAP CPI expert. Summarize iFlow XML technically."
        },
        {
            "role": "user",
            "content": (
                f"Analyze the following SAP CPI iFlow XML and produce a concise "
                f"technical summary covering:\n"
                f"- Purpose\n"
                f"- Sender adapters\n"
                f"- Receiver adapters\n"
                f"- Mappings\n"
                f"- Scripts\n"
                f"- Error handling\n\n"
                f"iFlow Name: {iflow_name}\n\n"
                f"XML:\n{xml}"
            )
        }
    ]

    return call_llm(messages, max_tokens=600)

# =====================================================
# Step 2: Summary → Full Document
# =====================================================

def generate_document(iflow_name, summary):
    messages = [
        {
            "role": "system",
            "content": "You are a senior SAP CPI Technical Architect."
        },
        {
            "role": "user",
            "content": (
                "Generate a professional SAP CPI Technical Specification document "
                "using EXACTLY this structure:\n\n"
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
                f"Technical Summary:\n{summary}"
            )
        }
    ]

    return call_llm(messages, max_tokens=1200)

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

    for flow in flows:
        try:
            print(f"➡ Processing {flow.name}")

            xml = flow.read_text(encoding="utf-8")
            ET.fromstring(xml)

            summary = summarize_iflow(flow.stem, xml)
            doc_text = generate_document(flow.stem, summary)

            output = out_dir / f"{flow.stem}.docx"
            save_docx(doc_text, output)

            print(f"✅ Generated {output}")

        except Exception as e:
            print(f"❌ {flow.name}: {e}")

    print("\n🎉 Documentation generation completed")

if __name__ == "__main__":
    main()
