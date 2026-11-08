#!/usr/bin/env python3
"""Extract text from a PDF, page by page.

Usage:
    python parse_pdf.py FILE.pdf                  # all pages to stdout
    python parse_pdf.py FILE.pdf --pages 1-5      # page range (1-based, inclusive)
    python parse_pdf.py FILE.pdf --info           # page count + metadata only
    python parse_pdf.py FILE.pdf --out out.md     # write to a file

Requires: pypdf (pip install pypdf)
"""
import argparse
import sys
from pathlib import Path

try:
    from pypdf import PdfReader
except ImportError:
    sys.exit("pypdf is not installed. Run: pip install pypdf")


def parse_range(spec: str, total: int) -> range:
    """'3' -> page 3; '2-5' -> pages 2..5. Clamped to the document."""
    start, _, end = spec.partition("-")
    first = max(1, int(start))
    last = min(total, int(end) if end else first)
    if first > last:
        sys.exit(f"Invalid page range {spec!r} for a {total}-page document")
    return range(first, last + 1)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf", type=Path)
    ap.add_argument("--pages", help="1-based page or range, e.g. 4 or 2-10")
    ap.add_argument("--info", action="store_true", help="print page count and metadata only")
    ap.add_argument("--out", type=Path, help="write output to this file instead of stdout")
    args = ap.parse_args()

    reader = PdfReader(args.pdf)
    total = len(reader.pages)

    if args.info:
        print(f"pages: {total}")
        for key, value in (reader.metadata or {}).items():
            print(f"{key.lstrip('/')}: {value}")
        return

    pages = parse_range(args.pages, total) if args.pages else range(1, total + 1)
    chunks = [f"\n--- page {n} ---\n{reader.pages[n - 1].extract_text() or ''}" for n in pages]
    text = "".join(chunks).strip() + "\n"

    if args.out:
        args.out.write_text(text, encoding="utf-8")
        print(f"wrote {len(pages)} page(s) to {args.out}")
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
