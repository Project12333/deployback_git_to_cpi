#!/usr/bin/env python3
"""
Generate Markdown (.md) and Word (.docx) documentation per iFlow folder.
Uses DeepSeek R1 through Ollama (deepseek-r1 model).
"""

import os
import sys
import subprocess
import requests
import textwrap
from pathlib import Path
from datetime import datetime
from docx import Document
from docx.shared import Inches, Pt

# ============================================================
# CONFIG — Updated for deepseek-r1
# ============================================================

MODEL_NAME = "deepseek-r1"
OLLAMA_URL = "http://localhost:11434/api/generate"

SAP_LOGO_PATH = "tools/logos/sap.png"
MOTIVEMINDS_LOGO_PATH = "tools/logos/motiveminds.png"

OUTPUT_DIR = "docs_generated"

# ============================================================
# SYSTEM PROMPT EXACT (FULL, NOT TRUNCATED)
# ============================================================

SYSTEM_PROMPT = r"""
You are a senior SAP CPI Technical Architect. Your task is to analyze ALL provided code and configuration files from the SINGLE iFlow provided and synthesize them into ONE consolidated Markdown documentation report. You MUST adhere strictly to the following hierarchical 6-point structure, using Markdown headings (# for main sections, ## for subsections). Ensure all technical details (like Groovy, XSLT, Adapters, Security) are thoroughly explained within the relevant sections.

**MANDATORY FIRST SECTION: TABLE OF CONTENTS (TOC) PAGE**
The very first output of the document MUST be the Table of Contents. Format the TOC heading using HTML like:
<h1 style="color: #1f4e79; font-size: 2.5em;">Table of Contents</h1>

Below this heading, list all 6 main sections and their subsections using standard Markdown numbered list syntax. Insert 10 blank lines after the TOC, then the unique marker:
---TOC-END-PAGE-BREAK---

# 1. Introduction
## 1.1 Purpose
## 1.2 Scope

# 2. Integration Overview
## 2.1 Integration Architecture
Output the High-Level Process Flow Diagram immediately after the architecture text using only Mermaid inside ```mermaid . Must be graph TD. One blank line must appear after closing ```.

## 2.2 Integration Components

# 3. Integration Scenarios
## 3.1 Scenario Description
## 3.2 Data Flows
## 3.3 Security Requirements

# 4. Error Handling and Logging

# 5. Testing Validation

# 6. Reference Documents
"""

# ============================================================
# iFlow Search
# ============================================================

def find_iflows(base_dir: Path):
    roots = set()
    for root, _, files in os.walk(base_dir):
        for f in files:
            if f == "iFlowContent.xml" or f.endswith(".iflw"):
                roots.add(Path(root))
    return sorted(list(roots))

# ============================================================
# Collect artifacts text
# ============================================================

def collect_artifacts_text(iflow_dir: Path):
    parts = []
    for root, _, files in os.walk(iflow_dir):
        for f in files:
            if f.endswith((".iflw", ".groovy", ".xslt")) or f == "iFlowContent.xml":
                p = Path(root) / f
                try:
                    txt = p.read_text(encoding="utf-8", errors="replace")
                except:
                    txt = "[UNREADABLE]"
                parts.append(f"\n--- START ARTIFACT: {p} ---\n{txt}\n--- END ARTIFACT: {p} ---")
    return "\n".join(parts)

# ============================================================
# Call DeepSeek R1 model via Ollama
# ============================================================

def call_ollama(system_prompt, user_prompt):
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.1
    }

    response = requests.post(OLLAMA_URL, json=payload, timeout=500)
    response.raise_for_status()

    data = response.json()

    if "choices" in data:
        return data["choices"][0]["message"]["content"]

    return data.get("content", "")

# ============================================================
# Build Cover Page HTML
# ============================================================

def build_cover_page(iFlowName: str):
    author = subprocess.run(
        ["git", "log", "-1", "--pretty=format:%an"],
        capture_output=True, text=True
    ).stdout.strip() or "Unknown"

    version = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        capture_output=True, text=True
    ).stdout.strip() or "n/a"

    date_str = datetime.utcnow().strftime("%Y-%m-%d")

    cover = f"""
<div style="float: left;">
<img src="{SAP_LOGO_PATH}" width="150"/>
</div>

<div style="float: right;">
<img src="{MOTIVEMINDS_LOGO_PATH}" width="150"/>
</div>

<div style="clear: both;"></div>
<div style="height: 80px;"></div>

<h1 style="color:#1f4e79; font-size:3em; text-align:center;">{iFlowName}</h1>
<h2 style="color:#1f4e79; text-align:center;">SAP CPI Technical Specification Document</h2>

<div style="height: 100px;"></div>

<div style="width:100%; text-align:center;">
<table border="1" style="width:400px; border-collapse:collapse; border-color:black; margin:0 auto;">
<tr><td><b>Author</b></td><td>{author}</td></tr>
<tr><td><b>Date</b></td><td>{date_str}</td></tr>
<tr><td><b>Version</b></td><td>{version}</td></tr>
</table>
</div>

<div style="page-break-after: always;"></div>
"""
    return cover

# ============================================================
# Write DOCX
# ============================================================

def write_docx(out_doc: Path, md_text: str, iflow_name: str):
    doc = Document()

    tbl = doc.add_table(rows=1, cols=2)
    left, right = tbl.rows[0].cells

    try:
        left.paragraphs[0].add_run().add_picture(SAP_LOGO_PATH, width=Inches(1.5))
    except:
        pass
    try:
        right.paragraphs[0].add_run().add_picture(MOTIVEMINDS_LOGO_PATH, width=Inches(1.5))
    except:
        pass

    title = doc.add_paragraph()
    title.alignment = 1
    run = title.add_run(iflow_name)
    run.bold = True
    run.font.size = Pt(28)

    doc.add_page_break()

    for line in md_text.split("\n"):
        doc.add_paragraph(line)

    doc.save(out_doc)

# ============================================================
# MAIN
# ============================================================

def main():
    base = Path(".")
    out_root = Path(OUTPUT_DIR)
    out_root.mkdir(exist_ok=True)

    iflows = find_iflows(base)
    if not iflows:
        print("No iFlows found")
        return

    for iflow in iflows:
        name = iflow.name
        print(f"\n=== Processing iFlow: {name} ===")

        artifacts = collect_artifacts_text(iflow)

        user_prompt = f"""
Synthesize the documentation for iFlow '{name}':

```text
{artifacts}
