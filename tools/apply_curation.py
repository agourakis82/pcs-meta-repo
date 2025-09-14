#!/usr/bin/env python3
"""
Apply moves suggested by CURATION_INDEX.yaml in a safe, dry-run by default.

Usage:
  python tools/apply_curation.py [--apply]

This parser is minimal and only understands the YAML produced by
tools/generate_root_curation.py (path/type/action/target/reason under items).
"""
from __future__ import annotations

import argparse
import os
import shutil
from typing import List, Dict


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
INDEX_PATH = os.path.join(REPO_ROOT, "CURATION_INDEX.yaml")


def parse_index(path: str) -> List[Dict[str, str]]:
    items: List[Dict[str, str]] = []
    current: Dict[str, str] | None = None
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if s.startswith("- path:"):
                if current:
                    items.append(current)
                current = {"path": s.split(":", 1)[1].strip()}
            elif current and (s.startswith("type:") or s.startswith("action:") or s.startswith("target:") or s.startswith("reason:")):
                key, val = s.split(":", 1)
                current[key.strip()] = val.strip()
        if current:
            items.append(current)
    return items


def ensure_dir(path: str) -> None:
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


def move_file(src_rel: str, dst_rel: str, dry_run: bool) -> None:
    src = os.path.join(REPO_ROOT, src_rel)
    dst = os.path.join(REPO_ROOT, dst_rel)
    ensure_dir(os.path.dirname(dst))
    if dry_run:
        print(f"DRY-RUN: mv {src_rel} -> {dst_rel}")
        return
    if not os.path.exists(src):
        print(f"SKIP (missing): {src_rel}")
        return
    shutil.move(src, dst)
    print(f"MOVED: {src_rel} -> {dst_rel}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="Perform changes (default: dry-run)")
    args = ap.parse_args()
    dry = not args.apply

    items = parse_index(INDEX_PATH)
    planned = 0
    for it in items:
        action = it.get("action")
        path = it.get("path")
        target = it.get("target")
        if action not in ("move", "archive"):
            continue
        if not target:
            continue
        # Compose destination path
        base = target.rstrip("/")
        dst_rel = f"{base}/{os.path.basename(path)}"
        move_file(path, dst_rel, dry)
        planned += 1
    print(f"Done. {'Planned' if dry else 'Applied'} {planned} moves.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

