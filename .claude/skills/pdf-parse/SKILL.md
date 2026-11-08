---
name: pdf-parse
description: Extract text from PDF files with Python (pypdf). Use when you need to read a PDF in this project, such as the Marstek API spec docs/MarstekDeviceOpenApi.pdf, list its pages and metadata, or save its text to a file.
---

# PDF parse

Reads PDFs with `scripts/parse_pdf.py` (it uses pypdf). Run every command from the project root.

## Setup (once)
```bash
python3 -m venv .venv && .venv/bin/pip install pypdf
```

## Usage
Check the size first, then read the pages you need:
```bash
.venv/bin/python -I .claude/skills/pdf-parse/scripts/parse_pdf.py FILE.pdf --info
.venv/bin/python -I .claude/skills/pdf-parse/scripts/parse_pdf.py FILE.pdf --pages 1-5
.venv/bin/python -I .claude/skills/pdf-parse/scripts/parse_pdf.py FILE.pdf --out docs/FILE.md
```

## Guidelines
- For big documents, extract once to `docs/<name>.md` with `--out`, then grep and read that file. Don't re-parse the PDF every time.
- Tables come out as plain text. Check field names and types against the original page before writing code from them.
- If a page comes back empty, it is probably a scanned image. Tell the user, because this skill doesn't do OCR.
