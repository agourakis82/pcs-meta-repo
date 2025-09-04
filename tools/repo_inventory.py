#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
REPORTS.mkdir(parents=True, exist_ok=True)

TARGET_VERSION = "v4.3.2"

EXCLUDES = {
    ".git",
    ".github/workflows/cache",
    "venv",
    ".venv",
    "env",
    "__pycache__",
}


def should_skip(p: Path) -> bool:
    parts = set(p.parts)
    for ex in EXCLUDES:
        if ex in parts:
            return True
    return False


def sha256sum(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    rows = []
    for p in ROOT.rglob("*"):
        if should_skip(p):
            continue
        if p.is_file():
            rel = str(p.relative_to(ROOT))
            try:
                size = p.stat().st_size
                digest = sha256sum(p)
            except Exception:
                size = -1
                digest = ""
            rows.append({"relative_path": rel, "size_bytes": size, "sha256": digest})

    rows.sort(key=lambda r: r["relative_path"])  # stable order
    # JSON
    (REPORTS / f"repo_inventory_{TARGET_VERSION}.json").write_text(
        json.dumps(rows, indent=2), encoding="utf-8"
    )
    # CSV
    with (REPORTS / f"repo_inventory_{TARGET_VERSION}.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["relative_path", "size_bytes", "sha256"])
        w.writeheader()
        w.writerows(rows)
    print(f"inventory: {len(rows)} files indexed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

