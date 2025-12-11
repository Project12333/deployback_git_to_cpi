#!/usr/bin/env python3
"""
Generate Markdown (.md) and Word (.docx) documentation per iFlow folder.
Uses DeepSeek R1 (Ollama model name: deepseek-r1)
"""

import os
import sys
import subprocess
import requests
import textwrap
from pathlib import Path
from datetime import datetime
from docx import Document
from docx.shared import Inches, Pt

# ============================================================
# CONFIG — Model, paths
# ============================================================

MODEL_NAME = "deepseek-r1"
OLLAMA_URL = "http://localhost:11434/api/generate"

SAP_LOGO_PATH = "tools/logos/sap.png"
MOTIVEMINDS_LOGO_PATH = "tools/logos/motiveminds.png"

OUTPUT_DIR = "docs_generated"

# ============================================================
# INLINE FULL SYSTEM PROMPT (SAFE TRIPLE-QUOTED VERSION)
# ============================================================

SYSTEM_PROMPT = """
You are a senior SAP CPI Technical Architect. Your task is to analyze ALL provided code and configuration files from the SINGLE iFlow provided and synthesize them into ONE consolidated Markdown documentation report. You MUST adhere strictly to the following hierarchical 6-point structure, using Markdown headings (# for main sections, ## for subsections). Ensure all technical details (like Groovy, XSLT, Adapters, Security) are thoroughly explained within the relevant sections.

MANDATORY FIRST SECTION: TABLE OF CONTENTS (TOC) PAGE
The very first output of the document MUST be the Table of Contents. Format the TOC heading using HTML to achieve a prominent blue color and large font, like this:
<h1 style="color: #1f4e79; font-size: 2.5em;">Table of Contents</h1>

Below this heading, list all 6 main sections and their subsections using standard Markdown numbered list syntax (e.g., 1., 1.1., 1.2., etc.), ensuring proper indentation and avoiding the use of HTML entities like &nbsp; for spacing.

Insert 10 blank lines after the TOC list, then add:
---TOC-END-PAGE-BREAK---

The mandatory sections are:

# 1. Introduction
## 1.1 Purpose
## 1.2 Scope

# 2. Integration Overview
## 2.1 Integration Architecture
After describing architecture, immediately output a Process Flow Diagram in Mermaid using:
```mermaid
graph TD
...
