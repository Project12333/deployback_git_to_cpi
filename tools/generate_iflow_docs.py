#!/usr/bin/env python3
import os
import sys
import argparse
import subprocess
import requests
from pathlib import Path
from datetime import datetime

from docx import Document
from docx.shared import Inches, Pt, RGBColor

# --------------------------
# Configuration (Option B)
# --------------------------
HARDCODE_AUTHOR = "Nidhi Srivastava"
HARDCODE_DATE = "2025-12-01"
HARDCODE_VERSION = "Draft"

MODEL_NAME = "deepseek-r1"
OLLAMA_URL = "http://localhost:11434/api/generate"

SAP_LOGO = "tools/logos/sap.png"
MM_LOGO = "tools/logos/motiveminds.png"

# Load system prompt (fallback included)
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
- If artifacts do not contain enough details, infer typical CPI patterns and note assumptions.
- DO NOT skip any section.
- Be clear and professional.
"""


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

                parts.append(
                    f"\n--- START ARTIFACT: {p} ---\n{content}\n--- END ARTIFACT: {p} ---\n"
                )
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

    # Standard Ollama-like response formats
    if isinstance(data, dict):
        if "choices" in data and data["choices"]:
            msg = data["choices"][0].get("message", {})
            if isinstance(msg, dict) and "content" in msg:
                return msg["content"]
        if "content" in data:
            return data["content"]

    return str(data)


def write_docx(doc_path: Path, content: str, iflow_name: str):
    doc = Document()

    # ------------------------
    # COVER PAGE – LOGOS
    # ------------------------
    header_table = doc.add_table(rows=1, cols=2)
    row = header_table.rows[0].cells

    try:
        row[0].paragraphs[0].add_run().add_picture(SAP_LOGO, width=Inches(1.5))
        row[1].paragraphs[0].add_run().add_picture(MM_LOGO, width=Inches(1.5))
    except:
        pass

    # Spacing
    doc.add_paragraph("\n\n\n")

    # ------------------------
    # TITLE (centered blue text)
    # ------------------------
    title = doc.add_paragraph()
    title.alignment = 1  # center
    t_run = title.add_run(iflow_name)
    t_run.bold = True
    t_run.font.size = Pt(28)
    try:
        t_run.font.color.rgb = RGBColor(31, 78, 121)
    except:
        pass

    doc.add_paragraph("\n\n")

    # ------------------------
    # AUTHOR / DATE / VERSION TABLE
    # ------------------------
    info_table = doc.add_table(3, 2)
    info_table.style = "Table Grid"

    info_table.cell(0, 0).text = "Author:"
    info_table.cell(1, 0).text = "Date:"
    info_table.cell(2, 0).text = "Version:"

    info_table.cell(0, 1).text = HARDCODE_AUTHOR
    info_table.cell(1, 1).text = HARDCODE_DATE
    info_table.cell(2, 1).text = HARDCODE_VERSION

    # PAGE BREAK
    doc.add_page_break()

    # ------------------------
    # TABLE OF CONTENTS (STATIC FORMAT)
    # ------------------------
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

    doc.add_page_break()

    # ------------------------
    # AI-GENERATED CONTENT
    # ------------------------
    for line in content.split("\n"):
        doc.add_paragraph(line)

    doc.save(doc_path)


# --------------------------
# MAIN SCRIPT
# --------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", required=True, help="Package folder inside cpi-artifacts/")
    args = parser.parse_args()

    package_path = Path("cpi-artifacts") / args.package

    if not package_path.exists():
        print("❌ Package not found:", package_path)
        sys.exit(1)

    print("📦 Selected package:", args.package)

    iflows = find_iflows(package_path)
    if not iflows:
        print("❌ No iFlows found.")
        return

    print("➡ Found", len(iflows), "iFlow(s)")

    for iflow in iflows:
        iflow_name = iflow.name
        print(f"\n--- Processing iFlow: {iflow_name} ---")

        artifacts = collect_artifacts(iflow)

        user_prompt = (
            "Generate a detailed SAP CPI iFlow documentation using this exact required structure:\n\n"
            "1. Introduction (Purpose, Scope)\n"
            "2. Integration Overview (Architecture & Components)\n"
            "3. Integration Scenarios (Description, Data Flows, Security Requirements)\n"
            "4. Error Handling and Logging\n"
            "5. Testing Validation\n"
            "6. Reference Documents\n\n"
            f"iFlow Name: {iflow_name}\n\n"
            "Use the following iFlow artifacts as input:\n\n"
            + artifacts
        )

        try:
            generated_content = call_ollama(SYSTEM_PROMPT, user_prompt)
        except Exception as e:
            print("❌ Error calling DeepSeek:", e)
            generated_content = "Error generating content."

        # OUTPUT PATHS
        out_dir = iflow / "docs"
        out_dir.mkdir(exist_ok=True)

        docx_path = out_dir / f"{iflow_name}.docx"
        md_path = out_dir / f"{iflow_name}.md"

        # Save MD
        try:
            md_path.write_text(generated_content, encoding="utf-8")
        except:
            pass

        # Save DOCX
        write_docx(docx_path, generated_content, iflow_name)

        print("✔ Saved DOCX:", docx_path)
        print("✔ Saved MD:", md_path)

    print("\n✨ Documentation generation completed!")


if __name__ == "__main__":
    main()
