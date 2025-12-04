import sys
import os
import json
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
def parse(path):
    root = tree.getroot()
    info = { 'flowname': Path(path).stem, 'adapters': [], 'scripts': [], 'mappings': [], 'exceptions': [], 'properties': [] }
    for elem in root.iter():
        tag = elem.tag.split('}')[-1].lower()
        name = elem.attrib.get('name') or elem.attrib.get('id')
        if 'adapter' in tag or 'sender' in tag or 'receiver' in tag:
            info['adapters'].append(name)
        if 'script' in tag:
            info['scripts'].append(name)
        if 'mapping' in tag:
            info['mappings'].append(name)
        if 'exception' in tag or 'error' in tag:
            info['exceptions'].append(name)
        if 'property' in tag or 'header' in tag:
            info['properties'].append(name)
    with open(path, 'r', errors='ignore') as f: info['xml'] = f.read(15000)
    return info
def prompt(summary):
    return f'Generate CPI iFlow documentation in Markdown based on this summary: {json.dumps(summary)}'
def run_llm(text):
    cmd = f"echo \"{text}\" | ollama run mistral"
    return subprocess.check_output(cmd, shell=True, text=True)
def write_docs(path, md):
    folder = Path(path).parent / 'docs'
    folder.mkdir(exist_ok=True)
    md_file = folder / f"{Path(path).stem}_Documentation.md"
    docx_file = folder / f"{Path(path).stem}_Documentation.docx"
    md_file.write_text(md, encoding='utf8')
    subprocess.run(['pandoc', str(md_file), '-o', str(docx_file)])
if __name__ == '__main__':
    for f in sys.argv[1:]: write_docs(f, run_llm(prompt(parse(f))))
