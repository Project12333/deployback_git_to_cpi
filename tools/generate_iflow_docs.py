#!/usr/bin/env python3
"""
tools/generate_iflow_docs.py

Generates one DOCX (and MD) per iFlow folder found under cpi-artifacts/<PACKAGE>.
- File name uses the iFlow display name extracted from the .iflw file (Option A).
- Cover page contains logos, title, hardcoded Author/Date/Version.
- Table of contents page (static).
- AI-generated documentation from DeepSeek (6-section template).
"""

import os
import re
import sys
import argparse
import requests
from pathlib import Path
from datetime import datetime

from docx import Document
from docx.shared import Inches, Pt, RGBColor

# --------------------------
# CONFIGURATION
# --------------------------
HARDCODE_AUTHOR = "Sindhu"
HARDCODE_DATE = datetime.utcnow().strftime("%Y-%m-%d")
HARDCODE_VERSION = "Draft"

MODEL_NAME = "deepseek-r1"
OLLAMA_URL = "http://localhost:11434/api/generate"

SAP_LOGO = "tools/logos/sap.png"
MM_LOGO = "tools/logos/motiveminds.png"

PROMPT_PATH = Path("tools/prompts/system_prompt.txt")
if PROMPT_PATH.exists():
    SYSTEM_PROMPT = PROMPT_PATH.read_text(encoding="utf-8", errors="ignore")
else:
    SYSTEM_PROMPT = """
You are an SAP CPI Documentation Generator.

Generate the iFlow documentation using EXACTLY this structure:

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

RULES:
- Use all artifacts to produce meaningful details.
- Infer details where needed and mention assumptions.
- Always produce all 6 sections.
"""

# --------------------------
# UTILITY FUNCTIONS
# --------------------------

def sanitize_filename(name: str):
    name = re.sub(r'\s+', '_', name)
    name = re.sub(r'[<>:"/\\|?*]+', '', name)
    return name[:200]


def find_iflows(package_dir: Path):
    roots = set()
    for root, _, files in os.walk(package_dir):
        for f in files:
            if f.endswith(".iflw") or f == "iFlowContent.xml":
                roots.add(Path(root))
                break
    return sorted(roots)


def collect_artifacts(iflow_dir: Path):
    parts = []
    for root, _, files in os.walk(iflow_dir):
        for f in files:
            if f.endswith((".iflw", ".groovy", ".xslt")) or f == "iFlowContent.xml":
                p = Path(root) / f
                try:
                    txt = p.read_text(encoding="utf-8", errors="replace")
                except:
                    txt = "[UNREADABLE FILE]"
                parts.append(f"\n--- START ARTIFACT: {p} ---\n{txt}\n--- END ARTIFACT: {p} ---\n")
    return "\n".join(parts)


def find_iflw_file(iflow_dir: Path):
    for file in iflow_dir.glob("*.iflw"):
        return file
    xml_file = iflow_dir / "iFlowContent.xml"
    if xml_file.exists():
        return xml_file
    return None


def extract_iflow_display_name_from_iflw(iflw_path: Path):
    try:
        text = iflw_path.read_text(encoding="utf-8", errors="replace")
    except:
        return sanitize_filename(iflw_path.stem)

    # Try name=""
    m = re.search(r'IntegrationFlow[^>]*name="(.*?)"', text, re.IGNORECASE)
    if m:
        return sanitize_filename(m.group(1))

    # Try id=""
    m = re.search(r'IntegrationFlow[^>]*id="(.*?)"', text, re.IGNORECASE)
    if m:
        return sanitize_filename(m.group(1))

    return sanitize_filename(iflw_path.stem)


