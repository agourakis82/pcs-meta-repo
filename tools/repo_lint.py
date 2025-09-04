#!/usr/bin/env python3
"""
Repository lint for PCS Meta-Repo (v4.3.2)
Produces reports/lint_report.json with errors/warnings/fixes and exits non-zero on errors.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List

REPO_ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = REPO_ROOT / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

TARGET_VERSION = "v4.3.2"
VERSION_DOI = "10.5281/zenodo.17053446"
CONCEPT_DOI = "10.5281/zenodo.16921951"

REQUIRED_FILES = [
    "README.md",
    "CHANGELOG.md",
    "CITATION.cff",
    "metadata.yaml",
    ".zenodo.json",
    "LICENSE",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    "QUALITY_GATES.md",
    ".github/PULL_REQUEST_TEMPLATE.md",
]

REQUIRED_DIRS = [
    "docs",
    "src",
    "notebooks",
    "data/raw_public",
    "data/processed",
    "figures",
    "manuscripts",
    "reports",
    "tools",
]

ALLOW_ROOT_BINARIES = {"coverage.svg", "data_release.tar.gz"}


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def main() -> int:
    errors: List[str] = []
    warnings: List[str] = []
    fixes: List[str] = []

    # Required files
    for rel in REQUIRED_FILES:
        p = REPO_ROOT / rel
        if not p.exists():
            errors.append(f"Missing required file: {rel}")

    # Required directories (ensure .gitkeep if empty)
    for rel in REQUIRED_DIRS:
        d = REPO_ROOT / rel
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            fixes.append(f"Created directory: {rel}")
        if d.is_dir():
            if not any(d.iterdir()):
                (d / ".gitkeep").write_text("", encoding="utf-8")
                fixes.append(f"Created {rel}/.gitkeep")

    # Version sync checks
    def contains_version(rel: str) -> bool:
        return TARGET_VERSION in read_text(REPO_ROOT / rel)

    for rel in ["README.md", "CITATION.cff", "metadata.yaml", ".zenodo.json"]:
        if not contains_version(rel):
            errors.append(f"Version {TARGET_VERSION} not found in {rel}")

    # DOI checks
    if VERSION_DOI not in read_text(REPO_ROOT / "README.md"):
        errors.append("Version DOI not present in README.md")
    if VERSION_DOI not in read_text(REPO_ROOT / "CITATION.cff"):
        errors.append("Version DOI not present in CITATION.cff")

    # License statements in README
    readme = read_text(REPO_ROOT / "README.md")
    if not re.search(r"\bMIT\b", readme):
        warnings.append("MIT license mention not found in README.md")
    if not ("CC BY 4.0" in readme or "CC-BY-4.0" in readme):
        warnings.append("CC BY 4.0 statement not found in README.md")

    # Forbidden large binaries in repo root
    for entry in REPO_ROOT.iterdir():
        if entry.is_file():
            if entry.name in ALLOW_ROOT_BINARIES:
                continue
            # flag files larger than 10MB
            try:
                size = entry.stat().st_size
                if size > 10 * 1024 * 1024:
                    warnings.append(f"Large file in repo root (>10MB): {entry.name}")
            except Exception:
                pass

    report: Dict[str, List[str]] = {
        "errors": sorted(set(errors)),
        "warnings": sorted(set(warnings)),
        "fixes": fixes,
        "version": TARGET_VERSION,
        "version_doi": VERSION_DOI,
        "concept_doi": CONCEPT_DOI,
    }
    (REPORTS_DIR / "lint_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    if errors:
        print("repo_lint: errors found — see reports/lint_report.json", file=sys.stderr)
        return 1
    print("repo_lint: OK — reports/lint_report.json", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

