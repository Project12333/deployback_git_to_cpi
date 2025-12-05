#!/usr/bin/env python3
import sys
import json
import requests
import xml.etree.ElementTree as ET
from pathlib import Path
import subprocess

# Ollama HTTP endpoint (Docker)
OLLAMA_URL = "http://localhost:11434/api/generate"


# ---------------------------------------------------------
# Parse .iflw XML safely (never fails)
# ---------------------------------------------------------
def parse_iflw(path):
    try:
        tree = ET.parse(path)
        root = tree.getroot()
    except Exception as e:
        return {
            "flowname": Path(path).stem,
            "error": f"Failed to parse XML: {str(e)}",
            "path": str(path)
        }

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

    # Read first part of XML for LLM context
    try:
        with open(path, "r", errors="ignore") as f:
            data["xml_sample"] = f.read(20000)
    except:
        data["xml_sample"] = "<Failed to read XML text>"

    return data


# ---------------------------------------------------------
# SAFE Prompt Builder (No f-string, No triple quotes)
# ---------------------------------------------------------
def doc_prompt(data):
    metadata = json.dumps(data, indent=2, ensure_ascii=False)

    prompt_parts = [
        "You are an expert SAP CPI Integration Architect.",
        "",
        "Generate a highly detailed, professional CPI iFlow documentation in Markdown.",
        "",
        "REQUIRED SECTIONS:",
        "1. Flow Name",
        "2. Business Purpose",
        "3. High-Level Technical Overview",
        "4. Architecture Diagram (text explanation)",
        "5. Sender & Receiver Adapters",
        "6. Detailed Message Processing Steps",
        "7. Groovy Script Analysis",
        "8. Mapping Logic Explanation",
        "9. Exception Handling",
        "10. Properties & Headers",
        "11. Runtime Behavior",
        "12. Test Scenarios",
        "13. Deployment Notes",
        "14. Security Considerations",
        "15. Assumptions & Limitations",
        "",
        "PARSED METADATA (use this to infer missing details):",
        metadata,
        "",
        "RULES:",
        "- Output must be Markdown only.",
        "- Be detailed and infer logically based on best practices.",
        "- Never say 'cannot determine'.",
        "- Produce long, structured explanations."
    ]

    return "\n".join(prompt_parts)


# ---------------------------------------------------------
# Call DeepSeek model through Ollama HTTP API
# ---------------------------------------------------------
def call_deepseek(prompt):
    payload = {
        "model": "deepseek-r1:14b",
        "prompt": prompt,
        "stream": False
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload)
        response.raise_for_status()
    except Exception as e:
        raise RuntimeError(f"Ollama HTTP API failed: {str(e)}")

    data = response.json()
    return data.get("response", "")


# ---------------------------------------------------------
# Save Markdown + DOCX files
# ---------------------------------------------------------
def write_output(iflw_path, content):
    flow_dir = Path(iflw_path).parent / "docs"
    flow_dir.mkdir(parents=True, exist_ok=True)

    name = Path(iflw_path).stem
    md_path = flow_dir / f"{name}_Documentation.md"
    docx_path = flow_dir / f"{name}_Documentation.docx"

    md_path.write_text(content, encoding="utf-8")

    # Convert Markdown → DOCX using pandoc
    try:
        subprocess.run(["pandoc", str(md_path), "-o", str(docx_path)], check=True)
    except Exception as e:
        print(f"⚠ WARNING: DOCX creation failed: {e}")

    print(f"📄 Markdown generated: {md_path}")
    print(f"📄 Word document generated: {docx_path}")


# ---------------------------------------------------------
# Main runner
# ---------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ ERROR: No .iflw file provided.")
        sys.exit(1)

    for iflw in sys.argv[1:]:
        print(f"📂 Processing iFlow: {iflw}")

        parsed = parse_iflw(iflw)
        prompt = doc_prompt(parsed)

        print("🤖 Calling DeepSeek to generate documentation...")
        markdown = call_deepseek(prompt)

        write_output(iflw, markdown)

    print("✅ All documentation generated successfully.")
