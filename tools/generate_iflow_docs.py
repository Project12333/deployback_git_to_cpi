#!/usr/bin/env python3
"""
Generate per-iFlow DOCX/MD using DeepSeek Cloud API (chat endpoint).
Reads DEEPSEEK_API_KEY from env and optional DEEPSEEK_API_URL.
"""

import os
import re
import sys
import argparse
import requests
from pathlib import Path
from datetime import datetime
from typing import Optional

from docx import Document
from docx.shared import Inches, Pt, RGBColor

# ------------------------
# CONFIG
# ------------------------
HARDCODE_AUTHOR = "Sindhu"
HARDCODE_DATE = datetime.utcnow().strftime("%Y-%m-%d")
HARDCODE_VERSION = "Draft"

MODEL_NAME = "deepseek-r1"
# default cloud endpoint (can be overridden by env DEEPSEEK_API_URL)
DEFAULT_DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

SAP_LOGO = "tools/logos/sap.png"
MM_LOGO = "tools/logos/motiveminds.png"

PROMPT_FILE = Path("tools/prompts/system_prompt.txt")


# ------------------------
# Load system prompt
# ------------------------
if PROMPT_FILE.exists():
    SYSTEM_PROMPT = PROMPT_FILE.read_text(encoding="utf-8", errors="ignore")
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
        "- Infer missing details but explicitly state assumptions.\n"
        "- Always generate all 6 sections with the exact headings."
    )


# ------------------------
# Helpers
# ------------------------
def sanitize_filename(name: str) -> str:
    name = re.sub(r"\s+", "_", name)
    name = re.sub(r'[<>:"/\\|?*]+', "", name)
    return name[:200]


def find_iflows(package_path: Path):
    roots = set()
    for root, _, files in os.walk(package_path):
        for f in files:
            if f.endswith(".iflw") or f == "iFlowContent.xml":
                roots.add(Path(root))
                break
    return sorted(roots)


def collect_artifacts(iflow_dir: Path) -> str:
    parts = []
    for root, _, files in os.walk(iflow_dir):
        for fname in files:
            if fname.endswith((".iflw", ".groovy", ".xslt")) or fname == "iFlowContent.xml":
                p = Path(root) / fname
                try:
                    txt = p.read_text(encoding="utf-8", errors="replace")
                except Exception:
                    txt = "[UNREADABLE FILE]"
                parts.append(f"\n--- START ARTIFACT: {p} ---\n{txt}\n--- END ARTIFACT: {p} ---\n")
    return "\n".join(parts)


def find_iflw(iflow_dir: Path) -> Optional[Path]:
    for f in iflow_dir.glob("*.iflw"):
        return f
    xml = iflow_dir / "iFlowContent.xml"
    return xml if xml.exists() else None


def extract_display_name(iflw_file: Optional[Path]) -> str:
    if iflw_file is None:
        return "unknown_iflow"
    try:
        txt = iflw_file.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return sanitize_filename(iflw_file.stem)
    m = re.search(r'IntegrationFlow[^>]*name="(.*?)"', txt, re.IGNORECASE)
    if m:
        return sanitize_filename(m.group(1))
    m = re.search(r'IntegrationFlow[^>]*id="(.*?)"', txt, re.IGNORECASE)
    if m:
        return sanitize_filename(m.group(1))
    return sanitize_filename(iflw_file.stem)


# ------------------------
# DeepSeek Cloud call
# ------------------------
def call_deepseek(system_prompt: str, user_prompt: str) -> str:
    key = os.environ.get("DEEPSEEK_API_KEY")
    if not key:
        raise RuntimeError("DEEPSEEK_API_KEY is not set in the environment.")

    url = os.environ.get("DEEPSEEK_API_URL", DEFAULT_DEEPSEEK_API_URL)

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "User-Agent": "cpi-docs-generator/1.0"
    }

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.1
    }

    resp = requests.post(url, json=payload, headers=headers, timeout=600)
    resp.raise_for_status()
    data = resp.json()

    # Try to pull typical fields
    if isinstance(data, dict):
        # common: choices -> [ { message: { content: "..." } } ]
        if "choices" in data and data["choices"]:
            try:
                msg = data["choices"][0].get("message")
                if isinstance(msg, dict) and "content" in msg:
                    return msg["content"]
            except Exception:
                pass
        # some providers return { message: { content: "..." } }
        if "message" in data and isinstance(data["message"], dict) and "content" in data["message"]:
            return data["message"]["content"]
        # fallback to top-level 'content' or 'response'
        if "content" in data and isinstance(data["content"], str):
            return data["content"]
        if "response" in data and isinstance(data["response"], str):
            return data["response"]

    # final fallback: convert to string
    return str(data)


