#!/usr/bin/env python3
import os
import re
import sys
import argparse
import requests
from pathlib import Path
from datetime import datetime
from docx import Document
from docx.shared import Inches, Pt

# ================= CONFIG =================
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "deepseek/deepseek-r1:free"

AUTHOR = "Sindhu"
VERSION = "Draft"
DATE = datetime.utcnow().strftime("%Y-%m-%d")

SAP_LOGO = "tools/logos/sap.png"
MM_LOGO = "tools/logos/motiveminds.png"

REFERER = "https://github.com/Project12333/deployback_git_to_cpi"

STRUCTURE = """
Generate SAP CPI documentation with EXACT structure:

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
"""

# ================= HELPERS =================
def sanitize(name):
    return re.sub(r'[<>:"/\\|?*]', "", name)

def find_iflows(pkg):
    roots = set()
    for r, _, files in os.walk(pkg):
        if any(f.endswith(".iflw") for f in files):
            roots.add(Path(r))
    return sorted(roots)

def read_artifacts(dirp):
    out = []
    for r, _, files in os.walk(dirp):
        for f in files:
            if f.endswith((".iflw", ".groovy", ".xslt")):
                p = Path(r) / f
                out.append(f"\n--- {p} ---\n{p.read_text(errors='ignore')}")
    return "\n".join(out)

# ================= OPENROUTER =================
def call_openrouter(prompt):
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY not found")

    headers = {
        "Authorization": f"Bearer {key}",
        "HTTP-Referer": REFERER,
        "X-Title": "CPI-iFlow-Doc-Generator",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": STRUCTURE},
            {"role": "user", "content": prompt}
        ]
    }

    r = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=120)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

# ================= DOCX =================
def write_doc(path, title, body):
    doc = Document()

    t = doc.add_table(1, 2)
    try:
        t.cell(0, 0).paragraphs[0].add_run().add_picture(SAP_LOGO, width=Inches(1.5))
        t.cell(0, 1).paragraphs[0].add_run().add_picture(MM_LOGO, width=Inches(1.5))
    except:
        pass

    p = doc.add_paragraph(title)
    p.alignment = 1
    p.runs[0].bold = True
    p.runs[0].font.size = Pt(26)

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
    ap = argparse.ArgumentParser()
    ap.add_argument("--package", required=True)
    args = ap.parse_args()

    base = Path("cpi-artifacts") / args.package
    for iflow in find_iflows(base):
        name = sanitize(iflow.name)
        print("Generating summary for:", name)

        prompt = f"iFlow Name: {name}\n\nArtifacts:\n{read_artifacts(iflow)}"
        summary = call_openrouter(prompt)

        out = iflow / "docs"
        out.mkdir(exist_ok=True)
        write_doc(out / f"{name}.docx", name, summary)

    print("✔ Documentation generated")

if __name__ == "__main__":
    main()
