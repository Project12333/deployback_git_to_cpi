#!/usr/bin/env python3
"""
Generate documentation for a specific CPI package.
Output: <iflow_folder>/docs/<iflowname>.md and .docx
"""

import os
import sys
import argparse
import subprocess
import requests
import textwrap
from pathlib import Path
from datetime import datetime

from docx import Document
from docx.shared import Inches, Pt

# -----------------------
# Load external SYSTEM PROMPT
# -----------------------

SYSTEM_PROMPT = Path("tools/prompts/system_prompt.txt").read_text(encoding="utf-8")

MODEL_NAME = "deepseek-r1"
OLLAMA_URL = "http://localhost:11434/api/generate"

SAP_LOGO = "tools/logos/sap.png"
MM_LOGO = "tools/logos/motiveminds.png"


# -----------------------
# Find iFlows inside selected package folder
# -----------------------

def find_iflows(package_dir: Path):
    roots = set()
    for root, _, files in os.walk(package_dir):
        for f in files:
            if f == "iFlowContent.xml" or f.endswith(".iflw"):
                roots.add(Path(root))
                break
    return sorted(roots)


# -----------------------
# Collect artifacts
# -----------------------

def collect_artifacts(iflow_dir: Path):
    parts = []
    for root, _, files in os.walk(iflow_dir):
        for f in files:
            if f.endswith((".iflw", ".groovy", ".xslt")) or f == "iFlowContent.xml":
                p = Path(root) / f
                try:
                    content = p.read_text(encoding="utf-8", errors="replace")
                except:
                    content = "[UNREADABLE FILE]"
                parts.append(f"\n--- START ARTIFACT: {p} ---\n{content}\n--- END ARTIFACT: {p} ---\n")
    return "\n".join(parts)


# -----------------------
# Call Ollama
# -----------------------

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

    # Clean content
    if "choices" in data:
        return data["choices"][0]["message"]["content"]

    return data.get("content", "")


# -----------------------
# Build Cover HTML
# -----------------------

def build_cover(iflow_name):
    author = subprocess.run(
        ["git", "log", "-1", "--pretty=format:%an"],
        capture_output=True, text=True
    ).stdout.strip() or "Unknown"

    version = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        capture_output=True, text=True
    ).stdout.strip() or "n/a"

    date = datetime.utcnow().strftime("%Y-%m-%d")

    return f"""
<div style="float:left;">
<img src="{SAP_LOGO}" width="150"/>
</div>

<div style="float:right;">
<img src="{MM_LOGO}" width="150"/>
</div>

<div style="clear:both;"></div>
<div style="height:60px;"></div>

<h1 style='color:#1f4e79; text-align:center; font-size:36px;'>{iflow_name}</h1>
<h2 style='color:#1f4e79; text-align:center;'>SAP CPI Technical Specification Document</h2>

<div style="height:40px;"></div>

<table border="1" style="width:400px; margin:0 auto;">
<tr><td><b>Author:</b></td><td>{author}</td></tr>
<tr><td><b>Date:</b></td><td>{date}</td></tr>
<tr><td><b>Version:</b></td><td>{version}</td></tr>
</table>

<div style="page-break-after: always;"></div>
"""


# -----------------------
# DOCX Writer
# -----------------------

def write_docx(doc_path: Path, md: str, iflow_name: str):
    doc = Document()

    # Logo Row
    row = doc.add_table(rows=1, cols=2)
    left, right = row.rows[0].cells

    try:
        left.paragraphs[0].add_run().add_picture(SAP_LOGO, width=Inches(1.6))
        right.paragraphs[0].add_run().add_picture(MM_LOGO, width=Inches(1.6))
    except:
        pass

    t = doc.add_paragraph()
    t.alignment = 1
    run = t.add_run(iflow_name)
    run.bold = True
    run.font.size = Pt(26)

    doc.add_page_break()

    for line in md.split("\n"):
        doc.add_paragraph(line)

    doc.save(doc_path)


# -----------------------
# MAIN
# -----------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", required=True, help="Package folder name inside cpi-artifacts/")
    args = parser.parse_args()

    package_path = Path("cpi-artifacts") / args.package
    if not package_path.exists():
        print(f"❌ Package not found: {package_path}")
        sys.exit(1)

    print(f"📦 Selected package: {args.package}")

    iflows = find_iflows(package_path)
    if not iflows:
        print("❌ No iFlows found in this package.")
        return

    print(f"➡ Found {len(iflows)} iFlows")

    for iflow in iflows:
        name = iflow.name
        print(f"\n--- Processing iFlow: {name} ---")

        artifacts = collect_artifacts(iflow)

        user_prompt = f"""
Generate documentation for the iFlow '{name}' with the 6-section format:

```text
{artifacts}
