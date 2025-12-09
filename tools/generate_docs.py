#!/usr/bin/env python3
import sys
import json
import requests
import xml.etree.ElementTree as ET
from pathlib import Path
import subprocess

OLLAMA_URL = "http://localhost:11434/api/generate"


# ---------------------------------------------------------
# Parse .iflw BPMN file
# ---------------------------------------------------------
def parse_iflw(path):
    meta = {
        "flowname": Path(path).stem,
        "senders": [],
        "receivers": [],
        "adapters": [],
        "scripts": [],
        "mappings": [],
        "gateways": [],
        "subprocesses": [],
        "servicetasks": [],
        "callactivities": [],
        "startevents": [],
        "endevents": []
    }

    try:
        tree = ET.parse(path)
        root = tree.getroot()

        for elem in root.iter():
            tag = elem.tag.split("}")[-1]
            name = elem.attrib.get("name") or elem.attrib.get("id") or tag

            tag_lower = tag.lower()

            if "sender" in tag_lower:
                meta["senders"].append(name)

            if "receiver" in tag_lower:
                meta["receivers"].append(name)

            if "adapter" in tag_lower:
                meta["adapters"].append(name)

            if "script" in tag_lower or "groovy" in tag_lower:
                meta["scripts"].append(name)

            if "mapping" in tag_lower:
                meta["mappings"].append(name)

            # BPMN components
            if tag == "serviceTask":
                meta["servicetasks"].append(name)

            if tag == "callActivity":
                meta["callactivities"].append(name)

            if tag in ["exclusiveGateway", "inclusiveGateway", "parallelGateway"]:
                meta["gateways"].append(name)

            if tag == "subProcess":
                meta["subprocesses"].append(name)

            if tag == "startEvent":
                meta["startevents"].append(name)

            if tag == "endEvent":
                meta["endevents"].append(name)

    except Exception as e:
        meta["error"] = f"Could not parse .iflw: {e}"

    return meta


# ---------------------------------------------------------
# Mermaid architecture diagram
# ---------------------------------------------------------
def generate_mermaid(meta):
    sender = meta["senders"][0] if meta["senders"] else "Sender"
    receiver = meta["receivers"][0] if meta["receivers"] else "Receiver"

    return f"""
```mermaid
graph TD
    {sender} --> CPI
    CPI --> {receiver}
```
"""


# ---------------------------------------------------------
# Build prompt (Option A: hidden metadata block)
# ---------------------------------------------------------
def build_prompt(meta, diagram):

    metadata_json = json.dumps(meta, indent=2)

    return f"""
You are an SAP CPI documentation expert.

<<METADATA>>
{metadata_json}
<</METADATA>>

Use ONLY the information inside the metadata block to write the documentation.
DO NOT repeat, restate, quote, or output anything from inside the metadata block.
DO NOT guess or hallucinate any components.
Include a section ONLY if its components appear in the metadata block.

FOLLOW THE EXACT DOCUMENT STRUCTURE BELOW:

# Technical Documentation – {meta['flowname']}

## 1. Overview
<Generate a short overview of this iFlow based ONLY on detected components.>

## 2. Systems Involved
### Sender Systems
{meta["senders"]}

### Receiver Systems
{meta["receivers"]}

## 3. Adapters Used
{meta["adapters"]}

## 4. Key Functional Steps
<Generate ONLY the subsections that apply. Use metadata checks.>

### 4.1 Initialization
<Include only if start events, property setups, or initialization scripts exist.>

### 4.2 Execution Mode / Gateway Logic
<Include only if gateways exist.>

### 4.3 Source System Data Retrieval
<Include only if service tasks exist. List them.>

### 4.4 Message Preprocessing
<Include only if scripts or content modifiers exist.>

### 4.5 Message Splitting and Aggregation
<Include only if any splitter or callActivities exist.>

### 4.6 Transformation / Mapping
<Include only if mappings exist.>

### 4.7 Outbound Call to Receiver System
<Describe based ONLY on detected adapters and receivers.>

### 4.8 Response Handling
<Include only if response-handling subprocess or callActivity exists.>

### 4.9 Exception Handling
<Include only if subprocesses or error-handling flows exist.>

### 4.10 Flow Finalization
<Include only if end events exist.>

## 5. Mapping Logic Summary
<Explain mapping logic only if mappings exist.>

## 6. Groovy Script Summary
Scripts detected: {meta["scripts"]}
<Explain their purpose ONLY if they exist.>

## 7. Error Handling Approach
<Explain error handling based ONLY on detected gateways and subprocesses.>

## 8. High-Level Architecture Diagram (Mermaid)
{diagram}

## 9. Component Inventory (Extracted)
- Start Events: {meta["startevents"]}
- End Events: {meta["endevents"]}
- Service Tasks: {meta["servicetasks"]}
- Call Activities: {meta["callactivities"]}
- Gateways: {meta["gateways"]}
- SubProcesses: {meta["subprocesses"]}
- Scripts: {meta["scripts"]}
- Mappings: {meta["mappings"]}
"""


# ---------------------------------------------------------
# Call DeepSeek
# ---------------------------------------------------------
def call_llm(prompt):
    res = requests.post(OLLAMA_URL, json={
        "model": "deepseek-r1:1.5b",
        "prompt": prompt,
        "stream": False
    })
    res.raise_for_status()
    return res.json().get("response", "")


# ---------------------------------------------------------
# Write MD and DOCX
# ---------------------------------------------------------
def write_output(path, markdown):

    outdir = Path(path).parent / "docs"
    outdir.mkdir(exist_ok=True, parents=True)

    mdfile = outdir / f"{Path(path).stem}_Documentation.md"
    docxfile = outdir / f"{Path(path).stem}_Documentation.docx"

    mdfile.write_text(markdown, encoding="utf-8")

    try:
        subprocess.run(["pandoc", str(mdfile), "-o", str(docxfile)], check=True)
    except Exception:
        pass

    print(f"Generated: {mdfile}")
    print(f"Generated: {docxfile}")


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------
if __name__ == "__main__":

    for f in sys.argv[1:]:
        print(f"Processing {f}")

        meta = parse_iflw(f)
        diagram = generate_mermaid(meta)
        prompt = build_prompt(meta, diagram)

        markdown = call_llm(prompt)

        write_output(f, markdown)

    print("Done.")
