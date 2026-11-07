import pypdf

reader = pypdf.PdfReader("data/raw/courses of study.pdf")
for i, page in enumerate(reader.pages):
    txt = page.extract_text() or ""
    if "CSL304" in txt:
        print(f"CSL304 found on page {i+1}:")
        for line in txt.split("\n"):
            if "CSL304" in line or "Credits" in line or "Title" in line:
                print("  ", line)
    if "CSL510" in txt:
        print(f"CSL510 found on page {i+1}:")
        for line in txt.split("\n"):
            if "CSL510" in line or "Credits" in line or "Title" in line:
                print("  ", line)