# ------------------------
# DOCX writer (cover, toc, ai content)
# ------------------------
def write_docx(path: Path, content: str, title_text: str):
    doc = Document()

    # logos table (left/right)
    tbl = doc.add_table(1, 2)
    left, right = tbl.rows[0].cells

    p_left = left.paragraphs[0]
    p_left.alignment = 0
    try:
        p_left.add_run().add_picture(SAP_LOGO, width=Inches(1.5))
    except Exception:
        pass

    p_right = right.paragraphs[0]
    p_right.alignment = 2
    try:
        p_right.add_run().add_picture(MM_LOGO, width=Inches(1.5))
    except Exception:
        pass

    doc.add_paragraph("\n\n")

    # Title
    p = doc.add_paragraph()
    p.alignment = 1
    r = p.add_run(title_text)
    r.bold = True
    r.font.size = Pt(28)
    try:
        r.font.color.rgb = RGBColor(31, 78, 121)
    except Exception:
        pass

    doc.add_paragraph("\n")

    # Author/Date/Version
    info = doc.add_table(3, 2)
    info.style = "Table Grid"
    info.cell(0, 0).text = "Author:"
    info.cell(1, 0).text = "Date:"
    info.cell(2, 0).text = "Version:"
    info.cell(0, 1).text = HARDCODE_AUTHOR
    info.cell(1, 1).text = HARDCODE_DATE
    info.cell(2, 1).text = HARDCODE_VERSION

    doc.add_page_break()

    # TOC (static)
    toc_lines = [
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
        "6. Reference Documents"
    ]
    for line in toc_lines:
        doc.add_paragraph(line)

    doc.add_page_break()

    # AI content
    for line in content.split("\n"):
        doc.add_paragraph(line)

    doc.save(path)


# ------------------------
# MAIN
# ------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", required=True, help="Folder name inside cpi-artifacts/")
    args = parser.parse_args()

    package_path = Path("cpi-artifacts") / args.package
    if not package_path.exists():
        print("❌ Package not found:", package_path)
        sys.exit(1)

    print("📦 Generating docs for package:", args.package)
    iflow_dirs = find_iflows(package_path)
    print("➡ Found", len(iflow_dirs), "iFlow(s)")

    for iflow_dir in iflow_dirs:
        print("\n--- Processing:", iflow_dir)
        iflw = find_iflw(iflow_dir)
        display_name = extract_display_name(iflw)
        print("📌 iFlow display name:", display_name)

        artifacts = collect_artifacts(iflow_dir)
        if not artifacts.strip():
            print("⚠️ No artifacts found for", display_name)

        user_prompt = (
            f"Generate SAP CPI documentation for iFlow '{display_name}'. "
            "Produce sections 1-6 exactly as listed. Use the artifacts below "
            "to populate Purpose, Scope, Architecture, Components, Scenarios, "
            "Data Flows, Security, Error Handling, Testing, and References.\n\n"
            "ARTIFACTS:\n" + artifacts
        )

        try:
            ai_out = call_deepseek(SYSTEM_PROMPT, user_prompt)
        except Exception as e:
            print("❌ Error calling DeepSeek API:", e)
            ai_out = (
                "1. Introduction\n\n1.1 Purpose\n\nUnable to generate content due to API error.\n\n"
                "1.2 Scope\n\n"
            )

        out_dir = iflow_dir / "docs"
        out_dir.mkdir(parents=True, exist_ok=True)

        fname = sanitize_filename(display_name)
        md_path = out_dir / f"{fname}.md"
        docx_path = out_dir / f"{fname}.docx"

        md_path.write_text(ai_out, encoding="utf-8")
        write_docx(docx_path, ai_out, display_name)

        print("✔ Saved:", docx_path)

    print("\n✨ All done.")


if __name__ == "__main__":
    main()
