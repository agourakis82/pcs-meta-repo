#!/usr/bin/env python3
# MIT License
"""
Compute ΔR²_adj (percentage points) between base (controls) and full (controls + KEC)
for reading outcomes. Expect two CSVs or one with flags.
"""
from pathlib import Path
import pandas as pd

PROC = Path("data/processed")
out = PROC/"delta_r2_reading_hstar.csv"

# Auto-discovery: either combined table with columns model_type in {base,full}
# or paired files *_base.csv and *_full.csv with columns outcome, r2_adj
cand = [PROC/"models_reading_r2.csv", PROC/"models_reading_models.csv"]
base, full = None, None

if (PROC/"models_reading_base.csv").exists():
    base = pd.read_csv(PROC/"models_reading_base.csv")
if (PROC/"models_reading_full.csv").exists():
    full = pd.read_csv(PROC/"models_reading_full.csv")

if base is None or full is None:
    for c in cand:
        if c.exists():
            df = pd.read_csv(c)
            if "model_type" in df.columns and "r2_adj" in df.columns:
                base = df[df["model_type"].str.lower().eq("base")]
                full = df[df["model_type"].str.lower().eq("full")]
                break

if base is not None and full is not None and not base.empty and not full.empty:
    key = ["outcome","dataset","task"]
    for k in ["dataset","task"]:
        if k not in base.columns:
            base[k] = None
        if k not in full.columns:
            full[k] = None
    m = pd.merge(base, full, on=key, suffixes=("_base","_full"))
    if {"r2_adj_base","r2_adj_full"}.issubset(m.columns):
        m["delta_r2_adj_pp"] = (m["r2_adj_full"] - m["r2_adj_base"]) * 100.0
        m.to_csv(out, index=False)
        print(f"[ΔR2] Wrote {out}")
    else:
        print("[ΔR2] r2_adj columns not found in merged table.")
else:
    print("[ΔR2] No base/full R2 tables found.")

