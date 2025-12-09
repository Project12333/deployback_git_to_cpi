#!/usr/bin/env python3
import sys
import json
import requests
import xml.etree.ElementTree as ET
from pathlib import Path

OLLAMA_URL = "http://localhost:11434/api/generate"


def parse_iflw(path):
    meta = {
        "flowname": Path(path).stem.replace(" ", "_"),
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

            if "script" in tag or "groovy" in tag or "scripttask" in tag:
                meta["scripts"].append(name)

            if "mapping" in tag:
                meta["mappings"].append(name)

            meta["steps"].append(name)

    except Exception as e:
        meta["error"] = f"XML parse error: {e}"

    return meta


def create_mermaid(meta):
    steps = [s.replace(" ", "_") for s in meta["steps"]]
    lines = ["flowchart LR"]

    prev = None
    for step in steps:
        if prev is not None:
            lines.append(f"    {prev} --> {step}")
        prev = step

    return "\n".join(lines)


def build_prompt(meta, mermaid):
    return (
        "You are an SAP CPI documentation expert.\n\n"
        f"# Technical Documentation for iFlow: {meta['flowname']}\n\n"
        "## 1. High-level architecture\n<describe architecture>\n\n"
        "## 2. Purpose\n<short purpose>\n\n"
        f"## 3. Sender/Receiver\nSenders: {meta['senders']}\nReceivers: {meta['receivers']}\n\n"
        f"## 4. Adapters Used\n{meta['adapters']}\n\n"
        "## 5. Steps Explanation\n<describe steps>\n\n"
        f"## 6. Mapping Logic\n{meta['mappings']}\n\n"
        f"## 7. Groovy Scripts\n{meta['scripts']}\n\n"
        "## 8. Error Handling\n<explain error logic>\n\n"
        "## 9. Mermaid Diagram\n"
        f"```mermaid\n{mermaid}\n```\n\n"
        "REFERENCE DATA (DO NOT OUTPUT):\n"
        f"{json.dumps(meta, indent=2)}"
    )


def call_llm(prompt):
    r = requests.post(OLLAMA_URL, json={
        "model": "deepseek-r1:1.5b",
        "prompt": prompt,
        "stream": False
    })
    r.raise_for_status()
    return r.json().get("response", "")


def write_output(path, markdown, mermaid):
    flow = Path(path).stem.replace(" ", "_")
    outdir = Path(path).parent.joinpath("docs")
    outdir.mkdir(parents=True, exist_ok=True)

    md_path = outdir / f"{flow}_Documentation.md"
    mmd_path = outdir / f"{flow}.mmd"

    md_path.write_text(markdown, encoding="utf-8")
    mmd_path.write_text(mermaid, encoding="utf-8")

    print(f"Generated: {md_path}")
    print(f"Generated: {mmd_path}")


if __name__ == "__main__":
    for iflw in sys.argv[1:]:
        print(f"Processing {iflw}")

        meta = parse_iflw(iflw)
        mermaid = create_mermaid(meta)
        prompt = build_prompt(meta, mermaid)

        markdown = call_llm(prompt)
        write_output(iflw, markdown, mermaid)

    print("Done: documentation + Mermaid generated.")
