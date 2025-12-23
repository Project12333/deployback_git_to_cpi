import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "deepseek-r1:7b"

def generate(prompt):
    r = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False
        },
        timeout=300
    )
    r.raise_for_status()
    return r.json()["response"]
