#!/usr/bin/env python3
from pathlib import Path
import csv

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / 'reports'

ALLOWED_TOP = { 'docs','src','scripts','notebooks','data','figures','reports','tools','.github','.vscode','.vscode-server' }

def main():
    violations = []
    for p in ROOT.iterdir():
        if p.name.startswith('.') or p.name in ALLOWED_TOP: continue
        if p.is_file():
            violations.append({'path': p.name, 'issue': 'file in repo root', 'suggestion': 'move under appropriate folder'})
        elif p.is_dir():
            violations.append({'path': p.name+'/', 'issue': 'dir in repo root', 'suggestion': 'move under appropriate folder'})
    REPORTS.mkdir(parents=True, exist_ok=True)
    with open(REPORTS / 'violations.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['path','issue','suggestion'])
        w.writeheader()
        for v in violations: w.writerow(v)
    print(f"[layout] wrote {REPORTS/'violations.csv'} ({len(violations)} violations)")

if __name__ == '__main__':
    main()

