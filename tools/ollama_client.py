import requests
import json

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "deepseek-r1:7b"

def call_ollama(prompt: str) -> str:
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": True,
        "options": {
            "temperature": 0.2,
            "num_ctx": 4096
        }
    }

    response = requests.post(
        OLLAMA_URL,
        json=payload,
        stream=True,
        timeout=None
    )

    full_text = ""

    for line in response.iter_lines():
        if not line:
            continue
        data = json.loads(line.decode("utf-8"))
        full_text += data.get("response", "")
        if data.get("done"):
            break

    return full_text
