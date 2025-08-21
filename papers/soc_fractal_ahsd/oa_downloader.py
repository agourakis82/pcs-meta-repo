#!/usr/bin/env python3
"""
oa_downloader.py  –  baixa todos os PDFs OA listados em oa_status.csv

uso: python oa_downloader.py oa_status.csv --dest literature/pdf
"""
import os, argparse, requests, pandas as pd
from urllib.parse import urlparse
from pathlib import Path

def sanitize(name):
    return "".join(c for c in name if c.isalnum() or c in "._-")[:120]

def main(csv_file, dest):
    df = pd.read_csv(csv_file)
    dest_path = Path(dest)
    dest_path.mkdir(parents=True, exist_ok=True)

    ok, skipped, errors = 0, 0, 0
    for _, row in df.iterrows():
        if not (row.get("is_oa") and isinstance(row.get("url"), str)):
            skipped += 1
            continue

        doi = row["doi"]
        url = row["url"]
        fname = sanitize(doi.replace("/", "_")) + ".pdf"
        outfile = dest_path / fname
        if outfile.exists():
            skipped += 1
            continue

        try:
            r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20, allow_redirects=True)
            ct = r.headers.get("content-type", "")
            if r.status_code == 200 and "pdf" in ct:
                outfile.write_bytes(r.content)
                ok += 1
                print(f"✓ {doi}  →  {fname}")
            else:
                print(f"✗ {doi}  não parece PDF  (content-type {ct})")
                errors += 1
        except Exception as e:
            print(f"✗ {doi}  erro: {e}")
            errors += 1

    print(f"\nResumo: baixados {ok}, pulados {skipped}, erros {errors}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", help="arquivo oa_status.csv")
    ap.add_argument("--dest", default="literature/pdf", help="pasta destino")
    args = ap.parse_args()
    main(args.csv, args.dest)