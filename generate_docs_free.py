import os
import zipfile
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import subprocess

# CONFIG
MODEL = "mistral"  # or "mixtral" or "llama3.2"
OLLAMA_API = "http://localhost:11434"

def extract_iflow(zip_path, out_dir):
    out = Path(out_dir)
    out.mkdir(exist_ok=True, parents=True)
    with zipfile.ZipFile(zip_path, 'r') as z:
        z.extractall(out)
    return out

def find_xml_files(folder):
    return list(Path(folder).rglob("*.iflw")) + \
           list(Path(folder).rglob("*.iflow")) + \
           list(Path(folder).rglob("*.xml"))

def read_file(path):
    try:
        return Path(path).read_text(encoding="utf-8", errors="ignore")
    except:
        return ""

def call_llm(prompt):
    payload = json.dumps({
        "model": MODEL,
        "prompt": prompt
    })

    process = subprocess.Popen(
        ["ollama", "run", MODEL],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    out, err = process.communicate(prompt)
    return out

def build_prompt(parsed_xml):
    return f"""
You are a senior SAP CPI integration architect.

Generate professional CPI documentation with the following sections:

1. Executive Summary  
2. Flow Purpose  
3. Sender/Receiver Adapter Explanation  
4. Steps Breakdown  
5. Mapping Logic Summary  
6. Groovy Script Descriptions (if present)  
7. Parameters Explained  
8. Exception Handling  
9. Sequence Diagram (Mermaid format)  
10. End-to-End Flow Description  
11. Testing Instructions  
12. Sample Payloads  

Here is the extracted iFlow XML:

{parsed_xml[:20000]}
"""

def generate_documentation(zip_path):
    extracted = extract_iflow(zip_path, "./iflow_extracted")
    xml_files = find_xml_files(extracted)

    if not xml_files:
        return "❌ No iFlow XML found inside ZIP."

    main_xml = xml_files[0]
    xml_text = read_file(main_xml)

    prompt = build_prompt(xml_text)
    doc = call_llm(prompt)

    Path("Documentation.md").write_text(doc, encoding="utf-8")
    return "✔ Documentation generated: Documentation.md"

# Run
print(generate_documentation("Email_receiver_xlsxToXML.zip"))
