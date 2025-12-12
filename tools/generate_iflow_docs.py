#!/usr/bin/env python3
"""
Fully corrected SAP CPI iFlow documentation generator.

Fixes included:
- Uses Ollama /api/chat properly for DeepSeek (summary now appears)
- Logos aligned correctly (SAP left, MotiveMinds right)
- TOC fits on one page (no excessive blank lines)
- iFlow display name extracted from .iflw (Option A)
- Cover page uses Author=Sindhu, Date=today, Version=Draft
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
OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"

SAP_LOGO = "tools/logos/sap.png"
MM_LOGO = "tools/logos/motiveminds.png"

SYSTEM_PROMPT_PATH = Path("tools/prompts/system_prompt.txt")
if SYSTEM_PROMPT_PATH.exists():
    SYSTEM_PROMPT = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8", errors="ignore")
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
- Use provided artifacts to generate meaningful content.
- If details are missing, infer typical CPI logic and state assumptions.
- Always fill all 6 sections clearly and professionally.
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
            if f.endswith((".iflw", ".groovy", ".xslt", "iFlowContent.xml")):
                p = Path(root) / f
                try:
                    content = p.read_text(encoding="utf-8", errors="replace")
                except:
                    content = "[UNREADABLE FILE]"
                parts.append(f"\n--- START ARTIFACT: {p} ---\n{content}\n--- END ARTIFACT: {p} ---\n")
    return "\n".join(parts)


def find_iflw_file(iflow_dir: Path):
    for f in iflow_dir.glob("*.iflw"):
        return f
    xml = iflow_dir / "iFlowContent.xml"
    if xml.exists():
        return xml
    return None


def extract_iflow_display_name_from_iflw(iflw_path: Path):
    try:
        txt = iflw_path.read_text(encoding="utf-8", errors="replace")
    except:
        return sanitize_filename(iflw_path.stem)

    m = re.search(r'IntegrationFlow[^>]*name="(.*?)"', txt, re.IGNORECASE)
    if m:
        return sanitize_filename(m.group(1))

    m = re.search(r'IntegrationFlow[^>]*id="(.*?)"', txt, re.IGNORECASE)
    if m:
        return sanitize_filename(m.group(1))

    return sanitize_filename(iflw_path.stem)


# --------------------------
# AI CALL (CORRECTED)
# --------------------------

def call_ollama(system_prompt: str, user_prompt: str):
    """
    Correct DeepSeek API call using /api/chat.
    """
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "stream": False
    }

    resp = requests.post(OLLAMA_CHAT_URL, json=payload, timeout=600)
    resp.raise_for_status()

    data = resp.json()

    # Expected:
    # { "message": {"role":"assistant", "content":"..."} }
    if "message" in data and "content" in data["message"]:
        return data["message"]["content"]

    # fallback
    return str(data)


# --------------------------
# DOCX GENERATION
# --------------------------

def write_docx(doc_path: Path, ai_content: str, iflow_name: str):
    doc = Document()

    # ---- COVER PAGE ----
    header = doc.add_table(1, 2)
    row = header.rows[0].cells

    p_left = row[0].paragraphs[0]
    p_left.alignment = 0  # LEFT
    try:
        p_left.add_run().add_picture(SAP_LOGO, width=Inches(1.5))
    except:
        pass

    p_right = row[1].paragraphs[0]
    p_right.alignment = 2  # RIGHT
    try:
        p_right.add_run().add_picture(MM_LOGO, width=Inches(1.5))
    except:
        pass

    doc.add_paragraph("\n\n")

    title = doc.add_paragraph()
    title.alignment = 1
    r = title.add_run(iflow_name)
    r.bold = True
    r.font.size = Pt(28)
    r.font.color.rgb = RGBColor(31, 78, 121)

    doc.add_paragraph("\n")

    info = doc.add_table(3, 2)
    info.style = "Table Grid"

    info.cell(0, 0).text = "Author:"
    info.cell(1, 0).text = "Date:"
    info.cell(2, 0).text = "Version:"

    info.cell(0, 1).text = HARDCODE_AUTHOR
    info.cell(1, 1).text = HARDCODE_DATE
    info.cell(2, 1).text = HARDCODE_VERSION

    doc.add_page_break()

    # ---- TOC ----
    toc_title = doc.add_paragraph()
    toc_title.add_run("Table of Contents").bold = True
    toc_title.runs[0].font.size = Pt(14)

    toc = [
        "1. Introduction",
        "   1.1 Purpose",
        "   1.2 Scope",
        "",
        "2. Integration Overview",
        "   2.1 Integration Architecture",
        "   2.2 Integration Components",
        "",
        "3. Integration Scenarios",
        "   3.1 Scenario Description",
        "   3.2 Data Flows",
        "   3.3 Security Requirements",
        "",
        "4. Error Handling and Logging",
        "5. Testing Validation",
        "6. Reference Documents"
    ]

    for line in toc:
        doc.add_paragraph(line)

    doc.add_page_break()

    # ---- AI CONTENT PAGE ----
    for line in ai_content.split("\n"):
        doc.add_paragraph(line)

    doc.save(doc_path)


# --------------------------
# MAIN
# --------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", required=True)
    args = parser.parse_args()

    package_path = Path("cpi-artifacts") / args.package
    if not package_path.exists():
        print("❌ Package not found:", package_path)
        sys.exit(1)

    print("📦 Package:", args.package)

    iflows = find_iflows(package_path)
    print("➡ Found", len(iflows), "iFlows")

    for iflow in iflows:
        print("\n--- Processing:", iflow)

        iflw_file = find_iflw_file(iflow)
        display_name = extract_iflow_display_name_from_iflw(iflw_file)

        print("📌 iFlow Name:", display_name)

        artifacts = collect_artifacts(iflow)

        user_prompt = (
            f"Generate SAP CPI documentation for iF
