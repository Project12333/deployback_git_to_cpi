#!/usr/bin/env python3
import sys
import json
import requests
import xml.etree.ElementTree as ET
from pathlib import Path
import subprocess
import os
from datetime import datetime

from docx import Document
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH


# =========================================================
# PATH RESOLUTION (IMPORTANT FOR GITHUB ACTIONS)
# =========================================================
BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_PATH = BASE_DIR / "reference.docx"
SAP_LOGO_PATH = BASE_DIR / "logos" / "sap.png"
MM_LOGO_PATH = BASE_DIR / "logos" / "motiveminds.png"

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "deepseek-r1:1.5b"


# ---------------------------------------------------------
# Parse .iflw XML metadata
# ---------------------------------------------------------
def parse_iflw(path):
    meta = {
        "flowname": Path(path).stem,
        "senders": [],
        "receivers": [],
        "adapters": [],
        "scripts": [],
        "mappings": [],
        "steps": []
    }

    try:
        tree = ET.parse(path)
        root = tree.getroot()

        for elem in root.iter():
            tag = elem.tag.split("}")[-1].lower()
            name = (
                elem.attrib.get("name")
                or elem.attrib.get("id")
                or elem.attrib.get("idref")
                or tag
            )

            if "sender" in tag or "start" in tag:
                meta["senders"].append(name)

            if "receiver" in tag or "end" in tag:
                meta["receivers"].append(name)

            if "adapter" in tag:
                meta["adapters"].append(name)

            if "script" in tag or "groovy" in tag or "scripttask" in tag:
                meta["scripts"].append(name)

            if "mapping" in tag:
                meta["mappings"].append(name)

            meta["steps"].append(name)

    except Exception as e:
        meta["error"] = f"XML parse error: {e}"

    return meta


# ---------------------------------------------------------
# Mermaid diagram
# ---------------------------------------------------------
def sanitize_id(s):
    return "".join(c if c.isalnum() else "_" for c in str(s))


def high_level_diagram(meta):
    sender = meta["senders"][0] if meta["senders"] else "Sender"
    receiver = meta["receivers"][0] if meta["receivers"] else "Receiver"

    return (
        "```mermaid\n"
        "graph TD\n"
        f"  {sanitize_id(sender)}([\"{sender}\"]) -->|Request| CPI\n"
        f"  CPI -->|Response| {sanitize_id(receiver)}([\"{receiver}\"])\n"
        "```\n"
    )


# ---------------------------------------------------------
# Version Resolver
# ---------------------------------------------------------
def determine_version(flow_name):
    mode = os.getenv("VERSION_MODE", "none")
    manual = os.getenv("VERSION_VALUE", "")

    if mode == "manual" and manual:
        return manual
    if mode == "date":
        return datetime.now().strftime("%Y-%m-%d")
    if mode == "git-sha":
        try:
            sha = subprocess.check_output(
                ["git", "rev-parse", "--short", "HEAD"]
            ).decode().strip()
            return sha
        except:
            return "unknown"

    return "1.0"


# ---------------------------------------------------------
# Build LLM Prompt
# ---------------------------------------------------------
def build_prompt(meta, diagram):
    return (
        "Generate a structured SAP CPI Technical Specification document.\n"
        "Sections required:\n"
        "1.1 Purpose\n1.2 Scope\n"
        "2.1 Integration Architecture\n2.2 Integration Components\n"
        "3.1 Scenario Description\n3.2 Data Flows\n3.3 Security Requirements\n"
        "4 Error Handling and Logging\n"
        "5 Testing Validation\n"
        "6 Reference Documents\n"
        "\nDiagram:\n" + diagram +
        "\nMetadata:\n" + json.dumps(meta, indent=2)
    )


# ---------------------------------------------------------
# Call DeepSeek (Ollama)
# ---------------------------------------------------------
def call_llm(prompt):
    res = requests.post(
        OLLAMA_URL,
        json={"model": MODEL_NAME, "prompt": prompt, "stream": False},
        timeout=180
    )
    res.raise_for_status()
    j = res.json()
    return j.get("response") or j.get("text") or str(j)


