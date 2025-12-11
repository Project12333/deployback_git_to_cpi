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
                elem.attrib.get("name") or
                elem.attrib.get("id") or
                elem.attrib.get("idref") or
                tag
            )

            if "sender" in tag or "start" in tag:
                meta["senders"].append(name)

            if "receiver" in tag or "end" in tag:
                meta["receivers"].append(name)

            if "adapter" in tag:
                meta["adapters"].append(name)

            if "script" in tag or "scripttask" in tag or "groovy" in tag:
                meta["scripts"].append(name)

            if "mapping" in tag:
                meta["mappings"].append(name)

            meta["steps"].append(name)

    except Exception as e:
        meta["error"] = f"XML parse error: {e}"

    return meta


# ---------------------------------------------------------
# High-Level Mermaid Diagram
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
# Version from workflow inputs
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
# Build DeepSeek prompt
# ---------------------------------------------------------
def build_prompt(meta, diagram):
    return (
        "You are a senior SAP CPI integration architect. Produce a structured "
        "technical specification in Markdown following EXACT sections:\n\n"
        "1. Introduction\n"
        "  1.1 Purpose\n"
        "  1.2 Scope\n\n"
        "2. Integration Overview\n"
        "  2.1 Integration Architecture\n"
        "  2.2 Integration Components\n\n"
        "3. Integration Scenarios\n"
        "  3.1 Scenario Description\n"
        "  3.2 Data Flows\n"
        "  3.3 Security Requirements\n\n"
        "4. Error Handling and Logging\n"
        "5. Testing Validation\n"
        "6. Reference Documents\n\n"
        "Appendix: High-Level Process Flow Diagram\n\n"
        "Use the following metadata:\n"
        f"{json.dumps(meta, indent=2)}\n\n"
        "Insert this Mermaid diagram exactly under the Appendix:\n"
        f"{diagram}\n\n"
        "Output ONLY the markdown, no explanations."
    )


# ---------------------------------------------------------
# Call DeepSeek via Ollama
# ---------------------------------------------------------
def call_llm(prompt):
    res = requests.post(
        OLLAMA_URL,
        json={"model": MODEL_NAME, "prompt": prompt, "stream": False},
        timeout=120
    )
    res.raise_for_status()
    j = res.json()
    return j.get("response") or j.get("text") or str(j)


# ---------------------------------------------------------
# Extract markdown sections
# ---------------------------------------------------------
def extract_section(md, heading):
    lines = md.splitlines()
    result = []
    start = False

    for i, line in enumerate(lines):
        if line.strip().startswith(heading):
            start = True
            continue

        if start:
            if line.strip().startswith(tuple("0123456789")) or line.startswith("#"):
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
# Replace placeholders in DOCX template
# ---------------------------------------------------------
def render_docx_from_template(template_path, output_path, fields):
    doc = Document(template_path)

    def replace_para(p):
        for key, value in fields.items():
            placeholder = "{{" + key + "}}"
            if placeholder in p.text:
                for run in p.runs:
                    run.text = run.text.replace(placeholder, value)

    def replace_table(t):
        for row in t.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    replace_para(p)

    for p in doc.paragraphs:
        replace_para(p)

    for t in doc.tables:
        replace_table(t)

    doc.save(output_path)


# ---------------------------------------------------------
# Insert Logos into Header
# ---------------------------------------------------------
def inject_logos(docx_path, sap_logo, mm_logo):
    try:
        doc = Document(docx_path)
        header = doc.sections[0].header

        # Clear existing content
        for p in header.paragraphs:
            p.clear()

        table = header.add_table(rows=1, cols=2)
        table.autofit = False
        table.columns[0].width = Inches(3)
        table.columns[1].width = Inches(3)

        # SAP logo left
        left = table.rows[0].cells[0].paragraphs[0]
        run_left = left.add_run()
        if os.path.exists(sap_logo):
            run_left.add_picture(sap_logo, width=Inches(1.4))
        left.alignment = WD_ALIGN_PARAGRAPH.LEFT

        # Motiveminds logo right
        right = table.rows[0].cells[1].paragraphs[0]
        run_right = right.add_run()
        if os.path.exists(mm_logo):
            run_right.add_picture(mm_logo, width=Inches(1.4))
        right.alignment = WD_ALIGN_PARAGRAPH.RIGHT

        doc.save(docx_path)
        print(f"✔ Logos inserted into: {docx_path}")

    except Exception as e:
        print("⚠ Error inserting logos:", e)


# ---------------------------------------------------------
# Write final DOCX
# ---------------------------------------------------------
def write_output(path, markdown, meta):
    out = Path(path).parent / "docs"
    out.mkdir(exist_ok=True)

    flow = meta["flowname"]
    today = datetime.now().strftime("%Y-%m-%d")
    version = determine_version(flow)
    author = "Sindhu K V"

    temp_md = out / f"{flow}.md"
    temp_docx = out / f"{flow}_temp.docx"
    final_docx = out / f"{flow}_Documentation_v{version}.docx"

    # Save md for debugging
    temp_md.write_text(markdown, encoding="utf-8")

    # Convert md → temp docx
    subprocess.run(["pandoc", str(temp_md), "-o", str(temp_docx)], check=False)

    # Prepare placeholders
    fields = {
        "flow_name": flow,
        "author": author,
        "date": today,
        "version": version,
        "purpose": extract_section(markdown, "1.1 Purpose"),
        "scope": extract_section(markdown, "1.2 Scope"),
        "architecture": extract_section(markdown, "2.1 Integration Architecture"),
        "sender_systems": ", ".join(meta["senders"]),
        "receiver_systems": ", ".join(meta["receivers"]),
        "sender_adapters": ", ".join(meta["adapters"]),
        "receiver_adapters": "<Not parsed>",
        "scripts_used": ", ".join(meta["scripts"]),
        "mappings": ", ".join(meta["mappings"]),
        "scenario_description": extract_section(markdown, "3.1 Scenario Description"),
        "data_flows": extract_section(markdown, "3.2 Data Flows"),
        "security_requirements": extract_section(markdown, "3.3 Security Requirements"),
        "error_handling": extract_section(markdown, "4. Error Handling"),
        "testing_validation": extract_section(markdown, "5. Testing Validation"),
        "reference_documents": extract_section(markdown, "6. Reference Documents"),
        "diagram": extract_mermaid(markdown)
    }

    # Build final docx from template
    render_docx_from_template(
        "tools/reference.docx",
        final_docx,
        fields
    )

    # Insert logos
    inject_logos(
        final_docx,
        "tools/logos/sap.png",
        "tools/logos/motiveminds.png"
    )

    print(f"✔ FINAL DOCX GENERATED: {final_docx}")


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
