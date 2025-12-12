#!/usr/bin/env python3
"""
Generate per-iFlow DOCX/MD using a local Ollama server (deepseek-r1:7b).
Assumes Ollama HTTP API available at http://localhost:11434/api/chat
"""

import os
import re
import sys
import time
import argparse
import requests
from pathlib import Path
from datetime import datetime

from docx import Document
from docx.shared import Inches, Pt, RGBColor

# --------------------------
# Config
# --------------------------
HARDCODE_AUTHOR = "Sindhu"
HARDCODE_VERSION = "Draft"
HARDCODE_DATE = datetime.utcnow().strftime("%Y-%m-%d")

OLLAMA_CHAT_URL = os.environ.get("OLLAMA_CHAT_URL", "http://localhost:11434/api/chat")
MODEL_NAME = "deepseek-r1:7b"

SAP_LOGO = "tools/logos/sap.png"
MM_LOGO = "tools/logos/motiveminds.png"

SYSTEM_PROMPT = Path("tools/prompts/system_prompt.txt").read_text(encoding="utf-8", errors="ignore") \
    if Path("tools/prompts/system_prompt.txt").exists() else (
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
    "RULES:\n- Use provided artifacts.\n- If details missing, infer reasonable CPI patterns and note assumptions.\n- Always produce all 6 sections using those exact headings."
)

# --------------------------
# Helpers
# --------------------------

def sanitize_filename(name: str) -> str:
    name = re.sub(r"\s+", "_", name)
    name = re.sub(r'[<>:"/\\|?*]+', "", name)
    return name[:180]


def find_iflows(package_dir: Path):
    roots = set()
    for root, _, files in os.walk(package_dir):
        for f in files:
            if f.endswith(".iflw") or f == "iFlowContent.xml":
                roots.add(Path(root))
                break
    return sorted(roots)


def collect_artifacts(iflow_dir: Path) -> str:
    parts = []
    for root, _, files in os.walk(iflow_dir):
        for f in sorted(files):
            if f.endswith((".iflw", ".groovy", ".xslt")) or f == "iFlowContent.xml":
                p = Path(root) / f
                try:
                    content = p.read_text(encoding="utf-8", errors="replace")
                except Exception:
                    content = "[UNREADABLE FILE]"
                parts.append(f"\n--- START ARTIFACT: {p} ---\n{content}\n--- END ARTIFACT: {p} ---\n")
    return "\n".join(parts)


def find_iflw_file(iflow_dir: Path):
    for p in iflow_dir.glob("*.iflw"):
        return p
    f = iflow_dir / "iFlowContent.xml"
    return f if f.exists() else None


def extract_iflow_display_name_from_iflw(iflw_path: Path):
    if iflw_path is None:
        return sanitize_filename(iflow_path.name if (iflow_path := None) else "unknown_iflow")
    try:
        text = iflw_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return sanitize_filename(iflw_path.stem)

    m = re.search(r'IntegrationFlow[^>]*name="(.*?)"', text, re.IGNORECASE)
    if m:
        return sanitize_filename(m.group(1))
    m = re.search(r'IntegrationFlow[^>]*id="(.*?)"', text, re.IGNORECASE)
    if m:
        return sanitize_filename(m.group(1))
    return sanitize_filename(iflw_path.stem)


# --------------------------
# Ollama call (chat) with retries
# --------------------------

def call_ollama(system_prompt: str, user_prompt: str, max_retries=3, backoff=3) -> str:
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.05,
        "stream": False
    }

    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.post(OLLAMA_CHAT_URL, json=payload, timeout=600)
            resp.raise_for_status()
            data = resp.json()
            # expected: { "message": { "role": "assistant", "content": "..." } } or choices array
            if isinstance(data, dict):
                if "message" in data and isinstance(data["message"], dict) and "content" in data["message"]:
                    return data["message"]["content"]
                if "choices" in data and data["choices"]:
                    c = data["choices"][0]
                    if isinstance(c, dict) and "message" in c and "content" in c["message"]:
                        return c["message"]["content"]
                    if "content" in c and isinstance(c["content"], str):
                        return c["content"]
            # fallback to string representation
            return str(data)
        except Exception as e:
            print(f"Warning: Ollama call attempt {attempt} failed: {e}", file=sys.stderr)
            if attempt < max_retries:
                time.sleep(backoff * attempt)
            else:
                raise

