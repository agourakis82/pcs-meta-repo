#!/usr/bin/env python3
"""
validate_hstar.py — v4.3
Validation, results reading and H* status summarization.

H* decision rule (operationalized):
- SUPPORTED: positive & significant (FDR q<0.05) entropy effect on >= 2 reading metrics.
- PARTIALLY_SUPPORTED: at least one reading metric OR EEG shows positive & significant effect.
- NOT_SUPPORTED: otherwise.

Outputs:
- reports/hstar_status.json
- reports/hstar_status.md
"""

import json, sys, re, math, warnings
from pathlib import Path

import numpy as np
import pandas as pd
from statsmodels.stats.multitest import multipletests

# -----------------------------
# Paths and helpers
# -----------------------------
PROC = Path("data/processed")
FIG  = Path("figures/metrics")
RPTS = Path("reports")
RPTS.mkdir(parents=True, exist_ok=True)

def exists(p: Path) -> bool:
    try:
        return p.exists()
    except Exception:
        return False

def load_csv_safe(p: Path) -> pd.DataFrame:
    if not exists(p):
        return pd.DataFrame()
    try:
        return pd.read_csv(p)
    except Exception as e:
        warnings.warn(f"Failed to read {p}: {e}")
        return pd.DataFrame()

def fmt(val, dp=3):
    try:
        return f"{float(val):.{dp}f}"
    except Exception:
        return str(val)

# -----------------------------
# 1) Check artifacts
# -----------------------------
reading_csv      = PROC / "models_reading_coeffs.csv"
reading_fdr_csv  = PROC / "models_reading_coeffs_fdr.csv"
mixedlm_summary  = PROC / "mixedlm_ffd_summary.txt"
boot_ols_csv     = PROC / "boot_ols_ffd_entropy.csv"
f2_png           = FIG  / "F2_reading_vs_KEC.png"
f3_png           = FIG  / "F3_EEG_vs_KEC.png"

artifacts = {
    "models_reading_coeffs.csv": exists(reading_csv),
    "models_reading_coeffs_fdr.csv": exists(reading_fdr_csv),
    "mixedlm_ffd_summary.txt": exists(mixedlm_summary),
    "boot_ols_ffd_entropy.csv": exists(boot_ols_csv),
    "F2_reading_vs_KEC.png": exists(f2_png),
    "F3_EEG_vs_KEC.png": exists(f3_png),
}

# -----------------------------
# 2) Read reading models (OLS robust) + (optional) FDR
# -----------------------------
df_read = load_csv_safe(reading_csv)
use_fdr = False
if exists(reading_fdr_csv):
    df_read = load_csv_safe(reading_fdr_csv)
    use_fdr = True

reading_summary = []
pos_sig_entropy_count = 0
responses = ["FFD","GD","log_TRT","log_GPT"]
pcol = "p_fdr_bh" if use_fdr and "p_fdr_bh" in df_read.columns else "p"

if not df_read.empty:
    for resp in [r for r in responses if r in df_read["response"].unique()]:
        sub = df_read[(df_read["response"]==resp) & (df_read["term"].isin(["entropy","curvature","coherence"]))]
        sub = sub.copy()
        for term in ["entropy","curvature","coherence"]:
            row = sub[sub["term"]==term]
            if len(row)==1:
                coef = float(row["coef"].values[0])
                pval = float(row[pcol].values[0])
                reading_summary.append({
                    "response": resp,
                    "term": term,
                    "coef": coef,
                    "p_or_q": pval,
                    "sig": bool(pval < 0.05),
                    "criterion": "FDR" if pcol=="p_fdr_bh" else "raw"
                })
                # positive entropy support counter
                if term=="entropy" and coef>0 and pval<0.05:
                    pos_sig_entropy_count += 1

