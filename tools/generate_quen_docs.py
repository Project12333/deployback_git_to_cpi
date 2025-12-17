import os
import argparse
import xml.etree.ElementTree as ET
from datetime import date
from docx import Document
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, ns

from ollama_client import generate_section

SAP_LOGO = "tools/logos/sap.png"
MOTIVE_LOGO = "tools/logos/motiveminds.png"


# -------------------------------------------------
# Locate iFlow
# -------------------------------------------------
def find_iflow(package):
    base = f"cpi-artifacts/{package}"
    for root, _, files in os.walk(base):
        for f in files:
            if f.endswith(".iflw"):
                return os.path.join(root, f)
    return None


# -------------------------------------------------
# Extract REAL iFlow semantics
# -------------------------------------------------
def extract_iflow_semantics(iflw_path):
    nsmap = {
        "bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL",
        "sap": "http://sap.com/bpmn/extension"
    }

    tree = ET.parse(iflw_path)
    root = tree.getroot()

    data = {
        "flow_name": os.path.splitext(os.path.basename(iflw_path))[0],
        "senders": set(),
        "receivers": set(),
        "content_modifiers": [],
        "scripts": [],
        "mappings": [],
        "exception_handling": False
    }

    for elem in root.iter():
        tag = elem.tag.split("}")[-1]
        name = elem.attrib.get("name", "").strip()

        if tag == "startEvent":
            data["senders"].add("Message-based Start Event")

        if tag == "endEvent":
            data["receivers"].add("Receiver Endpoint")

        if tag == "serviceTask":
            impl = elem.attrib.get("{http://sap.com/bpmn/extension}type", "")

            if "ContentModifier" in impl:
                data["content_modifiers"].append(name or "Content Modifier")
            elif "Groovy" in impl:
                data["scripts"].append(name or "Groovy Script")
            elif "MessageMapping" in impl:
                data["mappings"].append(name or "Message Mapping")

        if tag == "subProcess" and elem.attrib.get("triggeredByEvent") == "true":
            data["exception_handling"] = True

    return data


# -------------------------------------------------
# Word helpers
# -------------------------------------------------
def add_header(section):
    header = section.header
    header.is_linked_to_previous = False

    table = header.add_table(rows=1, cols=2, width=Inches(6))
    table.cell(0, 0).paragraphs[0].add_run().add_picture(SAP_LOGO, width=Inches(1.2))

    right = table.cell(0, 1).paragraphs[0]
    right.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    right.add_run().add_picture(MOTIVE_LOGO, width=Inches(1.5))


# -------------------------------------------------
# Main generator
# -------------------------------------------------
def generate_doc(package):
    iflw = find_iflow(package)
    if not iflw:
        raise Exception("No .iflw file found in package")

    iflow = extract_iflow_semantics(iflw)

    out_dir = f"cpi-artifacts/{package}/docs"
    os.makedirs(out_dir, exist_ok=True)

    doc = Document()
    add_header(doc.sections[0])

    # ---------------- COVER PAGE ----------------
    doc.add_heading(iflow["flow_name"], 0)
    doc.add_paragraph("\nAuthor\nSindhu")
    doc.add_paragraph(f"\nDate\n{date.today()}")
    doc.add_paragraph("\nVersion\nDraft")
    doc.add_page_break()

    # ---------------- TOC PAGE ----------------
    doc.add_heading("Table of Contents", level=1)
    doc.add_paragraph(
        "1. Introduction\n"
        "   1.1 Purpose\n"
        "   1.2 Scope\n\n"
        "2. Integration Overview\n"
        "   2.1 Integration Architecture\n"
        "   2.2 Integration Components\n\n"
        "3. Integration Scenarios\n"
        "   3.1 Scenario Description\n"
        "   3.2 Data Flows\n"
        "   3.3 Security Requirements\n\n"
        "4. Error Handling and Logging\n\n"
        "5. Testing Validation\n\n"
        "6. Reference Documents"
    )
    doc.add_page_break()

    # ---------------- CONTENT ----------------
    sections = [
        ("1.1 Purpose",
         f"This document describes the SAP Cloud Integration iFlow "
         f"'{iflow['flow_name']}' based strictly on its design-time configuration."),

        ("1.2 Scope",
         "The scope includes message flow behavior, processing steps, and runtime characteristics "
         "explicitly modeled in the iFlow."),

        ("2.1 Integration Architecture",
         f"Sender: {', '.join(iflow['senders']) or 'Not defined in iFlow'}\n"
         f"Receiver: {', '.join(iflow['receivers']) or 'Not defined in iFlow'}\n"
         "Runtime: SAP Cloud Integration tenant"),

        ("2.2 Integration Components",
         f"Content Modifiers: {', '.join(iflow['content_modifiers']) or 'None'}\n"
         f"Groovy Scripts: {', '.join(iflow['scripts']) or 'None'}\n"
         f"Message Mappings: {', '.join(iflow['mappings']) or 'None'}"),

        ("3.1 Scenario Description",
         "The iFlow processes inbound messages through a linear sequence of steps "
         "as defined in its BPMN model."),

        ("3.2 Data Flows",
         "Message flows from the sender through configured processing components "
         "and is delivered to the receiver endpoint."),

        ("3.3 Security Requirements",
         "Security settings are defined at adapter level. No explicit security configuration "
         "is visible within the iFlow design itself."),

        ("4. Error Handling and Logging",
         "Explicit exception handling is modeled in the iFlow."
         if iflow["exception_handling"]
         else "The iFlow relies
