#!/usr/bin/env python3

import os
import requests
import json

# =====================================================
# Configuration
# =====================================================

API_KEY = os.getenv("QUBRID_API_KEY")

if not API_KEY:
    raise RuntimeError("QUBRID_API_KEY environment variable not set")

QUBRID_API_URL = "https://platform.qubrid.com/api/v1/qubridai/multimodal/chat"
MODEL_NAME = "Qwen/Qwen2.5-VL-7B-Instruct"

# =====================================================
# Request
# =====================================================

payload = {
    "model": MODEL_NAME,
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "What is in this image? Describe the main elements."
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://cdn.britannica.com/61/93061-050-99147DCE/Statue-of-Liberty-Island-New-York-Bay.jpg"
                    }
                }
            ]
        }
    ],
    "temperature": 0.7,
    "max_tokens": 300,
    "stream": False
}

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# =====================================================
# Call API
# =====================================================

response = requests.post(
    QUBRID_API_URL,
    headers=headers,
    json=payload,
    timeout=120
)

response.raise_for_status()

result = response.json()

# =====================================================
# Output
# =====================================================

print("=== Model Response ===\n")
print(result["choices"][0]["message"]["content"])
