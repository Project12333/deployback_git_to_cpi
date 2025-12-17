import os
import argparse
import xml.etree.ElementTree as ET
from docx import Document
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, ns

from ollama_client import generate_section

SAP_LOGO = "tools/logos/sap.png"
MOTIVE_LOGO = "tools/logos/motiveminds.png"


# -------------------------------------------------
# Utility: Find .iflw file
# -------------------------------------------------
def find_iflow_file(package):
    base = f"cpi-artifacts/{package}"
    for root, _, files in os.walk(base):
        for f in files:
            if f.endswith(".iflw"):
                return os.path.join(root, f)
    return None


# -------------------------------------------------
# Parse iFlow (.iflw XML) – best effort
# -------------------------------------------------
def parse_iflow(iflw_path):
    meta = {
        "flow_name": os.path.basename(iflw_path),
        "sender_adapters": set(),
        "receiver_adapters": set(),
        "scripts": set(),
        "mappings": set(),
        "properties": set(),
    }

    try:
        tree = ET.parse(iflw_path)
        root = tree.getroot()

        for elem in root.iter():
            tag = elem.tag.lower()

            if "sender" in tag or "inbound" in tag:
                meta["sender_adapters"].add(elem.attrib.get("name", "Unknown"))

            if "receiver" in tag or "outbound" in tag:
                meta["receiver_adapters"].add(elem.attrib.get("name", "Unknown"))

            if "groovy" in tag or "script" in tag:
                meta["scripts"].add(elem.attrib.get("name", "GroovyScript"))

            if "mapping" in tag:
                meta["mappings"].add(elem.attrib.get("name", "MessageMapping"))

            if "property" in tag:
                meta["properties"].add(elem.attrib.get("name", "ExchangeProperty"))

    except Exception as e:
        meta["error"] = str(e)

    # Convert sets to lists
    for k in meta:
        if isinstance(meta[k], set):
            meta[k] = sorted(meta[k])

    return meta


# -------------------------------------------------
# Generate Mermaid architecture diagram
# -------------------------------------------------
def generate_mermaid(meta):
    return f"""
flowchart LR
    Sender[Sender System]
    CPI[SAP CPI iFlow]
    Receiver[Receiver System]

    Sender -->|{', '.join(meta['sender_adapters']) or 'Adapter'}| CPI
    CPI -->|{', '.join(meta['receiver_adapters']) or 'Adapter'}| Receiver
"""


# -------------------------------------------------
# Word helpers
# -------------------------------------------------
def add_header(section):
    header = section.header
    header.is_linked_to_previous = False

    table = header.add_table(rows=1, cols=2, width=Inches(6))

    left = table.cell(0, 0).paragraphs[0]
    left.add_run().add_picture(SAP_LOGO, width=Inches(1.2))

    right = table.cell(0, 1).paragraphs[0]
    right.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    right.add_run().add_picture(MOTIVE_LOGO, width=Inches(1.5))


def add_toc(doc):
    p = doc.add_paragraph()
    r = p.add_run()

    begin = OxmlElement("w:fldChar")
    begin.set(ns.qn("w:fldCharType"), "begin")

    instr = OxmlElement("w:instrText")
    instr.text = 'TOC \\o "1-3" \\h \\z \\u'

    end = OxmlElement("w:fldChar")
    end.set(ns.qn("w:fldCharType"), "end")

    r._r.extend([begin, instr, end])


# -------------------------------------------------
# Main doc generator
# -------------------------------------------------
def generate_doc(package):
    print("NEW VERSION LOADED - IFLOW AWARE GENERATION")

    iflw = find_iflow_file(package)
    if not iflw:
        raise Exception("No .iflw file found in package")

    meta = parse_iflow(iflw)
    mermaid = generate_mermaid(meta)

    out_dir = f"cpi-artifacts/{package}/docs"
    os.makedirs(out_dir, exist_ok=True)

    doc = Document()
    add_header(doc.sections[0])

    # Cover
    doc.add_heading("SAP CPI Integration Technical Specification", 0)
    doc.add_paragraph(f"iFlow: {meta['flow_name']}")
    doc.add_page_break()

    # TOC
    doc.add_heading("Table of Contents", level=1)
    add_toc(doc)
    doc.add_page_break()

    # -------- Sections (REAL metadata injected) --------
    sections = [
        ("1. Introduction", f"This document describes the SAP CPI iFlow {meta['flow_name']}."),
        ("1.1 Purpose", "To document the integration flow based on actual CPI configuration."),
        ("1.2 Scope", "Covers adapters, scripts, mappings, and runtime behavior."),
        ("2. Integration Overview", f"Sender adapters: {meta['sender_adapters']}, Receiver adapters: {meta['receiver_adapters']}"),
        ("2.1 Integration Architecture", "Architecture derived from iFlow configuration."),
        ("2.2 Integration Components", f"Scripts: {meta['scripts']}, Mappings: {meta['mappings']}"),
        ("3. Integration Scenarios", "Describes the business scenario supported by this iFlow."),
        ("3.1 Scenario Description", "End-to-end flow execution."),
        ("3.2 Data Flows", "Message flow from sender to receiver."),
        ("3.3 Security Requirements", "Security handled by CPI tenant configuration."),
        ("4. Error Handling and Logging", "Exception subprocesses and CPI monitoring."),
        ("5. Testing Validation", "Unit and integration testing in CPI."),
        ("6. Reference Documents", "SAP CPI official documentation."),
    ]

    for title, context in sections:
        print(f"Generating section: {title}")
        level = 1 if title.count(".") == 1 else 2
        doc.add_heading(title, level)
        doc.add_paragraph(generate_section(title, context))

    # -------- Architecture Diagram --------
    doc.add_page_break()
    doc.add_heading("Integration Architecture Diagram", level=1)
    doc.add_paragraph("Mermaid Diagram (can be rendered externally):")
    doc.add_paragraph(mermaid)

    out_file = f"{out_dir}/{package}_Technical_Spec.docx"
    doc.save(out_file)
    print(f"Document generated: {out_file}")


# -------------------------------------------------
# Entry point
# -------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", required=True)
    args = parser.parse_args()
    generate_doc(args.package)
