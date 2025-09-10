#!/usr/bin/env python3
import json, csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / 'reports'

def classify(path: Path):
    rel = path.relative_to(ROOT).as_posix()
    ext = path.suffix.lower()
    if rel.startswith('notebooks/'): cat='notebook'; util='USEFUL'
    elif rel.startswith('scripts/'): cat='script'; util='USEFUL'
    elif rel.startswith('data/L0_') or rel.startswith('data/raw_public/'): cat='raw'; util='UNCERTAIN'
    elif rel.startswith('data/L1_') or rel.startswith('data/L2_') or rel.startswith('data/processed/'): cat='processed'; util='ESSENTIAL'
    elif rel.startswith('figures/'): cat='figure'; util='USEFUL'
    elif rel.startswith('reports/'): cat='report'; util='ESSENTIAL'
    elif rel.startswith('docs/'): cat='doc'; util='USEFUL'
    elif rel.startswith('config/'): cat='config'; util='ESSENTIAL'
    elif rel.startswith('tools/'): cat='meta'; util='USEFUL'
    else: cat='other'; util='UNCERTAIN'
    action = 'KEEP' if util in ('ESSENTIAL','USEFUL') else 'QUARANTINE'
    return {
        'path': rel,
        'category': cat,
        'utility': util,
        'action': action,
        'dest_suggested': '',
        'reason': ''
    }

def main():
    items = []
    for p in ROOT.rglob('*'):
        if p.is_file():
            items.append(classify(p))
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / 'classify_curadoria.jsonl').write_text('\n'.join(json.dumps(x) for x in items), encoding='utf-8')
    with open(REPORTS / 'classify_curadoria.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(items[0].keys()) if items else ['path'])
        w.writeheader()
        for it in items: w.writerow(it)
    print(f"[classify] wrote {REPORTS/'classify_curadoria.*'}")

if __name__ == '__main__':
    main()

