print("✅ NEW VERSION LOADED - SECTION WISE LLM")

import os
import argparse
from docx import Document
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, ns
from tools.ollama_client import generate_section

SAP_LOGO = "tools/logos/sap.png"
MOTIVE_LOGO = "tools/logos/motiveminds.png"

def add_header_with_logos(section):
    header = section.header
    header.is_linked_to_previous = False
    table = header.add_table(rows=1, cols=2)

    left = table.cell(0, 0).paragraphs[0]
    left.alignment = WD_ALIGN_PARAGRAPH.LEFT
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

def generate_doc(package):
    out_dir = f"cpi-artifacts/{package}/docs"
    os.makedirs(out_dir, exist_ok=True)

    doc = Document()
    section = doc.sections[0]
    add_header_with_logos(section)

    # Cover
    title = doc.add_heading("SAP CPI Integration Technical Specification", 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_page_break()

    # TOC
    doc.add_heading("Table of Contents", level=1)
    add_toc(doc)
    doc.add_page_break()

    sections = [
        ("1. Introduction", "Overview of the integration"),
        ("1.1 Purpose", "Purpose of this integration"),
        ("1.2 Scope", "Scope of the integration"),
        ("2. Integration Overview", "High-level overview"),
        ("2.1 Integration Architecture", "CPI architecture"),
        ("2.2 Integration Components", "Adapters, mappings, scripts"),
        ("3. Integration Scenarios", "Business scenarios"),
        ("3.1 Scenario Description", "Scenario details"),
        ("3.2 Data Flows", "Inbound and outbound flows"),
        ("3.3 Security Requirements", "Security mechanisms"),
        ("4. Error Handling and Logging", "Exception handling"),
        ("5. Testing Validation", "Testing strategy"),
        ("6. Reference Documents", "Reference materials"),
    ]

    for title, context in sections:
        print(f"🧠 Generating section: {title}")
        level = 1 if title.count(".") == 1 else 2
        doc.add_heading(title, level=level)
        doc.add_paragraph(generate_section(title, context))

    out_file = f"{out_dir}/{package}_Technical_Spec.docx"
    doc.save(out_file)
    print(f"✅ Document generated: {out_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", required=True)
    args = parser.parse_args()
    generate_doc(args.package)
