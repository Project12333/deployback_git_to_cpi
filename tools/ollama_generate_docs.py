#!/usr/bin/env python3
import sys
import json
import requests
import xml.etree.ElementTree as ET
from pathlib import Path
import subprocess

OLLAMA_URL = "http://localhost:11434/api/generate"

# -------------------------------
# Extract metadata from .iflw
# -------------------------------
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

            # Sender / Receiver detection
            if "sender" in tag:
                meta["senders"].append(name)
            if "receiver" in tag:
                meta["receivers"].append(name)

            # Adapters
            if "adapter" in tag:
                meta["adapters"].append(name)

            # Script detection (Groovy, JS, ScriptTask)
            if "script" in tag or "scripttask" in tag or "groovy" in tag:
                meta["scripts"].append(name)

            # Mapping
            if "mapping" in tag:
                meta["mappings"].append(name)

            # Order of execution
            meta["steps"].append(name)

    except Exception as e:
        meta["error"] = f"XML parse error: {e}"

    return meta


# -------------------------------
# High-level Mermaid Diagram
# -------------------------------
def high_level_diagram(meta):

    sender = meta["senders"][0] if meta["senders"] else "SenderSystem"
    receiver = meta["receivers"][0] if meta["receivers"] else "ReceiverSystem"

    diagram = f"""
```mermaid
graph TD
    {sender} -->|Request| CPI
    CPI -->|Processed Output| {receiver}
