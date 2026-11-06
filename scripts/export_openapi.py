#!/usr/bin/env python3
"""Export the FastAPI OpenAPI schema used by the typed frontend client."""

import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.main import app

OUTPUT_FILE = ROOT_DIR / "frontend" / "types" / "openapi.json"


def main() -> None:
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(
        json.dumps(app.openapi(), indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Exported OpenAPI schema to {OUTPUT_FILE.relative_to(ROOT_DIR)}")


if __name__ == "__main__":
    main()