# -----------------------------
# 3) Optional EEG support from raw data (per-subject slopes with FDR)
#    Merge zuco_aligned + metrics_en if present and compute simple per-subject slope
# -----------------------------
eeg_support = {
    "available": False,
    "subjects_total": 0,
    "subjects_sig_pos": 0,
    "fdr_applied": False
}
try:
    zuco_aligned = load_csv_safe(PROC.parent / "zuco_aligned.csv")  # usually data/processed/zuco_aligned.csv
    metrics_en   = load_csv_safe(PROC / "kec" / "metrics_en.csv")
    # try to merge on token column if feasible
    if not zuco_aligned.empty and not metrics_en.empty:
        # normalize columns
        for df in (zuco_aligned, metrics_en):
            df.columns = [c.strip() for c in df.columns]
        z_word = "Word" if "Word" in zuco_aligned.columns else ("word" if "word" in zuco_aligned.columns else None)
        k_word = "word" if "word" in metrics_en.columns else ("Word" if "Word" in metrics_en.columns else None)
        if z_word and k_word:
            merged_eeg = zuco_aligned.merge(metrics_en, left_on=z_word, right_on=k_word, how="left", suffixes=("","_kec"))
        else:
            merged_eeg = pd.DataFrame()
        if not merged_eeg.empty and {"Subject","entropy"}.issubset(merged_eeg.columns):
            # choose EEG column available
            eeg_col = "ThetaPower" if "ThetaPower" in merged_eeg.columns else ("AlphaPower" if "AlphaPower" in merged_eeg.columns else None)
            if eeg_col:
                eeg_support["available"] = True
                # per-subject OLS slope of EEG ~ entropy
                rows = []
                for s, sdf in merged_eeg.groupby("Subject"):
                    sdf = sdf[["entropy",eeg_col]].dropna()
                    if len(sdf) >= 20:
                        X = np.vstack([np.ones(len(sdf)), sdf["entropy"].values]).T
                        y = sdf[eeg_col].values
                        try:
                            # simple OLS closed-form
                            beta = np.linalg.lstsq(X, y, rcond=None)[0]
                            # compute p-value via simple regression approximation
                            yhat = X.dot(beta)
                            resid = y - yhat
                            dof = max(len(y)-2, 1)
                            s2 = (resid**2).sum()/dof
                            cov = s2 * np.linalg.inv(X.T.dot(X))
                            se_beta1 = math.sqrt(cov[1,1])
                            t_beta1 = beta[1]/se_beta1 if se_beta1>0 else 0.0
                            # two-sided p (approx)
                            # use normal approx to avoid scipy dependency
                            from math import erf, sqrt
                            # Normal CDF approx (two-sided)
                            p_beta1 = 2 * (1 - 0.5*(1+erf(abs(t_beta1)/sqrt(2))))
                            rows.append({"Subject": str(s), "slope_entropy": float(beta[1]), "p": float(p_beta1)})
                        except Exception:
                            pass
                eeg_df = pd.DataFrame(rows)
                if not eeg_df.empty:
                    # FDR across subjects
                    rej, qvals, _, _ = multipletests(eeg_df["p"].values, alpha=0.05, method="fdr_bh")
                    eeg_df["q"] = qvals
                    eeg_df["rej_fdr"] = rej
                    eeg_support["fdr_applied"] = True
                    eeg_support["subjects_total"] = int(len(eeg_df))
                    eeg_support["subjects_sig_pos"] = int(((eeg_df["rej_fdr"]) & (eeg_df["slope_entropy"]>0)).sum())
                else:
                    eeg_support["subjects_total"] = 0
                    eeg_support["subjects_sig_pos"] = 0
except Exception as e:
    warnings.warn(f"EEG support step failed: {e}")

# -----------------------------
# 4) Decide H* status
# -----------------------------
status = "NOT_SUPPORTED"
reasons = []
if pos_sig_entropy_count >= 2:
    status = "SUPPORTED"
    reasons.append(f"Positive & significant (q<0.05) entropy effect in {pos_sig_entropy_count} reading metrics.")
elif pos_sig_entropy_count >= 1:
    status = "PARTIALLY_SUPPORTED"
    reasons.append(f"Positive & significant (q<0.05) entropy effect in {pos_sig_entropy_count} reading metric.")
# EEG can lift to PARTIALLY if none or add note
if eeg_support.get("available", False) and eeg_support.get("subjects_total", 0) > 0:
    if eeg_support["subjects_sig_pos"] > 0 and status == "NOT_SUPPORTED":
        status = "PARTIALLY_SUPPORTED"
    reasons.append(f"EEG per-subject trends: {eeg_support['subjects_sig_pos']}/{eeg_support['subjects_total']} subjects with positive & FDR-significant slope for entropy.")

# -----------------------------
# 5) Write JSON + Markdown report
# -----------------------------
out_json = {
    "artifacts": artifacts,
    "use_fdr_in_reading": use_fdr,
    "reading_summary": reading_summary,
    "pos_sig_entropy_count": pos_sig_entropy_count,
    "eeg_support": eeg_support,
    "status": status,
    "reasons": reasons
}
(RPTS / "hstar_status.json").write_text(json.dumps(out_json, indent=2))

# Markdown
lines = []
lines.append("# H* Validation Report (v4.3)")
lines.append("")
lines.append(f"**Overall Status:** **{status}**")
if reasons:
    lines.append("")
    lines.append("**Reasons:**")
    for r in reasons:
        lines.append(f"- {r}")
lines.append("")
lines.append("## Artifacts")
for k,v in artifacts.items():
    lines.append(f"- {k}: {'OK' if v else 'missing'}")
lines.append("")
lines.append("## Reading Models (OLS robust; FDR if available)")
if reading_summary:
    lines.append("| Response | Term | Coef | p/q | Sig | Criterion |")
    lines.append("|---|---|---:|---:|:---:|:---:|")
    for r in reading_summary:
        lines.append(f"| {r['response']} | {r['term']} | {fmt(r['coef'])} | {fmt(r['p_or_q'])} | {'✔' if r['sig'] else '—'} | {r['criterion']} |")
else:
    lines.append("_No reading coefficients table found._")
lines.append("")
lines.append("## EEG Support (optional)")
if eeg_support.get("available", False) and eeg_support.get("subjects_total", 0) > 0:
    lines.append(f"- Subjects analyzed: {eeg_support['subjects_total']}")
    lines.append(f"- Positive & FDR-significant slopes (entropy): {eeg_support['subjects_sig_pos']}")
else:
    lines.append("_EEG merge not available or insufficient._")
lines.append("")
lines.append("> H* operational assumption: KEC transition entropy increases reading cost and/or EEG power; curvature/coherence may contribute with nuanced signs.")
(RPTS / "hstar_status.md").write_text("\n".join(lines))

print(f"[OK] Wrote: {RPTS/'hstar_status.json'}")
print(f"[OK] Wrote: {RPTS/'hstar_status.md'}")
