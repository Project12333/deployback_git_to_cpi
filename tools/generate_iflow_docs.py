#!/usr/bin/env python3
"""
Generate SAP CPI Documentation using DeepSeek-R1 model through OpenRouter API.
Requires GitHub secret: OPENROUTER_API_KEY.

This version includes:
✔ Correct HTTP-Referer (your GitHub repo)
✔ Correct X-Title header
✔ DeepSeek-R1:free model
✔ DOCX output (cover + TOC + AI summary)
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


# ============================================================
# CONFIGURATION
# ============================================================

AUTHOR_NAME = "Sindhu"
AUTHOR_VERSION = "Draft"
AUTHOR_DATE = datetime.utcnow().strftime("%Y-%m-%d")

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "deepseek/deepseek-r1:free"

REFERER_URL = "https://github.com/Project12333/deployback_git_to_cpi"

SAP_LOGO = "tools/logos/sap.png"
MM_LOGO = "tools/logos/motiveminds.png"


SYSTEM_PROMPT = """
You are an SAP CPI Documentation Generator.

Generate COMPLETE documentation using EXACTLY this structure:

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
- Use provided artifacts.
- Infer missing details but state assumptions clearly.
- ALWAYS generate all 6 sections.
"""


# ============================================================
# HELPERS
# ============================================================

def sanitize_filename(name):
    name = re.sub(r"\s+", "_", name)
    name = re.sub(r'[<>:"/\\|?*]+', "", name)
    return name[:150]


def find_iflows(package):
    dirs = set()
    for root, _, files in os.walk(package):
        for f in files:
            if f.endswith(".iflw") or f == "iFlowContent.xml":
                dirs.add(Path(root))
                break
    return sorted(dirs)


def find_iflw_file(iflow_dir):
    for f in iflow_dir.glob("*.iflw"):
        return f
    xml = iflow_dir / "iFlowContent.xml"
    return xml if xml.exists() else None


def extract_iflow_display_name(iflw_path):
    if iflw_path is None:
        return "Unknown_iFlow"
    try:
        content = iflw_path.read_text(encoding="utf-8", errors="replace")
    except:
        return sanitize_filename(iflw_path.stem)

    m = re.search(r'name="(.*?)"', content)
    if m:
        return sanitize_filename(m.group(1))

    m = re.search(r'id="(.*?)"', content)
    if m:
        return sanitize_filename(m.group(1))

    return sanitize_filename(iflw_path.stem)


def collect_artifacts(iflow_dir):
    parts = []
    for root, _, files in os.walk(iflow_dir):
        for f in files:
            if f.endswith((".iflw", ".groovy", ".xslt")) or f == "iFlowContent.xml":
                p = Path(root) / f
                try:
                    txt = p.read_text(encoding="utf-8", errors="replace")
                except:
                    txt = "[UNREADABLE FILE]"
                parts.append(
                    f"\n--- START ARTIFACT: {p} ---\n"
                    f"{txt}\n"
                    f"--- END ARTIFACT: {p} ---\n"
                )
    return "\n".join(parts)


# ============================================================
# OPENROUTER API CALL
# ============================================================

def call_openrouter(system_prompt, user_prompt):
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("❌ OPENROUTER_API_KEY missing in environment!")

    # REQUIRED HEADERS — without these, OpenRouter returns 404
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": REFERER_URL,
        "X-Title": "CPI-Doc-Generator",
        "Content-Type": "application/json",
    }

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    }

    response = requests.post(
        OPENROUTER_URL,
        headers=headers,
        json=payload,
        timeout=300
    )
    response.raise_for_status()

    data = response.json()
    return data["choices"][0]["message"]["content"]


# ============================================================
# DOCX BUILDER
# ============================================================

def write_doc(path, content, title):
    doc = Document()

    # LOGOS HEADER
    tbl = doc.add_table(1, 2)
    left, right = tbl.rows[0].cells

    try:
        left.paragraphs[0].add_run().add_picture(SAP_LOGO, width=Inches(1.5))
    except:
        pass

    try:
        p = right.paragraphs[0]
        p.alignment = 2
        p.add_run().add_picture(MM_LOGO, width=Inches(1.5))
    except:
        pass

    doc.add_paragraph("\n\n")

    # TITLE
    p = doc.add_paragraph()
    p.alignment = 1
    r = p.add_run(title)
    r.bold = True
    r.font.size = Pt(28)
    r.font.color.rgb = RGBColor(31, 78, 121)

    doc.add_paragraph("\n")

    # AUTHOR TABLE
    t = doc.add_table(3, 2)
    t.style = "Table Grid"

    t.cell(0, 0).text = "Author:"
    t.cell(1, 0).text = "Date:"
    t.cell(2, 0).text = "Version:"

    t.cell(0, 1).text = AUTHOR_NAME
    t.cell(1, 1).text = AUTHOR_DATE
    t.cell(2, 1).text = AUTHOR_VERSION

    doc.add_page_break()

    # TABLE OF CONTENTS
    toc = [
        "Table of Contents",
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
        "6. Reference Documents",
    ]
    for line in toc:
        doc.add_paragraph(line)

    doc.add_page_break()

    # AI CONTENT
    for line in content.split("\n"):
        doc.add_paragraph(line)

    doc.save(path)


# ============================================================
# MAIN LOGIC
# ============================================================

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", required=True)
    args = parser.parse_args()

    pkg = Path("cpi-artifacts") / args.package
    if not pkg.exists():
        print("❌ Package not found:", pkg)
        sys.exit(1)

    iflows = find_iflows(pkg)
    print("➡ Found", len(iflows), "iFlows")

    for iflow in iflows:
        print("\n--- Processing:", iflow)

        iflw_file = find_iflw_file(iflow)
        display_name = extract_iflow_display_name(iflw_file)

        print("📌 iFlow Name:", display_name)

        artifacts = collect_artifacts(iflow)

        user_prompt = (
            f"Generate SAP CPI documentation for iFlow '{display_name}'.\n"
            f"Use EXACT 6-section structure.\n\n"
            f"ARTIFACTS:\n{artifacts}"
        )

        try:
            ai_output = call_openrouter(SYSTEM_PROMPT, user_prompt)
        except Exception as e:
            print("❌ OpenRouter Error:", e)
            ai_output = "Documentation could not be generated due to API error."

        outdir = iflow / "docs"
        outdir.mkdir(exist_ok=True)

        fname = sanitize_filename(display_name)
        md_path = outdir / f"{fname}.md"
        doc_path = outdir / f"{fname}.docx"

        md_path.write_text(ai_output, encoding="utf-8")
        write_doc(doc_path, ai_output, display_name)

        print("✔ Saved:", doc_path)

    print("\n✨ Documentation Completed Successfully")


if __name__ == "__main__":
    main()
