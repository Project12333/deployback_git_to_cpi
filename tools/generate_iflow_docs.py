#!/usr/bin/env python3
import sys, json, subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

def parse_iflw(path):
    try:
        tree = ET.parse(path)
        root = tree.getroot()
    except Exception as e:
        return {"error": str(e)}

    data = {
        "flowname": Path(path).stem,
        "adapters": [],
        "scripts": [],
        "mappings": [],
        "exceptions": [],
        "properties": [],
        "xml_sample": ""
    }

    for elem in root.iter():
        tag = elem.tag.split('}')[-1].lower()
        name = elem.attrib.get("name") or elem.attrib.get("id")

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

    with open(path, "r", errors="ignore") as f:
        data["xml_sample"] = f.read(20000)

    return data

def doc_prompt(data):
    return f"""
Generate FULL CPI iFlow documentation in Markdown.

Sections required:
- Flow Name
- Purpose
- Overview
- Sender & Receiver Adapters
- Groovy Script explanation
- Mappings used
- Exception Handling
- Properties/Headers
- Message Flow Steps
- Test Cases
- Deployment Notes

iFlow Summary:
{json.dumps(data, indent=2)}
"""

def run_llm(prompt):
    cmd = f"echo \"{prompt}\" | ollama run mistral"
    return subprocess.check_output(cmd, shell=True, text=True)

def write_output(iflw_path, md_text):
    base = Path(iflw_path).parent / "docs"
    base.mkdir(exist_ok=True)

    name = Path(iflw_path).stem
    md_file = base / f"{name}_Documentation.md"
    docx_file = base / f"{name}_Documentation.docx"

    md_file.write_text(md_text, encoding="utf-8")
    subprocess.run(["pandoc", md_file, "-o", docx_file])

    return md_file, docx_file

if __name__ == "__main__":
    for p in sys.argv[1:]:
        data = parse_iflw(p)
        prompt = doc_prompt(data)
        md = run_llm(prompt)
        mdf, dxf = write_output(p, md)
        print("Generated:", mdf, dxf)
