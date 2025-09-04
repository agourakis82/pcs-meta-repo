#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import os
import sys
import time
import json
import pandas as pd
import yaml


def read_provenance_counts(base_dir: Path) -> tuple[int, int]:
    prov = base_dir / "provenance.yaml"
    nulls_n, seed = 1000, 271828
    try:
        with open(prov, "r", encoding="utf-8") as f:
            y = yaml.safe_load(f)
        d = y.get("randomness", {}).get("null_graphs", {})
        nulls_n = int(d.get("n", nulls_n))
        seed = int(d.get("seed", seed))
    except Exception:
        pass
    # Allow env overrides
    nulls_n = int(os.getenv("NULLS_N", nulls_n))
    seed = int(os.getenv("NULLS_SEED", seed))
    return nulls_n, seed


def main():
    base_dir = Path(__file__).resolve().parents[1]
    repo_root = Path(__file__).resolve().parents[2]
    results_dir = base_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    # Load SWOW graph (igraph)
    sys.path.insert(0, str(repo_root / "src"))
    from pcs_toolbox.swow import load_swow_graph  # type: ignore
    from pcs_toolbox.kec import compute_kec_metrics  # type: ignore
    from pcs_toolbox.common import token_norm  # type: ignore

    swow_csv = repo_root / "data/processed/swow/swow_tidy.csv"
    if not swow_csv.exists():
        raise SystemExit(f"SWOW tidy CSV not found at {swow_csv}.")
    g0 = load_swow_graph(swow_csv)

    # Prepare reading/EEG processed merge (official)
    proc_merged = repo_root / "data/processed/zuco_kec_merged.csv"
    if not proc_merged.exists():
        msg = (
            "Processed merged dataset not found: "
            "data/processed/zuco_kec_merged.csv"
        )
        raise SystemExit(msg)
    merged_df = pd.read_csv(proc_merged)

    # Aggregate to sentence level for outcomes and KEC terms
    keys = [c for c in ["Subject", "SentenceID"] if c in merged_df.columns]
    out_candidates = [c for c in ["FFD", "GD", "TRT", "GPT"] if c in merged_df.columns]
    k_cols = [
        c for c in ["entropy", "curvature", "coherence"] if c in merged_df.columns
    ]
    if not keys or not out_candidates or not k_cols:
        err = (
            "Processed merge missing required columns "
            "(Subject/SentenceID/outcomes/kec terms)"
        )
        raise SystemExit(err)
    # Aggregate (computed on the fly per null instead)

    # Null settings
    N, seed = read_provenance_counts(base_dir)

    # Iterate nulls: rewire graph (degree-preserving), compute metrics, OLS per outcome
    import statsmodels.formula.api as smf
    rows = []
    m = g0.ecount()
    swaps = int(10 * m)
    for i in range(N):
        gi = g0.copy()
        try:
            gi.rewire(swaps, mode="simple")  # degree-preserving double-edge swaps
        except Exception:
            # If rewire unsupported, break
            pass
        dfk = compute_kec_metrics(gi)
        dfk["token_norm"] = dfk["name"].astype(str).map(token_norm)
        # Replace original KEC terms with null KEC by dropping them before merge
        left = merged_df.drop(columns=k_cols, errors="ignore")
        tok = left.merge(dfk[["token_norm", *k_cols]], on="token_norm", how="left")
        agg_dict = {
            **{o: "mean" for o in out_candidates},
            **{k: "mean" for k in k_cols},
        }
        gsent = (
            tok.groupby(keys, dropna=False)
            .agg(agg_dict)
            .reset_index()
        )
        for outcome in out_candidates:
            sub = gsent[[outcome, *k_cols]].copy()
            sub = sub.dropna(subset=[outcome, *k_cols])
            if sub.empty:
                continue
            rhs = " + ".join(k_cols)
            mod = smf.ols(f"{outcome} ~ {rhs}", data=sub).fit(cov_type="HC3")
            for t in k_cols:
                rows.append({
                    "iter": i,
                    "outcome": outcome,
                    "term": t,
                    "estimate": float(mod.params.get(t, float("nan"))),
                    "p": float(mod.pvalues.get(t, float("nan"))),
                })

    out_csv = results_dir / "nulls_reading_coeffs.csv"
    pd.DataFrame(rows).to_csv(out_csv, index=False)
    meta = {
        "n": N,
        "swaps_per_graph": swaps,
        "seed": seed,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    (results_dir / "nulls_meta.json").write_text(
        json.dumps(meta, indent=2),
        encoding="utf-8",
    )
    print(f"[OK] generate_nulls.py: wrote {out_csv}")


if __name__ == "__main__":
    main()
