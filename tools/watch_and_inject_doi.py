#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Optional
from urllib.parse import urlencode
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def zenodo_search(version: str, concept: Optional[str] = None, timeout: int = 20) -> dict:
    # Try exact metadata.version match first
    queries = []
    if concept:
        queries.append({
            'q': f'conceptdoi:"{concept}" AND version:"{version}"',
            'size': 5,
            'sort': 'mostrecent'
        })
    # Fallback: just version
    queries.append({'q': f'version:"{version}"', 'size': 5, 'sort': 'mostrecent'})
    for q in queries:
        url = f'https://zenodo.org/api/records/?{urlencode(q)}'
        try:
            with urllib.request.urlopen(url, timeout=timeout) as r:
                data = json.load(r)
            hits = data.get('hits', {}).get('hits', [])
            if hits:
                return {'query_url': url, 'found': True, 'hit': hits[0]}
        except Exception:
            continue
    return {'found': False}


def inject_doi(doi: str, pub_date: Optional[str], version: str) -> dict:
    changes = {}
    # CITATION.cff
    cff = (ROOT / 'CITATION.cff')
    if cff.exists():
        t = cff.read_text(encoding='utf-8')
        t = re.sub(r'(?m)^doi:\s*"[^"]*"', f'doi: "{doi}"', t)
        t = re.sub(r'(?m)^preferred-citation:\s*\n', 'preferred-citation:\n', t)
        t = re.sub(r'(?m)^\s*doi:\s*"[^"]*"', f'  doi: "{doi}"', t, count=1)
        if pub_date:
            t = re.sub(r'(?m)^date-released:\s*"[^"]*"', f'date-released: "{pub_date}"', t)
            t = re.sub(r'(?m)^\s*date-released:\s*"[^"]*"', f'  date-released: "{pub_date}"', t, count=1)
        cff.write_text(t, encoding='utf-8')
        changes['CITATION.cff'] = True
    # metadata.yaml
    meta = (ROOT / 'metadata.yaml')
    if meta.exists():
        m = meta.read_text(encoding='utf-8')
        if 'version_doi:' in m:
            m = re.sub(r'(?m)^\s*version_doi:\s*"[^"]*"', f'  version_doi: "{doi}"', m)
        else:
            # add under identifiers:
            m = re.sub(r'(?m)^identifiers:\s*$', f'identifiers:\n  version_doi: "{doi}"', m)
        if pub_date:
            m = re.sub(r'(?m)^date:\s*"[^"]*"', f'date: "{pub_date}"', m)
        meta.write_text(m, encoding='utf-8')
        changes['metadata.yaml'] = True
    # README.md badge
    readme = (ROOT / 'README.md')
    if readme.exists():
        r = readme.read_text(encoding='utf-8')
        badge = f' [![Version DOI](https://zenodo.org/badge/DOI/{doi}.svg)](https://doi.org/{doi})'
        lines = r.splitlines()
        if lines:
            if 'zenodo.org/badge/DOI' in lines[0]:
                if doi not in lines[0]:
                    lines[0] = lines[0] + badge
            else:
                lines[0] = badge + '\n' + lines[0]
        readme.write_text('\n'.join(lines) + ('\n' if not r.endswith('\n') else ''), encoding='utf-8')
        changes['README.md'] = True
    return changes


def main() -> int:
    ap = argparse.ArgumentParser(description='Watch Zenodo for a version DOI, then inject into repo files.')
    ap.add_argument('--version', required=True, help='Version string, e.g., v4.3.2.2')
    ap.add_argument('--concept', action='append', default=[], help='Concept DOI(s) to narrow search (optional).')
    ap.add_argument('--attempts', type=int, default=40)
    ap.add_argument('--interval', type=int, default=30)
    ap.add_argument('--commit', action='store_true', help='Commit and push changes when injected')
    args = ap.parse_args()

    attempt = 0
    found = None
    while attempt < args.attempts and not found:
        attempt += 1
        for c in (args.concept or [None]):
            res = zenodo_search(args.version, c)
            if res.get('found'):
                found = res
                break
        if not found:
            time.sleep(args.interval)

    reports = ROOT / 'reports'
    reports.mkdir(exist_ok=True)

    if not found:
        (reports / f'watch_inject_{args.version}.json').write_text(json.dumps({'found': False}, indent=2), encoding='utf-8')
        print(f'[watch] DOI not found for {args.version}', file=sys.stderr)
        return 1

    hit = found['hit']
    md = hit.get('metadata', {})
    doi = md.get('doi') or hit.get('doi')
    pub_date = md.get('publication_date')
    changes = inject_doi(doi, pub_date, args.version)
    out = {'found': True, 'doi': doi, 'publication_date': pub_date, 'changes': list(changes.keys()), 'query_url': found.get('query_url')}
    (reports / f'watch_inject_{args.version}.json').write_text(json.dumps(out, indent=2), encoding='utf-8')

    if args.commit and changes:
        os.system('git add CITATION.cff metadata.yaml README.md')
        msg = f'chore(meta): inject Zenodo Version DOI {doi} for {args.version}'
        os.system(f"git commit -m \"{msg}\" || true")
        os.system('git push || true')
    print(json.dumps(out, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())

