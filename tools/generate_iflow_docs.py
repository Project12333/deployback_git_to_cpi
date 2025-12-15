#!/usr/bin/env python3
import os
import argparse
import requests
from pathlib import Path
from datetime import datetime, timezone
from docx import Document
from docx.shared import Inches, Pt

# ================= CONFIG =================
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5:7b"

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
    iflow_dirs = set()
    for root, _, files in os.walk(package_dir):
        for f in files:
            if f.endswith(".iflw"):
                iflow_dirs.add(Path(root))
    return sorted(iflow_dirs)


def collect_artifacts(iflow_dir: Path):
    content = ""
    for root, _, files in os.walk(iflow_dir):
        for f in files:
            if f.endswith((".iflw", ".groovy", ".xslt", ".xsl")):
                p = Path(root) / f
                try:
                    content += "\n\n### FILE: " + p.name + "\n"
                    content += p.read_text(encoding="utf-8", errors="ignore")
                except Exception as e:
                    print("WARN: Could not read file:", p, e)
    return content


def call_ollama(user_prompt: str):
    payload = {
        "model": MODEL,
        "prompt": SYSTEM_PROMPT + "\n\n" + user_prompt,
        "stream": False,
        "options": {"temperature": 0.1}
    }

    print("Sending request to Ollama...")
    resp = requests.post(OLLAMA_URL, json=payload, timeout=600)
    resp.raise_for_status()
    return resp.json()["response"]


# ================= DOCX =================
def write_docx(doc_path: Path, iflow_name: str, body: str):
    doc = Document()

    # Logos
    table = doc.add_table(1, 2)
    try:
        table.cell(0, 0).paragraphs[0].add_run().add_picture(
            SAP_LOGO, width=Inches(1.5)
        )
        table.cell(0, 1).paragraphs[0].add_run().add_picture(
            MM_LOGO, width=Inches(1.5)
        )
    except Exception as e:
        print("WARN: Logo load failed:", e)

    # Title
    title = doc.add_paragraph(iflow_name)
    title.alignment = 1
    run = title.runs[0]
    run.bold = True
    run.font.size = Pt(26)

    # Metadata
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

    doc.save(doc_path)


# ================= MAIN =================
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", required=True)
    args = parser.parse_args()

    base = Path("cpi-artifacts") / args.package
    print("Package path:", base)

    if not base.exists():
        print("ERROR: Package not found")
        return

    iflows = find_iflows(base)
    print("iFlows found:", len(iflows))

    if not iflows:
        print("ERROR: No iFlows detected")
        return

    for iflow_dir in iflows:
        iflow_name = iflow_dir.name
        print("Processing iFlow:", iflow_name)

        artifacts = collect_artifacts(iflow_dir)
        print("Artifact size:", len(artifacts))

        prompt = "iFlow Name: " + iflow_name + "\n\nArtifacts:\n" + artifacts
        ai_text = call_ollama(prompt)

        docs_dir = iflow_dir / "docs"
        docs_dir.mkdir(exist_ok=True)

        doc_path = docs_dir / f"{iflow_name}.docx"
        write_docx(doc_path, iflow_name, ai_text)

        print("Document generated:", doc_path)

    print("Documentation generation completed successfully")


if __name__ == "__main__":
    main()
