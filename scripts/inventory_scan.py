#!/usr/bin/env python3
"""Inventory scanner for repository curation"""

import argparse
import csv
import hashlib
import json
import logging
import mimetypes
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of file"""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except Exception:
        return ""


def count_lines(file_path: Path) -> int:
    """Count lines in text file"""
    try:
        if file_path.suffix in [".py", ".md", ".txt", ".yaml", ".yml", ".sh", ".R"]:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return sum(1 for _ in f)
    except Exception:
        pass
    return 0


def classify_file(file_path: Path) -> str:
    """Classify file into category"""
    suffix = file_path.suffix.lower()
    name = file_path.name.lower()

    if suffix in [".ipynb"]:
        return "notebook"
    elif suffix in [".py", ".R", ".sh", ".bat"]:
        return "script"
    elif suffix in [".csv", ".tsv", ".parquet", ".mat", ".fif", ".h5"]:
        if "raw" in str(file_path):
            return "raw"
        else:
            return "processed"
    elif suffix in [".png", ".jpg", ".jpeg", ".pdf", ".svg"]:
        return "figure"
    elif suffix in [".json", ".yaml", ".yml", ".xml"]:
        if name in ["metadata.yaml", "zenodo.json", "citation.cff"]:
            return "meta"
        else:
            return "config"
    elif suffix in [".md", ".rst", ".txt"]:
        return "doc"
    elif suffix in [".log", ".tmp", ".cache"]:
        return "temp"
    elif "logo" in name or "icon" in name:
        return "logo"
    else:
        return "other"


def scan_repository(repo_path: Path) -> List[Dict[str, Any]]:
    """Scan repository and collect file information"""
    inventory = []

    # Skip common irrelevant directories
    skip_dirs = {".git", "__pycache__", ".pytest_cache", "node_modules", ".DS_Store"}

    for file_path in repo_path.rglob("*"):
        # Skip if in skip directories
        if any(skip_dir in file_path.parts for skip_dir in skip_dirs):
            continue

        if file_path.is_file():
            try:
                stat = file_path.stat()
                mime_type, _ = mimetypes.guess_type(str(file_path))

                file_info = {
                    "path": str(file_path.relative_to(repo_path)),
                    "name": file_path.name,
                    "ext": file_path.suffix,
                    "bytes": stat.st_size,
                    "mtime": stat.st_mtime,
                    "sha256": compute_sha256(file_path),
                    "lines": count_lines(file_path),
                    "mime": mime_type or "unknown",
                    "category": classify_file(file_path),
                }

                inventory.append(file_info)

            except Exception as e:
                logger.warning(f"Failed to process {file_path}: {e}")

    return inventory


def main():
    parser = argparse.ArgumentParser(description="Scan repository inventory")
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="Repository path")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/inventory"),
        help="Output directory",
    )

    args = parser.parse_args()

    # Create output directory
    args.output.mkdir(parents=True, exist_ok=True)

    # Scan repository
    print(f"Scanning repository: {args.repo}")
    inventory = scan_repository(args.repo)

    # Save as JSON
    json_path = args.output / "inventory_full.json"
    with open(json_path, "w") as f:
        json.dump(inventory, f, indent=2)
    print(f"Saved JSON: {json_path}")

    # Save as CSV
    csv_path = args.output / "inventory_full.csv"
    if inventory:
        fieldnames = inventory[0].keys()
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(inventory)
        print(f"Saved CSV: {csv_path}")

    # Summary stats
    total_files = len(inventory)
    total_size = sum(item["bytes"] for item in inventory)
    categories = {}
    for item in inventory:
        cat = item["category"]
        categories[cat] = categories.get(cat, 0) + 1

    print(f"\nSummary:")
    print(f"Total files: {total_files}")
    print(f"Total size: {total_size / (1024*1024):.1f} MB")
    print("Categories:")
    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count}")


if __name__ == "__main__":
    main()
