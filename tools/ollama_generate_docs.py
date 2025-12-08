#!/usr/bin/env python3
import sys
import json
import requests
import xml.etree.ElementTree as ET
from pathlib import Path
import subprocess

OLLAMA_URL = "http://localhost:11434/api/generate"


# ---------------------------------------------------------
# Parse .iflw XML (Fast + Lightweight)
# ---------------------------------------------------------
def parse_iflw(path):
    data = {
        "flowname": Path(path).stem,
        "path": str(path),
        "steps": []
    }

    try:
        tree = ET.parse(path)
        root = tree.getroot()

        for elem in root.iter():
            tag = elem.tag.split("}")[-1].lower()
            name = elem.attrib.get("name") or elem.attrib.get("id") or tag

            if any(k in tag for k in ["adapter", "sender", "receiver",
                                      "script", "mapping", "exception"]):
                data["steps"].append({
                    "tag": tag,
                    "name": name.replace(" ", "_")
                })

    except Exception as e:
        data["error"] = f"XML parse failed: {e}"

    # Read small XML sample for LLM
    try:
        with open(path, "r", errors="ignore") as f:
            data["xml_sample"] = f.read(3000)
    except:
        data["xml_sample"] = ""

    return data


# ---------------------------------------------------------
# Mermaid Diagram Generator (AUTO)
# ---------------------------------------------------------
def build_mermaid(data):
    steps = data.get("steps", [])
    if not steps:
        return "No steps found"

    mer = ["flowchart TD"]
    prev = None

    for s in steps:
        node = s["name"]
        if prev:
            mer.append(f"    {prev} --> {node}")
        prev = node

    return "```mermaid\n" + "\n".join(mer) + "\n```"


# ---------------------------------------------------------
# Fast Prompt Builder
# ---------------------------------------------------------
def build_prompt(meta, mermaid):
    payload = {
        "meta": meta,
        "diagram": mermaid
    }

    return (
        "You are an SAP CPI Integration Architect.\n"
        "Generate a clean, concise, fast Markdown documentation for the iFlow.\n\n"
        "REQUIRED SECTIONS:\n"
        "1. Flow Name\n"
        "2. Business Purpose (short but meaningful)\n"
        "3. High-Level Technical Flow\n"
        "4. Mermaid Diagram (use provided one)\n"
        "5. Steps Explanation (describe each extracted step)\n"
        "6. Scripts & Mappings Summary\n"
        "7. Exception Handling\n"
        "8. Properties Used\n"
        "9. Test Cases\n"
        "10. Deployment Notes\n\n"
        "Here is the parsed data:\n"
        f"{json.dumps(payload, indent=2)}\n\n"
        "RULES:\n"
        "- Use the Mermaid diagram exactly as provided.\n"
        "- Output only Markdown.\n"
        "- Be fast, structured, and professional.\n"
    )


# ---------------------------------------------------------
# Call Ollama (Optimized + Small Model)
# ---------------------------------------------------------
def call_llm(prompt):
    payload = {
        "model": "deepseek-r1:1.5b",   # ⚡ SUPER FAST MODEL
        "prompt": prompt,
        "stream": False
    }

    response = requests.post(OLLAMA_URL, json=payload)
    response.raise_for_status()
    return response.json().get("response", "")


# ---------------------------------------------------------
# Write MD + DOCX
# ---------------------------------------------------------
def write_output(path, markdown):
    out_dir = Path(path).parent / "docs"
    out_dir.mkdir(parents=True, exist_ok=True)

    name = Path(path).stem
    md = out_dir / f"{name}_Documentation.md"
    docx = out_dir / f"{name}_Documentation.docx"

    md.write_text(markdown, encoding="utf-8")

    try:
        subprocess.run(["pandoc", str(md), "-o", str(docx)], check=True)
    except Exception as e:
        print(f"⚠ DOCX generation failed: {e}")

    print(f"📄 Markdown: {md}")
    print(f"📄 DOCX: {docx}")


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("No .iflw provided")
        sys.exit(1)

    for f in sys.argv[1:]:
        print(f"📂 Processing: {f}")

        meta = parse_iflw(f)
        mermaid = build_mermaid(meta)
        prompt = build_prompt(meta, mermaid)

        print("🤖 Calling LLM...")
        md = call_llm(prompt)

        write_output(f, md)

    print("✅ All docs generated FAST!")
