#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
integrate_entropy_curvature_pro.py
- Gera `source_fig2_entropy_curvature.csv` a partir de um CSV de entrada.
- Tolera ausência de 'kappa' (cria coluna NaN) e permite filtro por beta.
"""
import argparse
import sys

import numpy as np
import pandas as pd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--in", dest="inp", required=True, help="CSV com H_rate/kappa/regime/beta"
    )
    ap.add_argument("--out", dest="out", default="source_fig2_entropy_curvature.csv")
    ap.add_argument("--select-beta", type=float, default=None)
    args = ap.parse_args()

    df = pd.read_csv(args.inp)
    if "H_rate" not in df.columns or "regime" not in df.columns:
        print("[ERROR] Input CSV must have columns: H_rate and regime", file=sys.stderr)
        sys.exit(2)
    if "kappa" not in df.columns:
        df["kappa"] = np.nan

    if args.select_beta is not None and "beta" in df.columns:
        df = df[df["beta"].round(8) == float(args.select_beta)]
        if df.empty:
            print(f"[ERROR] no rows for beta={args.select_beta}", file=sys.stderr)
            sys.exit(3)

    out = df[["H_rate", "kappa", "regime"]].copy()
    out.to_csv(args.out, index=False)
    print(f"Wrote {args.out} ({len(out)} rows)")


if __name__ == "__main__":
    main()
