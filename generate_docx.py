import sys, json, requests
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

def add_numbered_heading(doc, text, level, num_str):
    p = doc.add_heading(level=level)
    run = p.add_run(f"{num_str} {text}")
    run.font.color.rgb = RGBColor(31, 56, 100)
    run.font.size = Pt(16 if level == 1 else 13)

def format_content(content):
    """Ensures content is a string and handles lists/dicts if AI sends them."""
    if isinstance(content, list):
        return ", ".join(map(str, content))
    if isinstance(content, dict):
        return ". ".join([f"{k}: {v}" for k, v in content.items()])
    return str(content) if content else ""

def build_docx(iflow_name, author, date, json_raw, output_path):
    doc = Document()
    
    # Clean JSON string (remove markdown blocks if present)
    json_raw = json_raw.strip().removeprefix("```json").removesuffix("```")
    try:
        data = json.loads(json_raw)
    except Exception as e:
        print(f"JSON Parse Error: {e}")
        data = {"scenario_desc": "Error parsing AI response. Raw: " + json_raw}

    # --- PAGE 1: COVER ---
    for _ in range(5): doc.add_paragraph()
    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title_p.add_run(iflow_name)
    run.font.size, run.font.bold = Pt(32), True
    doc.add_paragraph("Technical Specification").alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_page_break()

    # --- PAGE 2: TABLE OF CONTENTS ---
    doc.add_heading("Table of Contents", level=1)
    items = [
        ("1. Introduction", 0), ("1.1 Purpose", 1), ("1.2 Scope", 1),
        ("2. Integration Overview", 0), ("2.1 Integration Architecture", 1), ("2.2 Integration Components", 1),
        ("3. Integration Scenarios", 0), ("3.1 Scenario Description", 1), ("3.2 Data Flows", 1), ("3.3 Security Requirements", 1),
        ("4. Error Handling and Logging", 0),
        ("5. Testing Validation", 0),
        ("6. Reference Documents", 0)
    ]
    for text, ind in items:
        p = doc.add_paragraph(text)
        if ind == 1: p.paragraph_format.left_indent = Inches(0.3)
    doc.add_page_break()

    # --- PAGE 3+: CONTENT ---
    mapping = [
        ("1.", "Introduction", 1, None),
        ("1.1", "Purpose", 2, "purpose"),
        ("1.2", "Scope", 2, "scope"),
        ("2.", "Integration Overview", 1, None),
        ("2.1", "Integration Architecture", 2, "architecture"),
        ("2.2", "Integration Components", 2, "components"),
        ("3.", "Integration Scenarios", 1, None),
        ("3.1", "Scenario Description", 2, "scenario_desc"),
        ("3.2", "Data Flows", 2, "data_flows"),
        ("3.3", "Security Requirements", 2, "security"),
        ("4.", "Error Handling and Logging", 1, "error_handling"),
        ("5.", "Testing Validation", 1, "testing"),
        ("6.", "Reference Documents", 1, "references")
    ]

    for num, title, lvl, key in mapping:
        add_numbered_heading(doc, title, lvl, num)
        if key:
            doc.add_paragraph(format_content(data.get(key, "Information not provided.")))

    doc.save(output_path)

if __name__ == "__main__":
    build_docx(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
