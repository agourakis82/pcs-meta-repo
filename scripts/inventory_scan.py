#!/usr/bin/env python3
import os, sys, hashlib, json, csv, mimetypes, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / 'reports'
REPORTS.mkdir(parents=True, exist_ok=True)

def sha256_of(path, chunk=1024*1024):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()

def category_of(p: Path) -> str:
    rel = p.relative_to(ROOT).as_posix()
    if rel.startswith('notebooks/'): return 'notebook'
    if rel.startswith('scripts/'): return 'script'
    if rel.startswith('data/'): return 'raw' if '/L0_' in rel else 'processed'
    if rel.startswith('figures/'): return 'figure'
    if rel.startswith('reports/'): return 'report'
    if rel.startswith('docs/'): return 'doc'
    if rel.startswith('config/'): return 'config'
    if rel.startswith('tools/'): return 'meta'
    return 'other'

def main():
    items = []
    for base, _, files in os.walk(ROOT):
        for fn in files:
            p = Path(base) / fn
            if p.is_symlink():
                continue
            try:
                stat = p.stat()
                mt = mimetypes.guess_type(p.name)[0] or 'application/octet-stream'
                items.append({
                    'path': str(p.relative_to(ROOT)),
                    'name': p.name,
                    'ext': p.suffix,
                    'bytes': stat.st_size,
                    'mtime': int(stat.st_mtime),
                    'sha256': sha256_of(p) if p.stat().st_size < 50*1024*1024 else '',
                    'mime': mt,
                    'category': category_of(p)
                })
            except Exception:
                continue

    (REPORTS / 'inventory.json').write_text(json.dumps(items, indent=2), encoding='utf-8')
    with open(REPORTS / 'inventory.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(items[0].keys()) if items else ['path'])
        w.writeheader()
        for it in items: w.writerow(it)
    print(f"[inventory] wrote {REPORTS/'inventory.json'} ({len(items)} items)")

if __name__ == '__main__':
    main()

