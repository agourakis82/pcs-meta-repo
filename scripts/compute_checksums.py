#!/usr/bin/env python3
import os, sys, hashlib, csv, time
try:
    import yaml  # optional
except Exception:
    yaml = None

ROOT = os.path.abspath(os.getcwd())
CHECKS_DIR = os.path.join(ROOT, 'data', 'CHECKS')
os.makedirs(CHECKS_DIR, exist_ok=True)

def sha256_of(path, chunk=1024*1024):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()

def collect_files():
    targets = []
    data_root = os.path.join(ROOT, 'data')
    if os.path.isdir(data_root):
        for base, _, files in os.walk(data_root):
            for fn in files:
                p = os.path.join(base, fn)
                # Skip checks artifacts themselves
                if os.path.relpath(p, ROOT).startswith('data/CHECKS'):
                    continue
                targets.append(p)
    # Also include catalog-like files if present
    for extra in ['PROVENANCE.yaml', 'DATA_DICTIONARY.md']:
        ep = os.path.join(ROOT, extra)
        if os.path.isfile(ep):
            targets.append(ep)
    return sorted(targets)

def update_provenance(checksums):
    prov_path = os.path.join(ROOT, 'PROVENANCE.yaml')
    if not os.path.isfile(prov_path):
        return
    if yaml is None:
        print("[checksum] INFO: PyYAML not available; skipping provenance update")
        return
    try:
        with open(prov_path, 'r', encoding='utf-8') as f:
            prov = yaml.safe_load(f) or {}
        datasets = prov.get('datasets', [])
        changed = False
        for d in datasets:
            p = d.get('path')
            if p:
                absp = os.path.join(ROOT, p)
                if absp in checksums:
                    if d.get('sha256') != checksums[absp]['sha256']:
                        d['sha256'] = checksums[absp]['sha256']
                        changed = True
        if changed:
            with open(prov_path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(prov, f, sort_keys=False)
    except Exception as e:
        print(f"[checksum] WARN: could not update PROVENANCE.yaml: {e}")

def main():
    files = collect_files()
    checksums = {}
    out_csv = os.path.join(CHECKS_DIR, 'checksums.csv')
    with open(out_csv, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['path', 'sha256', 'bytes', 'mtime'])
        for p in files:
            try:
                s = sha256_of(p)
                st = os.stat(p)
                w.writerow([
                    os.path.relpath(p, ROOT), s, st.st_size, int(st.st_mtime)
                ])
                checksums[p] = {'sha256': s}
            except Exception as e:
                print(f"[checksum] WARN: cannot checksum {p}: {e}")
    update_provenance(checksums)
    print(f"[checksum] Wrote {out_csv}")

if __name__ == '__main__':
    main()
