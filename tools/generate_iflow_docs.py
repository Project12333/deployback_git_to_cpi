#!/usr/bin/env python3

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
#  CONFIGURATION
# ============================================================

HARDCODE_AUTHOR = "Sindhu"
HARDCODE_DATE = datetime.utcnow().strftime("%Y-%m-%d")
HARDCODE_VERSION = "Draft"

MODEL_NAME = "deepseek-r1"
OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"

SAP_LOGO = "tools/logos/sap.png"
MM_LOGO = "tools/logos/motiveminds.png"

PROMPT_FILE = Path("tools/prompts/system_prompt.txt")


# ============================================================
#  LOAD SYSTEM PROMPT
# ============================================================

if PROMPT_FILE.exists():
    SYSTEM_PROMPT = PROMPT_FILE.read_text(
        encoding="utf-8", errors="ignore"
    )
else:
    SYSTEM_PROMPT = (
        "You are an SAP CPI Documentation Generator.\n"
        "Generate COMPLETE documentation using EXACTLY this structure:\n\n"
        "1. Introduction\n"
        "   1.1 Purpose\n"
        "   1.2 Scope\n\n"
        "2. Integration Overview\n"
        "   2.1 Integration Architecture\n"
        "   2.2 Integration Components\n\n"
        "3. Integration Scenarios\n"
        "   3.1 Scenario Description\n"
        "   3.2 Data Flows\n"
        "   3.3 Security Requirements\n\n"
        "4. Error Handling and Logging\n\n"
        "5. Testing Validation\n\n"
        "6. Reference Documents\n\n"
        "RULES:\n"
        "- Use provided artifacts.\n"
        "- Infer missing details but specify assumptions.\n"
        "- ALWAYS generate all sections.\n"
    )


# ============================================================
#  HELPER FUNCTIONS
# ============================================================

def sanitize_filename(name: str) -> str:
    name = re.sub(r"\s+", "_", name)
    name = re.sub(r'[<>:"/\\|?*]+', "", name)
    return name[:200]


def find_iflows(package_path: Path):
    results = set()
    for root, _, files in os.walk(package_path):
        for f in files:
            if f.endswith(".iflw") or f == "iFlowContent.xml":
                results.add(Path(root))
                break
    return sorted(results)


def collect_artifacts(iflow_dir: Path) -> str:
    parts = []
    for root, _, files in os.walk(iflow_dir):
        for fname in files:
            if fname.endswith((".iflw", ".groovy", ".xslt")) \
               or fname == "iFlowContent.xml":

                p = Path(root) / fname
                try:
                    txt = p.read_text(
                        encoding="utf-8",
                        errors="replace"
                    )
                except:
                    txt = "[UNREADABLE FILE]"

                parts.append(
                    f"\n--- START ARTIFACT: {p} ---\n"
                    f"{txt}\n"
                    f"--- END ARTIFACT: {p} ---\n"
                )
    return "\n".join(parts)


def find_iflw(iflow_dir: Path):
    for f in iflow_dir.glob("*.iflw"):
        return f
    xml = iflow_dir / "iFlowContent.xml"
    return xml if xml.exists() else None


def extract_display_name(iflw_file: Path) -> str:
    try:
        text = iflw_file.read_text(
            encoding="utf-8",
            errors="replace"
        )
    except:
        return sanitize_filename(iflw_file.stem)

    # Try name=""
    m = re.search(
        r'IntegrationFlow[^>]*name="(.*?)"',
        text,
        re.IGNORECASE
    )
    if m:
        return sanitize_filename(m.group(1))

    # Try id=""
    m = re.search(
        r'IntegrationFlow[^>]*id="(.*?)"',
        text,
        re.IGNORECASE
    )
    if m:
        return sanitize_filename(m.group(1))

    return sanitize_filename(iflw_file.stem)


# ============================================================
#  AI CALL (DeepSeek via Ollama /api/chat)
# ============================================================

def call_ollama(system_prompt: str, user_prompt: str) -> str:
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "stream": False
    }

    resp = requests.post(
        OLLAMA_CHAT_URL,
        json=payload,
        timeout=600
    )
    resp.raise_for_status()
    data = resp.json()

    if (
        isinstance(data, dict)
        and "message" in data
        and "content" in data["message"]
    ):
        return data["message"]["content"]

    return str(data)


# ============================================================
#  DOCX GENERATION
# ============================================================

def write_docx(path: Path, content: str, title_text: str):
    doc = Document()

    # ------------------ COVER PAGE LOGOS ------------------
    table = doc.add_table(1, 2)
    left, right = table.rows[0].cells

    p_left = left.paragraphs[0]
    p_left.alignment = 0
    try:
        p_left.add_run().add_picture(SAP_LOGO, width=Inches(1.5))
    except:
        pass

    p_right = right.paragraphs[0]
    p_right.alignment = 2
    try:
        p_right.add_run().add_picture(MM_LOGO, width=Inches(1.5))
    except:
        pass

    doc.add_paragraph("\n\n")

    # ------------------ TITLE ------------------
    p = doc.add_paragraph()
    p.alignment = 1
    r = p.add_run(title_text)
    r.bold = True
    r.font.size = Pt(28)
    r.font.color.rgb = RGBColor(31, 78, 121)

    doc.add_paragraph("\n")

    # ------------------ DETAILS TABLE ------------------
    info = doc.add_table(3, 2)
    info.style = "Table Grid"

    info.cell(0, 0).text = "Author:"
    info.cell(1, 0).text = "Date:"
    info.cell(2, 0).text = "Version:"

    info.cell(0, 1).text = HARDCODE_AUTHOR
    info.cell(1, 1).text = HARDCODE_DATE
    info.cell(2, 1).text = HARDCODE_VERSION

    doc.add_page_break()

    # ------------------ TABLE OF CONTENTS ------------------
    toc_title = doc.add_paragraph()
    toc_title.add_run("Table of Contents").bold = True

    toc_lines = [
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

    for line in toc_lines:
        doc.add_paragraph(line)

    doc.add_page_break()

    # ------------------ AI CONTENT ------------------
    for line in content.split("\n"):
        doc.add_paragraph(line)

    doc.save(path)


# ============================================================
#  MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", required=True)
    args = parser.parse_args()

    package = Path("cpi-artifacts") / args.package

    if not package.exists():
        print("❌ Invalid package")
        sys.exit(1)

    print("📦 Package:", args.package)

    iflow_dirs = find_iflows(package)
    print("➡ Found", len(iflow_dirs), "iFlows")

    for iflow in iflow_dirs:
        print("\n--- Processing directory:", iflow)

        iflw_file = find_iflw(iflow)
        display_name = extract_display_name(iflw_file)

        print("📌 iFlow Display Name:", display_name)

        artifacts = collect_artifacts(iflow)

        user_prompt = (
            f"Generate full SAP CPI documentation for iFlow '{display_name}'. "
            "Use the required 6-section structure. Write clearly and completely. "
            "Below are the iFlow artifacts:\n\n"
            f"{artifacts}"
        )

        ai_text = call_ollama(SYSTEM_PROMPT, user_prompt)

        out_dir = iflow / "docs"
        out_dir.mkdir(exist_ok=True)

        fname = sanitize_filename(display_name)

        docx_path = out_dir / f"{fname}.docx"
        md_path = out_dir / f"{fname}.md"

        md_path.write_text(ai_text, encoding="utf-8")
        write_docx(docx_path, ai_text, display_name)

        print("✔ Created:", docx_path)

    print("\n✨ Documentation Generated Successfully!")


if __name__ == "__main__":
    main()
