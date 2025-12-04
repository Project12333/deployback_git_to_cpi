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
You are an expert SAP CPI architect.

Generate a FULL technical documentation for the CPI iFlow.

The documentation MUST include:

1. **Flow Name**
2. **Purpose**
3. **End-to-end Scenario Overview**
4. **Sender Adapter** – type + meaning
5. **Receiver Adapter** – type + meaning
6. **Groovy Scripts** – purpose of each script
7. **Mappings** – logic summary
8. **Exception Handling** – how errors are managed
9. **Properties / Headers Used**
10. **Message Flow Steps** – sequence of actions in the iFlow
11. **Test Cases**
12. **Deployment Notes**

Here is the structured iFlow summary:
{json.dumps(data, indent=2)}
"""

def run_llm(prompt):
    cmd = f"echo \"{prompt}\" | ollama run mistral"
    return subprocess.check_output(cmd, shell=True, text=True)

def write_output(iflw_path, md_text):
    base = Path(iflw_path).parent / "docs"
    base.mkdir(exist_ok=True)

    fname = Path(iflw_path).stem
    md_file = base / f"{fname}_Documentation.md"
    docx_file = base / f"{fname}_Documentation.docx"

    md_file.write_text(md_text, encoding="utf-8")

    subprocess.run(["pandoc", str(md_file), "-o", str(docx_file)])

    return md_file, docx_file

if __name__ == "__main__":
    for p in sys.argv[1:]:
        data = parse_iflw(p)
        prompt = doc_prompt(data)
        md = run_llm(prompt)
        md_file, docx_file = write_output(p, md)
        print("Generated:", md_file, "and", docx_file)
