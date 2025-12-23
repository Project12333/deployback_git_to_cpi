import argparse
from pathlib import Path
import xml.etree.ElementTree as ET

from docx import Document
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

from ollama_client import call_ollama

# -------------------------------------------------
# Argument parsing
# -------------------------------------------------
parser = argparse.ArgumentParser(description="Generate SAP CPI iFlow documentation")
parser.add_argument(
    "--package",
    required=True,
    help="CPI package folder name inside cpi-artifacts"
)
args = parser.parse_args()
PACKAGE = args.package

# -------------------------------------------------
# Paths
# -------------------------------------------------
PACKAGE_DIR = Path("cpi-artifacts") / PACKAGE
if not PACKAGE_DIR.exists():
    raise SystemExit(f"❌ Package '{PACKAGE}' not found under cpi-artifacts/")

OUTPUT_DIR = Path("generated-docs") / PACKAGE
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

LOGOS_DIR = Path("tools/logos")
SAP_LOGO = LOGOS_DIR / "sap.png"
MM_LOGO = LOGOS_DIR / "motiveminds.png"

if not SAP_LOGO.exists() or not MM_LOGO.exists():
    raise SystemExit("❌ Logo files missing in tools/logos")

# -------------------------------------------------
# Word helpers
# -------------------------------------------------
def add_header(doc: Document):
    section = doc.sections[0]
    section.different_first_page_header_footer = False

    header = section.header

    # Create table WITH WIDTH (mandatory in header)
    table = header.add_table(
        rows=1,
        cols=2,
        width=Inches(6.5)
    )
    table.autofit = False

    # Left cell – SAP logo
    left_cell = table.cell(0, 0)
    left_para = left_cell.paragraphs[0]
    left_para.alignment = WD_ALIGN_PARAGRAPH.LEFT
    left_para.add_run().add_picture(
        str(SAP_LOGO),
        width=Inches(1.2)
    )

    # Right cell – MotiveMinds logo
    right_cell = table.cell(0, 1)
    right_para = right_cell.paragraphs[0]
    right_para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    right_para.add_run().add_picture(
        str(MM_LOGO),
        width=Inches(1.5)
    )

# -------------------------------------------------
# CPI parsing
# -------------------------------------------------
def parse_iflow(iflw_path: Path):
    try:
        tree = ET.parse(iflw_path)
        root = tree.getroot()
    except Exception as e:
        return {
            "flow_name": iflw_path.stem,
            "components": "Unable to parse iFlow XML"
        }

    components = set()
    for elem in root.iter():
        name = elem.attrib.get("name")
        if name:
            components.add(name)

    return {
        "flow_name": iflw_path.stem,
        "components": ", ".join(sorted(components))
    }

def build_prompt(meta: dict) -> str:
    return f"""
You are a senior SAP CPI Technical Architect.

Generate a professional SAP CPI Technical Specification with the structure:

1. Introduction
   1.1 Purpose
   1.2 Scope

2. Integration Overview
   2.1 Integration Architecture
   2.2 Integration Components

3. Integration Scenarios
   3.1 Scenario Description
   3.2 Data Flow
   3.3 Security Requirements

4. Error Handling and Logging
5. Testing and Validation
6. Reference Documents

Package Name: {PACKAGE}
Integration Flow Name: {meta['flow_name']}
Components: {meta['components']}

Use concise, enterprise-grade language.
"""

# -------------------------------------------------
# Main execution
# -------------------------------------------------
iflows = list(PACKAGE_DIR.rglob("*.iflw"))

print(f"📦 Package path: {PACKAGE_DIR}")
print(f"🔍 iFlows found: {len(iflows)}")

if not iflows:
    raise SystemExit("⚠ No iFlows found")

for iflw in iflows:
    print(f"\n➡ Processing iFlow: {iflw.stem}")

    meta = parse_iflow(iflw)

    print("🤖 Sending request to Ollama (DeepSeek)...")
    ai_text = call_ollama(build_prompt(meta))

    doc = Document()
    add_header(doc)

    doc.add_heading(meta["flow_name"], level=1)

    for line in ai_text.splitlines():
        doc.add_paragraph(line)

    output_file = OUTPUT_DIR / f"{meta['flow_name']}.docx"
    doc.save(output_file)

    print(f"✅ Generated: {output_file}")

print("\n🎉 Documentation generation completed successfully")
