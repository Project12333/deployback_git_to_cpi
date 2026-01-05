from docx import Document
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
import sys
from datetime import datetime

# Arguments
input_text_file = sys.argv[1]
output_docx = sys.argv[2]
iflow_name = sys.argv[3]
author = sys.argv[4]
version = sys.argv[5]

doc = Document()

# ---------------- HEADER (ALL PAGES) ----------------
section = doc.sections[0]
header = section.header
p = header.paragraphs[0]
p.alignment = WD_ALIGN_PARAGRAPH.LEFT

run = p.add_run()
run.add_picture("tools/logos/sap.png", width=Inches(1.6))

p.add_run("\t" * 6)

run2 = p.add_run()
run2.add_picture("tools/logos/motiveminds.png", width=Inches(1.5))

# ---------------- COVER PAGE ----------------
title = doc.add_paragraph()
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
title.add_run(iflow_name).bold = True

subtitle = doc.add_paragraph()
subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
subtitle.add_run("Technical Specification Document")

doc.add_paragraph("\n")

meta = doc.add_paragraph()
meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
meta.add_run(f"Author: {author}\n")
meta.add_run(f"Date: {datetime.today().strftime('%Y-%m-%d')}\n")
meta.add_run(f"Version: {version}")

doc.add_page_break()

# ---------------- MAIN CONTENT ----------------
with open(input_text_file, "r", encoding="utf-8") as f:
    for line in f:
        doc.add_paragraph(line.rstrip())

doc.save(output_docx)
