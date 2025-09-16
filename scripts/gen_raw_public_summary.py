#!/usr/bin/env python3
import json
from pathlib import Path
from collections import defaultdict

def main():
    repo = Path.cwd()
    inv_path = repo / 'reports' / 'data_inventory.json'
    if not inv_path.exists():
        print(f"Inventory not found: {inv_path}")
        return 1
    with open(inv_path) as f:
        data = json.load(f)

    summary = defaultdict(lambda: {'files': 0, 'bytes': 0})
    for rel, meta in data.items():
        if not isinstance(meta, dict):
            continue
        path = (meta.get('path') or rel) if isinstance(rel, str) else rel
        if not isinstance(path, str):
            continue
        if not path.startswith('data/raw_public/'):
            continue
        parts = path.split('/')
        dataset = parts[2] if len(parts) > 2 else 'unknown'
        size = int(meta.get('size_bytes', 0))
        summary[dataset]['files'] += 1
        summary[dataset]['bytes'] += size

    ordered = sorted(summary.items(), key=lambda kv: kv[1]['bytes'], reverse=True)
    out = {
        'summary': [
            {'dataset': ds, 'files': v['files'], 'bytes': v['bytes']} for ds, v in ordered
        ],
        'total_files': sum(v['files'] for v in summary.values()),
        'total_bytes': sum(v['bytes'] for v in summary.values()),
    }

    report = repo / 'reports' / 'provenance' / 'raw_public_summary.json'
    report.parent.mkdir(parents=True, exist_ok=True)
    with open(report, 'w') as f:
        json.dump(out, f, indent=2)
    print(f"Wrote {report}")
    return 0

if __name__ == '__main__':
    raise SystemExit(main())

