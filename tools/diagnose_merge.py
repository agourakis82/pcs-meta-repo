#!/usr/bin/env python3
import json, sys
from pathlib import Path
import pandas as pd

MERGED = Path("data/processed/zuco_aligned.csv")   # seu alinhado
KEC    = Path("data/processed/kec/metrics_en.csv")

def exists(p): 
    try: return p.exists()
    except: return False

out = {"files":{}}

if not exists(MERGED) or not exists(KEC):
    print("Missing required files. Expected:", MERGED, KEC); sys.exit(1)

zuco = pd.read_csv(MERGED)
kec  = pd.read_csv(KEC)

for d in (zuco, kec):
    d.columns = [c.strip() for c in d.columns]

# tenta normalizar token para aumentar cobertura
import re
def norm_token(s):
    if not isinstance(s,str): return s
    s = s.lower()
    s = re.sub(r'[\W_]+','', s)
    return s

z_word = "Word" if "Word" in zuco.columns else ("word" if "word" in zuco.columns else None)
k_word = "word" if "word" in kec.columns else ("Word" if "Word" in kec.columns else None)
zuco['token_norm'] = zuco[z_word].map(norm_token) if z_word else None
kec['token_norm']  = kec[k_word].map(norm_token)  if k_word else None

merged = zuco.merge(kec, on='token_norm', how='left', suffixes=('','_kec'))

# leitura de colunas
rc_candidates = ['FFD','GD','TRT','GPT','duration_ms','fixation_samples']
eeg_candidates = ['ThetaPower','AlphaPower']
kec_cols = ['entropy','curvature','coherence']

rc_present  = [c for c in rc_candidates if c in merged.columns]
eeg_present = [c for c in eeg_candidates if c in merged.columns]
kec_present = [c for c in kec_cols if c in merged.columns]

# cobertura
n = len(merged)
cov = {c: float(merged[c].notna().mean())*100.0 for c in kec_present}
out["files"]["zuco_aligned.csv"]   = True
out["files"]["metrics_en.csv"]     = True
out["rows_merged"] = n
out["reading_cols_present"] = rc_present
out["eeg_cols_present"] = eeg_present
out["kec_cols_present"] = kec_present
out["kec_coverage_pct"] = cov
out["example_head"] = merged.head(5).to_dict(orient='list')

Path("reports").mkdir(parents=True, exist_ok=True)
Path("reports/diagnose_merge.json").write_text(json.dumps(out, indent=2))
print(json.dumps(out, indent=2))
