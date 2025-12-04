import os

def find_iflow_file(iflow_dir):
    """Locate the .iflw file inside the integrationflow folder."""
    for root, _, files in os.walk(iflow_dir):
        for f in files:
            if f.endswith(".iflw") or f.endswith(".iflow"):
                return os.path.join(root, f)
    return None


def read_iflow(iflow_dir):
    iflow_file = find_iflow_file(iflow_dir)

    if iflow_file is None:
        return {"id": "unknown", "name": os.path.basename(iflow_dir), "raw": ""}

    with open(iflow_file, "r", encoding="utf-8") as f:
        xml = f.read()

    # Extract ID and name if possible
    id = os.path.basename(iflow_dir)
    name = id

    return {
        "id": id,
        "name": name,
        "path": iflow_file,
        "raw": xml
    }
