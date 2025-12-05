#!/usr/bin/env python3
import sys, json, subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

# ---------------------------------------------------------
# Parse the .iflw file (CPI integration flow XML format)
# ---------------------------------------------------------
def parse_iflw(path):
    try:
        tree = ET.parse(path)
        root = tree.getroot()
    except Exception as e:
        return {"error": f"Failed to parse XML: {str(e)}"}

    data = {
        "flowname": Path(path).stem,
        "adapters": [],
        "scripts": [],
        "mappings": [],
        "exceptions": [],
        "properties": [],
        "xml_sample": ""
    }

    # Loop over all XML elements
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

    # Read XML text (partial)
    try:
        with open(path, "r", errors="ignore") as f:
            data["xml_sample"] = f.read(20000)
    except:
        data["xml_sample"] = "<Unable to read XML content>"

    return data


# ---------------------------------------------------------
# LLM Prompt for DeepSeek R1 (high detail + structured)
# ---------------------------------------------------------
def doc_prompt(data):
    return f"""
You are an expert SAP Integration Suite / CPI architect.

Generate an extremely detailed and professionally formatted CPI iFlow documentation in **Markdown**.
This documentation will be used as an official customer deliverable.

### R
