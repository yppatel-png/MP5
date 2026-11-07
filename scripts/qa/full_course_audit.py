import pypdf
import json

reader = pypdf.PdfReader("data/raw/courses of study.pdf")
courses = json.load(open("data/seed_bhilai/courses.json", encoding="utf-8"))

print(f"Auditing all {len(courses)} courses against PDF...")
mismatches = []
verified = []

for c in courses:
    code = c["code"]
    title = c["title"]
    credits = c["credits"]
    page_num = c.get("source_page")
    
    # Check page
    found = False
    if page_num and page_num <= len(reader.pages):
        text = reader.pages[page_num - 1].extract_text() or ""
        if code in text:
            found = True
            # Check title snippet
            # Clean words
            words = title.lower().split()
            matched_words = [w for w in words if w in text.lower()]
            if len(matched_words) < len(words) * 0.7:
                mismatches.append({
                    "code": code,
                    "seed_title": title,
                    "seed_credits": credits,
                    "page": page_num,
                    "issue": f"Title mismatch on page {page_num}",
                    "page_snippet": text[:400]
                })
            else:
                verified.append(code)
    if not found:
        # Search all pages
        hit_pages = []
        for p_idx, page in enumerate(reader.pages):
            if code in (page.extract_text() or ""):
                hit_pages.append(p_idx + 1)
        if not hit_pages:
            mismatches.append({"code": code, "issue": "Code not found in PDF"})
        else:
            mismatches.append({
                "code": code,
                "seed_title": title,
                "seed_credits": credits,
                "seed_page": page_num,
                "actual_pages": hit_pages,
                "issue": f"Page mismatch: seed says {page_num}, found on {hit_pages}"
            })

print(f"Verified courses ({len(verified)}): {verified}")
print(f"Mismatches/Issues ({len(mismatches)}):")
for m in mismatches:
    print(m)
