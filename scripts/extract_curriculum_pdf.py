#!/usr/bin/env python3
"""Extract every page of the official IIT Bhilai curriculum PDF with page provenance."""

import json
from pathlib import Path

from pypdf import PdfReader

ROOT_DIR = Path(__file__).resolve().parent.parent
SOURCE_PDF = ROOT_DIR / "data" / "raw" / "courses of study.pdf"
OUTPUT = ROOT_DIR / "data" / "raw" / "courses_of_study_extracted.json"


def main() -> None:
    reader = PdfReader(str(SOURCE_PDF))
    pages = [
        {"source_page": page_number, "text": page.extract_text() or ""}
        for page_number, page in enumerate(reader.pages, start=1)
    ]
    OUTPUT.write_text(
        json.dumps(
            {
                "source_file": "courses of study.pdf",
                "source_page_count": len(pages),
                "extraction_method": "pypdf text extraction; no OCR",
                "pages": pages,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Extracted {len(pages)} of {len(reader.pages)} PDF pages to {OUTPUT}.")


if __name__ == "__main__":
    main()
