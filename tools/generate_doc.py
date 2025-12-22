import os
import json
import requests
from parse_iflow import parse_iflow

QWEN_API_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
QWEN_API_KEY = os.environ["QWEN_API_KEY"]

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

if __name__ == "__main__":
    iflow = os.environ["IFLOW_PATH"]
    meta = parse_iflow(iflow)

    doc = call_qwen(build_prompt(meta))

    out = f"docs/{meta['name']}.md"
    os.makedirs("docs", exist_ok=True)

    with open(out, "w", encoding="utf-8") as f:
        f.write(doc)

    print(f"Generated {out}")
