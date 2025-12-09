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
# Mermaid diagram
# ---------------------------------------------------------
def generate_mermaid(meta):
    s = meta["senders"][0] if meta["senders"] else "Sender"
    r = meta["receivers"][0] if meta["receivers"] else "Receiver"
    return f"""
```mermaid
graph TD
    {s} --> CPI
    CPI --> {r}
```
"""


# ---------------------------------------------------------
# Build prompt (NO METADATA INCLUDED!)
# ---------------------------------------------------------
def build_prompt(meta, diagram):

    return f"""
You are an SAP CPI documentation expert.

You will receive metadata in hidden model context.
DO NOT restate, summarize, or output metadata keys.
Use it ONLY to generate CPI documentation sections that apply.

Follow this EXACT document structure:

# Technical Documentation – {meta['flowname']}

## 1. Overview
(Short overview)

## 2. Systems Involved
### Sender Systems
<List senders>

### Receiver Systems
<List receivers>

## 3. Adapters Used
<List adapters>

## 4. Key Functional Steps
<Only output subsections supported by metadata>

### 4.1 Initialization
<Only if start events or init steps exist>

### 4.2 Execution Mode / Gateway Logic
<Only if gateways exist>

### 4.3 Source System Data Retrieval
<Only if service tasks exist — list them>

### 4.4 Message Preprocessing
<Only if scripts exist>

### 4.5 Message Splitting and Aggregation
<Only if callActivities exist>

### 4.6 Transformation / Mapping
<Only if mappings exist>

### 4.7 Outbound Call to Receiver System
<Only if receivers+adapters exist>

### 4.8 Response Handling
<Only if subprocess names indicate response handling>

### 4.9 Exception Handling
<Only if subprocesses or gateways exist>

### 4.10 Flow Finalization
<Only if end events exist>

## 5. Mapping Logic Summary
<Only if mappings exist>

## 6. Groovy Script Summary
<Only if scripts exist>

## 7. Error Handling Approach
<Only if gateways/subprocesses exist>

## 8. High-Level Architecture Diagram (Mermaid)
{diagram}

## 9. Component Inventory (Extracted)
<List all extracted items>
"""


# ---------------------------------------------------------
# Convert metadata INTO CONTEXT TOKENS (without showing text)
# ---------------------------------------------------------
def create_context(metadata):
    """
    We send metadata to the model in a *hidden* message using internal tokenization.
    This prevents the model from reading or imitating metadata text.
    """
    resp = requests.post(
        OLLAMA_URL,
        json={
            "model": "deepseek-r1:1.5b",
            "prompt": json.dumps(metadata)
        }
    )
    resp.raise_for_status()
    return resp.json().get("context", [])


# ---------------------------------------------------------
# Generate documentation
# ---------------------------------------------------------
def call_llm(prompt, meta):

    ctx = create_context(meta)

    resp = requests.post(
        OLLAMA_URL,
        json={
            "model": "deepseek-r1:1.5b",
            "prompt": prompt,
            "context": ctx,     # THIS IS THE FIX
            "stream": False
        }
    )
    resp.raise_for_status()
    return resp.json().get("response", "")


# ---------------------------------------------------------
# Write output
# ---------------------------------------------------------
def write_output(path, markdown):

    outdir = Path(path).parent / "docs"
    outdir.mkdir(exist_ok=True, parents=True)

    md = outdir / f"{Path(path).stem}_Documentation.md"
    doc = outdir / f"{Path(path).stem}_Documentation.docx"

    md.write_text(markdown, encoding="utf-8")

    try:
        subprocess.run(["pandoc", str(md), "-o", str(doc)], check=True)
    except Exception:
        pass

    print(f"Generated: {md}")
    print(f"Generated: {doc}")


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------
if __name__ == "__main__":

    for f in sys.argv[1:]:

        print("Processing:", f)

        meta = parse_iflw(f)
        diagram = generate_mermaid(meta)
        prompt = build_prompt(meta, diagram)

        markdown = call_llm(prompt, meta)

        write_output(f, markdown)

    print("Done.")
