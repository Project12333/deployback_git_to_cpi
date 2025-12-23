import os
import json
import requests
from pathlib import Path
from parse_iflow import parse_iflow

QWEN_API_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
QWEN_API_KEY = os.environ["QWEN_API_KEY"]

PACKAGE_NAME = os.environ.get("PACKAGE_NAME")
if not PACKAGE_NAME:
    raise Exception("PACKAGE_NAME environment variable not set")

BASE_DIR = Path("cpi-artifacts") / PACKAGE_NAME
OUTPUT_DIR = Path("docs") / PACKAGE_NAME

if not BASE_DIR.exists():
    raise Exception(f"Package folder not found: {BASE_DIR}")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def build_prompt(meta):
    return f"""
You are a senior SAP CPI Technical Architect.

Using ONLY the following extracted metadata:
{json.dumps(meta, indent=2)}

Generate a Markdown document with EXACTLY this structure:

# 1. Introduction
## 1.1 Purpose
## 1.2 Scope

# 2. Integration Overview
## 2.1 Integration Architecture
## 2.2 Integration Components

# 3. Integration Scenarios
## 3.1 Scenario Description
## 3.2 Data Flows
## 3.3 Security Requirements

# 4. Error Handling and Logging

# 5. Testing Validation

# 6. Reference Documents

Rules:
- Do NOT invent systems or adapters
- If information is missing, say "Not configured in this iFlow"
- Use professional SAP CPI language
- Output Markdown only
"""

def call_qwen(prompt):
    payload = {
        "model": "qwen3-max",
        "input": {"prompt": prompt}
    }

    headers = {
        "Authorization": f"Bearer {QWEN_API_KEY}",
        "Content-Type": "application/json"
    }

    r = requests.post(QWEN_API_URL, headers=headers, json=payload)
    r.raise_for_status()
    return r.json()["output"]["text"]

# -------- MAIN --------
iflow_files = list(BASE_DIR.rglob("*.iflw"))

if not iflow_files:
    raise Exception(f"No .iflw files found in package {PACKAGE_NAME}")

for iflow in iflow_files:
    print(f"Processing iFlow: {iflow}")

    meta = parse_iflow(iflow)
    doc = call_qwen(build_prompt(meta))

    out_file = OUTPUT_DIR / f"{meta['name']}.md"
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(doc)

    print(f"Generated {out_file}")

print(f"Documentation generation completed for package: {PACKAGE_NAME}")
