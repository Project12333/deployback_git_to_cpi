#!/usr/bin/env python3
import sys
import json
import requests
import xml.etree.ElementTree as ET
from pathlib import Path
import subprocess

OLLAMA_URL = "http://localhost:11434/api/generate"

# ----------------------------------------
# Parse metadata from .iflw
# ----------------------------------------
def parse_iflw(path):
    meta = {
        "flowname": Path(path).stem,
        "senders": [],
        "receivers": [],
        "adapters": [],
        "scripts": [],
        "mappings": [],
        "steps": []
    }

    try:
        tree = ET.parse(path)
        root = tree.getroot()

        for elem in root.iter():
            tag = elem.tag.split("}")[-1].lower()
            name = elem.attrib.get("name") or elem.attrib.get("id") or tag

            if "sender" in tag:
                meta["senders"].append(name)

            if "receiver" in tag:
                meta["receivers"].append(name)

            if "adapter" in tag:
                meta["adapters"].append(name)

            if "script" in tag or "scripttask" in tag or "groovy" in tag:
                meta["scripts"].append(name)

            if "mapping" in tag:
                meta["mappings"].append(name)

            meta["steps"].append(name)

    except Exception as e:
        meta["error"] = f"XML parse error: {e}"

    return meta


# ----------------------------------------
# Generate high-level Mermaid diagram
# ----------------------------------------
def high_level_diagram(meta):

    sender = meta["senders"][0] if meta["senders"] else "SenderSystem"
    receiver = meta["receivers"][0] if meta["receivers"] else "ReceiverSystem"

    diagram = (
        "```mermaid\n"
        "graph TD\n"
        f"    {sender} -->|Request| CPI\n"
        f"    CPI -->|Processed Output| {receiver}\n"
        "```"
    )

    return diagram


# ----------------------------------------
# Build strict documentation prompt
# ----------------------------------------
def build_prompt(meta, diagram):

    prompt = (
        "You are an SAP CPI documentation expert.\n"
        "Generate the CPI documentation STRICTLY using the EXACT TEMPLATE below.\n"
        "DO NOT add extra sections.\n"
        "DO NOT modify headings.\n"
        "DO NOT output XML.\n"
        "DO NOT hallucinate missing values.\n\n"
        "# Consolidated Technical Report for SAP CPI iFlow: " + meta["flowname"] + "\n\n"
        "## 1. High-level architecture\n"
        "<Describe high-level architecture based on sender/receiver and adapters.>\n\n"
        "## 2. Purpose of this iFlow\n"
        "<Short purpose of this iFlow.>\n\n"
        "## 3. Sender/Receiver systems\n"
        "Sender Systems: " + str(meta["senders"]) + "\n"
        "Receiver Systems: " + str(meta["receivers"]) + "\n\n"
        "## 4. Adapter types used\n"
        + str(meta["adapters"]) + "\n\n"
        "## 5. Step-by-step flow explanation\n"
        "<Explain the end-to-end steps in high-level terms.>\n\n"
        "## 6. Mapping logic summary\n"
        "<Explain mapping logic (XSLT, message mapping) if applicable.>\n\n"
        "## 7. Groovy script explanations\n"
        "Scripts detected:\n"
        + str(meta["scripts"]) + "\n"
        "<Explain each script's purpose.>\n\n"
        "## 8. Error handling\n"
        "<Explain error-handling approach.>\n\n"
        "## 9. High-Level Process Flow Diagram\n"
        "(Use ONLY this Mermaid diagram):\n\n"
        + diagram +
        "\n\n"
        "REFERENCE METADATA (DO NOT OUTPUT THIS):\n"
        + json.dumps(meta, indent=2)
    )

    return prompt


# ----------------------------------------
# Call LLM
# ----------------------------------------
def call_llm(prompt):
    res = requests.post(OLLAMA_URL, json={
        "model": "deepseek-r1:1.5b",
        "prompt": prompt,
        "stream": False
    })
    res.raise_for_status()
    return res.json().get("response", "")


# ----------------------------------------
# Write Markdown + DOCX
# ----------------------------------------
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


# ----------------------------------------
# MAIN
# ----------------------------------------
if __name__ == "__main__":
    for f in sys.argv[1:]:
        print(f"Processing {f}")

        meta = parse_iflw(f)
        diagram = high_level_diagram(meta)
        prompt = build_prompt(meta, diagram)

        md = call_llm(prompt)
        write_output(f, md)

    print("Done.")
