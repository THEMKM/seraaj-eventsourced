"""
Generate OpenAPI JSON files for all FastAPI services.

Writes to openapi/ directory:
 - bff.openapi.json
 - auth.openapi.json
 - applications.openapi.json
 - matching.openapi.json
"""
from __future__ import annotations

import json
from pathlib import Path
import sys, os


def write_openapi(app, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    spec = app.openapi()
    out_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    out_dir = Path("openapi")
    # Ensure repository root is on sys.path
    sys.path.insert(0, os.getcwd())

    # BFF
    try:
        from bff.main import app as bff_app
        write_openapi(bff_app, out_dir / "bff.openapi.json")
        print("Wrote openapi/bff.openapi.json")
    except Exception as e:
        print(f"[WARN] Failed to generate BFF OpenAPI: {e}")

    # Auth
    try:
        from services.auth.api import app as auth_app
        write_openapi(auth_app, out_dir / "auth.openapi.json")
        print("Wrote openapi/auth.openapi.json")
    except Exception as e:
        print(f"[WARN] Failed to generate Auth OpenAPI: {e}")

    # Applications
    try:
        from services.applications.api import app as applications_app
        write_openapi(applications_app, out_dir / "applications.openapi.json")
        print("Wrote openapi/applications.openapi.json")
    except Exception as e:
        print(f"[WARN] Failed to generate Applications OpenAPI: {e}")

    # Matching
    try:
        from services.matching.api import app as matching_app
        write_openapi(matching_app, out_dir / "matching.openapi.json")
        print("Wrote openapi/matching.openapi.json")
    except Exception as e:
        print(f"[WARN] Failed to generate Matching OpenAPI: {e}")


if __name__ == "__main__":
    main()
