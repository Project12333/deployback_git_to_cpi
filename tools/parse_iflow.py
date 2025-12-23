import xml.etree.ElementTree as ET
from pathlib import Path

def parse_iflow(iflow_path):
    data = {
        "name": Path(iflow_path).stem,
        "adapters": set(),
        "scripts": [],
        "mappings": [],
        "security": []
    }

    try:
        tree = ET.parse(iflow_path)
        root = tree.getroot()
    except Exception as e:
        data["error"] = str(e)
        return data

    for elem in root.iter():
        tag = elem.tag.lower()

        if "adaptertype" in tag:
            val = elem.attrib.get("adapterType")
            if val:
                data["adapters"].add(val)

        if "script" in tag:
            name = elem.attrib.get("name")
            if name:
                data["scripts"].append(name)

        if "mapping" in tag:
            name = elem.attrib.get("name")
            if name:
                data["mappings"].append(name)

        if "security" in tag:
            data["security"].append(elem.attrib)

    data["adapters"] = list(data["adapters"])
    return data
