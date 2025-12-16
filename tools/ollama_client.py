import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5:7b"

def generate_section(section_title: str, context: str) -> str:
    """
    Generates ONE documentation section using Ollama (Qwen).
    Designed to avoid timeouts by keeping prompts small.
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
- Write in professional paragraph form
- No markdown
- No excessive bullet points
"""

    payload = {
        "model": MODEL,
        "prompt": prompt.strip(),
        "stream": False,
        "options": {
            "temperature": 0.3,
            "num_predict": 300   # 🔑 reduced to prevent timeout
        }
    }

    try:
        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=(60, 600)   # connect, read timeout
        )
        response.raise_for_status()

        text = response.json().get("response", "").strip()
        return text if text else "Content could not be generated."

    except requests.exceptions.Timeout:
        return "⚠ Documentation generation timed out for this section."

    except Exception as e:
        return f"⚠ LLM generation error: {e}"
