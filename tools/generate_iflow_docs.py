#!/usr/bin/env python3
"""
tools/generate_iflow_docs.py

Generates one DOCX (and MD) per iFlow folder found under cpi-artifacts/<PACKAGE>.
- File name will use the iFlow display name (extracted from the .iflw file).
- Cover page contains SAP + MotiveMinds logos, Title (iFlow display name), Author = Sindhu,
  Date = today's date (auto), Version = Draft.
- Page 2 is a static Table of Contents.
- Remaining pages are populated with the AI-generated 6-section documentation (DeepSeek).
- Robust handling of Ollama/DeepSeek JSON response formats.
"""

import os
import re
import sys
import argparse
import subprocess
import requests
from pathlib import Path
from datetime import datetime

from docx import Document
from docx.shared import Inches, Pt, RGBColor

# --------------------------
# Configuration (Option A)
# --------------------------
HARDCODE_AUTHOR = "Sindhu"
HARDCODE_DATE = datetime.utcnow().strftime("%Y-%m-%d")  # today's date automatically
HARDCODE_VERSION = "Draft"

MODEL_NAME = "deepseek-r1"
# Ollama local endpoint used earlier; keep same unless your environment differs
OLLAMA_URL = "http://localhost:11434/api/generate"

SAP_LOGO = "tools/logos/sap.png"
MM_LOGO = "tools/logos/motiveminds.png"

SYSTEM_PROMPT_PATH = Path("tools/prompts/system_prompt.txt")
if SYSTEM_PROMPT_PATH.exists():
    SYSTEM_PROMPT = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8", errors="ignore")
else:
    SYSTEM_PROMPT = """
You are an SAP CPI Documentation Generator.

Your task is to create a complete, professional iFlow documentation following EXACTLY this structure:

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
- You MUST fill ALL sections with meaningful content based on the provided iFlow artifacts.
- If artifacts do not contain enough details, infer typical CPI patterns and explicitly note assumptions.
- DO NOT skip any section.
- Use the exact headings shown above in the output.
- Keep answers concise, professional, and technical.
"""

# --------------------------
# Utility functions
# --------------------------

def find_iflows(package_dir: Path):
    """
    Return sorted list of directories that appear to contain iFlows (files ending with .iflw or iFlowContent.xml).
    """
    roots = set()
    for root, _, files in os.walk(package_dir):
        for f in files:
            if f.endswith(".iflw") or f == "iFlowContent.xml":
                roots.add(Path(root))
                break
    return sorted(roots)


def collect_artifacts(iflow_dir: Path):
    """
    Collect artifacts (iflw, groovy, xslt, iFlowContent.xml) into a single text blob for the AI prompt.
    """
    parts = []
    for root, _, files in os.walk(iflow_dir):
        for f in files:
            if f.endswith((".iflw", ".groovy", ".xslt")) or f == "iFlowContent.xml":
                p = Path(root) / f
                try:
                    content = p.read_text(encoding="utf-8", errors="replace")
                except Exception:
                    content = "[UNREADABLE FILE]"
                parts.append(f"\n--- START ARTIFACT: {p} ---\n{content}\n--- END ARTIFACT: {p} ---\n")
    return "\n".join(parts)


def extract_iflow_display_name_from_iflw(iflw_path: Path):
    """
    Parse the .iflw file for an IntegrationFlow element and extract a display name.
    Looks for patterns like:
      <iflow:IntegrationFlow id="CPI-Mail-Reader_3" name="My Flow" ...>
      <IntegrationFlow id="CPI-Mail-Reader_3" name="My Flow" ...>
    Returns: preferred display name (name attribute), fallback to id attribute, fallback to filename stem.
    """
    try:
        text = iflw_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return iflw_path.stem

    # Try to find name attribute first
    # regex to find <...IntegrationFlow ... name="...">
    m = re.search(r'<[^>]*IntegrationFlow[^>]*\bname\s*=\s*"(.*?)"', text, re.IGNORECASE | re.DOTALL)
    if m:
        name = m.group(1).strip()
        if name:
            return sanitize_filename(name)

    # fallback to id attribute
    m2 = re.search(r'<[^>]*IntegrationFlow[^>]*\bid\s*=\s*"(.*?)"', text, re.IGNORECASE | re.DOTALL)
    if m2:
        idval = m2.group(1).strip()
        if idval:
            return sanitize_filename(idval)

    # fallback: use file stem
    return sanitize_filename(iflw_path.stem)


