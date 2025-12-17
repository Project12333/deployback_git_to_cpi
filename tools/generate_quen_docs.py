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
# Extract BPMN behavior
# -------------------------------------------------
def extract_bpmn(iflw_path):
    nsmap = {"bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL"}
    tree = ET.parse(iflw_path)
    root = tree.getroot()

    result = {
        "flow_name": os.path.splitext(os.path.basename(iflw_path))[0],
        "collaboration": "Default Collaboration",
        "participants": [],
        "steps": []
    }

    collab = root.find(".//bpmn:collaboration", nsmap)
    if collab is not None:
        result["collaboration"] = collab.attrib.get("name", "Default Collaboration")
        for p in collab.findall("bpmn:participant", nsmap):
            result["participants"].append(p.attrib.get("name", "Unnamed Participant"))

    process = root.find(".//bpmn:process", nsmap)
    if process is not None:
        for elem in process:
            tag = elem.tag.split("}")[-1]
            name = elem.attrib.get("name", tag)

            if tag == "startEvent":
                result["steps"].append("The integration flow starts with a message start event.")
            elif tag in ["callActivity", "task", "serviceTask"]:
                result["steps"].append(
                    f"The activity '{name}' processes or enriches the message."
                )
            elif tag == "endEvent":
                result["steps"].append("The flow ends with an end event after successful processing.")

    return result


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
# Main generator
# -------------------------------------------------
def generate_doc(package):
    iflw = find_iflow(package)
    if not iflw:
        raise Exception("No .iflw file found")

    bpmn = extract_bpmn(iflw)
    steps_text = "\n".join(f"- {s}" for s in bpmn["steps"])

    out_dir = f"cpi-artifacts/{package}/docs"
    os.makedirs(out_dir, exist_ok=True)

    doc = Document()
    add_header(doc.sections[0])

    # ---------------- PAGE 1: COVER ----------------
    doc.add_heading(bpmn["flow_name"], 0)
    doc.add_paragraph("\nAuthor\nSindhu")
    doc.add_paragraph(f"\nDate\n{date.today()}")
    doc.add_paragraph("\nVersion\nDraft")
    doc.add_page_break()

    # ---------------- PAGE 2: TOC ----------------
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

    # ---------------- PAGE 3+: CONTENT ----------------
    sections = [
        ("1.1 Purpose", f"This document provides a technical specification for the SAP CPI integration flow '{bpmn['flow_name']}'."),
        ("1.2 Scope", "The scope includes internal processing logic, message flow, and operational behavior."),
        ("2.1 Integration Architecture", f"The iFlow operates in collaboration '{bpmn['collaboration']}' involving participants {', '.join(bpmn['participants'])}."),
        ("2.2 Integration Components", "The flow consists of start events, processing activities, and end events."),
        ("3.1 Scenario Description", f"The integration flow executes the following steps:\n{steps_text}"),
        ("3.2 Data Flows", "Message flows from sender to receiver through the defined processing steps."),
        ("3.3 Security Requirements", "Security is governed by CPI tenant configuration and adapter-level settings."),
        ("4. Error Handling and Logging", "Standard SAP CPI monitoring and logging are used."),
        ("5. Testing Validation", "Testing includes execution validation and monitoring verification."),
        ("6. Reference Documents", "SAP CPI Integration Suite documentation.")
    ]

    for title, context in sections:
        doc.add_heading(title, level=2)
        doc.add_paragraph(generate_section(title, context))

    output = f"{out_dir}/{package}_Technical_Spec.docx"
    doc.save(output)
    print(f"Document generated: {output}")


# -------------------------------------------------
# Entry point
# -------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", required=True)
    args = parser.parse_args()
    generate_doc(args.package)
