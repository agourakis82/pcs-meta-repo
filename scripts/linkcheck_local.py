#!/usr/bin/env python3
import os, re, json

ROOT = os.path.abspath(os.getcwd())
CHECKS_DIR = os.path.join(ROOT, 'data', 'CHECKS')
os.makedirs(CHECKS_DIR, exist_ok=True)

md_link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")

def is_relative(link):
    if re.match(r'^[a-zA-Z]+://', link):
        return False
    if link.startswith('#') or link.startswith('mailto:'):
        return False
    return True

def find_md_files():
    files = []
    for base, _, fns in os.walk(ROOT):
        for fn in fns:
            if fn.lower().endswith('.md'):
                files.append(os.path.join(base, fn))
    return files

def main():
    details = []
    for md in find_md_files():
        try:
            with open(md, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
        except Exception:
            continue
        for m in md_link_pattern.finditer(text):
            link = m.group(1).strip()
            if not is_relative(link):
                continue
            # strip anchors if any
            file_part = link.split('#', 1)[0]
            if not file_part:
                continue
            abs_path = os.path.normpath(os.path.join(os.path.dirname(md), file_part))
            exists = os.path.exists(abs_path)
            if not exists:
                details.append({
                    'file': os.path.relpath(md, ROOT),
                    'link': link,
                    'resolved': os.path.relpath(abs_path, ROOT),
                    'status': 'missing'
                })
    report = {
        'missing_count': len(details),
        'status': 'OK' if len(details) == 0 else 'ISSUES',
        'details': details,
    }
    out_path = os.path.join(CHECKS_DIR, 'linkcheck_report.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    print(f"[linkcheck] Wrote {out_path} ({report['status']})")

if __name__ == '__main__':
    main()
