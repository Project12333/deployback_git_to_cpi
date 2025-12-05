#!/usr/bin/env python3
import sys
import json
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

# -------------------------
# Parse .iflw file safely
# -------------------------
def parse_iflw(path):
    try:
        tree = ET.parse(path)
        root = tree.getroot()
    except Exception as e:
        return {"error": f"Failed to parse XML: {str(e)}", "flowname": Path(path).stem}

    data = {
        "flowname": Path(path).stem,
        "path": str(path),
        "adapters": [],
        "scripts": [],
        "mappings": [],
        "exceptions": [],
        "properties": [],
        "xml_sample": ""
    }

    for elem in root.iter():
        tag = elem.tag.split('}')[-1].lower()
        name = elem.attrib.get("name") or elem.attrib.get("id") or elem.attrib.get("value")

        if any(x in tag for x in ["adapter", "sender", "receiver"]):
            data["adapters"].append({"tag": tag, "name": name})

        if "script" in tag:
            data["scripts"].append({"tag": tag, "name": name})

        if "mapping" in tag:
            data["mappings"].append({"tag": tag, "name": name})

        if "exception" in tag or "error" in tag:
            data["exceptions"].append({"tag": tag, "name": name})

        if "property" in tag or "header" in tag:
            data["properties"].append({"tag": tag, "name": name})

    try:
        with open(path, "r", errors="ignore") as f:
            data["xml_sample"] = f.read(20000)
    except Exception:
        data["xml_sample"] = "<Unable to read XML content>"

    return data

# -------------------------
# Prompt builder (safe)
# -------------------------
def doc_prompt(data):
    # triple-single-quote f-string to avoid delimiting issues
    return f'''
You are an expert SAP Integration Suite / CPI architect.

Generate a very detailed, professionally structured CPI iFlow documentation in Markdown.
This will be used as an official deliverable.

REQUIRED SECTIONS:
1. Flow Name
2. Business Purpose
3. High-Level Technical Overview
4. Integration Flow Architecture (text-based)
5. Sender & Receiver Adapters (protocol, purpose, config consideration)
6. Detailed Message Processing Steps (step-by-step)
7. Groovy Script Analysis
8. Mapping Logic Explanation
9. Exception Handling
10. Properties & Headers
11. End-to-End Runtime Behavior
12. Test Scenarios (positive, negative, retry)
13. Deployment Notes
14. Security Considerations
15. Assumptions & Limitations
16. Sample Payloads (if inferable)

PARSED METADATA (use to infer gaps):
{json.dumps(data, indent=2)}

RULES:
- Output only valid Markdown.
- Be verbose and thorough.
- If something is not explicit in the XML, infer in a reasonable, professional manner.
- Don't output triple quotes that would break scripts; just Markdown.
'''

# -------------------------
# Run the LLM (use subprocess with stdin)
# -------------------------
def run_llm(prompt):
    # call ollama run with the model; pass prompt via stdin to avoid quoting issues
    proc = subprocess.run(
        ["ollama", "run", "deepseek-r1:14b"],
        input=prompt,
        text=True,
        capture_output=True
    )
    if proc.returncode != 0:
        raise RuntimeError(f"LLM run failed: {proc.stderr}")
    return proc.stdout

# -------------------------
# Write outputs (Markdown + DOCX)
# -------------------------
def write_output(iflw_path, md_text):
    flow_dir = Path(iflw_path).parent
    docs_dir = flow_dir / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)

    name = Path(iflw_path).stem
    md_file = docs_dir / f"{name}_Documentation.md"
    docx_file = docs_dir / f"{name}_Documentation.docx"

    md_file.write_text(md_text, encoding="utf-8")

    # try pandoc conversion; if it fails, continue (we still have the md)
    try:
        subprocess.run(["pandoc", str(md_file), "-o", str(docx_file)], check=True)
    except Exception as e:
        print(f"⚠ WARNING: DOCX generation failed: {e}")

    return md_file, docx_file

# -------------------------
# Main
# -------------------------
def main():
    if len(sys.argv) < 2:
        print("Usage: tools/ollama_generate_docs.py <iflw-file> [<iflw-file> ...]")
        sys.exit(1)

    for p in sys.argv[1:]:
        p = Path(p)
        if not p.exists():
            print(f"❌ File not found: {p}")
            continue

        print(f"📄 Processing iFlow: {p}")
        data = parse_iflw(p)
        prompt = doc_prompt(data)

        try:
            md = run_llm(prompt)
        except Exception as e:
            print(f"❌ LLM generation failed for {p}: {e}")
            continue

        mdf, dxf = write_output(p, md)
        print(f"✅ Generated documentation: {mdf} {dxf}")

if __name__ == "__main__":
    main()
