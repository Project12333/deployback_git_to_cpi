#!/usr/bin/env python3
import sys
import json
import requests
import xml.etree.ElementTree as ET
from pathlib import Path
import subprocess

# IMPORTANT — DeepSeek MUST NOT SEE METADATA; embeddings are used instead.
OLLAMA_GENERATE = "http://localhost:11434/api/generate"
OLLAMA_EMBEDDINGS = "http://localhost:11434/api/embeddings"


# ---------------------------------------------------------
# Parse .iflw BPMN metadata
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
            if tag in ["exclusiveGateway", "parallelGateway", "inclusiveGateway"]:
                meta["gateways"].append(name)
            if tag == "subProcess": meta["subprocesses"].append(name)
            if tag == "startEvent": meta["startevents"].append(name)
            if tag == "endEvent": meta["endevents"].append(name)

    except Exception as e:
        meta["error"] = f"Parse error: {e}"

    return meta


# ---------------------------------------------------------
# Mermaid Architecture Diagram
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
# Create hidden metadata context (DeepSeek cannot “see” this text)
# ---------------------------------------------------------
def create_context(metadata):
    resp = requests.post(
        OLLAMA_EMBEDDINGS,
        json={
            "model": "deepseek-r1:1.5b",
            "prompt": json.dumps(metadata)
        }
    )
    resp.raise_for_status()
    return resp.json().get("embedding", [])


# ---------------------------------------------------------
# Build the main prompt (NO metadata inside!)
# ---------------------------------------------------------
def build_prompt(meta, diagram):

    # Main CPI documentation template (strict format)
    return f"""
You are an SAP CPI documentation expert.
The metadata required for documentation has been passed to you in hidden context embeddings.
DO NOT show or summarize metadata fields.
DO NOT hallucinate any components.
ONLY describe sections where metadata exists.

Follow EXACTLY this document structure:

# Technical Documentation – {meta['flowname']}

## 1. Overview
(Provide a brief overview based solely on available context.)

## 2. Systems Involved
### Sender Systems
(List senders extracted from context)

### Receiver Systems
(List receivers extracted from context)

## 3. Adapters Used
(List all adapters detected)

## 4. Key Functional Steps
(Generate ONLY subsections that apply based on context)

### 4.1 Initialization
(Only if start events or initialization logic detected)

### 4.2 Execution Mode / Gateway Logic
(Only if gateways exist)

### 4.3 Source System Data Retrieval
(Only if service tasks exist — list and describe them)

### 4.4 Message Preprocessing
(Only if scripts or modifiers exist)

### 4.5 Message Splitting and Aggregation
(Only if call activities or multi-branch flows exist)

### 4.6 Transformation / Mapping
(Only if mappings exist)

### 4.7 Outbound Call to Receiver System
(Only if receiver + adapter exist)

### 4.8 Response Handling
(Only if related subprocess exists)

### 4.9 Exception Handling
(Only if subprocesses or gateways exist)

### 4.10 Flow Finalization
(Only if end events exist)

## 5. Mapping Logic Summary
(Only if mappings exist)

## 6. Groovy Script Summary
(Only if scripts exist)

## 7. Error Handling Approach
(Based only on gateways / subprocesses detected)

## 8. High-Level Architecture Diagram (Mermaid)
{diagram}

## 9. Component Inventory (Extracted)
(List all extracted components)
"""


# ---------------------------------------------------------
# Generate CPI documentation
# ---------------------------------------------------------
def call_llm(prompt, meta):

    ctx = create_context(meta)  # Hidden metadata tokens (DeepSeek cannot “see” them)

    resp = requests.post(
        OLLAMA_GENERATE,
        json={
            "model": "deepseek-r1:1.5b",
            "prompt": prompt,
            "context": ctx,  # THIS IS THE FIX
            "stream": False
        }
    )
    resp.raise_for_status()
    return resp.json().get("response", "")


# ---------------------------------------------------------
# Write Markdown + DOCX
# ---------------------------------------------------------
def write_output(path, markdown):

    out = Path(path).parent / "docs"
    out.mkdir(parents=True, exist_ok=True)

    md = out / f"{Path(path).stem}_Documentation.md"
    docx = out / f"{Path(path).stem}_Documentation.docx"

    md.write_text(markdown, encoding="utf-8")

    try:
        subprocess.run(["pandoc", str(md), "-o", str(docx)], check=True)
    except Exception:
        pass

    print(f"Generated: {md}")
    print(f"Generated: {docx}")


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
