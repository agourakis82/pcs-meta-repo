#!/usr/bin/env python3
# MIT License
"""Compute BH-FDR q-values for models_reading_coeffs.csv if missing."""
import pandas as pd
from pathlib import Path

PROC = Path("data/processed")
inp = PROC/"models_reading_coeffs.csv"
out = PROC/"models_reading_coeffs_fdr.csv"

def bh_fdr(p):
    import numpy as np
    p = pd.to_numeric(p, errors="coerce").values
    m = p.size
    o = p.argsort()
    ranks = (1+np.arange(m))
    q = (p[o] * m / ranks).cummin()[::-1][::-1]
    z = p.copy()
    z[o] = q
    return z

if inp.exists():
    df = pd.read_csv(inp)
    # best-effort normalize
    cols = {c:c.lower() for c in df.columns}
    df = df.rename(columns=cols)
    if "qval" not in df.columns and "pval" in df.columns:
        df["qval"] = bh_fdr(df["pval"])  # family-wise over entire table; adjust in analysis if families differ
    df.to_csv(out, index=False)
    print(f"[FDR] Wrote {out}")
else:
    print("[FDR] Input not found:", inp)
