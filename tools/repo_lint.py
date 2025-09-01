#!/usr/bin/env python3
"""Simple repository lint checker for required files and directories."""
import json
from pathlib import Path

REQUIRED_FILES = [
    "README.md",
    "LICENSE",
    "CITATION.cff",
    "metadata.yaml",
    "zenodo.json",
]
REQUIRED_DIRS = [
    "docs",
    "src",
    "notebooks",
    "data",
    "figures",
    "manuscripts",
    "reports",
    "tools",
]


def main():
    missing_files = [f for f in REQUIRED_FILES if not Path(f).exists()]
    missing_dirs = [d for d in REQUIRED_DIRS if not Path(d).is_dir()]
    result = {
        "missing_files": missing_files,
        "missing_dirs": missing_dirs,
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
