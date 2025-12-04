import os
from openai import OpenAI

MODEL = "gpt-4o-mini"
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_documentation(iflow):
    prompt = f"""
You are an SAP CPI expert.
Generate clean documentation for the below iFlow.

### RAW IFLOW XML ###
{iflow['raw']}

### OUTPUT FORMAT (Markdown) ###
# {iflow['name']} ({iflow['id']})

## TL;DR
Short summary.

## Overview
Explain what the iFlow does.

## Sender / Receiver Adapters
Extract adapter types, protocols, endpoints.

## Flow Steps
Describe each step in sequence.

## Message Mappings
List mapping files, important fields.

## Properties Used
List header, exchange, external parameters.

## Security / Auth
Mention OAuth, certificates, basic auth if visible.

## Exception Handling
Describe exception subprocesses.

## Test Payloads
Create example request + response.

## Deployment Notes
How to deploy, dependencies.

If information is missing, say "Not provided".
"""

    res = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1800,
    )

    return res.choices[0].message["content"]
