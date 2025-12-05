#!/usr/bin/env python3
import sys
import json
import requests
import xml.etree.ElementTree as ET
from pathlib import Path

OLLAMA_HOST = "http://localhost:11434"

# --------------------------------------
# Parse .iflw XML
# --------------------------------------
def parse_iflw(path):
    try:
        tree = ET.parse(path)
        root = tree.getroot()
    except Exception as e:
        return {"error": str(e), "flowname": Path(path).stem}

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
        tag = elem.tag.split("}")[-1].lower()
        name = elem.attrib.get("name") or elem.attrib.get("id")

        if any(t in tag for t in ["adapter", "sender", "receiver"]):
            data["adapters"].append({"tag": tag, "name": name})

        if "script" in tag:
            data["scripts"].append({"tag": tag, "name": name})

        if "mapping" in tag:
            data["mappings"].append({"tag": tag, "name": name})

        if "exception" in tag or "error" in tag:
            data["exceptions"].append({"tag": tag, "name": name})

        if "property" in tag or "header" in tag:
            data["properties"].append({"tag": tag, "name": name})

    # Read portion of XML for context
    try:
        with open(path, "r", errors="ignore") as f:
            data["xml_sample"] = f.read(20000)
    except:
        data["xml_sample"] = "<Unable to read XML>"

    return data

# --------------------------------------
# Build DeepSeek prompt
# --------------------------------------
def build_prompt(data):
    return f'''
You are an SAP CPI Integration Architect.

Generate a highly detailed, professional CPI iFlow documentation in Markdown.

### REQUIRED SECTIONS:
1. Flow Name  
2. Business Purpose  
3. High-Level Technical Overview  
4. Architecture (text-based diagram)  
5. Sender & Receiver Adapters  
6. Detailed Message Processing Steps  
7. Groovy Script Analysis  
8. Mapping Logic  
9. Exception Handling  
10. Properties & Headers  
11. Runtime Behavior  
12. Test Scenarios  
13. Deployment Notes  
14. Security Considerations  
15. Assumptions & Limitations  

### PARSED iFLOW METADATA (Use this to infer details)
```json
{json.dumps(data, indent=2)}
