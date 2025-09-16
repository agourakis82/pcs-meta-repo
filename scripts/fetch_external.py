#!/usr/bin/env python3
"""
Fetch external datasets to data/raw_public/*

Supports:
  - geco:   requires GECO_URL env var or --url to a downloadable archive/CSV set
  - onestop: uses bundled repo script to download data files
  - derco:  assumes local presence (FIFs present in data/raw_public/derco)
  - lpp:    assumes local presence
  - all:    runs supported fetchers in sequence

Notes:
  - No rehosting; only pulls from official project scripts/URLs.
  - Safe to run multiple times; creates data/raw_public/<dataset> if missing.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_ROOT = REPO_ROOT / "data" / "raw_public"


def run_cmd(cmd: list[str], cwd: Path | None = None) -> int:
    print("$", " ".join(cmd))
    return subprocess.call(cmd, cwd=str(cwd) if cwd else None)


def _extract_archive(archive: Path, target_dir: Path) -> None:
    # Detect type and extract with appropriate tool
    cmd = [
        "bash",
        "-lc",
        (
            f"mime=$(file -b --mime-type '{archive}') ; "
            "case $mime in "
            "application/zip) unzip -o -q '{archive}' -d '{target_dir}' ;; "
            "application/x-tar|application/x-gtar|application/x-gtar-compressed|"
            "application/gzip|application/x-gzip) "
            f"mkdir -p '{target_dir}' && tar -xf '{archive}' -C '{target_dir}' ;; "
            "*) echo 'Unknown archive type:' $mime ;; "
            "esac"
        ),
    ]
    run_cmd(cmd)


def fetch_geco(url: str | None = None, path: str | None = None) -> None:
    target_dir = RAW_ROOT / "geco"
    target_dir.mkdir(parents=True, exist_ok=True)
    archive: Path | None = None
    if path:
        archive = Path(path)
        if not archive.exists():
            print(f"[fetch-geco] Provided path does not exist: {archive}")
            return
    else:
        if url is None:
            url = os.environ.get("GECO_URL")
        if not url:
            print("[fetch-geco] No URL provided. Set GECO_URL or pass --url/--path.")
            return
        # Download to a temp file
        tmp = target_dir / "geco_download"
        tmp.parent.mkdir(parents=True, exist_ok=True)
        rc = run_cmd(
            [
                "bash",
                "-lc",
                f"curl -fL '{url}' -o '{tmp}' || wget -O '{tmp}' '{url}'",
            ]
        )
        if rc != 0:
            print(f"[fetch-geco] Download failed with code {rc}")
            return
        archive = tmp

    # Try to extract archive if it's an archive, otherwise leave file as-is
    # mypy/pylance sometimes narrow this as always true; keep explicit check
    if archive is not None:  # type: ignore[redundant-expr]
        _extract_archive(archive, target_dir / "extracted")
        print(f"[fetch-geco] Fetched to {target_dir}")


def fetch_onestop() -> None:
    repo_dir = RAW_ROOT / "onestop" / "OneStop-Eye-Movements-main"
    if not repo_dir.exists():
        print(
            f"[fetch-onestop] Repo not found: {repo_dir}\n"
            "Clone or place it under data/raw_public/onestop"
        )
        return
    # Use the project's downloader if present
    downloader = repo_dir / "download_data_files.py"
    if downloader.exists():
        print("[fetch-onestop] Running project downloader...")
        rc = run_cmd([sys.executable, str(downloader)], cwd=repo_dir)
        if rc != 0:
            print(f"[fetch-onestop] Downloader exited with code {rc}")
    else:
        print(
            "[fetch-onestop] download_data_files.py not found; "
            "manual data placement required."
        )


def fetch_derco() -> None:
    # Nothing to fetch here; expecting FIFs present locally
    root = RAW_ROOT / "derco"
    print(f"[fetch-derco] Raw dir: {root} -> exists={root.exists()}")


def fetch_lpp() -> None:
    root = RAW_ROOT / "lpp"
    print(f"[fetch-lpp] Raw dir: {root} -> exists={root.exists()}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--dataset",
        required=True,
        choices=["geco", "onestop", "derco", "lpp", "all"],
        help="dataset to fetch",
    )
    ap.add_argument("--url", help="Optional URL for GECO")
    ap.add_argument("--path", help="Optional local archive path for GECO")
    args = ap.parse_args()

    RAW_ROOT.mkdir(parents=True, exist_ok=True)

    if args.dataset in ("geco", "all"):
        fetch_geco(args.url, args.path)
    if args.dataset in ("onestop", "all"):
        fetch_onestop()
    if args.dataset in ("derco", "all"):
        fetch_derco()
    if args.dataset in ("lpp", "all"):
        fetch_lpp()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
