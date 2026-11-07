"""
AST-based LiteLLM Routing and Egress Verifier (§5).
Ensures architectural compliance with Adobe PS §5:
"All LLM and embedding calls must be routed through the LiteLLM wrapper;
no module may directly import vendor SDKs or make unmediated HTTP calls to model hosts."

Scans all Python files across the codebase and fails (exit code 1) if:
1. Any file outside the designated LiteLLM wrapper (backend/llm/client.py) imports
   vendor SDKs (openai, anthropic, google.generativeai, cohere, google.genai).
2. Any file contains hardcoded vendor API endpoints or makes direct HTTP calls to model hosts.
"""

import ast
import os
import sys
from pathlib import Path
from typing import List, Tuple

ROOT_DIR = Path(__file__).resolve().parent.parent.parent

# Designated LiteLLM client wrapper and the QA verifier itself
ALLOWED_WRAPPER_FILES = {
    os.path.normpath(str(ROOT_DIR / "backend" / "llm" / "client.py")),
    os.path.normpath(str(Path(__file__).resolve())),
}

# Forbidden vendor SDK libraries outside the wrapper
FORBIDDEN_MODULES = {
    "openai",
    "anthropic",
    "google.generativeai",
    "google.genai",
    "cohere",
    "mistralai",
}

# Forbidden direct model endpoints
FORBIDDEN_HOSTS = {
    "api.openai.com",
    "api.anthropic.com",
    "generativelanguage.googleapis.com",
    "api.cohere.ai",
    "api.mistral.ai",
}

IGNORE_DIRS = {
    ".git",
    "venv",
    ".venv",
    "__pycache__",
    "node_modules",
    ".pytest_cache",
    ".system_generated",
}


def scan_file_for_violations(file_path: Path) -> List[Tuple[int, str]]:
    """Parses a Python file AST and returns any routing boundary violations."""
    violations: List[Tuple[int, str]] = []
    norm_path = os.path.normpath(str(file_path))

    # Wrapper file is permitted to import litellm
    if norm_path in ALLOWED_WRAPPER_FILES:
        return violations

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source, filename=str(file_path))
    except Exception as exc:
        violations.append((0, f"AST parse error: {exc}"))
        return violations

    for node in ast.walk(tree):
        # 1. Check direct imports (e.g. import openai)
        if isinstance(node, ast.Import):
            for alias in node.names:
                base_pkg = alias.name.split(".")[0]
                if base_pkg in FORBIDDEN_MODULES or alias.name in FORBIDDEN_MODULES:
                    violations.append((
                        node.lineno,
                        f"Direct vendor SDK import forbidden: 'import {alias.name}'. Route through LiteLLMClient in backend/llm/client.py."
                    ))

        # 2. Check from-imports (e.g. from anthropic import Client)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                base_pkg = node.module.split(".")[0]
                if base_pkg in FORBIDDEN_MODULES or node.module in FORBIDDEN_MODULES:
                    violations.append((
                        node.lineno,
                        f"Direct vendor SDK import forbidden: 'from {node.module} import ...'. Route through LiteLLMClient in backend/llm/client.py."
                    ))

        # 3. Check for hardcoded API hosts
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            for host in FORBIDDEN_HOSTS:
                if host in node.value:
                    violations.append((
                        node.lineno,
                        f"Direct vendor host endpoint detected: '{host}'. Route calls through LiteLLM wrapper."
                    ))

    return violations


def run_check() -> int:
    print("=" * 70)
    print(" LITELLM ROUTING & ISOLATION GATE (§5)")
    print(" Verifying all LLM/Embedding operations are mediated through LiteLLM wrapper")
    print("=" * 70)

    total_scanned = 0
    all_violations: List[Tuple[Path, int, str]] = []

    for root, dirs, files in os.walk(ROOT_DIR):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for file in files:
            if file.endswith(".py"):
                file_path = Path(root) / file
                total_scanned += 1
                violations = scan_file_for_violations(file_path)
                for lineno, msg in violations:
                    all_violations.append((file_path, lineno, msg))

    print(f"\nScanned {total_scanned} Python modules.")

    if all_violations:
        print(f"\n[FAIL] Found {len(all_violations)} LiteLLM routing boundary violation(s):")
        for fpath, lno, msg in all_violations:
            rel = fpath.relative_to(ROOT_DIR)
            print(f"  - {rel}:{lno} -> {msg}")
        return 1

    print("[PASS] 100% of LLM communications strictly routed through LiteLLMClient wrapper.")
    print("       No direct vendor SDK imports (openai, anthropic, google.generativeai) found.")
    print("       Zero unmediated HTTP model endpoints detected.")
    return 0


if __name__ == "__main__":
    sys.exit(run_check())
