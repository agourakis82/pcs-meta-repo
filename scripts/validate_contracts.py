#!/usr/bin/env python3
import os, sys, json, math
import yaml

ROOT = os.path.abspath(os.getcwd())
CONTRACTS_DIR = os.path.join(ROOT, 'data', 'CONTRACTS')
CHECKS_DIR = os.path.join(ROOT, 'data', 'CHECKS')
os.makedirs(CHECKS_DIR, exist_ok=True)

_PD = None

def _get_pd():
    global _PD
    if _PD is not None:
        return _PD
    try:
        import pandas as pd  # noqa: F401
        _PD = pd
        return _PD
    except Exception:
        return None

def read_df(path, fmt=None):
    pd = _get_pd()
    if pd is None:
        raise RuntimeError('pandas not available')
    ext = (fmt or os.path.splitext(path)[1].lstrip('.')).lower()
    if ext in ('csv', ''):
        return pd.read_csv(path)
    if ext in ('tsv',):
        return pd.read_csv(path, sep='\t')
    if ext in ('parquet', 'pq'):
        return pd.read_parquet(path)
    if ext in ('json',):
        return pd.read_json(path, lines=False)
    # fallback
    return pd.read_csv(path)

def check_ranges(series, lo, hi):
    if lo is None and hi is None:
        return []
    issues = []
    if lo is not None:
        bad = series[series < lo]
        if len(bad) > 0:
            issues.append(f"values < {lo}: {len(bad)}")
    if hi is not None:
        bad = series[series > hi]
        if len(bad) > 0:
            issues.append(f"values > {hi}: {len(bad)}")
    return issues

def coerce_float(series):
    pd = _get_pd()
    return pd.to_numeric(series, errors='coerce') if pd is not None else series

def validate_contract(contract_path):
    with open(contract_path, 'r', encoding='utf-8') as f:
        c = yaml.safe_load(f) or {}
    ds_name = c.get('dataset', os.path.basename(contract_path))
    exp = c.get('expected_file')
    fmt = c.get('format')
    result = {'dataset': ds_name, 'contract': os.path.relpath(contract_path, ROOT), 'status': 'SKIPPED', 'issues': [], 'stats': {}}
    if not exp:
        result['issues'].append('missing expected_file')
        result['status'] = 'ERROR'
        return result
    path = os.path.join(ROOT, exp)
    if not os.path.isfile(path):
        result['issues'].append(f"expected_file not found: {exp}")
        result['status'] = 'SKIPPED'
        return result

    try:
        pd = _get_pd()
        if pd is None:
            result['issues'].append('pandas not available; skipping detailed validation')
            result['status'] = 'SKIPPED'
            return result
        df = read_df(path, fmt)
        result['stats'] = {'rows': int(df.shape[0]), 'cols': int(df.shape[1])}
        # required columns
        cols = c.get('columns', [])
        required = [col['name'] for col in cols if col.get('required')]
        missing = [col for col in required if col not in df.columns]
        if missing:
            result['issues'].append(f"missing required columns: {missing}")
        # pk uniqueness
        pk = c.get('pk') or []
        if pk:
            if not set(pk).issubset(df.columns):
                result['issues'].append(f"pk columns missing: {[x for x in pk if x not in df.columns]}")
            else:
                dups = df.duplicated(subset=pk).sum()
                if dups > 0:
                    result['issues'].append(f"duplicate PK rows: {dups}")
        # unique rules
        uniq_rules = (c.get('rules') or {}).get('unique') or []
        for group in uniq_rules:
            group = list(group)
            if not set(group).issubset(df.columns):
                result['issues'].append(f"unique group missing cols: {group}")
                continue
            dups = df.duplicated(subset=group).sum()
            if dups > 0:
                result['issues'].append(f"violated uniqueness {group}: {dups} dups")
        # ranges
        ranges = (c.get('rules') or {}).get('ranges') or {}
        for col, bounds in ranges.items():
            if col not in df.columns:
                result['issues'].append(f"range check missing column: {col}")
                continue
            lo, hi = None, None
            if isinstance(bounds, (list, tuple)) and len(bounds) == 2:
                lo, hi = bounds
            lo = None if lo in (None, 'inf', 'INF', 'nan') else float(lo)
            hi = None if hi in (None, 'inf', 'INF', 'nan') else float(hi)
            series = coerce_float(df[col])
            rng_issues = check_ranges(series, lo, hi)
            if rng_issues:
                result['issues'].append(f"{col}: {'; '.join(rng_issues)}")
        result['status'] = 'PASSED' if not result['issues'] else 'FAILED'
        return result
    except Exception as e:
        result['issues'].append(f"exception: {e}")
        result['status'] = 'ERROR'
        return result

def main():
    contracts = []
    if os.path.isdir(CONTRACTS_DIR):
        for fn in os.listdir(CONTRACTS_DIR):
            if fn.endswith(('.yml', '.yaml')):
                contracts.append(os.path.join(CONTRACTS_DIR, fn))
    results = [validate_contract(p) for p in sorted(contracts)]
    out = {
        'summary': {
            'total': len(results),
            'passed': sum(1 for r in results if r['status'] == 'PASSED'),
            'failed': sum(1 for r in results if r['status'] == 'FAILED'),
            'skipped': sum(1 for r in results if r['status'] == 'SKIPPED'),
            'error': sum(1 for r in results if r['status'] == 'ERROR'),
        },
        'results': results,
    }
    out_path = os.path.join(CHECKS_DIR, 'validation_report.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=2)
    print(f"[validate] Wrote {out_path}")

if __name__ == '__main__':
    main()
