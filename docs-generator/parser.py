import os

def find_iflow_file(path):
    for root, dirs, files in os.walk(path):
        for f in files:
            if f.endswith(".iflw"):
                return os.path.join(root, f)
    return None


def read_iflow(path):
    iflow_file = find_iflow_file(path)

    if iflow_file is None:
        return {
            "id": os.path.basename(path),
            "name": os.path.basename(path),
            "raw": ""
        }

    with open(iflow_file, "r", encoding="utf-8") as f:
        xml = f.read()

    id = os.path.basename(path)

    return {
        "id": id,
        "name": id,
        "raw": xml
    }
