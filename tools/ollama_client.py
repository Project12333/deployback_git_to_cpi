import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5:7b"


def generate_section(section_title: str, context: str) -> str:
    """
    Generate ONE documentation section using Ollama (Qwen).
    Context is STRICTLY derived from iFlow XML.
    """

    prompt = f"""
You are a senior SAP CPI Technical Architect.

Write a clear and factual technical documentation section.

Section Title:
{section_title}

FACT CONTEXT (derived from iFlow XML):
{context}

STRICT RULES:
- Use ONLY the provided context
- DO NOT assume adapters, systems, or security if not stated
- If something is missing, explicitly say it is not defined in the iFlow
- Use SAP CPI terminology
- Write professional paragraphs
- No markdown
- No bullets unless unavoidable
"""

    payload = {
        "model": MODEL,
        "prompt": prompt.strip(),
        "stream": False,
        "options": {
            "temperature": 0.2,
            "num_predict": 350
        }
    }

    try:
        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=(60, 600)
        )
        response.raise_for_status()

        return response.json().get("response", "").strip() or \
            "Content could not be generated from the provided iFlow."

    except requests.exceptions.Timeout:
        return "Documentation generation timed out for this section."

    except Exception as e:
        return f"LLM g
