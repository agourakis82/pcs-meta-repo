#!/usr/bin/env python3
import os, hashlib, csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / 'reports'

def sha256_of(path, chunk=1024*1024):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()

def main():
    hashes = {}
    dups = []
    for base, _, files in os.walk(ROOT):
        for fn in files:
            p = Path(base) / fn
            if p.is_symlink(): continue
            try:
                h = sha256_of(p)
                rel = p.relative_to(ROOT).as_posix()
                if h in hashes:
                    dups.append({'sha256': h, 'a': hashes[h], 'b': rel})
                else:
                    hashes[h] = rel
            except Exception:
                continue
    REPORTS.mkdir(parents=True, exist_ok=True)
    with open(REPORTS / 'duplicates.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['sha256','a','b'])
        w.writeheader()
        for d in dups: w.writerow(d)
    print(f"[dups] wrote {REPORTS/'duplicates.csv'} ({len(dups)} duplicates)")

if __name__ == '__main__':
    main()

