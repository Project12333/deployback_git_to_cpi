import os
from parser import read_iflow
from generator import generate_documentation

BASE_DIR = "cpi-artifacts"

def find_iflow_folders():
    """Find all folders containing an iflw iFlow file."""
    flow_dirs = []
    for root, dirs, files in os.walk(BASE_DIR):
        for d in dirs:
            full = os.path.join(root, d)
            integration_path = os.path.join(
                full, "src/main/resources/scenarioflows/integrationflow"
            )
            if os.path.isdir(integration_path):
                flow_dirs.append(full)
    return flow_dirs


def main():
    flows = find_iflow_folders()
    if not flows:
        print("No iFlows found!")
        return

    for flow_path in flows:
        print("Generating documentation for:", flow_path)
        
        data = read_iflow(flow_path)
        md = generate_documentation(data)

        # Write Documentation.md inside the same folder
        out_file = os.path.join(flow_path, "Documentation.md")
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(md)
        
        print("✔ Documentation created at:", out_file)


if __name__ == "__main__":
    main()
