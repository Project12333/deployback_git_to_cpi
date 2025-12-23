import argparse
from pathlib import Path
import xml.etree.ElementTree as ET
from datetime import date

from docx import Document
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

from ollama_client import call_ollama

# -------------------------------------------------
# Argument parsing
# -------------------------------------------------
parser = argparse.ArgumentParser(description="Generate SAP CPI iFlow documentation")
parser.add_argument("--package", required=True)
parser.add_argument("--author", default="Sindhu")
args = parser.parse_args()

PACKAGE = args.package
AUTHOR = args.author

# -------------------------------------------------
# Paths
# -------------------------------------------------
PACKAGE_DIR = Path("cpi-artifacts") / PACKAGE
if not PACKAGE_DIR.exists():
    raise SystemExit(f"❌ Package '{PACKAGE}' not found")

OUTPUT_DIR = Path("generated-docs") / PACKAGE
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

LOGOS_DIR = Path("tools/logos")
SAP_LOGO = LOGOS_DIR / "sap.png"
MM_LOGO = LOGOS_DIR / "motiveminds.png"

# -------------------------------------------------
# Header (logos)
# -------------------------------------------------
def add_header(doc: Document):
    header = doc.sections[0].header
    table = header.add_table(rows=1, cols=2, width=Inches(6.5))
    table.autofit = False

    left = table.cell(0, 0).paragraphs[0]
    left.add_run().add_picture(str(SAP_LOGO), width=Inches(1.2))

    right = table.cell(0, 1).paragraphs[0]
    right.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    right.add_run().add_picture(str(MM_LOGO), width=Inches(1.5))

# -------------------------------------------------
# Cover page
# -------------------------------------------------
def add_cover_page(doc: Document, flow_name: str):
    doc.add_heading(flow_name, level=0)

    table = doc.add_table(rows=3, cols=2)
    table.style = "Table Grid"

    table.cell(0, 0).text = "Author:"
    table.cell(0, 1).text = AUTHOR

    table.cell(1, 0).text = "Date:"
    table.cell(1, 1).text = date.today().isoformat()

    table.cell(2, 0).text = "Version:"
    table.cell(2, 1).text = "Draft"

    doc.add_page_break()

# -------------------------------------------------
# Table of Contents (static)
# -------------------------------------------------
def add_table_of_contents(doc: Document):
    doc.add_heading("Table of Contents", level=1)

    toc = [
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

# -------------------------------------------------
# CPI parsing
# -------------------------------------------------
def parse_iflow(iflw_path: Path):
    components = set()
    try:
        root = ET.parse(iflw_path).getroot()
        for e in root.iter():
            if "name" in e.attrib:
                components.add(e.attrib["name"])
    except Exception:
        pass

    return {
        "flow_name": iflw_path.stem,
        "components": ", ".join(sorted(components))
    }

# -------------------------------------------------
# Prompt
# -------------------------------------------------
def build_prompt(meta: dict) -> str:
    return f"""
Generate ONLY the section content text.
DO NOT use Markdown (#, ##, ###).
DO NOT generate title page or table of contents.

Sections:
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

Package: {PACKAGE}
Flow: {meta['flow_name']}
Components: {meta['components']}
"""

# -------------------------------------------------
# Clean AI output
# -------------------------------------------------
def clean_text(text: str):
    lines = []
    for l in text.splitlines():
        l = l.replace("#", "").strip()
        if l:
            lines.append(l)
    return lines

# -------------------------------------------------
# Main
# -------------------------------------------------
iflows = list(PACKAGE_DIR.rglob("**/*.iflw"))

for iflw in iflows:
    meta = parse_iflow(iflw)
    ai_text = call_ollama(build_prompt(meta))
    lines = clean_text(ai_text)

    doc = Document()
    add_header(doc)
    add_cover_page(doc, meta["flow_name"])
    add_table_of_contents(doc)

    for line in lines:
        if line.startswith(("1.", "2.", "3.", "4.", "5.", "6.")):
            doc.add_heading(line, level=1)
        elif line.startswith(("1.1", "1.2", "2.1", "2.2", "3.1", "3.2", "3.3")):
            doc.add_heading(line, level=2)
        else:
            doc.add_paragraph(line)

    output = OUTPUT_DIR / f"{meta['flow_name']}.docx"
    doc.save(output)
    print(f"✅ Generated: {output}")