def sanitize_filename(name: str):
    """
    Make a filesystem-safe filename (remove characters that can cause issues).
    """
    # replace whitespace with underscore and remove unsafe characters
    name = re.sub(r'\s+', '_', name)
    name = re.sub(r'[<>:"/\\|?*]+', '', name)
    # limit length reasonably
    return name[:200]


def find_iflw_file(iflow_dir: Path):
    """
    Return first .iflw file path found in the given directory (or None).
    """
    for p in sorted(iflow_dir.glob("*.iflw")):
        return p
    # fallback to iFlowContent.xml
    f = iflow_dir / "iFlowContent.xml"
    if f.exists():
        return f
    return None


def call_ollama(system_prompt: str, user_prompt: str):
    """
    Call the Ollama / DeepSeek endpoint in a forgiving manner and try multiple known response shapes.
    Returns the textual content (string) or raises exception on fatal errors.
    """
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        # Do not request streaming here; ask for full response
    }

    resp = requests.post(OLLAMA_URL, json=payload, timeout=600)
    resp.raise_for_status()
    data = resp.json()

    # Try many likely shapes:
    # 1) OpenAI-like: data['choices'][0]['message']['content']
    try:
        if isinstance(data, dict):
            if "choices" in data and data["choices"]:
                choice = data["choices"][0]
                # common: choice['message']['content']
                if isinstance(choice, dict):
                    msg = choice.get("message")
                    if isinstance(msg, dict) and "content" in msg:
                        return msg["content"]
                    # some variants might have 'content' directly
                    if "content" in choice:
                        return choice["content"]
            # 2) direct message / content
            if "message" in data and isinstance(data["message"], dict) and "content" in data["message"]:
                return data["message"]["content"]
            if "content" in data:
                return data["content"]
            # 3) some Ollama models return {'result': {'output': '...'}} or {'response': '...'}
            if "response" in data and isinstance(data["response"], str) and data["response"].strip():
                return data["response"]
            if "result" in data and isinstance(data["result"], dict):
                # try to join text-ish fields
                for k in ("output", "content", "text"):
                    if k in data["result"] and isinstance(data["result"][k], str) and data["result"][k].strip():
                        return data["result"][k]
    except Exception:
        # fallback to string conversion at the end
        pass

    # As a last resort, attempt to extract any 'content' string anywhere in the JSON recursively
    def find_first_string(d):
        if isinstance(d, str):
            return d
        if isinstance(d, dict):
            for v in d.values():
                r = find_first_string(v)
                if r:
                    return r
        if isinstance(d, list):
            for v in d:
                r = find_first_string(v)
                if r:
                    return r
        return None

    text = find_first_string(data)
    if text:
        return text

    # If nothing found, return a descriptive placeholder
    return "[EMPTY_RESPONSE_FROM_MODEL]"


