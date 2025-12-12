#!/usr/bin/env python3
"""
tools/generate_iflow_docs.py

Generates Markdown (.md) and Word (.docx) documentation for each iFlow found
under the repository. Uses Ollama (model: deepseek-r1) via the HTTP API.

System prompt is loaded from: tools/prompts/system_prompt.txt
"""

import os
import sys
import subprocess
import requests
import textwrap
from pathlib import Path
from datetime import datetime
from typing import Optional

# python-docx imports
try:
    from docx import Document
    from docx.shared import Inches, Pt
except Exception:
    Document = None  # docx not installed; we'll still create markdown

# -----------------------
# Configuration
# -----------------------
MODEL_NAME = os.environ.get("DEEPSEEK_MODEL", "deepseek-r1")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")

SAP_LOGO_PATH = os.environ.get("SAP_LOGO_PATH", "tools/logos/sap.png")
MOTIVEMINDS_LOGO_PATH = os.environ.get("MM_LOGO_PATH", "tools/logos/motiveminds.png")

OUTPUT_DIR = Path(os.environ.get("OUTPUT_DIR", "docs_generated"))
PROMPT_PATH = Path("tools/prompts/system_prompt.txt")

# -----------------------
# Helpers
# -----------------------
def load_system_prompt(prompt_path: Path) -> str:
    if not prompt_path.exists():
        print(f"Error: SYSTEM_PROMPT file not found: {prompt_path}", file=sys.stderr)
        sys.exit(2)
    return prompt_path.read_text(encoding="utf-8")

def find_iflow_roots(base_dir: Path) -> list:
    roots = set()
    for root, _, files in os.walk(base_dir):
        for fname in files:
            if fname == "iFlowContent.xml" or fname.lower().endswith(".iflw"):
                roots.add(Path(root))
                break
    return sorted(roots)

def collect_artifacts_text(iflow_dir: Path) -> str:
    parts = []
    for root, _, files in os.walk(iflow_dir):
        for f in files:
            # consider only target artifact types
            if f.lower().endswith((".iflw", ".groovy", ".xslt")) or f == "iFlowContent.xml":
                p = Path(root) / f
                try:
                    txt = p.read_text(encoding="utf-8", errors="replace")
                except Exception:
                    txt = f"[UNREADABLE FILE: {p}]"
                parts.append(f"\n--- START ARTIFACT: {p} ---\n{txt}\n--- END ARTIFACT: {p} ---\n")
    return "\n".join(parts)

def call_ollama(system_prompt: str, user_query: str, model: str=MODEL_NAME, api_url: str=OLLAMA_URL, timeout: int=600) -> str:
    """
    Call Ollama HTTP API with a chat-like payload (system + user).
    Returns generated text or raises an exception.
    """
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ],
        "temperature": 0.1
    }
    headers = {"Content-Type": "application/json"}
    try:
        resp = requests.post(api_url, json=payload, headers=headers, timeout=timeout)
        resp.raise_for_status()
    except Exception as e:
        raise RuntimeError(f"Ollama API request failed: {e}")

    try:
        j = resp.json()
    except Exception:
        # fallback to raw text
        return resp.text

    # Try common response shapes
    if isinstance(j, dict):
        choices = j.get("choices")
        if choices and isinstance(choices, list) and len(choices) > 0:
            first = choices[0]
            # common: choices[0].message.content
            if isinstance(first, dict):
                m = first.get("message")
                if isinstance(m, dict) and "content" in m:
                    return m["content"]
                if "content" in first:
                    return first["content"]
        if "content" in j:
            return j["content"]
    # fallback
    return str(j)

def build_cover_html(iflow_name: str, sap_logo: str, mm_logo: str) -> str:
    author = run_git_command(["git", "log", "-1", "--pretty=format:%an"]) or "Unknown"
    version = run_git_command(["git", "rev-parse", "--short", "HEAD"]) or "n/a"
    date_str = datetime.utcnow().strftime("%Y-%m-%d")

    sap_block = f'<div style="float: left; text-align: left;"><img src="{sap_logo}" alt="SAP Logo" width="150" height="60"/></div>' if sap_logo else ""
    mm_block = f'<div style="float: right; text-align: right;"><img src="{mm_logo}" alt="MotiveMinds Logo" width="150" height="55" style="margin-top: 5px;"/></div>' if mm_logo else ""

    cover = sap_block + mm_block + '<div style="clear: both;"></div>'
    cover += '\n<div style="height: 80px;"></div>\n'
    cover += f'<h1 style="color: #1f4e79; font-size: 3em; text-align: center; margin-top: 5px; margin-bottom: 5px;">{iflow_name}</h1>\n'
    cover += '<h2 style="color: #1f4e79; font-size: 1.5em; text-align: center; margin-top: 5px; margin-bottom: 0px;">SAP CPI Technical Specification Document</h2>\n'
    cover += '<div style="height: 100px;"></div>\n'
    cover += '<div style="width: 100%; text-align: center;">\n'
    cover += '<table border="1" style="width: 400px; border-collapse: collapse; border-color: black; margin: 0 auto; text-align: left;">\n'
    cover += f'  <tr><td style="width: 30%; padding: 5px;"><strong>Author:</strong></td><td style="padding: 5px;">{author}</td></tr>\n'
    cover += f'  <tr><td style="padding: 5px;"><strong>Date:</strong></td><td style="padding: 5px;">{date_str}</td></tr>\n'
    cover += f'  <tr><td style="padding: 5px;"><strong>Version (Commit):</strong></td><td style="padding: 5px;">{version}</td></tr>\n'
    cover += '</table>\n</div>\n'
    cover += '\n<div style="page-break-after: always;"></div>\n\n'
    return cover

