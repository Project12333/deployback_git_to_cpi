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

            # Sender / Receiver
            if "sender" in tag.lower():
                meta["senders"].append(name)

            if "receiver" in tag.lower():
                meta["receivers"].append(name)

            # Adapters
            if "adapter" in tag.lower():
                meta["adapters"].append(name)

            # Scripts
            if "script" in tag.lower() or "groovy" in tag.lower():
                meta["scripts"].append(name)

            # Mapping
            if "mapping" in tag.lower():
                meta["mappings"].append(name)

            # BPMN elements
            if tag == "serviceTask":
                meta["servicetasks"].append(name)

            if tag == "callActivity":
                meta["callactivities"].append(name)

            if tag == "exclusiveGateway" or tag == "parallelGateway" or tag == "inclusiveGateway":
                meta["gateways"].append(name)

            if tag == "subProcess":
                meta["subprocesses"].append(name)

            if tag == "startEvent":
                meta["startevents"].append(name)

            if tag == "endEvent":
                meta["endevents"].append(name)

    except Exception as e:
        meta["error"] = f"Failed to parse .iflw: {e}"

    return meta


# ---------------------------------------------------------
# Generate improved Mermaid diagram
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
# Build final standardized documentation
# ---------------------------------------------------------
def build_prompt(meta, diagram):

    return (
f"You are an SAP CPI documentation expert.\n"
f"Generate documentation STRICTLY in the exact format below.\n"
f"DO NOT hallucinate missing elements—only describe components present in metadata.\n\n"

f"# Technical Documentation – {meta['flowname']}\n\n"

f"## 1. Overview\n"
f"<Generate a short overview of this iFlow using only available metadata.>\n\n"

f"## 2. Systems Involved\n"
f"### Sender Systems\n{meta['senders']}\n\n"
f"### Receiver Systems\n{meta['receivers']}\n\n"

f"## 3. Adapters Used\n{meta['adapters']}\n\n"

f"## 4. Key Functional Steps\n"
f"<Generate only relevant subsections based on metadata.>\n\n"

f"## 5. Mapping Logic Summary\n"
f"<Describe mapping logic only if mappings exist.>\n\n"

f"## 6. Groovy Script Summary\nScripts detected: {meta['scripts']}\n"
f"<Explain purpose only if scripts exist.>\n\n"

f"## 7. Error Handling Approach\n"
f"<Describe error handling based on gateways/subprocesses if present.>\n\n"

f"## 8. High-Level Architecture Diagram (Mermaid)\n"
f"{diagram}\n\n"

f"## 9. Component Inventory (Extracted)\n"
f"- Start Events: {meta['startevents']}\n"
f"- End Events: {meta['endevents']}\n"
f"- Service Tasks: {meta['servicetasks']}\n"
f"- Call Activities: {meta['callactivities']}\n"
f"- Gateways: {meta['gateways']}\n"
f"- SubProcesses: {meta['subprocesses']}\n"
f"- Scripts: {meta['scripts']}\n"
f"- Mappings: {meta['mappings']}\n\n"

"REFERENCE (Do Not Output):\n"
+ json.dumps(meta, indent=2)
)


# ---------------------------------------------------------
# Call DeepSeek (Ollama)
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
# Write MD + DOCX
# ---------------------------------------------------------
def write_output(path, markdown):

    outdir = Path(path).parent / "docs"
    outdir.mkdir(exist_ok=True, parents=True)

    mdfile = outdir / f"{Path(path).stem}_Documentation.md"
    docxfile = outdir / f"{Path(path).stem}_Documentation.docx"

    mdfile.write_text(markdown, encoding="utf-8")

    # Generate DOCX through Pandoc (best-effort)
    try:
        subprocess.run(["pandoc", str(mdfile), "-o", str(docxfile)], check=True)
    except Exception:
        pass

    print(f"Created: {mdfile}")
    print(f"Created: {docxfile}")


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------
if __name__ == "__main__":

    for f in sys.argv[1:]:

        print(f"Processing: {f}")

        meta = parse_iflw(f)
        diagram = generate_mermaid(meta)
        prompt = build_prompt(meta, diagram)
        markdown = call_llm(prompt)

        write_output(f, markdown)

    print("Completed.")
