#!/usr/bin/env python3
import os
import argparse
import requests
from pathlib import Path
from datetime import datetime
from docx import Document
from docx.shared import Inches, Pt

# ================= CONFIG =================
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "deepseek-r1:7b"

AUTHOR = "Sindhu"
VERSION = "Draft"
DATE = datetime.utcnow().strftime("%Y-%m-%d")

SAP_LOGO = "tools/logos/sap.png"
MM_LOGO = "tools/logos/motiveminds.png"

SYSTEM_PROMPT = """
You are a Senior SAP CPI Integration Architect.

You will be given COMPLETE SAP CPI iFlow artifacts:
- iFlow XML (.iflw)
- Groovy scripts
- Message mappings

Your task:
Analyze the integration flow in depth and generate a PROFESSIONAL
SAP CPI Technical Specification using EXACTLY this structure:

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
- Use ONLY information inferred from the artifacts
- Do NOT hallucinate systems
- If something is missing, state assumptions clearly
- Write clear, enterprise-grade documentation
"""

# ================= HELPERS =================
def find_iflows(pkg):
    roots = set()
    for r, _, files in os.walk(pkg):
        if any(f.endswith(".iflw") for f in files):
            roots.add(Path(r))
    return sorted(roots)

def collect_artifacts(iflow_dir):
    text = ""
    for r, _, files in os.walk(iflow_dir):
        for f in files:
            if f.endswith((".iflw", ".groovy", ".xslt", ".xsl")):
                p = Path(r) / f
                try:
                    text += f"\n\n### FILE: {p.name}\n{p.read_text(errors='ignore')}"
                except:
                    pass
    return text

def call_ollama(prompt):
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,
        "stream": False
    }
    r = requests.post(OLLAMA_URL, json=payload, timeout=600)
    r.raise_for_status()
    return r.json()["message"]["content"]

# ================= DOCX =================
def write_docx(path, iflow_name, body):
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
    title.runs[0].bold = True
    title.runs[0].font.size = Pt(26)

    # Meta
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
    parser.add_argument("--package", required=True)
    args = parser.parse_args()

    base = Path("cpi-artifacts") / args.package
    iflows = find_iflows(base)

    for iflow in iflows:
        name = iflow.name
        print("Generating AI documentation for:", name)

        artifacts = collect_artifacts(iflow)
        prompt = f"iFlow Name: {name}\n\nArtifacts:\n{artifacts}"

        ai_text = call_ollama(prompt)

        out = iflow / "docs"
        out.mkdir(exist_ok=True)
        write_docx(out / f"{name}.docx", name, ai_text)

    print("✔ AI Documentation generated successfully")

if __name__ == "__main__":
    main()