def run_git_command(cmd: list) -> Optional[str]:
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except Exception:
        return None

def write_markdown(iflow_out_dir: Path, filename: str, content: str) -> None:
    path = iflow_out_dir / filename
    path.write_text(content, encoding="utf-8")
    print(f"  -> Markdown saved: {path}")

def write_docx_simple(iflow_out_dir: Path, filename: str, md_content: str, sap_logo: str, mm_logo: str) -> None:
    if Document is None:
        print("python-docx not installed; skipping .docx generation.")
        return
    doc = Document()

    # Cover: 1-row 2-col table for logos
    tbl = doc.add_table(rows=1, cols=2)
    try:
        if sap_logo and Path(sap_logo).exists():
            tbl.cell(0,0).paragraphs[0].add_run().add_picture(sap_logo, width=Inches(1.8))
    except Exception as e:
        print("Warning: couldn't add SAP logo to docx:", e)
    try:
        if mm_logo and Path(mm_logo).exists():
            tbl.cell(0,1).paragraphs[0].add_run().add_picture(mm_logo, width=Inches(1.8))
    except Exception as e:
        print("Warning: couldn't add MotiveMinds logo to docx:", e)

    # Title
    doc.add_paragraph()
    title = doc.add_paragraph()
    title.alignment = 1
    run = title.add_run(iflow_out_dir.name)
    run.bold = True
    run.font.size = Pt(24)

    doc.add_paragraph()
    doc.add_page_break()

    # Add markdown lines as plain paragraphs (naive)
    for line in md_content.splitlines():
        doc.add_paragraph(line)

    out_path = iflow_out_dir / filename
    doc.save(out_path)
    print(f"  -> Word doc saved: {out_path}")

# -----------------------
# Main flow
# -----------------------
def main():
    # Load system prompt from external file (safe)
    system_prompt = load_system_prompt(PROMPT_PATH)

    base_dir = Path(".")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    iflows = find_iflow_roots(base_dir)
    if not iflows:
        print("No iFlows found (no 'iFlowContent.xml' or '*.iflw'). Exiting.")
        return

    for iflow_dir in iflows:
        iflow_name = iflow_dir.name
        print("\n" + "="*60)
        print(f"➡ Processing iFlow: {iflow_name} (folder: {iflow_dir})")

        artifacts_text = collect_artifacts_text(iflow_dir)
        if not artifacts_text.strip():
            print(f"  ⚠️ No artifacts found in {iflow_dir}. Skipping.")
            continue

        user_query = textwrap.dedent(f"""
            Synthesize a single, consolidated technical report following the required 6-section hierarchical template for the iFlow '{iflow_name}'.

            ```text
            {artifacts_text}
            ```
        """)

        # Call model
        try:
            print("  -> Calling Ollama (model: {}) ...".format(MODEL_NAME))
            generated = call_ollama(system_prompt, user_query)
            if not generated or not generated.strip():
                print("  ⚠️ Model returned empty response. Skipping this iFlow.")
                continue
            print("  ✅ Documentation generated by model.")
        except Exception as e:
            print(f"  ❌ Model call failed: {e}")
            continue

        # Build final content (cover + generated content)
        cover_html = build_cover_html(iflow_name, SAP_LOGO_PATH, MOTIVEMINDS_LOGO_PATH)
        full_md = cover_html + generated
        # replace marker with page break div
        full_md = full_md.replace("---TOC-END-PAGE-BREAK---", '<div style="page-break-after: always;"></div>')

        # Write outputs
        out_dir = OUTPUT_DIR / iflow_name
        out_dir.mkdir(parents=True, exist_ok=True)

        md_filename = f"{iflow_name}_Summary.md"
        docx_filename = f"{iflow_name}_Summary.docx"

        write_markdown(out_dir, md_filename, full_md)
        write_docx_simple(out_dir, docx_filename, full_md, SAP_LOGO_PATH, MOTIVEMINDS_LOGO_PATH)

    print("\n✨ All done. Generated documentation is in:", OUTPUT_DIR)

if __name__ == "__main__":
    main()
