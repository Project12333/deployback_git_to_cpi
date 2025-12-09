#!/usr/bin/env python3
import sys
import json
import requests
import xml.etree.ElementTree as ET
from pathlib import Path

OLLAMA_URL = "http://localhost:11434/api/generate"


# ----------------------------------------------------------
# Parse .iflw for metadata
# ----------------------------------------------------------
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


# ----------------------------------------------------------
# Build Mermaid diagram from steps
# ----------------------------------------------------------
def create_mermaid(meta):
    steps = [s.replace(" ", "_") for s in meta["steps"]]
    lines = ["flowcha]()
