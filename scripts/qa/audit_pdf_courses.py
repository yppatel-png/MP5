import pypdf
import json

reader = pypdf.PdfReader("data/raw/courses of study.pdf")
print(f"Total pages: {len(reader.pages)}")

# Search for LAL225, CSL304, CSL510
targets = ["LAL225", "CSL304", "CSL510", "CSL301", "CSL302", "CSL303", "CSL351", "CSP352", "CSQ401"]
findings = {}

for idx, page in enumerate(reader.pages):
    text = page.extract_text() or ""
    for t in targets:
        if t in text:
            lines = [line.strip() for line in text.split("\n") if t in line]
            findings.setdefault(t, []).append((idx + 1, lines))

for t, hits in findings.items():
    print(f"\n=== {t} ===")
    for page_num, lines in hits:
        print(f"Page {page_num}: {lines}")
