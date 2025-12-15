#!/usr/bin/env python3
import os
import argparse
import requests
from pathlib import Path
from datetime import datetime, timezone
from docx import Document
from docx.shared import Inches, Pt

# ================= CONFIG =================
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "deepseek-r1:7b"

AUTHOR = "Sindhu"
VERSION = "Draft"
DATE = datetime.now(timezone.utc).strftime("%Y-%m-%d")

SAP_LOGO = "tools/logos/sap.png"
MM_LOGO = "tools/logos/motiveminds.png"

SYSTEM_PROMPT = """
You are a Senior SAP CPI Integration Architect.

Analyze the provided SAP CPI iFlow artifacts (iFlow XML, Groovy scripts, mappings).
Generate a PROFESSIONAL SAP CPI Technical Specification using EXACTLY this structure:

1. Introduction
   1.1 Purpose
   1.2 Scope

2. Integration Overview
   2.1 Integration Architecture
   2.2 Integration Components

3. Integration Scenarios
   3.1 Scenario Description
   3.2 Data Flows
   3.3 Security Requirements

4. Error Handling and Logging

5. Testing Validation

6. Reference Documents

Rules:
- Use only information inferred from the artifacts
- If details are missing, state assumptions clearly
- Do NOT invent systems
- Use enterprise-quality language
"""

# ================= HELPERS =================
def find_iflows(package_dir: Path):
    roots = set()
    for root, _, files in os.walk(package_dir):
        if "iFlowContent.xml" in files:
            roots.add(Path(root))
    return sorted(roots)

def collect_artifacts(iflow_dir: Path):
    content = ""
    for root, _, files in os.walk(iflow_dir):
        for f in files:
            if f.endswith((".iflw", ".groovy", ".xslt", ".xsl")):
                p = Path(root) / f
                try:
                    content += f"\n\n### FILE: {p.name}\n"
                    content += p.read_text(encoding="utf-8", errors="ignore")
                except:
                    pass
    return content

def call_ollama(user_prompt: str):
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.1,
        "stream": False
    }
    resp = requests.post(OLLAMA_URL, json=payload, timeout=600)
    resp.raise_for_status()
    return resp.json()["message"]["content"]

# ================= DOCX =================
def write_docx(path: Path, iflow_name: str, body: str):
    doc = Document()

    # Logos
    table = doc.add_table(1, 2)
    try:
        table.cell(0, 0).paragraphs[0].add_run().add_picture(SAP_LOGO, width=Inches(1.5))
        table.cell(0, 1).paragraphs[0].add_run().add_picture(MM_LOGO, width=Inches(1.5))
    except:
        pass

    # Title
    title = doc.add_paragraph(iflow_name)
    title.alignment = 1
    run = title.runs[0]
    run.bold = True
    run.font.size = Pt(26)

    # Metadata table
    meta = doc.add_table(3, 2)
    meta.style = "Table Grid"
    meta.cell(0, 0).text = "Author"
    meta.cell(1, 0).text = "Date"
    meta.cell(2, 0).text = "Version"
    meta.cell(0, 1).text = AUTHOR
    meta.cell(1, 1).text = DATE
    meta.cell(2, 1).text = VERSION

    doc.add_page_break()

    for line in body.split("\n"):
        doc.add_paragraph(line)

    doc.save(path)

# ================= MAIN =================
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", required=True, help="CPI package folder under cpi-artifacts/")
    args = parser.parse_args()

    base = Path("cpi-artifacts") / args.package
    if not base.exists():
        raise RuntimeError(f"Package not found: {base}")

   iflows = find_iflows(base)

print(f"📦 Package path: {base}")
print(f"📂 iFlows found: {len(iflows)}")

if not iflows:
    print("❌ No iFlows found.")
    return

for f in iflows:
    print(f"   ➜ {f}")
