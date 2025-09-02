#!/usr/bin/env python3
from __future__ import annotations
import json, sys, uuid
from pathlib import Path

try:
    import nbformat as nbf
except Exception as e:
    print("[error] nbformat not available:", e)
    sys.exit(1)

def ensure_ids(nb):
    changed = False
    for cell in nb.get('cells', []):
        if 'id' not in cell:
            cell['id'] = uuid.uuid4().hex[:12]
            changed = True
    return changed

def normalize(paths):
    total = 0
    fixed = 0
    for p in paths:
        path = Path(p)
        if not path.exists():
            continue
        try:
            nb = nbf.read(path, as_version=4)
        except Exception as e:
            print(f"[warn] Cannot read {path}: {e}")
            continue
        total += 1
        if ensure_ids(nb):
            nbf.write(nb, path)
            fixed += 1
            print(f"[ok] Added missing ids: {path}")
    print(f"[done] normalized {fixed}/{total} notebooks")

def main(argv):
    if len(argv) > 1:
        normalize(argv[1:])
    else:
        # default set
        nb = [
            'notebooks/01_build_swow_graph.ipynb',
            'notebooks/02_kec_metrics.ipynb',
            'notebooks/03_process_zuco.ipynb',
            'notebooks/04_merge_data.ipynb',
            'notebooks/05_analysis_reading.ipynb',
            'notebooks/06_analysis_eeg.ipynb',
        ]
        normalize(nb)
    return 0

if __name__ == '__main__':
    raise SystemExit(main(sys.argv))

