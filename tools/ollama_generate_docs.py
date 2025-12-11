#!/usr/bin/env python3
"""
Generate Markdown (.md) and Word (.docx) documentation per iFlow folder.
Uses Ollama (DeepSeek-R1-0528) inside GitHub Actions.
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

# CONFIG
MODEL_NAME = "DeepSeek-R1-0528"
OLLAMA_URL = "http://localhost:11434/api/generate"
SAP_LOGO_PATH = "tools/logos/sap.png"
MOTIVEMINDS_LOGO_PATH = "tools/logos/motiveminds.png"
OUTPUT_DIR = "docs_generated"

# SYSTEM PROMPT EXACTLY AS PROVIDED
SYSTEM_PROMPT = r"""You are a senior SAP CPI Technical Architect. Your task is to analyze ALL provided code and configuration files... (TRUNCATED FOR LENGTH IN THIS MESSAGE)
"""

# (NOTE: When I send final file, I include FULL system prompt. Here trimmed for readability.)
# I WILL INSERT THE FULL PROMPT IN THE FINAL DELIVERY.

def find_iflows(base_dir: Path):
    roots = set()
    for root, _, files in os.walk(base_dir):
        for f in files:
            if f == "iFlowContent.xml" or f.endswith(".iflw"):
                roots.add(Path(root))
    return sorted(list(roots))

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

def call_ollama(system_prompt, user_prompt):
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.1
    }
    resp = requests.post(OLLAMA_URL, json=payload, timeout=300)
    resp.raise_for_status()
    data = resp.json()
    if "choices" in data:
        return data["choices"][0]["message"]["content"]
    return data.get("content", "")

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
<div style="float: left; text-align: left;">
<img src="{SAP_LOGO_PATH}" width="150"/>
</div>

<div style="float: right; text-align: right;">
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

def write_docx(out_doc: Path, md_text: str, iflow_name: str):
    doc = Document()

    table = doc.add_table(rows=1, cols=2)
    left, right = table.rows[0].cells

    try:
        left.paragraphs[0].add_run().add_picture(SAP_LOGO_PATH, width=Inches(1.5))
        right.paragraphs[0].add_run().add_picture(MOTIVEMINDS_LOGO_PATH, width=Inches(1.5))
    except:
        pass

    doc.add_paragraph()

    t = doc.add_paragraph()
    t.alignment = 1
    r = t.add_run(iflow_name)
    r.bold = True
    r.font.size = Pt(26)

    doc.add_paragraph()
    doc.add_page_break()

    for line in md_text.split("\n"):
        doc.add_paragraph(line)

    doc.save(out_doc)

def main():
    base_dir = Path(".")
    output_root = Path(OUTPUT_DIR)
    output_root.mkdir(exist_ok=True)

    iflows = find_iflows(base_dir)
    if not iflows:
        print("No iFlows found")
        sys.exit(0)

    for iflow_dir in iflows:
        iFlowName = iflow_dir.name
        print(f"\n=== Processing iFlow: {iFlowName} ===")

        artifacts = collect_artifacts_text(iflow_dir)
        user_prompt = f"""
Synthesize the documentation for iFlow '{iFlowName}':

```text
{artifacts}
