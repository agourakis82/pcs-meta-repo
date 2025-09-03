#!/usr/bin/env python3
from pathlib import Path
import json
import time
import sys
import math
from collections import defaultdict


def _entropy(probs):
    p = [x for x in probs if x > 0 and math.isfinite(x)]
    if not p:
        return 0.0
    return float(-sum(pi * math.log(pi) for pi in p))


def build_kec_from_swow_csv(csv_path: Path, out_csv: Path):
    import pandas as pd
    import numpy as np

    df = pd.read_csv(csv_path)
    cols = {c.lower(): c for c in df.columns}
    cue = cols.get("cue") or cols.get("source") or list(df.columns)[0]
    resp = cols.get("response") or cols.get("target") or list(df.columns)[1]
    wcol = cols.get("weight") or cols.get("frequency")
    if wcol is None:
        df["__w__"] = 1.0
        wcol = "__w__"

    # Build out-neighbor weight lists per node
    outw = defaultdict(list)
    for _, row in df.iterrows():
        c = str(row[cue])
        outw[c].append(float(row[wcol]))

    # Entropy per node
    names = sorted(set(df[cue].astype(str)).union(set(df[resp].astype(str))))
    ent = {}
    for n in names:
        ws = outw.get(n, [])
        s = float(sum(ws))
        probs = [w/s for w in ws] if s > 0 else []
        ent[n] = _entropy(probs)

    # KEC proxy = z-score of entropy (curvature/coherence omitted if unavailable)
    e = list(ent.values())
    mu = float(np.mean(e)) if e else 0.0
    sd = float(np.std(e)) if e else 1.0
    z = {n: ((ent[n] - mu) / sd if sd > 0 else 0.0) for n in names}

    out = pd.DataFrame({
        "name": names,
        "entropy": [ent[n] for n in names],
        "kec": [z[n] for n in names],
    })
    out.to_csv(out_csv, index=False)


def main():
    base_dir = Path(__file__).resolve().parents[1]
    repo_root = Path(__file__).resolve().parents[2]
    results_dir = base_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    # Prefer processed tidy SWOW if available
    swow_csv = repo_root / "data/processed/swow/swow_tidy.csv"
    if not swow_csv.exists():
        raise SystemExit(f"SWOW tidy CSV not found at {swow_csv}.")

    # Try full KEC via pcs_toolbox (entropy+curvature+coherence)
    sys.path.insert(0, str(repo_root / "src"))
    try:
        from pcs_toolbox.swow import load_swow_graph  # type: ignore
        from pcs_toolbox.kec import compute_kec_metrics  # type: ignore
        g = load_swow_graph(swow_csv)
        df = compute_kec_metrics(g)
        out_csv = results_dir / "kec_metrics.csv"
        df.to_csv(out_csv, index=False)
        method = "KEC (entropy+curvature+coherence)"
    except Exception as e:
        # Fallback to entropy-only proxy
        out_csv = results_dir / "kec_metrics.csv"
        build_kec_from_swow_csv(swow_csv, out_csv)
        method = f"KEC proxy (entropy z-score) — fallback: {e}"

    meta = {
        "version": "v4.3",
        "source": str(swow_csv),
        "method": method,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    log_text = json.dumps(meta, indent=2)
    (results_dir / "kec_build.log").write_text(log_text, encoding="utf-8")
    print(f"[OK] build_kec.py: wrote {out_csv}")


if __name__ == "__main__":
    main()
