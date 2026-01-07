import sys, requests, os
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

def add_numbered_heading(doc, text, level, num_str):
    p = doc.add_heading(level=level)
    run = p.add_run(f"{num_str} {text}")
    run.font.color.rgb = RGBColor(31, 56, 100)
    if level == 1:
        run.font.size = Pt(16)
    else:
        run.font.size = Pt(13)

def build_docx(iflow_name, author, date, ai_content, output_path):
    doc = Document()
    # --- HEADER (LOGOS ON EVERY PAGE) ---
    section = doc.sections[0]
    header = section.header
    htable = header.add_table(1, 2, width=Inches(6.5))
    htable.allow_autofit = False
    sap_url = "https://raw.githubusercontent.com/Akila710/CPI_Demo1/main/assets/logos/SAP.jpg"
    mm_url = "https://raw.githubusercontent.com/Akila710/CPI_Demo1/main/assets/logos/mm_logo.png"
    try:
        with open("sap.jpg", "wb") as f: f.write(requests.get(sap_url).content)
        with open("mm.png", "wb") as f: f.write(requests.get(mm_url).content)
        htable.rows[0].cells[0].paragraphs[0].add_run().add_picture("sap.jpg", height=Inches(0.75))
        mm_p = htable.rows[0].cells[1].paragraphs[0]
        mm_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        mm_p.add_run().add_picture("mm.png", height=Inches(0.75))
    except: pass

    # --- PAGE 1: COVER PAGE ---
    for _ in range(5): doc.add_paragraph()
    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title_p.add_run(iflow_name)
    run.font.size = Pt(32)
    run.font.bold = True
    run.font.color.rgb = RGBColor(31, 56, 100)

    doc.add_paragraph("Technical Specification Document").alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph("\n" * 2)

    meta = doc.add_table(rows=3, cols=2)
    meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    meta.style = 'Table Grid'
    for i, (l, v) in enumerate([("Author:", author), ("Date:", date), ("Version:", "1.0")]):
        meta.rows[i].cells[0].text = l
        meta.rows[i].cells[1].text = v
    doc.add_page_break()

    # --- PAGE 2: TABLE OF CONTENTS ---
    doc.add_heading("Table of Contents", level=1).runs[0].font.color.rgb = RGBColor(31, 56, 100)
    items = [
        ("1. Introduction", 0), ("1.1 Purpose", 1), ("1.2 Scope", 1),
        ("2. Integration Overview", 0), ("2.1 Integration Architecture", 1), ("2.2 Integration Components", 1),
        ("3. Integration Scenarios", 0), ("3.1 Scenario Description", 1), ("3.2 Data Flows", 1),
        ("4. Error Handling", 0), ("5. Testing Validation", 0)
    ]
    for text, ind in items:
        p = doc.add_paragraph(text)
        if ind == 1: p.paragraph_format.left_indent = Inches(0.3)
    doc.add_page_break()

    # --- PAGE 3: TECHNICAL CONTENT ---
    add_numbered_heading(doc, "Introduction", 1, "1.")
    add_numbered_heading(doc, "Purpose", 2, "1.1")
    doc.add_paragraph("This document provides a detailed explanation of the solution as conceptualized for " + iflow_name + ".")
    add_numbered_heading(doc, "Scope", 2, "1.2")
    doc.add_paragraph("The technical specification outlines integration touchpoints and business scenarios required for consistent identity management.")

    add_numbered_heading(doc, "Integration Overview", 1, "2.")
    add_numbered_heading(doc, "Integration Architecture", 2, "2.1")
    doc.add_paragraph("The integration architecture follows the standard SAP BTP Cloud Integration pattern.")

    add_numbered_heading(doc, "Integration Scenarios", 1, "3.")
    add_numbered_heading(doc, "Scenario Description", 2, "3.1")
    doc.add_paragraph(ai_content)
    doc.save(output_path)
if __name__ == "__main__":
    build_docx(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
