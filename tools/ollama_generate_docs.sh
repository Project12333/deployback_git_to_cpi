
---

# ✅ FILE 2 — `tools/run_generate_docs.sh`  
(Minimal executor for GitHub Actions)

```bash
#!/usr/bin/env bash
set -e

echo "Installing Python dependencies..."
python -m pip install --upgrade pip
python -m pip install requests python-docx

echo "Running documentation generator..."
python tools/generate_iflow_docs.py

echo "Documentation complete."
