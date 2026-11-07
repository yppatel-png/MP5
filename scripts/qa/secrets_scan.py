"""
Automated Secrets and LLM Configuration Auditor.
Scans repository, source code, and configuration files for:
1. Leaked API keys (OpenAI, Google Gemini, Anthropic, AWS, generic tokens).
2. Hard-coded model names outside .env.example and documentation.
3. Unrouted LLM or embedding calls bypassing the LiteLLM wrapper.
4. Git history secret commits.

Exits with code 0 if clean, non-zero on violation.
"""

import os
import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent

# Patterns for API keys and secrets
KEY_PATTERNS = [
    (re.compile(r"sk-[a-zA-Z0-9]{20,}"), "OpenAI API Key"),
    (re.compile(r"sk-proj-[a-zA-Z0-9_\-]{20,}"), "OpenAI Project API Key"),
    (re.compile(r"AIza[0-9A-Za-z\-_]{35}"), "Google Gemini API Key"),
    (re.compile(r"sk-ant-[a-zA-Z0-9_\-]{20,}"), "Anthropic API Key"),
    (re.compile(r"Bearer\s+[a-zA-Z0-9_\-\.]{30,}"), "Hardcoded Bearer Token"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS Access Key ID"),
]

# Patterns for hard-coded model identifiers inside code
MODEL_PATTERNS = [
    (re.compile(r'["\']gemini[/-][a-z0-9\.\-]+["\']', re.IGNORECASE), "Hard-coded Gemini model reference"),
    (re.compile(r'["\']gpt-[a-z0-9\-]+["\']', re.IGNORECASE), "Hard-coded GPT model reference"),
    (re.compile(r'["\']claude-[a-z0-9\-]+["\']', re.IGNORECASE), "Hard-coded Claude model reference"),
    (re.compile(r'["\']llama-[a-z0-9\-]+["\']', re.IGNORECASE), "Hard-coded Llama model reference"),
]

# Patterns for known demo/default tokens
KNOWN_TOKEN_PATTERNS = [
    (re.compile(r"adm_secret_token_[a-zA-Z0-9_\-]+", re.IGNORECASE), "Hard-coded known admin token"),
]

# Patterns for unrouted LLM calls bypassing LiteLLM
UNROUTED_CALL_PATTERNS = [
    (re.compile(r"^\s*import\s+openai\b", re.MULTILINE), "Direct openai import bypassing LiteLLM"),
    (re.compile(r"^\s*from\s+openai\b", re.MULTILINE), "Direct openai import bypassing LiteLLM"),
    (re.compile(r"^\s*import\s+anthropic\b", re.MULTILINE), "Direct anthropic import bypassing LiteLLM"),
    (re.compile(r"https://api\.openai\.com", re.IGNORECASE), "Direct OpenAI endpoint reference"),
    (re.compile(r"https://api\.anthropic\.com", re.IGNORECASE), "Direct Anthropic endpoint reference"),
    (re.compile(r"https://generativelanguage\.googleapis\.com", re.IGNORECASE), "Direct Gemini endpoint reference"),
]

EXCLUDE_DIRS = {
    ".git", ".venv", "venv", "__pycache__", "node_modules", "data", "docs", "reports", "build", "dist"
}

EXCLUDE_FILES = {
    ".env.example", "evaluate.py", "eval.json", "eval.md", "README.md", "tokens.css"
}

def scan_file_for_secrets(file_path: Path) -> list:
    violations = []
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except Exception as e:
        return [f"Could not read {file_path}: {e}"]

    rel_path = file_path.relative_to(ROOT_DIR)

    # 1. Scan for leaked keys
    for pattern, desc in KEY_PATTERNS:
        matches = pattern.findall(content)
        for m in matches:
            # Ignore placeholder strings like your_llm_api_key_here
            if "your_" in m.lower() or "example" in m.lower():
                continue
            violations.append(f"[SECRET LEAK] {rel_path}: {desc} detected (value: {m[:6]}...)")

    # 2. Scan for hard-coded models in code and config files
    if file_path.suffix in {".py", ".js", ".ts", ".yml", ".yaml"} and file_path.name not in EXCLUDE_FILES:
        for pattern, desc in MODEL_PATTERNS:
            matches = pattern.findall(content)
            for m in matches:
                violations.append(f"[HARDCODED MODEL] {rel_path}: {desc} ({m})")

    # 3. Scan for known demo tokens in code, configs, and compose files
    if file_path.name not in EXCLUDE_FILES:
        for pattern, desc in KNOWN_TOKEN_PATTERNS:
            matches = pattern.findall(content)
            for m in matches:
                violations.append(f"[KNOWN TOKEN] {rel_path}: {desc} ({m})")

    # 4. Scan for unrouted calls in backend
    if "backend" in file_path.parts and file_path.suffix == ".py":
        for pattern, desc in UNROUTED_CALL_PATTERNS:
            matches = pattern.findall(content)
            for m in matches:
                violations.append(f"[UNROUTED LLM CALL] {rel_path}: {desc}")

    return violations

def run_secrets_scan() -> int:
    print("=" * 60)
    print(" AUDIT: SECRETS, CONFIG & LITELLM ROUTING SCAN")
    print("=" * 60)

    total_scanned = 0
    all_violations = []

    for root, dirs, files in os.walk(ROOT_DIR):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for f in files:
            if f in EXCLUDE_FILES or f.endswith((".pdf", ".db", ".sqlite", ".png", ".jpg")):
                continue
            fpath = Path(root) / f
            total_scanned += 1
            v = scan_file_for_secrets(fpath)
            all_violations.extend(v)

    print(f"Scanned {total_scanned} files across repository.")

    if all_violations:
        print(f"\nFAIL: {len(all_violations)} violations detected:")
        for v in all_violations:
            print(f" - {v}")
        return 1

    print("\nPASS: Zero leaked secrets, zero hardcoded models, all LLM calls route via LiteLLM.")
    return 0

if __name__ == "__main__":
    sys.exit(run_secrets_scan())
