import requests
import time

# -------------------------------------------------
# Ollama Configuration
# -------------------------------------------------
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5:7b"

# -------------------------------------------------
# Generate ONE document section using LLM
# -------------------------------------------------
def generate_section(section_title: str, context: str) -> str:
    """
    Generates medium-detail SAP CPI documentation text
    for a single section using Ollama (Qwen).
    """

    prompt = f"""
You are a senior SAP CPI Technical Architect.

Write a MEDIUM-detail technical documentation section.

Section Title:
{section_title}

Context:
{context}

Guidelines:
- Use SAP CPI terminology
- Write clear technical paragraphs
- No assumptions beyond given context
- Avoid bullet overuse
- No markdown formatting
- Professional documentation tone
"""

    payload = {
        "model": MODEL,
        "prompt": prompt.strip(),
        "stream": False,
        "options": {
            "temperature": 0.3,
            "top_p": 0.9,
            "num_predict": 500
        }
    }

    try:
        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=(60, 600)  # connect timeout, read timeout
        )
        response.raise_for_status()

        data = response.json()
        text = data.get("response", "").strip()

        if not text:
            return "Content could not be generated for this section."

        return text

    except requests.exceptions.Timeout:
        return (
            "Documentation generation timed out for this section. "
            "Please review system resources or reduce section scope."
        )

    except requests.exceptions.RequestException as e:
        return f"Error while generating documentation: {str(e)}"

# -------------------------------------------------
# Health check (optional but recommended)
# -------------------------------------------------
def ollama_health_check() -> bool:
    """
    Verifies Ollama is reachable and responsive.
    """
    try:
        test_payload = {
            "model": MODEL,
            "prompt": "Health check",
            "stream": False,
            "options": {"num_predict": 5}
        }
        r = requests.post(OLLAMA_URL, json=test_payload, timeout=30)
        return r.status_code == 200
    except Exception:
        return False