# ---------------------------------------------------------
# Extract Section Helpers
# ---------------------------------------------------------
def extract_section(md, heading):
    lines = md.splitlines()
    result, capture = [], False

    for line in lines:
        if line.strip().startswith(heading):
            capture = True
            continue
        if capture:
            if line.strip().startswith(tuple("1234567890#")):
                break
            result.append(line)

    return "\n".join(result).strip()


def extract_mermaid(md):
    if "```mermaid" not in md:
        return ""
    start = md.index("```mermaid")
    end = md.find("```", start + 10)
    if end == -1:
        return md[start:]
    return md[start:end + 3]


# ---------------------------------------------------------
# Render DOCX from Template
# ---------------------------------------------------------
def render_docx_from_template(template_path, output_path, fields):
    doc = Document(template_path)

    def replace_paragraph(paragraph):
        for k, v in fields.items():
            tag = "{{" + k + "}}"
            if tag in paragraph.text:
                for run in paragraph.runs:
                    run.text = run.text.replace(tag, v)

    # Replace in paragraphs
    for p in doc.paragraphs:
        replace_paragraph(p)

    # Replace in tables
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    replace_paragraph(p)

    doc.save(output_path)


# ---------------------------------------------------------
# Insert Logos in Header (FIXED)
# ---------------------------------------------------------
def inject_logos(docx_path, sap_logo, mm_logo):
    doc = Document(docx_path)
    header = doc.sections[0].header

    # Clear header
    for p in header.paragraphs:
        p.clear()

    # *** FIX: width required ***
    table = header.add_table(rows=1, cols=2, width=Inches(6))

    table.columns[0].width = Inches(3)
    table.columns[1].width = Inches(3)

    # Left Logo
    left = table.rows[0].cells[0].paragraphs[0]
    run_left = left.add_run()
    if os.path.exists(sap_logo):
        run_left.add_picture(str(sap_logo), width=Inches(1.3))
    left.alignment = WD_ALIGN_PARAGRAPH.LEFT

    # Right Logo
    right = table.rows[0].cells[1].paragraphs[0]
    run_right = right.add_run()
    if os.path.exists(mm_logo):
        run_right.add_picture(str(mm_logo), width=Inches(1.3))
    right.alignment = WD_ALIGN_PARAGRAPH.RIGHT

    doc.save(docx_path)


# ---------------------------------------------------------
# Final Output Writer
# ---------------------------------------------------------
def write_output(path, markdown, meta):
    out_dir = Path(path).parent / "docs"
    out_dir.mkdir(exist_ok=True)

    flow = meta["flowname"]
    version = determine_version(flow)
    today = datetime.now().strftime("%Y-%m-%d")
    author = "Sindhu K V"

    final_docx = out_dir / f"{flow}_Documentation_v{version}.docx"

    fields = {
        "flow_name": flow,
        "author": author,
        "date": today,
        "version": version,
        "purpose": extract_section(markdown, "1.1"),
        "scope": extract_section(markdown, "1.2"),
        "architecture": extract_section(markdown, "2.1"),
        "sender_systems": ", ".join(meta["senders"]),
        "receiver_systems": ", ".join(meta["receivers"]),
        "sender_adapters": ", ".join(meta["adapters"]),
        "receiver_adapters": "",
        "scripts_used": ", ".join(meta["scripts"]),
        "mappings": ", ".join(meta["mappings"]),
        "scenario_description": extract_section(markdown, "3.1"),
        "data_flows": extract_section(markdown, "3.2"),
        "security_requirements": extract_section(markdown, "3.3"),
        "error_handling": extract_section(markdown, "4."),
        "testing_validation": extract_section(markdown, "5."),
        "reference_documents": extract_section(markdown, "6."),
        "diagram": extract_mermaid(markdown)
    }

    # Render final doc
    render_docx_from_template(TEMPLATE_PATH, final_docx, fields)

    # Insert logos
    inject_logos(final_docx, SAP_LOGO_PATH, MM_LOGO_PATH)

    print(f"✔ Final document generated: {final_docx}")


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------
if __name__ == "__main__":
    for f in sys.argv[1:]:
        print(f"Processing {f}")
        meta = parse_iflw(f)
        diagram = high_level_diagram(meta)
        prompt = build_prompt(meta, diagram)
        markdown = call_llm(prompt)
        write_output(f, markdown, meta)

    print("Done.")
