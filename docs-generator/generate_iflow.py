import os
from parser import read_iflow
from generator import generate_documentation

BASE_DIR = "cpi-artifacts"
OUTPUT_ROOT = "docs"


def find_iflow_folders():
    """Scan cpi-artifacts for folders containing .iflw iFlow files."""
    iflow_dirs = []

    for root, dirs, files in os.walk(BASE_DIR):
        for d in dirs:
            full = os.path.join(root, d)
            integration_path = os.path.join(
                full, "src/main/resources/scenarioflows/integrationflow"
            )
            if os.path.isdir(integration_path):
                iflow_dirs.append(full)

    return iflow_dirs


def main():
    print("🔍 Scanning for iFlows...")
    flows = find_iflow_folders()

    if not flows:
        print("❌ No iFlows found inside cpi-artifacts/")
        return

    print(f"Found {len(flows)} iFlows:")
    for f in flows:
        print(" -", f)

    for f in flows:
        print("\n📄 Reading iFlow:", f)
        data = read_iflow(f)

        print("✍️ Generating documentation...")
        md = generate_documentation(data)

        out_dir = os.path.join(OUTPUT_ROOT, data["id"])
        os.makedirs(out_dir, exist_ok=True)

        out_file = os.path.join(out_dir, "README.md")

        with open(out_file, "w", encoding="utf-8") as fw:
            fw.write(md)

        print("✅ Documentation written to", out_file)


if __name__ == "__main__":
    main()
