import os
import argparse
import xml.etree.ElementTree as ET
from datetime import date

from docx import Document
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

from ollama_client import generate_section

# -------------------------------------------------
# Logo paths
# -------------------------------------------------
SAP_LOGO = "tools/logos/sap.png"
MOTIVE_LOGO = "tools/logos/motiveminds.png"


# -------------------------------------------------
# Locate iFlow file
# -------------------------------------------------
def find_iflow(package):
    base = f"cpi-artifacts/{package}"
    for root, _, files in os.walk(base):
        for file in files:
            if file.endswith(".iflw"):
                return os.path.join(root, file)
    return None


# -------------------------------------------------
# Extract iFlow semantics from BPMN XML
# -------------------------------------------------
def extract_iflow_semantics(iflw_path):
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
        sap_type = elem.attrib.get("{http://sap.com/bpmn/extension}type", "")

        if tag == "startEvent":
            data["senders"].add("Message-based Start Event")

        elif tag == "endEvent":
            data["receivers"].add("Receiver Endpoint")

        elif tag == "serviceTask":
            if "ContentModifier" in sap_type:
                data["content_modifiers"].append(name or "Content Modifier")
            elif "Groovy" in sap_type:
                data["scripts"].append(name or "Groovy Script")
            elif "MessageMapping" in sap_type:
                data["mappings"].append(name or "Message Mapping")

        elif tag == "subProcess" and elem.attrib.get("triggeredByEvent") == "true":
            data["exception_handling"] = True

    return data


# -------------------------------------------------
# Word header with logos
# -------------------------------------------------
def add_header(section):
    header = section.header
    header.is_linked_to_previous = False

    table = header.add_table(rows=1, cols=2, width=Inches(6))

    left_para = table.cell(0, 0).paragraphs[0]
    left_para.add_run().add_picture(SAP_LOGO, width=Inches(1.2))

    right_para = table.cell(0, 1).paragraphs[0]
    right_para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    right_para.add_run().add_picture(MOTIVE_LOGO, width=Inches(1.5))


# -------------------------------------------------
# Main document generator
# -------------------------------------------------
def generate_doc(package):
    iflw_path = find_iflow(package)
    if not iflw_path:
        raise Exception("No .iflw file found for the given package")

    iflow = extract_iflow_semantics(iflw_path)

    output_dir = f"cpi-artifacts/{package}/docs"
    os.makedirs(output_dir, exist_ok=True)

    doc = Document()
    add_header(doc.sections[0])

    # ---------------- COVER PAGE ----------------
    doc.add_heading(iflow["flow_name"], level=0)
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

    # ---------------- CONTENT SECTIONS ----------------
    sections = [
        (
            "1.1 Purpose",
            f"This document provides a technical description of the SAP Cloud Integration "
            f"iFlow '{iflow['flow_name']}' based strictly on its design-time configuration."
        ),
        (
            "1.2 Scope",
            "The scope includes message flow behavior, processing steps, and runtime "
            "characteristics explicitly modeled in the iFlow."
        ),
        (
            "2.1 Integration Architecture",
            f"Sender: {', '.join(iflow['senders']) or 'Not defined in iFlow'}\n"
            f"Receiver: {', '.join(iflow['receivers']) or 'Not defined in iFlow'}\n"
            "Runtime: SAP Cloud Integration tenant"
        ),
        (
            "2.2 Integration Components",
            f"Content Modifiers: {', '.join(iflow['content_modifiers']) or 'None'}\n"
            f"Groovy Scripts: {', '.join(iflow['scripts']) or 'None'}\n"
            f"Message Mappings: {', '.join(iflow['mappings']) or 'None'}"
        ),
        (
            "3.1 Scenario Description",
            "The integration scenario processes inbound messages through a linear "
            "sequence of steps defined in the iFlow BPMN model."
        ),
        (
            "3.2 Data Flows",
            "Message flows sequentially from the sender through configured processing "
            "steps and is delivered to the receiver endpoint."
        ),
        (
            "3.3 Security Requirements",
            "Security is enforced at adapter level. No explicit security configuration "
            "is modeled directly within the iFlow design."
        ),
        (
            "4. Error Handling and Logging",
            "Explicit exception handling is modeled in the iFlow."
            if iflow["exception_handling"]
            else "The iFlow relies on standard SAP CPI error handling and monitoring."
        ),
        (
            "5. Testing Validation",
            "Testing includes test message execution, payload verification, and "
            "monitoring via SAP CPI operational dashboards."
        ),
        (
            "6. Reference Documents",
            "SAP Integration Suite – Cloud Integration official documentation."
        )
    ]

    for title, context in sections:
        doc.add_heading(title, level=2)
        doc.add_paragraph(generate_section(title, context))

    output_file = f"{output_dir}/{package}_Technical_Spec.docx"
    doc.save(output_file)

    print(f"Document generated successfully: {output_file}")


# -------------------------------------------------
# Entry point
# -------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate SAP CPI iFlow documentation")
    parser.add_argument("--package", required=True, help="CPI package name")
    args = parser.parse_args()

    generate_doc(args.package)
