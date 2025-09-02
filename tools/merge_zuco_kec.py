#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import pandas as pd
import numpy as np
import re

PROC = Path('data/processed')
ZUCO = PROC / 'zuco_aligned.csv'
KEC  = PROC / 'kec' / 'metrics_en.csv'
OUT  = PROC / 'zuco_kec_merged.csv'
PROC.mkdir(parents=True, exist_ok=True)

def norm_token(s: str) -> str:
    s = s if isinstance(s, str) else ''
    s = s.lower()
    return re.sub(r"[\W_]+", "", s)

def main() -> int:
    if not ZUCO.exists() or not KEC.exists():
        print(f"[merge_zuco_kec] INFO: missing inputs (zuco={ZUCO.exists()} kec={KEC.exists()}); skipping")
        return 0
    zuco = pd.read_csv(ZUCO, low_memory=False)
    kec  = pd.read_csv(KEC, low_memory=False)
    # Harmonize token_norm
    if 'token_norm' not in zuco.columns:
        word_col = 'Word' if 'Word' in zuco.columns else ('word' if 'word' in zuco.columns else None)
        if word_col:
            zuco['token_norm'] = zuco[word_col].astype(str).map(norm_token)
    if 'token_norm' not in kec.columns:
        src = 'token_norm' if 'token_norm' in kec.columns else ('word' if 'word' in kec.columns else ('node' if 'node' in kec.columns else None))
        if src:
            kec['token_norm'] = kec[src].astype(str).map(norm_token)
    keep_kec = ['token_norm','entropy','curvature','coherence']
    for c in keep_kec:
        if c not in kec.columns:
            kec[c] = pd.NA
    merged = zuco.merge(kec[keep_kec], on='token_norm', how='left')
    # If log_TRT/GPT missing, create from TRT/GPT
    if 'TRT' in merged.columns and 'log_TRT' not in merged.columns:
        merged['log_TRT'] = (merged['TRT']).apply(lambda x: pd.NA if pd.isna(x) else (0.0 if x<=0 else float(np.log1p(x))))
    if 'GPT' in merged.columns and 'log_GPT' not in merged.columns:
        merged['log_GPT'] = (merged['GPT']).apply(lambda x: pd.NA if pd.isna(x) else (0.0 if x<=0 else float(np.log1p(x))))
    OUT.write_text(merged.to_csv(index=False))
    print(f"[merge_zuco_kec] Wrote {OUT}")
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
