import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5:7b"


def generate_section(section_title: str, context: str) -> str:
    """
    Generate one documentation section using Ollama (Qwen).
    """

    prompt = (
        "You are a senior SAP CPI Technical Architect.\n\n"
        "Write a clear, factual technical documentation section.\n\n"
        f"Section Title:\n{section_title}\n\n"
        f"FACT CONTEXT (derived from iFlow XML):\n{context}\n\n"
        "STRICT RULES:\n"
        "- Use ONLY the provided context\n"
        "- DO NOT assume adapters, systems, or security if not stated\n"
        "- If information is missing, explicitly say it is not defined in the iFlow\n"
        "- Use SAP CPI terminology\n"
        "- Write professional paragraphs\n"
        "- No markdown\n"
        "- No bullet lists unless unavoidable\n"
    )

    payload = {
        "model": MODEL,
        "prompt": prompt,
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

        text = response.json().get("response", "")
        return text.strip() if text else "Content could not be generated from the iFlow."

    except requests.exceptions.Timeout:
        return "Documentation generation timed out for this section."

    except Exception as exc:
        return f"LLM generation error: {exc}"