def build_cover_html(iflow_name: str):
    # returns an HTML-ish cover used for md output if you want to keep it
    html = ""
    html += "<div style='float:left;'><img src='" + SAP_LOGO + "' width='150'/></div>"
    html += "<div style='float:right;'><img src='" + MM_LOGO + "' width='150'/></div>"
    html += "<div style='clear:both;'></div>"
    html += "<div style='height:60px;'></div>"
    html += f"<h1 style='text-align:center; color:#1f4e79; font-size:36px;'>{iflow_name}</h1>"
    html += "<h2 style='text-align:center; color:#1f4e79;'>SAP CPI Technical Specification Document</h2>"
    html += "<div style='height:40px;'></div>"
    html += "<table border='1' style='width:400px; margin:0 auto; border-collapse:collapse;'>"
    html += f"<tr><td><b>Author:</b></td><td>{HARDCODE_AUTHOR}</td></tr>"
    html += f"<tr><td><b>Date:</b></td><td>{HARDCODE_DATE}</td></tr>"
    html += f"<tr><td><b>Version:</b></td><td>{HARDCODE_VERSION}</td></tr>"
    html += "</table>"
    html += "<div style='page-break-after: always;'></div>"
    return html


def write_docx(doc_path: Path, ai_content: str, iflow_name: str):
    """
    Construct the DOCX with:
      - cover page (logos, title, author/date/version table)
      - table of contents (static)
      - AI-generated content (expects the 6 sections in ai_content)
    """
    doc = Document()

    # COVER: logos in a 2-column table to align left & right
    header_table = doc.add_table(rows=1, cols=2)
    row = header_table.rows[0].cells
    try:
        row[0].paragraphs[0].add_run().add_picture(SAP_LOGO, width=Inches(1.5))
    except Exception:
        pass
    try:
        row[1].paragraphs[0].add_run().add_picture(MM_LOGO, width=Inches(1.5))
    except Exception:
        pass

    # spacing like sample
    doc.add_paragraph("\n\n\n")

    # Title centered, blue color close to sample
    title = doc.add_paragraph()
    title.alignment = 1
    t_run = title.add_run(iflow_name)
    t_run.bold = True
    t_run.font.size = Pt(28)
    try:
        t_run.font.color.rgb = RGBColor(31, 78, 121)
    except Exception:
        pass

    doc.add_paragraph("\n\n")

    # Author/Date/Version table
    info_table = doc.add_table(rows=3, cols=2)
    info_table.style = "Table Grid"
    info_table.cell(0, 0).text = "Author:"
    info_table.cell(1, 0).text = "Date:"
    info_table.cell(2, 0).text = "Version:"
    info_table.cell(0, 1).text = HARDCODE_AUTHOR
    info_table.cell(1, 1).text = HARDCODE_DATE
    info_table.cell(2, 1).text = HARDCODE_VERSION

    # Page break to TOC
    doc.add_page_break()

    # TABLE OF CONTENTS (static)
    toc_title = doc.add_paragraph()
    toc_title.add_run("Table of Contents").bold = True
    toc_title.runs[0].font.size = Pt(14)

    toc_text = (
        "1. Introduction\n\n"
        "   1.1 Purpose\n\n"
        "   1.2 Scope\n\n"
        "2. Integration Overview\n\n"
        "   2.1 Integration Architecture\n\n"
        "   2.2 Integration Components\n\n"
        "3. Integration Scenarios\n\n"
        "   3.1 Scenario Description\n\n"
        "   3.2 Data Flows\n\n"
        "   3.3 Security Requirements\n\n"
        "4. Error Handling and Logging\n\n"
        "5. Testing Validation\n\n"
        "6. Reference Documents\n"
    )
    for line in toc_text.split("\n"):
        doc.add_paragraph(line)

    # Page break to AI content
    doc.add_page_break()

    # AI content: preserve paragraphs; ideally AI returns headings for sections
    for para in ai_content.split("\n"):
        # Avoid creating a thousand empty paras: keep as-is to preserve spacing
        doc.add_paragraph(para)

    # Save docx
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

    for iflow_dir in iflows:
        print(f"\n--- Processing iFlow directory: {iflow_dir} ---")
        # find a .iflw file to extract display name
        iflw_file = find_iflw_file(iflow_dir)
        if iflw_file:
            display_name = extract_iflow_display_name_from_iflw(iflw_file)
        else:
            # fallback: use folder name