def call_ollama(system_prompt: str, user_prompt: str):
    """
    Correct Ollama call handling DeepSeek R1.
    """
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "stream": False
    }

    resp = requests.post(OLLAMA_URL, json=payload, timeout=600)
    resp.raise_for_status()

    data = resp.json()

    # Try OpenAI-style response
    if "choices" in data:
        try:
            return data["choices"][0]["message"]["content"]
        except:
            pass

    # Direct "content"
    if "content" in data and isinstance(data["content"], str):
        return data["content"]

    # Some models return {"response": "..."}
    if "response" in data and isinstance(data["response"], str):
        return data["response"]

    # DeepSeek sometimes returns {"message": {"content": "..."}}
    if "message" in data and "content" in data["message"]:
        return data["message"]["content"]

    return "[EMPTY_RESPONSE_FROM_MODEL]"


# --------------------------
# DOCUMENT GENERATION
# --------------------------

def write_docx(doc_path: Path, ai_content: str, iflow_name: str):
    doc = Document()

    # ---- COVER PAGE ----
    header = doc.add_table(1, 2)
    row = header.rows[0].cells
    try:
        row[0].paragraphs[0].add_run().add_picture(SAP_LOGO, width=Inches(1.5))
    except:
        pass
    try:
        row[1].paragraphs[0].add_run().add_picture(MM_LOGO, width=Inches(1.5))
    except:
        pass

    doc.add_paragraph("\n\n\n")

    title = doc.add_paragraph()
    title.alignment = 1
    r = title.add_run(iflow_name)
    r.bold = True
    r.font.size = Pt(28)
    try:
        r.font.color.rgb = RGBColor(31, 78, 121)
    except:
        pass

    doc.add_paragraph("\n\n")

    info = doc.add_table(3, 2)
    info.style = "Table Grid"

    info.cell(0, 0).text = "Author:"
    info.cell(1, 0).text = "Date:"
    info.cell(2, 0).text = "Version:"

    info.cell(0, 1).text = HARDCODE_AUTHOR
    info.cell(1, 1).text = HARDCODE_DATE
    info.cell(2, 1).text = HARDCODE_VERSION

    doc.add_page_break()

    # ---- TABLE OF CONTENTS ----
    toc_title = doc.add_paragraph()
    toc_title.add_run("Table of Contents").bold = True
    toc_title.runs[0].font.size = Pt(14)

    toc = """
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
    for line in toc.split("\n"):
        doc.add_paragraph(line)

    doc.add_page_break()

    # ---- AI-GENERATED CONTENT ----
    for line in ai_content.split("\n"):
        doc.add_paragraph(line)

    doc.save(doc_path)


# --------------------------
# MAIN EXECUTION
# --------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", required=True)
    args = parser.parse_args()

    package_dir = Path("cpi-artifacts") / args.package
    if not package_dir.exists():
        print("❌ Package not found")
        sys.exit(1)

    print("📦 Package:", args.package)

    iflows = find_iflows(package_dir)
    print("➡ Found", len(iflows), "iFlows")

    for iflow in iflows:
        print("\n--- Processing:", iflow)

        iflw_file = find_iflw_file(iflow)
        if iflw_file:
            display_name = extract_iflow_display_name_from_iflw(iflw_file)
        else:
            display_name = sanitize_filename(iflow.name)

        print("📌 iFlow Display Name:", display_name)

        artifacts = collect_artifacts(iflow)

        user_prompt = (
            "Generate full SAP CPI iFlow documentation using the 6-section structure. "
            "Use headings exactly as provided.\n\n"
            f"iFlow Name: {display_name}\n\n"
            "Artifacts:\n" + artifacts
        )

        ai_output = call_ollama(SYSTEM_PROMPT, user_prompt)

        out_dir = iflow / "docs"
        out_dir.mkdir(exist_ok=True)

        base = sanitize_filename(display_name)
        docx_file = out_dir / f"{base}.docx"
        md_file = out_dir / f"{base}.md"

        md_file.write_text(ai_output, encoding="utf-8")
        write_docx(docx_file, ai_output, display_name)

        print("✔ Generated:", docx_file)

    print("\n✨ All documentation generated!")


if __name__ == "__main__":
    main()
