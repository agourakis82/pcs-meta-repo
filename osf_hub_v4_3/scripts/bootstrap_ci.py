#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import os
import json
import time
import numpy as np
import pandas as pd
import yaml


def read_bootstrap_counts(base_dir: Path) -> tuple[int, int]:
    prov = base_dir / "provenance.yaml"
    n, seed = 2000, 1337
    try:
        with open(prov, "r", encoding="utf-8") as f:
            y = yaml.safe_load(f)
        d = y.get("randomness", {}).get("bootstrap", {})
        n = int(d.get("n", n))
        seed = int(d.get("seed", seed))
    except Exception:
        pass
    # Env overrides
    n = int(os.getenv("BOOT_N", n))
    seed = int(os.getenv("BOOT_SEED", seed))
    return n, seed


def main():
    base_dir = Path(__file__).resolve().parents[1]
    repo_root = Path(__file__).resolve().parents[2]
    results_dir = base_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    proc_merged = repo_root / "data/processed/zuco_kec_merged.csv"
    if not proc_merged.exists():
        msg = "Processed merged dataset not found: data/processed/zuco_kec_merged.csv"
        raise SystemExit(msg)
    df = pd.read_csv(proc_merged)

    keys = [c for c in ["Subject", "SentenceID"] if c in df.columns]
    out_candidates = [c for c in ["FFD", "GD", "TRT", "GPT"] if c in df.columns]
    k_cols = [c for c in ["entropy", "curvature", "coherence"] if c in df.columns]
    if not keys or not out_candidates or not k_cols:
        err = (
            "Processed merge missing required columns "
            "(Subject/SentenceID/outcomes/kec terms)"
        )
        raise SystemExit(err)
    agg = (
        df.groupby(keys, dropna=False)
        .agg({**{o: "mean" for o in out_candidates}, **{k: "mean" for k in k_cols}})
        .reset_index()
    )

    import statsmodels.formula.api as smf
    N, seed = read_bootstrap_counts(base_dir)
    rng = np.random.default_rng(seed)
    rows = []
    for outcome in out_candidates:
        sub = agg[[outcome, *k_cols]].dropna(subset=[outcome])
        if sub.empty:
            continue
        n = len(sub)
        rhs = " + ".join(k_cols)
        # Point estimate
        mod0 = smf.ols(f"{outcome} ~ {rhs}", data=sub).fit(cov_type="HC3")
        for t in k_cols:
            rows.append({
                "phase": "point",
                "outcome": outcome,
                "term": t,
                "estimate": float(mod0.params.get(t, float("nan"))),
            })
        # Bootstrap CIs
        boot_ests = {t: [] for t in k_cols}
        for b in range(N):
            idx = rng.integers(0, n, size=n)
            sb = sub.iloc[idx]
            try:
                mb = smf.ols(f"{outcome} ~ {rhs}", data=sb).fit(cov_type="HC3")
                for t in k_cols:
                    boot_ests[t].append(float(mb.params.get(t, float("nan"))))
            except Exception:
                for t in k_cols:
                    boot_ests[t].append(float("nan"))
        for t in k_cols:
            arr = np.array(boot_ests[t], dtype=float)
            lo, hi = np.nanpercentile(arr, [2.5, 97.5])
            rows.append({
                "phase": "ci",
                "outcome": outcome,
                "term": t,
                "ci_low": float(lo),
                "ci_high": float(hi),
                "n_boot": N,
            })

    out_ci = results_dir / "boot_ols_reading_ci.csv"
    pd.DataFrame(rows).to_csv(out_ci, index=False)
    meta = {
        "n": N,
        "seed": seed,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    (results_dir / "bootstrap_meta.json").write_text(
        json.dumps(meta, indent=2),
        encoding="utf-8",
    )
    print(f"[OK] bootstrap_ci.py: wrote {out_ci}")


if __name__ == "__main__":
    main()
