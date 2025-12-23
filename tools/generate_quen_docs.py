#!/usr/bin/env python3

import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from docx import Document

BASE_ARTIFACTS_DIR = Path("cpi-artifacts")
BASE_DOCS_DIR = Path("docs")

# -----------------------------------------------------
# XML helpers
# -----------------------------------------------------

def strip_ns(tag):
    return tag.split("}")[-1] if "}" in tag else tag

def parse_iflow(xml_text):
    root = ET.fromstring(xml_text)

    adapters = set()
    scripts = set()
    mappings = set()
    has_exception = False

    for elem in root.iter():
        tag = strip_ns(elem.tag).lower()

        # Adapter detection
        if "adapter" in tag:
            adapter_type = elem.attrib.get("type") or elem.attrib.get("name")
            if adapter_type:
                adapters.add(adapter_type)

        # Groovy scripts
        if "groovy" in tag or "script" in tag:
            name = elem.attrib.get("name")
            if name:
                scripts.add(name)

        # Message mappings
        if "mapping" in tag:
            name = elem.attrib.get("name")
            if name:
                mappings.add(name)

        # Exception subprocess
        if "exception" in tag:
            has_exception = True

    return {
        "adapters": sorted(adapters),
        "scripts": sorted(scripts),
        "mappings": sorted(mappings),
        "has_exception": has_exception,
    }

# -----------------------------------------------------
# DOCX writer
# -----------------------------------------------------

def generate_docx(flow_name, package, data, output_file):
    doc = Document()

    doc.add_heading(flow_name, level=1)

    doc.add_heading("1. Introduction", level=2)
    doc.add_paragraph(
        f"This document describes the SAP CPI integration flow '{flow_name}' "
        f"belonging to the package '{package}'."
    )

    doc.add_heading("1.1 Purpose", level=3)
    doc.add_paragraph("To enable structured and automated data exchange between systems.")

    doc.add_heading("1.2 Scope", level=3)
    doc.add_paragraph("Covers inbound, processing, and outbound integration logic.")

    doc.add_heading("2. Integration Overview", level=2)

    doc.add_heading("2.1 Integration Architecture", level=3)
    if data["adapters"]:
        doc.add_paragraph("Adapters involved:")
        for a in data["adapters"]:
            doc.add_paragraph(f"- {a}", style="List Bullet")
    else:
        doc.add_paragraph("No adapters detected.")

    doc.add_heading("2.2 Integration Components", level=3)

    doc.add_paragraph("Groovy Scripts:")
    if data["scripts"]:
        for s in data["scripts"]:
            doc.add_paragraph(f"- {s}", style="List Bullet")
    else:
        doc.add_paragraph("- None")

    doc.add_paragraph("Message Mappings:")
    if data["mappings"]:
        for m in data["mappings"]:
            doc.add_paragraph(f"- {m}", style="List Bullet")
    else:
        doc.add_paragraph("- None")

    doc.add_heading("3. Integration Scenarios", level=2)

    doc.add_heading("3.1 Scenario Description", level=3)
    doc.add_paragraph("Processes inbound messages and applies transformations as configured.")

    doc.add_heading("3.2 Data Flow", level=3)
    doc.add_paragraph("Sender → CPI → Receiver")

    doc.add_heading("3.3 Security Requirements", level=3)
    doc.add_paragraph("Standard CPI security artifacts are applied where configured.")

    doc.add_heading("4. Error Handling and Logging", level=2)
    if data["has_exception"]:
        doc.add_paragraph("Exception subprocess is configured for error handling.")
    else:
        doc.add_paragraph("Default CPI error handling is applied.")

    doc.add_heading("5. Testing and Validation", level=2)
    doc.add_paragraph("Integration flow validated using test payloads and monitoring tools.")

    doc.save(output_file)

# -----------------------------------------------------
# Main
# -----------------------------------------------------

def main():
    if len(sys.argv) != 2:
        print("Usage: python generate_quen_docs.py <PACKAGE_NAME>")
        sys.exit(1)

    package = sys.argv[1]
    package_path = BASE_ARTIFACTS_DIR / package

    if not package_path.exists():
        print(f"❌ Package not found: {package}")
        sys.exit(1)

    flows = list(package_path.rglob("*.iflw"))
    if not flows:
        print("⚠️ No iFlows found")
        return

    output_dir = BASE_DOCS_DIR / package
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n🚀 Generating documentation for package: {package}\n")

    for flow in flows:
        try:
            xml_text = flow.read_text(encoding="utf-8")
            data = parse_iflow(xml_text)

            output_file = output_dir / f"{flow.stem}.docx"
            generate_docx(flow.stem, package, data, output_file)

            print(f"✅ Generated {output_file}")

        except Exception as e:
            print(f"❌ Failed {flow.name}: {e}")

    print("\n🎉 Documentation generation completed successfully")

if __name__ == "__main__":
    main()
