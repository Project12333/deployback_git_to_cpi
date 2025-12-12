#!/usr/bin/env python3
"""
Generate per-iFlow documentation using DeepSeek-R1 model via OPENROUTER.
Requires OPENROUTER_API_KEY in environment.

API Endpoint:
    https://openrouter.ai/api/v1/chat/completions
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
# CONFIG
# ============================================================

AUTHOR_NAME = "Sindhu"
AUTHOR_VERSION = "Draft"
AUTHOR_DATE = datetime.utcnow().strftime("%Y-%m-%d")

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "deepseek/deepseek-r1:free"

SAP_LOGO = "tools/logos/sap.png"
MM_LOGO = "tools/logos/motiveminds.png"

SYSTEM_PROMPT_DEFAULT = """
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
- Infer missing details, but state assumptions clearly.
- ALWAYS fill all sections.
"""


# ============================================================
# HELPERS
# ============================================================

def sanitize_filename(name):
    name = re.sub(r"\s+", "_", name)
    name = re.sub(r'[<>:"/\\|?*]+', "", name)
    return name[:150]


def find_iflows(package):
    roots = set()
    for root, _, files in os.walk(package):
        for f in files:
            if f.endswith(".iflw") or f == "iFlowContent.xml":
                roots.add(Path(root))
                break
    return sorted(roots)


def find_iflw_file(iflow_dir):
    for f in iflow_dir.glob("*.iflw"):
        return f
    xml = iflow_dir / "iFlowContent.xml"
    return xml if xml.exists() else None


def extract_iflow_display_name(iflw_path):
    if iflw_path is None:
        return "Unknown_iFlow"
    try:
        text = iflw_path.read_text(encoding="utf-8", errors="replace")
    except:
        return sanitize_filename(iflw_path.stem)

    m = re.search(r'name="(.*?)"', text)
    if m:
        return sanitize_filename(m.group(1))

    m = re.search(r'id="(.*?)"', text)
    if m:
        return sanitize_filename(m.group(1))

    return sanitize_filename(iflw_path.stem)


def collect_artifacts(iflow_dir):
    parts = []
    for root, _, files in os.walk(iflow_dir):
        for f in files:
            if f.endswith((".iflw", ".groovy", ".xslt")) or f == "iFlowContent.xml":
                full = Path(root) / f
                try:
                    txt = full.read_text(encoding="utf-8", errors="replace")
                except:
                    txt = "[UNREADABLE FILE]"
                parts.append(
                    f"\n--- START ARTIFACT: {full} ---\n{txt}\n--- END ARTIFACT: {full} ---\n"
                )
    return "\n".join(parts)


# ============================================================
# OPENROUTER API CALL
# ============================================================

def call_openrouter(system_prompt, user_prompt):
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is missing in environment!")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://github.com",
        "X-Title": "CPI iFlow Doc Generator",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    }

    response = requests.post(OPENROUTER_URL, json=payload, headers=headers, timeout=600)
    response.raise_for_status()

    data = response.json()

    try:
        return data["choices"][0]["message"]["content"]
    except Exception:
        return str(data)


# ============================================================
# DOCX BUILDER
# ============================================================

def write_doc(path, content, title):
    doc = Document()

    # --- Cover logos (left/right)
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

    # Title
    p = doc.add_paragraph()
    p.alignment = 1
    r = p.add_run(title)
    r.bold = True
    r.font.size = Pt(28)
    r.font.color.rgb = RGBColor(31, 78, 121)

    doc.add_paragraph("\n")

    tbl2 = doc.add_table(3, 2)
    tbl2.style = "Table Grid"
    tbl2.cell(0, 0).text = "Author:"
    tbl2.cell(1, 0).text = "Date:"
    tbl2.cell(2, 0).text = "Version:"

    tbl2.cell(0, 1).text = AUTHOR_NAME
    tbl2.cell(1, 1).text = AUTHOR_DATE
    tbl2.cell(2, 1).text = AUTHOR_VERSION

    doc.add_page_break()

    # TOC
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

    # AI generated content
    for line in content.split("\n"):
        doc.add_paragraph(line)

    doc.save(path)


# ============================================================
# MAIN
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
            "Use EXACT 6 sections.\n\n"
            "ARTIFACTS:\n"
            + artifacts
        )

        try:
            ai_text = call_openrouter(SYSTEM_PROMPT_DEFAULT, user_prompt)
        except Exception as e:
            print("❌ Error calling OpenRouter:", e)
            ai_text = "Error generating documentation."

        outdir = iflow / "docs"
        outdir.mkdir(exist_ok=True)

        fname = sanitize_filename(display_name)
        md_path = outdir / f"{fname}.md"
        docx_path = outdir / f"{fname}.docx"

        md_path.write_text(ai_text, encoding="utf-8")
        write_doc(docx_path, ai_text, display_name)

        print("✔ Saved:", docx_path)

    print("\n✨ Documentation Completed")


if __name__ == "__main__":
    main()
