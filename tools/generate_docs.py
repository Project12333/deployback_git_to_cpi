#!/usr/bin/env python3
import os
import re
import argparse
from pathlib import Path
from datetime import datetime

from docx import Document
from docx.shared import Inches, Pt

# ===================== CONFIG =====================
AUTHOR = "Sindhu"
VERSION = "Draft"
DATE = datetime.utcnow().strftime("%Y-%m-%d")

SAP_LOGO = "tools/logos/sap.png"
MM_LOGO = "tools/logos/motiveminds.png"

# ===================== HELPERS =====================
def sanitize(name):
    return re.sub(r'[<>:"/\\|?*]', "", name)

def find_iflows(package_dir):
    roots = set()
    for root, _, files in os.walk(package_dir):
        if any(f.endswith(".iflw") for f in files):
            roots.add(Path(root))
    return sorted(roots)

def read_files(iflow_dir):
    text = ""
    for root, _, files in os.walk(iflow_dir):
        for f in files:
            if f.endswith((".iflw", ".groovy", ".xslt")):
                p = Path(root) / f
                text += f"\n{p.name}\n"
    return text.lower()

# ===================== RULE ENGINE =====================
def detect_sender_receiver(text):
    sender = "Unknown Sender"
    receiver = "Unknown Receiver"

    if "mail" in text:
        sender = "Mail Adapter"
    elif "http" in text:
        sender = "HTTP Adapter"
    elif "sftp" in text:
        sender = "SFTP Adapter"
    elif "idoc" in text:
        sender = "IDoc Adapter"

    if "receiver" in text or "target" in text:
        receiver = "Target System"

    return sender, receiver

def detect_components(text):
    comps = []
    if "groovy" in text:
        comps.append("Groovy Script")
    if "xslt" in text or "mapping" in text:
        comps.append("Message Mapping")
    if "router" in text:
        comps.append("Router")
    if not comps:
        comps.append("Standard CPI Flow Steps")
    return comps

# ===================== CONTENT GENERATION =====================
def build_content(iflow_name, text):
    sender, receiver = detect_sender_receiver(text)
    components = detect_components(text)

    content = f"""
1. Introduction

1.1 Purpose  
This document describes the SAP CPI integration flow **{iflow_name}**.  
The iFlow is designed to process incoming messages and route them through SAP CPI for further processing.

1.2 Scope  
The scope includes message reception, processing, transformation, and forwarding to downstream systems.

2. Integration Overview

2.1 Integration Architecture  
The integration is implemented in SAP Cloud Integration (CPI).  
Messages are received via **{sender}**, processed using CPI flow steps, and sent to **{receiver}**.

2.2 Integration Components  
The following components are used in this integration:
- Sender Adapter: {sender}
- Receiver: {receiver}
- Processing Components: {", ".join(components)}

3. Integration Scenarios

3.1 Scenario Description  
The iFlow handles inbound messages, validates and processes the payload, and ensures correct delivery to the target system.

3.2 Data Flows  
Inbound Message → Processing Steps → Transformation → Target System

3.3 Security Requirements  
Credentials and sensitive information are managed using SAP CPI secure parameters.  
Authentication is handled at the adapter level.

4. Error Handling and Logging  
Errors are captured using CPI exception subprocesses.  
Message logs are enabled for monitoring and troubleshooting.

5. Testing Validation  
Unit testing and end-to-end testing are performed using test payloads.  
Message monitoring is used to validate successful processing.

6. Reference Documents  
SAP CPI Integration Suite Documentation  
Project-specific integration design documents
"""
    return content.strip()

# ===================== DOCX =====================
def write_docx(path, iflow_name, body):
    doc = Document()

    # Logos
    table = doc.add_table(1, 2)
    try:
        table.cell(0, 0).paragraphs[0].add_run().add_picture(SAP_LOGO, width=Inches(1.5))
        table.cell(0, 1).paragraphs[0].add_run().add_picture(MM_LOGO, width=Inches(1.5))
    except:
        pass

    # Title
    title = doc.add_paragraph(iflow_name)
    title.alignment = 1
    title.runs[0].bold = True
    title.runs[0].font.size = Pt(26)

    # Meta table
    meta = doc.add_table(3, 2)
    meta.style = "Table Grid"
    meta.cell(0, 0).text = "Author"
    meta.cell(1, 0).text = "Date"
    meta.cell(2, 0).text = "Version"
    meta.cell(0, 1).text = AUTHOR
    meta.cell(1, 1).text = DATE
    meta.cell(2, 1).text = VERSION

    doc.add_page_break()

    for line in body.split("\n"):
        doc.add_paragraph(line)

    doc.save(path)

# ===================== MAIN =====================
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", required=True)
    args = parser.parse_args()

    base = Path("cpi-artifacts") / args.package
    iflows = find_iflows(base)

    for iflow in iflows:
        name = sanitize(iflow.name)
        print("Generating documentation for:", name)

        text = read_files(iflow)
        content = build_content(name, text)

        out = iflow / "docs"
        out.mkdir(exist_ok=True)

        write_docx(out / f"{name}.docx", name, content)

    print("✔ Documentation generated successfully")

if __name__ == "__main__":
    main()