# --------------------------
# DOCX writer
# --------------------------

def write_docx(doc_path: Path, ai_text: str, iflow_name: str):
    doc = Document()

    # logos aligned left / right
    table = doc.add_table(1, 2)
    left, right = table.rows[0].cells
    try:
        pleft = left.paragraphs[0]
        pleft.alignment = 0
        pleft.add_run().add_picture(SAP_LOGO, width=Inches(1.5))
    except Exception:
        pass
    try:
        pright = right.paragraphs[0]
        pright.alignment = 2
        pright.add_run().add_picture(MM_LOGO, width=Inches(1.5))
    except Exception:
        pass

    doc.add_paragraph("\n\n")

    title = doc.add_paragraph()
    title.alignment = 1
    run = title.add_run(iflow_name)
    run.bold = True
    run.font.size = Pt(28)
    try:
        run.font.color.rgb = RGBColor(31, 78, 121)
    except Exception:
        pass

    doc.add_paragraph("\n")

    info = doc.add_table(3, 2)
    info.style = "Table Grid"
    info.cell(0, 0).text = "Author:"
    info.cell(1, 0).text = "Date:"
    info.cell(2, 0).text = "Version:"
    info.cell(0, 1).text = HARDCODE_AUTHOR
    info.cell(1, 1).text = HARDCODE_DATE
    info.cell(2, 1).text = HARDCODE_VERSION

    doc.add_page_break()

    # TOC (compact)
    toc_lines = [
        "Table of Contents",
        "1. Introduction",
        "   1.1 Purpose",
        "   1.2 Scope",
        "2. Integration Overview",
        "   2.1 Integration Architecture",
        "   2.2 Integration Components",
        "3. Integration Scenarios",
        "   3.1 Scenario Description",
        "   3.2 Data Flows",
        "   3.3 Security Requirements",
        "4. Error Handling and Logging",
        "5. Testing Validation",
        "6. Reference Documents",
    ]
    for ln in toc_lines:
        doc.add_paragraph(ln)

    doc.add_page_break()

    # AI content
    for line in ai_text.splitlines():
        doc.add_paragraph(line)

    doc.save(doc_path)


# --------------------------
# Main
# --------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", required=True)
    args = parser.parse_args()

    package_path = Path("cpi-artifacts") / args.package
    if not package_path.exists():
        print("Package not found:", package_path)
        sys.exit(1)

    iflows = find_iflows(package_path)
    if not iflows:
        print("No iFlows found")
        return

    print("Found", len(iflows), "iFlows")

    for iflow in iflows:
        print("\nProcessing iFlow dir:", iflow)
        iflw = find_iflw_file(iflow)
        display_name = extract_iflow_display_name_from_iflw(iflw)
        print("Using display name:", display_name)

        artifacts = collect_artifacts(iflow)
        user_prompt = (
            f"Generate documentation for SAP CPI iFlow '{display_name}' using EXACT headings:\n\n"
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
            "Use the following artifacts (files and content):\n\n"
            + artifacts
        )

        try:
            ai_text = call_ollama(SYSTEM_PROMPT, user_prompt)
        except Exception as e:
            print("Error calling Ollama:", e)
            ai_text = "Error: could not generate documentation due to Ollama error."

        out = iflow / "docs"
        out.mkdir(parents=True, exist_ok=True)
        base = sanitize_filename(display_name)
        md_path = out / f"{base}.md"
        docx_path = out / f"{base}.docx"

        md_path.write_text(ai_text, encoding="utf-8")
        write_docx(docx_path, ai_text, display_name)
        print("Saved:", docx_path)

    print("\nDone.")


if __name__ == "__main__":
    main()
