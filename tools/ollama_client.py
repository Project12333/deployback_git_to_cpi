import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5:7b"

def generate_section(section_title: str, context: str) -> str:
    """
    Generate MEDIUM-detail SAP CPI documentation text
    for a single section using Ollama (Qwen).
    """

    prompt = f"""
You are a senior SAP CPI Technical Architect.

Write a MEDIUM-detail technical documentation section.

Section Title:
{section_title}

Context:
{context}

Rules:
- Use SAP CPI terminology
- Professional paragraph style
- No markdown
- No bullet lists unless required
"""

    payload = {
        "model": MODEL,
        "prompt": prompt.strip(),
        "stream": False,
        "options": {
            "temperature": 0.3,
            "num_predict": 500
        }
    }

    try:
        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=(60, 600)
        )
        response.raise_for_status()
        return response.json().get("response", "").strip() or "Content not generated."
    except Exception as e:
        return f"LLM generation failed: {e}"
