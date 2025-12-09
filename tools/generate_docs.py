#!/usr/bin/env python3
import sys
import json
import requests
import xml.etree.ElementTree as ET
from pathlib import Path
import subprocess

OLLAMA_URL = "http://localhost:11434/api/generate"


# ---------------------------------------------------------
# Parse .iflw BPMN file into metadata dictionary
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
            low = tag.lower()

            if "sender" in low: meta["senders"].append(name)
            if "receiver" in low: meta["receivers"].append(name)
            if "adapter" in low: meta["adapters"].append(name)
            if "script" in low or "groovy" in low: meta["scripts"].append(name)
            if "mapping" in low: meta["mappings"].append(name)

            if tag == "serviceTask": meta["servicetasks"].append(name)
            if tag == "callActivity": meta["callactivities"].append(name)
            if tag in ["exclusiveGateway","parallelGateway","inclusiveGateway"]:
                meta["gateways"].append(name)
            if tag == "subProcess": meta["subprocesses"].append(name)
            if tag == "startEvent": meta["startevents"].append(name)
            if tag == "endEvent": meta["endevents"].append(name)

    except Exception as e:
        meta["error"] = f"Parse error: {e}"

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
# Build the MAIN PROMPT (metadata NOT included here!)
# ---------------------------------------------------------
def build_prompt(meta, diagram):
    
    return f"""
You are an SAP CPI documentation expert.
Use ONLY the metadata provided in the context (NOT visible here).

NEVER output or mention metadata fields directly.
NEVER hallucinate missing values.
Generate ONLY sections supported by metadata.

Follow EXACTLY this structure:

# Technical Documentation – {meta['flowname']}

## 1. Overview
<Short overview, based only on available metadata.>

## 2. Systems Involved
### Sender Systems
<List senders>

### Receiver Systems
<List receivers>

## 3. Adapters Used
<List adapters>

## 4. Key Functional Steps
<Generate ONLY subsections that apply based on metadata.>

### 4.1 Initialization
<Only if start events or initialization steps exist>

### 4.2 Execution Mode / Gateway Logic
<Only if gateways exist>

### 4.3 Source System Data Retrieval
<Only if service tasks exist. List names.>

### 4.4 Message Preprocessing
<Only if Groovy/scripts/content modifiers exist>

### 4.5 Message Splitting and Aggregation
<Only if callActivities or multiple branches exist>

### 4.6 Transformation / Mapping
<Only if mappings exist>

### 4.7 Outbound Call to Receiver System
<Only if receivers + adapters exist>

### 4.8 Response Handling
<Only if relevant subprocesses or callactivities detected>

### 4.9 Exception Handling
<Only if subprocesses exist>

### 4.10 Flow Finalization
<Only if end events exist>

## 5. Mapping Logic Summary
<Only if metadata['mappings'] contains values>

## 6. Groovy Script Summary
<Only if metadata['scripts'] contains scripts>

## 7. Error Handling Approach
<Explain exceptions only if subprocesses or gateways are present>

## 8. High-Level Architecture Diagram (Mermaid)
{diagram}

## 9. Component Inventory (Extracted)
- Start Events
- End Events
- Service Tasks
- Call Activities
- Gateways
- SubProcesses
- Scripts
- Mappings
"""


# ---------------------------------------------------------
# Call DeepSeek using OLLAMA CONTEXT
# ---------------------------------------------------------
def call_llm(prompt, meta):

    # convert metadata to token context (list of ints)
    meta_str = json.dumps(meta)
    ctx_req = requests.post(
        OLLAMA_URL,
        json={"model": "deepseek-r1:1.5b", "prompt": meta_str, "raw": True}
    )
    ctx_tokens = ctx_req.json().get("context", [])

    # send prompt + context correctly
    res = requests.post(
        OLLAMA_URL,
        json={
            "model": "deepseek-r1:1.5b",
            "prompt": prompt,
            "context": ctx_tokens,
            "stream": False
        }
    )

    res.raise_for_status()
    return res.json().get("response", "")


# ---------------------------------------------------------
# Write documentation files
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
        print(f"Processing:", f)

        meta = parse_iflw(f)
        diagram = generate_mermaid(meta)
        prompt = build_prompt(meta, diagram)

        markdown = call_llm(prompt, meta)

        write_output(f, markdown)

    print("Done.")
