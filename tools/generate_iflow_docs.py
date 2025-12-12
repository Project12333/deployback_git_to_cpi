#!/usr/bin/env python3
"""
SAFE VERSION — NO TRIPLE QUOTES ANYWHERE
Generates documentation for CPI iFlows inside a selected package.
Outputs:
    <IFLOW_DIR>/docs/<IFLOW_NAME>.md
    <IFLOW_DIR>/docs/<IFLOW_NAME>.docx
"""

import os
import sys
import argparse
import subprocess
import requests
from pathlib import Path
from datetime import datetime

from docx import Document
from docx.shared import Inches, Pt

# --------------------------
# Load external SYSTEM PROMPT
# --------------------------

SYSTEM_PROMPT = Path("tools/prompts/system_prompt.txt").read_text(encoding="utf-8")

MODEL_NAME = "deepseek-r1"
OLLAMA_URL = "http://localhost:11434/api/generate"

SAP_LOGO = "tools/logos/sap.png"
MM_LOGO = "tools/logos/motiveminds.png"


# --------------------------
# Utility functions
# --------------------------

def find_iflows(package_dir: Path):
    roots = set()
    for root, _, files in os.walk(package_dir):
        for f in files:
            if f == "iFlowContent.xml" or f.endswith(".iflw"):
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
                    content = p.read_text(encoding="utf-8", errors="replace")
                except:
                    content = "[UNREADABLE FILE]"

                parts.append("\n--- START ARTIFACT: " + str(p) + " ---\n" +
                             content +
                             "\n--- END ARTIFACT: " + str(p) + " ---\n")

    return "\n".join(parts)


def call_ollama(system_prompt: str, user_prompt: str):
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.1
    }

    resp = requests.post(OLLAMA_URL, json=payload, timeout=600)
    resp.raise_for_status()

    data = resp.json()

    # Standard Ollama response
    if "choices" in data:
        msg = data["choices"][0]["message"]
        if isinstance(msg, dict) and "content" in msg:
            return msg["content"]

    if "content" in data:
        return data["content"]

    return str(data)


def build_cover_html(iflow_name: str):
    author = subprocess.run(
        ["git", "log", "-1", "--pretty=format:%an"],
        capture_output=True, text=True
    ).stdout.strip() or "Unknown"

    version = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        capture_output=True, text=True
    ).stdout.strip() or "n/a"

    date = datetime.utcnow().strftime("%Y-%m-%d")

    html = ""

    html += "<div style='float:left;'>"
    html += "<img src='" + SAP_LOGO + "' width='150'/>"
    html += "</div>"

    html += "<div style='float:right;'>"
    html += "<img src='" + MM_LOGO + "' width='150'/>"
    html += "</div>"

    html += "<div style='clear:both;'></div>"
    html += "<div style='height:60px;'></div>"

    html += "<h1 style='text-align:center; color:#1f4e79; font-size:36px;'>" + iflow_name + "</h1>"
    html += "<h2 style='text-align:center; color:#1f4e79;'>SAP CPI Technical Specification Document</h2>"

    html += "<div style='height:40px;'></div>"

    html += "<table border='1' style='width:400px; margin:0 auto; border-collapse:collapse;'>"
    html += "<tr><td><b>Author:</b></td><td>" + author + "</td></tr>"
    html += "<tr><td><b>Date:</b></td><td>" + date + "</td></tr>"
    html += "<tr><td><b>Version:</b></td><td>" + version + "</td></tr>"
    html += "</table>"

    html += "<div style='page-break-after: always;'></div>"

    return html


def write_docx(doc_path: Path, content: str, iflow_name: str):
    doc = Document()

    # Cover logos
    table = doc.add_table(rows=1, cols=2)
    left, right = table.rows[0].cells

    try:
        left.paragraphs[0].add_run().add_picture(SAP_LOGO, width=Inches(1.6))
        right.paragraphs[0].add_run().add_picture(MM_LOGO, width=Inches(1.6))
    except:
        pass

    title = doc.add_paragraph()
    title.alignment = 1
    run = title.add_run(iflow_name)
    run.bold = True
    run.font.size = Pt(26)

    doc.add_page_break()

    for line in content.split("\n"):
        doc.add_paragraph(line)

    doc.save(doc_path)


# --------------------------
# MAIN
# --------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", required=True, help="Package folder name inside cpi-artifacts/")
    args = parser.parse_args()

    package_path = Path("cpi-artifacts") / args.package

    if not package_path.exists():
        print("❌ Package not found:", package_path)
        sys.exit(1)

    print("📦 Selected package:", args.package)

    iflows = find_iflows(package_path)
    if not iflows:
        print("❌ No iFlows found in the package.")
        return

    print("➡ Found", len(iflows), "iFlow(s)")

    for iflow in iflows:
        iflow_name = iflow.name
        print("\n--- Processing iFlow:", iflow_name, "---")

        artifacts = collect_artifacts(iflow)

        # SAFE: no triple-quotes
        user_prompt = (
            "Generate documentation for the SAP CPI iFlow named '" + iflow_name + "'. "
            "Follow the strict 6-section hierarchy and format. "
            "Below are the complete iFlow artifacts:\n\n"
            "```text\n" +
            artifacts +
            "\n```"
        )

        generated = call_ollama(SYSTEM_PROMPT, user_prompt)

        cover = build_cover_html(iflow_name)
        final_md = cover + generated

        # Page break replacement
        final_md = final_md.replace(
            "---TOC-END-PAGE-BREAK---",
            "<div style='page-break-after: always;'></div>"
        )

        out_dir = iflow / "docs"
        out_dir.mkdir(exist_ok=True)

        md_path = out_dir / (iflow_name + ".md")
        doc_path = out_dir / (iflow_name + ".docx")

        md_path.write_text(final_md, encoding="utf-8")
        write_docx(doc_path, final_md, iflow_name)

        print("✔ Saved:", md_path)
        print("✔ Saved:", doc_path)

    print("\n✨ Documentation generation completed successfully!")


if __name__ == "__main__":
    main()
