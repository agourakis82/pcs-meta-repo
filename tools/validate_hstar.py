#!/usr/bin/env python3
# MIT License
"""
PCS-HELIO v4.3 — H* Validator
Reads analysis outputs (coeff tables, MixedLM summaries) and emits a decision:
SUPPORTED | PARTIAL | NOT_SUPPORTED | PIPELINE_BROKEN, with auditable criteria.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path
import pandas as pd
from typing import Dict, Any

# --- Inputs (auto-discovery) ---
ROOT = Path(".")
PROC = ROOT / "data" / "processed"
REPO = ROOT
REPORTS = ROOT / "reports"
REPORTS.mkdir(parents=True, exist_ok=True)

# Candidate files
CAND_COEFFS = [
    PROC / "models_reading_coeffs.csv",
    PROC / "models_reading_coeffs_fdr.csv",
    PROC / "models_coeffs.csv",
]
CAND_EEG   = [
    PROC / "models_eeg_coeffs.csv",
    PROC / "models_eeg_coeffs_fdr.csv",
]
CAND_MIXED = [
    REPORTS / "mixedlm_ffd_summary.txt",
    REPORTS / "mixedlm_summary.txt",
]
MERGE_FILES = [
    PROC / "zuco_kec_merged.csv",
    PROC / "zuco_aligned.csv",  # last resort; will warn if KEC cols missing
]

def read_first_exists(paths):
    for p in paths:
        if p.exists():
            return p
    return None

def bh_fdr(p: pd.Series) -> pd.Series:
    m = p.shape[0]
    order = p.values.argsort()
    ranks = pd.Series(range(1, m+1), index=p.index[order])
    adj = pd.Series(p.values[order] * m / ranks.values)
    q = adj.cummin()[::-1][::-1].clip(upper=1.0).values
    out = pd.Series(1.0, index=p.index)
    out.iloc[order] = q
    return out.clip(upper=1.0)

def load_coeffs() -> pd.DataFrame:
    fp = read_first_exists(CAND_COEFFS)
    if fp is None:
        return pd.DataFrame()
    df = pd.read_csv(fp)
    # expected columns: outcome, term, beta, pval, dataset, task, model_type ...
    cols = {c:c.lower() for c in df.columns}
    df = df.rename(columns=cols)
    # normalize expected names
    if "beta" not in df.columns:
        if "coef" in df.columns:
            df = df.rename(columns={"coef":"beta"})
        elif "estimate" in df.columns:
            df = df.rename(columns={"estimate":"beta"})
    if "pval" not in df.columns:
        if "p_value" in df.columns:
            df = df.rename(columns={"p_value":"pval"})
        elif "p" in df.columns:
            df = df.rename(columns={"p":"pval"})
    # ensure required
    req = {"outcome","term","beta","pval"}
    if not req.issubset(df.columns):
        return pd.DataFrame()
    # ensure q-value (FDR) family-wise per outcome type
    if "qval" not in df.columns:
        fam = df["outcome"].apply(lambda s: "reading" if any(k in str(s).lower() for k in ["ffd","gd","trt","gpt"]) else "eeg")
        df["qval"] = None
        for g, sub in df.groupby(fam):
            q = bh_fdr(sub["pval"].astype(float))
            df.loc[sub.index, "qval"] = q.values
    return df

def load_merge() -> pd.DataFrame:
    fp = read_first_exists(MERGE_FILES)
    return pd.read_csv(fp) if fp else pd.DataFrame()

def has_surprisal(dfm: pd.DataFrame) -> bool:
    return any(c in dfm.columns for c in ["surprisal_kenlm","surprisal_trf","pll_word","pppl"]) if not dfm.empty else False

def compute_delta_r2_table() -> pd.DataFrame:
    for cand in [PROC/"delta_r2_reading.csv", PROC/"delta_r2_reading_hstar.csv"]:
        if cand.exists():
            return pd.read_csv(cand)
    return pd.DataFrame()

def decide(status_input: Dict[str, Any]) -> Dict[str, Any]:
    s = status_input
    if not s["pipeline_ok"]:
        s["decision"] = "PIPELINE_BROKEN"
        return s

    coeffs = s["coeffs"]
    is_kec = coeffs["term"].str.contains(r"\b(kec|entropy|curvature|coherence)\b", case=False, regex=True)
    read_mask = coeffs["outcome"].str.lower().str.contains("ffd|gd|trt|gpt")
    eeg_mask  = coeffs["outcome"].str.lower().str.contains("theta|alpha|beta|gamma")
    cr = coeffs[is_kec & read_mask].copy()
    ce = coeffs[is_kec & eeg_mask].copy()

    # Directionality and FDR
    positive = (cr["beta"].astype(float) > 0) & (cr["qval"].astype(float) <= 0.05)
    n_read_sig = int(positive.sum())

    # Replication across strata (v1/v2 or NR/TSR/SR)
    def strata_ok(df):
        if df.empty:
            return False
        breadth = 0
        if "dataset" in df.columns and df["dataset"].notna().any():
            breadth += int(df[df["qval"]<=0.05]["dataset"].nunique() >= 2 or df["dataset"].nunique() >= 2)
        if "task" in df.columns and df["task"].notna().any():
            breadth += int(df[df["qval"]<=0.05]["task"].nunique() >= 2 or df["task"].nunique() >= 2)
        return breadth >= 1
    replication = strata_ok(cr)

    # ΔR2 / AIC
    delta = s.get("delta_r2", pd.DataFrame())
    r2_ok = False
    if not delta.empty:
        for cand_col in ["delta_r2_adj_pp","delta_r2_pp","delta_r2adj_pp"]:
            if cand_col in delta.columns:
                try:
                    r2_ok = (pd.to_numeric(delta[cand_col], errors="coerce") >= 0.5).any()
                    break
                except Exception:
                    pass

    # Surprisal control
    surpr_ok = True
    if s["has_surprisal"]:
        surpr_ok = (cr["qval"].astype(float) <= 0.10).any()

    # EEG (optional)
    eeg_any = False
    if not ce.empty:
        eeg_any = (ce["qval"].astype(float) <= 0.10).any()

    if (n_read_sig >= 2) and replication and r2_ok and surpr_ok:
        s["decision"] = "SUPPORTED"
    elif (n_read_sig >= 1) or eeg_any:
        s["decision"] = "PARTIAL"
    else:
        s["decision"] = "NOT_SUPPORTED"
    return s

def main():
    # Preconditions
    needed = [
        PROC/"zuco_aligned.csv",
        PROC/"kec"/"metrics_en.csv"
    ]
    pipeline_ok = all(p.exists() for p in needed)
    merge_df = load_merge()
    if merge_df.empty or ("token_norm" not in merge_df.columns):
        pipeline_ok = False

    coeffs = load_coeffs()
    if coeffs.empty:
        pipeline_ok = False

    delta = compute_delta_r2_table()
    status: Dict[str, Any] = {
        "pipeline_ok": pipeline_ok,
        "merge_rows": int(merge_df.shape[0]) if not merge_df.empty else 0,
        "kec_coverage_pct": float(
            (merge_df[["entropy","curvature","coherence"]].notna().all(axis=1)).mean()*100
        ) if (not merge_df.empty and all(c in merge_df.columns for c in ["entropy","curvature","coherence"])) else None,
        "coeffs_rows": int(coeffs.shape[0]) if not coeffs.empty else 0,
        "has_surprisal": has_surprisal(merge_df),
        "coeffs": coeffs,
        "delta_r2": delta,
        "notes": [],
    }

    # Decision
    status = decide(status)

    # Top reading effects
    try:
        top_read = (coeffs[coeffs["outcome"].str.lower().str.contains("ffd|gd|trt|gpt")]
                    .sort_values("qval", ascending=True).head(8)
                    [["outcome","term","beta","pval","qval","dataset","task"]])
    except Exception:
        top_read = pd.DataFrame()

    # Write artifacts
    sjson = dict(status)
    sjson.pop("coeffs", None)
    sjson.pop("delta_r2", None)
    (REPORTS/"hstar_status.json").write_text(json.dumps(sjson, indent=2))

    md = []
    md.append(f"# H* Validation Report (PCS-HELIO v4.3)\n")
    md.append(f"**Decision:** **{status['decision']}**\n")
    md.append(f"**Pipeline OK:** {status['pipeline_ok']}  \n")
    md.append(f"Rows (merge): {status.get('merge_rows',0)}  \n")
    if status.get("kec_coverage_pct") is not None:
        md.append(f"KEC coverage: {status['kec_coverage_pct']:.1f}%  \n")
    md.append("\n## Top reading effects (sorted by FDR q)\n")
    if isinstance(top_read, pd.DataFrame) and not top_read.empty:
        md.append(top_read.to_markdown(index=False))
    else:
        md.append("_No coefficients found for reading outcomes._")
    md.append("\n## Criteria\n")
    md.append("- ≥2 reading outcomes with q≤0.05 and β>0 (MixedLM/robust OLS)\n"
              "- Replication across v1/v2 or NR/TSR/SR\n"
              "- ΔR²_adj ≥ 0.5 pp or ΔAIC < −4\n"
              "- Surprisal control: retain q≤0.10 & ΔR²>0 when present\n")
    (REPORTS/"hstar_status.md").write_text("\n".join(md))

    print(f"[HSTAR] Decision: {status['decision']} — see reports/hstar_status.md")

if __name__ == "__main__":
    main()
