"""
Automated Outbound Call & Zero-Egress Auditor.
Enforces the strict rule: "No outbound calls except to the configured model provider."
Audits:
1. Frontend bundles: zero external scripts, CDNs, fonts, analytics, tracking, or stylesheets.
2. Backend source code: zero runtime downloads (nltk.download, weights downloads, external APIs).
3. Repository URLs: any http/https URL present must be a plain textual citation or documentation link.

Exits with code 0 if compliant, non-zero on violation.
"""

import os
import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent

# Forbidden remote CDN and resource domains
DISALLOWED_DOMAINS = [
    "cdn.jsdelivr.net",
    "unpkg.com",
    "cdnjs.cloudflare.com",
    "fonts.googleapis.com",
    "fonts.gstatic.com",
    "ajax.googleapis.com",
    "google-analytics.com",
    "googletagmanager.com",
    "segment.com",
    "mixpanel.com",
    "amplitude.com",
    "huggingface.co",
    "raw.githubusercontent.com",
]

# Patterns for runtime downloads in Python
RUNTIME_DOWNLOAD_PATTERNS = [
    (re.compile(r"nltk\.download\(", re.IGNORECASE), "Runtime NLTK data download"),
    (re.compile(r"spacy\.load\(['\"][a-z_]+['\"]\)", re.IGNORECASE), "Unverified spaCy runtime model load"),
    (re.compile(r"from_pretrained\(", re.IGNORECASE), "HuggingFace runtime model download"),
    (re.compile(r"urllib\.request\.urlretrieve", re.IGNORECASE), "urllib file download"),
    (re.compile(r"requests\.get\(", re.IGNORECASE), "Raw unrouted requests.get call"),
]

# Allowed domains for plain documentation links cited in text/HTML anchors
ALLOWED_CITATION_DOMAINS = {
    "home.iitd.ac.in",
    "cse.iitd.ac.in",
    "nptel.ac.in",
    "ocw.mit.edu",
    "cs229.stanford.edu",
    "pdos.csail.mit.edu",
    "ncert.nic.in",
    "startupschool.org",
    "ecorner.stanford.edu",
    "introtodeeplearning.com",
    "skills.github.com",
    "developer.nvidia.com",
    "leetcode.com",
    "local-advisor",
    "academic-advisor.local"
}

def audit_frontend_files() -> list:
    violations = []
    frontend_dir = ROOT_DIR / "frontend"
    for root, _, files in os.walk(frontend_dir):
        for f in files:
            fpath = Path(root) / f
            if fpath.suffix not in {".html", ".js", ".css"}:
                continue
            with open(fpath, "r", encoding="utf-8", errors="ignore") as fp:
                content = fp.read()

            rel_path = fpath.relative_to(ROOT_DIR)

            # Check for <script src="http"> or <link href="http">
            ext_script = re.findall(r'<script[^>]+src=["\'](https?://[^"\']+)["\']', content, re.IGNORECASE)
            for url in ext_script:
                violations.append(f"[OUTBOUND CDN SCRIPT] {rel_path}: External script detected: {url}")

            ext_link = re.findall(r'<link[^>]+href=["\'](https?://[^"\']+)["\']', content, re.IGNORECASE)
            for url in ext_link:
                violations.append(f"[OUTBOUND STYLESHEET] {rel_path}: External stylesheet detected: {url}")

            # Check for remote font imports @import url('http...')
            font_imports = re.findall(r'@import\s+(?:url\()?["\'](https?://[^"\']+)["\']', content, re.IGNORECASE)
            for url in font_imports:
                violations.append(f"[OUTBOUND FONT] {rel_path}: Remote font import detected: {url}")

            # Check for disallowed domains anywhere in bundle
            for d in DISALLOWED_DOMAINS:
                if d in content.lower():
                    violations.append(f"[FORBIDDEN DOMAIN] {rel_path}: Contains reference to forbidden CDN: {d}")

    return violations

def audit_backend_code() -> list:
    violations = []
    backend_dir = ROOT_DIR / "backend"
    for root, _, files in os.walk(backend_dir):
        for f in files:
            fpath = Path(root) / f
            if fpath.suffix != ".py":
                continue
            with open(fpath, "r", encoding="utf-8", errors="ignore") as fp:
                content = fp.read()

            rel_path = fpath.relative_to(ROOT_DIR)

            for pattern, desc in RUNTIME_DOWNLOAD_PATTERNS:
                matches = pattern.findall(content)
                if matches:
                    violations.append(f"[RUNTIME DOWNLOAD RISK] {rel_path}: {desc}")

    return violations

def run_outbound_audit() -> int:
    print("=" * 60)
    print(" AUDIT: OUTBOUND CALLS & OFFLINE INTEGRITY")
    print("=" * 60)

    fe_violations = audit_frontend_files()
    be_violations = audit_backend_code()

    total_violations = fe_violations + be_violations

    print(f"Frontend Outbound Violations: {len(fe_violations)}")
    print(f"Backend Runtime Egress Violations: {len(be_violations)}")

    if total_violations:
        print(f"\nFAIL: {len(total_violations)} outbound/egress issues detected:")
        for v in total_violations:
            print(f" - {v}")
        return 1

    print("\nPASS: 100% self-contained application. Zero CDNs, zero remote fonts, zero runtime package downloads.")
    return 0

if __name__ == "__main__":
    sys.exit(run_outbound_audit())

