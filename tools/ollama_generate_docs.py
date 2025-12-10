#!/usr/bin/env python3
import sys
import json
import requests
import xml.etree.ElementTree as ET
from pathlib import Path
import subprocess
import os
from datetime import datetime

OLLAMA_URL = "http://localhost:11434/api/generate"


# ---------------------------------------------------------
# Parse .iflw XML
# ---------------------------------------------------------
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


# ---------------------------------------------------------
# Mermaid Diagram
# ---------------------------------------------------------
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


# ---------------------------------------------------------
# Determine version dynamically
# ---------------------------------------------------------
def determine_version(flow_name):
    mode = os.getenv("VERSION_MODE", "none")
    manual_version = os.getenv("VERSION_VALUE", "")

    if mode == "manual" and manual_version:
        return manual_version

    if mode == "date":
        return datetime.now().strftime("%Y-%m-%d")

    if mode == "git-sha":
        try:
            sha = subprocess.check_output(
                ["git", "rev-parse", "--short", "HEAD"]).decode().strip()
            return sha
        except:
            return "unknown"

    return "1.0"  # default version


# ---------------------------------------------------------
# Build Prompt Structure
# ---------------------------------------------------------
def build_prompt(meta, diagram):
    # NOTE:
    # - Keep this string a NORMAL string (not an f-string) so that "{{...}}" stays as double-brace tokens.
    # - We concatenate diagram at the end because diagram contains backticks/mermaid and can be inserted safely.
    prompt = (
        # Top logos for Markdown preview (GitHub): point to repo images
        "<table><tr>"
        f"<td><img src=\"tools/logos/sap.png\" alt=\"SAP\" width=\"180\"></td>"
        f"<td align=\"right\"><img src=\"tools/logos/motiveminds.png\" alt=\"Motiveminds\" width=\"180\"></td>"
        "</tr></table>\n\n"

        # Metadata placeholders (these will be replaced in write_output)
        "Document: {{flow_name}}\n"
        "Author: {{author}}\n"
        "Date: {{date}}\n"
        "Version: {{version}}\n\n"

        # Flow name as the main heading (this becomes Heading 1 in DOCX)
        "# {{flow_name}}\n\n"

        "# 1. Introduction\n\n"
        "## 1.1 Purpose\n"
        "<Describe purpose of the integration flow.>\n\n"
        "## 1.2 Scope\n"
        "<Describe the scope based on metadata.>\n\n"

        "# 2. Integration Overview\n\n"
        "## 2.1 Integration Architecture\n"
        "Explain architecture at a high level.\n\n"
        "## 2.2 Integration Components\n"
        f"Sender Systems: {meta['senders']}\n\n"
        f"Receiver Systems: {meta['receivers']}\n\n"
        f"Adapters Used: {meta['adapters']}\n\n"

        "# 3. Integration Scenarios\n\n"
        "## 3.1 Scenario Description\n"
        "<Describe integration scenario.>\n\n"
        "## 3.2 Data Flows\n"
        "<Explain messages and transformations.>\n\n"
        "## 3.3 Security Requirements\n"
        "<Describe authentication, tokens, etc.>\n\n"

        "# 4. Error Handling and Logging\n"
        "<Describe error handling logic.>\n\n"

        "# 5. Testing Validation\n"
        "<Provide high-level UAT/scenario descriptions.>\n\n"

        "# 6. Reference Documents\n"
        "<List mapping sheets, API docs, etc.>\n\n"

        "# High-Level Process Flow Diagram\n\n"
    )

    # append diagram (it can contain backticks / mermaid)
    prompt = prompt + diagram + "\n\n"

    # Append reference metadata (kept for debugging, not to be displayed to reader)
    prompt = prompt + "REFERENCE METADATA (DO NOT OUTPUT THIS):\n" + json.dumps(meta, indent=2) + "\n"

    return prompt


# ---------------------------------------------------------
# Call the LLM
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
# Write Markdown + DOCX (with placeholders replaced)
# ---------------------------------------------------------
def write_output(path, markdown):
    out = Path(path).parent / "docs"
    out.mkdir(parents=True, exist_ok=True)

    flow_name = Path(path).stem
    today = datetime.now().strftime("%Y-%m-%d")
    author = "Sindhu K V"

    version = determine_version(flow_name)

    # Replace placeholders
    markdown = (
        markdown.replace("{{flow_name}}", flow_name)
                .replace("{{date}}", today)
                .replace("{{version}}", version)
                .replace("{{author}}", author)
    )

    md = out / f"{flow_name}_Documentation_v{version}.md"
    docx = out / f"{flow_name}_Documentation_v{version}.docx"

    md.write_text(markdown, encoding="utf-8")

    try:
        subprocess.run([
            "pandoc", str(md),
            "--reference-doc=tools/reference.docx",
            "-o", str(docx)
        ], check=True)
    except Exception as e:
        print("Pandoc conversion failed:", e)

    print(f"Generated: {md}")
    print(f"Generated: {docx}")


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------
if __name__ == "__main__":
    for f in sys.argv[1:]:
        print(f"Processing {f}")

        meta = parse_iflw(f)
        diagram = high_level_diagram(meta)
        prompt = build_prompt(meta, diagram)

        md = call_llm(prompt)
        write_output(f, md)

    print("Done.")
