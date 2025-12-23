import sys
from pathlib import Path
from docx import Document
from docx.shared import Inches
import xml.etree.ElementTree as ET
from ollama_client import generate

# -----------------------------
# Validate input
# -----------------------------
if len(sys.argv) < 2:
    print("❌ Package name not provided")
    print("Usage: python generate_iflow_docs.py <PACKAGE_NAME>")
    sys.exit(1)

PACKAGE_NAME = sys.argv[1]

ROOT = Path("cpi-artifacts") / PACKAGE_NAME
if not ROOT.exists():
    print(f"❌ Package '{PACKAGE_NAME}' not found under cpi-artifacts/")
    sys.exit(1)

LOGOS = Path("tools/logos")
OUTPUT = Path("generated-docs") / PACKAGE_NAME
OUTPUT.mkdir(parents=True, exist_ok=True)

# -----------------------------
# Helpers
# -----------------------------
def add_header(doc):
    header = doc.sections[0].header
    table = header.add_table(rows=1, cols=2)
    table.autofit = False

    table.cell(0, 0).paragraphs[0] \
        .add_run() \
        .add_picture(str(LOGOS / "sap.png"), width=Inches(1.2))

    right = table.cell(0, 1).paragraphs[0]
    right.alignment = 2
    right.add_run() \
        .add_picture(str(LOGOS / "motiveminds.png"), width=Inches(1.5))

def parse_iflow(iflw_path):
    tree = ET.parse(iflw_path)
    root = tree.getroot()

    components = set()
    for e in root.iter():
        if "name" in e.attrib:
            components.add(e.attrib["name"])

    return {
        "flow": iflw_path.stem,
        "components": ", ".join(components)
    }

def build_prompt(meta):
    return f"""
You are an SAP CPI Technical Architect.

Generate SAP CPI Technical Documentation with this structure:

1. Introduction
   1.1 Purpose
   1.2 Scope
2. Integration Overview
   2.1 Architecture
   2.2 Components
3. Integration Scenarios
4. Error Handling and Logging
5. Testing Validation
6. Reference Documents

Integration Flow Name: {meta['flow']}
Integration Package: {PACKAGE_NAME}
Components: {meta['components']}
"""

# -----------------------------
# Main execution
# -----------------------------
iflows = list(ROOT.rglob("*.iflw"))

if not iflows:
    print(f"⚠ No iFlows found in package {PACKAGE_NAME}")
    sys.exit(0)

for iflw in iflows:
    meta = parse_iflow(iflw)
    content = generate(build_prompt(meta))

    doc = Document()
    add_header(doc)
    doc.add_heading(meta["flow"], level=1)

    for line in content.split("\n"):
        doc.add_paragraph(line)

    out = OUTPUT / f"{meta['flow']}.docx"
    doc.save(out)

    print(f"✅ Generated {out}")
