name: Generate CPI Package Docs (DeepSeek via Docker)

on:
  workflow_dispatch:
    inputs:
      package_id:
        required: true
        description: "Package ID inside cpi-artifacts to document"
        type: string

permissions:
  contents: write

jobs:
  docs:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Install dependencies
        run: |
          sudo apt-get update -y
          sudo apt-get install -y jq pandoc

      - name: Start Ollama in Docker
        run: |
          docker run -d --name ollama -p 11434:11434 ollama/ollama:latest
          # wait for Ollama server to initialize
          sleep 12
          docker exec ollama ollama pull deepseek-r1:14b

      - name: Make tools executable
        run: |
          chmod +x tools/ollama_generate_docs.sh
          chmod +x tools/ollama_generate_docs.py

      - name: Run documentation generator
        env:
          OLLAMA_HOST: http://localhost:11434
        run: |
          tools/ollama_generate_docs.sh "${{ github.event.inputs.package_id }}"

      - name: Commit results
        run: |
          git config user.name "github-actions"
          git config user.email "actions@github.com"

          PKG_DIR="cpi-artifacts/${{ github.event.inputs.package_id }}"
          git add "$PKG_DIR" || true

          if git diff --cached --quiet; then
            echo "No documentation changes"
            exit 0
          fi

          git commit -m "Generated DeepSeek documentation for package ${{ github.event.inputs.package_id }}"
          git push || true
