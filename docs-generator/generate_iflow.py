import os
from parser import read_iflow
from generator import generate_documentation

IFLOW_DIR = IFLOW_DIR = IFLOW_DIR = "cpi-artifacts/CPIPracticeflows/democicd"  # change this for each flow

def main():
    print("Reading iFlow...")
    data = read_iflow(IFLOW_DIR)

    print("Generating documentation...")
    md = generate_documentation(data)

    out_dir = f"docs/{data['id']}"
    os.makedirs(out_dir, exist_ok=True)

    with open(os.path.join(out_dir, "README.md"), "w", encoding="utf-8") as f:
        f.write(md)

    print("Documentation generated:", out_dir + "/README.md")


if __name__ == "__main__":
    main()
