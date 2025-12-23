from pathlib import Path
from docx import Document
from docx.shared import Inches
import xml.etree.ElementTree as ET
from ollama_client import generate

ROOT = Path(__file__).parent
LOGOS = ROOT / "logos"
OUTPUT = Path("generated-docs")
OUTPUT.mkdir(exist_ok=True)

def add_header(doc):
    header = doc.sections[0].header
    table = header.add_table(rows=1, cols=2)
    table.autofit = False

    left = table.cell(0, 0).paragraphs[0]
    left.add_run().add_picture(str(LOGOS / "sap.png"), width=Inches(1.2))

    right = table.cell(0, 1).paragraphs[0]
    right.alignment = 2
    right.add_run().add_picture(str(LOGOS / "motiveminds.png"), width=Inches(1.5))

def parse_iflow(path):
    tree = ET.parse(path)
    root = tree.getroot()
    names = set()

    for e in root.iter():
        if "name" in e.attrib:
            names.add(e.attrib["name"])

    return {
        "flow": path.stem,
        "components": ", ".join(names)
    }

def prompt(meta):
    return f"""
Generate SAP CPI Technical Documentation with the following structure:

1. Introduction
   1.1 Purpose
   1.2 Scope
2. Integration Overview
   2.1 Architecture
   2.2 Components
3. Integration Scenarios
4. Error Handling
5. Testing
6. Reference Documents

Integration Flow Name: {meta['flow']}
Components: {meta['components']}
"""

def generate_doc(iflw):
    meta = parse_iflow(iflw)
    content = generate(prompt(meta))

    doc = Document()
    add_header(doc)
    doc.add_heading(meta["flow"], level=1)

    for line in content.split("\n"):
        doc.add_paragraph(line)

    out = OUTPUT / f"{meta['flow']}.docx"
    doc.save(out)
    print(f"Generated {out}")

if __name__ == "__main__":
    for f in Path("cpi-artifacts").rglob("*.iflw"):
        generate_doc(f)
