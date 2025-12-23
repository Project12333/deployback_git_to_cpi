import sys
from pathlib import Path
import xml.etree.ElementTree as ET
from docx import Document
from docx.shared import Inches
from ollama_client import call_ollama

# -----------------------------
# Validate input
# -----------------------------
if len(sys.argv) < 2:
    print("❌ Usage: python generate_iflow_docs.py <PACKAGE_NAME>")
    sys.exit(1)

PACKAGE = sys.argv[1]
PACKAGE_DIR = Path("cpi-artifacts") / PACKAGE

if not PACKAGE_DIR.exists():
    print(f"❌ Package '{PACKAGE}' not found")
    sys.exit(1)

OUTPUT_DIR = Path("generated-docs") / PACKAGE
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

LOGOS = Path("tools/logos")

# -----------------------------
def add_header(doc):
    header = doc.sections[0].header
    table = header.add_table(1, 2)

    table.cell(0, 0).paragraphs[0] \
        .add_run() \
        .add_picture(str(LOGOS / "sap.png"), width=Inches(1.2))

    right = table.cell(0, 1).paragraphs[0]
    right.alignment = 2
    right.add_run() \
        .add_picture(str(LOGOS / "motiveminds.png"), width=Inches(1.5))

def parse_iflow(iflw):
    tree = ET.parse(iflw)
    root = tree.getroot()
    comps = set()

    for e in root.iter():
        if "name" in e.attrib:
            comps.add(e.attrib["name"])

    return {
        "flow": iflw.stem,
        "components": ", ".join(comps)
    }

def build_prompt(meta):
    return f"""
You are an SAP CPI Technical Architect.

Create a SAP CPI Technical Specification with:
1. Introduction (Purpose, Scope)
2. Integration Overview (Architecture, Components)
3. Integration Scenarios
4. Error Handling and Logging
5. Testing Validation
6. Reference Documents

Package: {PACKAGE}
Integration Flow: {meta['flow']}
Components: {meta['components']}
"""

# -----------------------------
# Main
# -----------------------------
for iflw in PACKAGE_DIR.rglob("*.iflw"):
    meta = parse_iflow(iflw)
    content = call_ollama(build_prompt(meta))

    doc = Document()
    add_header(doc)
    doc.add_heading(meta["flow"], level=1)

    for line in content.split("\n"):
        doc.add_paragraph(line)

    out = OUTPUT_DIR / f"{meta['flow']}.docx"
    doc.save(out)

    print(f"✅ Generated {out}")
