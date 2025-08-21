#!/usr/bin/env python3
# Generate CHECKSUMS.sha256 and MANIFEST.csv for a directory tree.
# Usage: python osf_checksums_manifest.py <target_dir> [--output <out_dir>]

import csv
import hashlib
import sys
import time
from pathlib import Path


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    if len(sys.argv) < 2:
        print(
            "Usage: python osf_checksums_manifest.py <target_dir> [--output <out_dir>]"
        )
        sys.exit(1)

    target = Path(sys.argv[1]).resolve()
    out_dir = target
    if len(sys.argv) >= 4 and sys.argv[2] == "--output":
        out_dir = Path(sys.argv[3]).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)

    now = time.strftime("%Y-%m-%dT%H:%M:%S")
    checksums_path = out_dir / "CHECKSUMS.sha256"
    manifest_path = out_dir / "MANIFEST.csv"

    with checksums_path.open("w", encoding="utf-8") as chks, manifest_path.open(
        "w", newline="", encoding="utf-8"
    ) as mf:
        writer = csv.writer(mf)
        writer.writerow(
            ["path", "size", "sha256", "source", "generated_by", "created_at"]
        )

        for p in sorted(target.rglob("*")):
            if p.is_file() and p.name not in {"CHECKSUMS.sha256", "MANIFEST.csv"}:
                digest = sha256_file(p)
                rel = str(p.relative_to(target))
                size = p.stat().st_size
                chks.write(f"{digest}  {rel}\n")
                writer.writerow(
                    [rel, size, digest, str(target), "osf_checksums_manifest.py", now]
                )

    print(f"Written: {checksums_path}")
    print(f"Written: {manifest_path}")


if __name__ == "__main__":
    main()
