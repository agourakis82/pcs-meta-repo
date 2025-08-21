#!/usr/bin/env python3
# integrate_entropy_curvature.py
# Read entropy_curvature_all.csv (from compute_entropy_curvature_* runners)
# and produce source_fig2_entropy_curvature.csv in the Scientific Reports format.

import argparse
import sys

import pandas as pd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--in", dest="inp", required=True, help="Input CSV (entropy_curvature_all.csv)"
    )
    ap.add_argument(
        "--out",
        dest="out",
        default="source_fig2_entropy_curvature.csv",
        help="Output CSV path",
    )
    ap.add_argument(
        "--select-beta",
        type=float,
        default=None,
        help="Optional: filter a single beta value (e.g., 1.0)",
    )
    ap.add_argument(
        "--rename-regimes",
        help="Optional: CSV with mapping 'from,to' to rename regime labels",
    )
    args = ap.parse_args()

    df = pd.read_csv(args.inp)
    # Expected columns: graph,beta,H_rate,kappa,regime,nnodes,nedges,weight_attr,curv_method
    required = {"H_rate", "kappa", "regime"}
    if not required.issubset(df.columns):
        print(
            f"ERROR: input missing columns {required - set(df.columns)}",
            file=sys.stderr,
        )
        sys.exit(2)

    if args.select_beta is not None:
        df = df[df["beta"].round(8) == float(args.select_beta)]
        if df.empty:
            print(f"ERROR: no rows with beta == {args.select_beta}", file=sys.stderr)
            sys.exit(3)

    if args.rename_regimes:
        # load mapping CSV with columns: from,to
        mp = pd.read_csv(args.rename_regimes)
        if not {"from", "to"}.issubset(mp.columns):
            print("ERROR: rename CSV must have columns: from,to", file=sys.stderr)
            sys.exit(4)
        m = dict(zip(mp["from"], mp["to"]))
        df["regime"] = df["regime"].map(lambda x: m.get(x, x))

    out = df[["H_rate", "kappa", "regime"]].copy()
    out.to_csv(args.out, index=False)
    print(f"Wrote {args.out} with {len(out)} rows.")


if __name__ == "__main__":
    main()
