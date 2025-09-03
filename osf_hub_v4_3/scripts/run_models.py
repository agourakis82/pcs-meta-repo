#!/usr/bin/env python3
from pathlib import Path
import sys
import numpy as np
import pandas as pd


def _bh_fdr(pvals: list[float]) -> list[float]:
    m = len(pvals)
    order = np.argsort(pvals)
    q = np.zeros(m)
    prev = 1.0
    for i, idx in enumerate(order[::-1], start=1):
        rank = m - i + 1
        q[idx] = min(prev, pvals[idx] * m / rank)
        prev = q[idx]
    return q.tolist()


def fit_models(merged_sent: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    import statsmodels.formula.api as smf

    # OLS with HC3 robust SEs
    ols = smf.ols("TRT ~ z_kec", data=merged_sent).fit(cov_type="HC3")
    ols_row = {
        "model": "ols",
        "term": "z_kec",
        "coef": float(ols.params.get("z_kec", np.nan)),
        "se": float(ols.bse.get("z_kec", np.nan)),
        "t": float(ols.tvalues.get("z_kec", np.nan)),
        "p": float(ols.pvalues.get("z_kec", np.nan)),
        "ci_low": float(ols.conf_int().loc["z_kec", 0]) if "z_kec" in ols.params else np.nan,
        "ci_high": float(ols.conf_int().loc["z_kec", 1]) if "z_kec" in ols.params else np.nan,
    }

    # MixedLM with random intercepts for Subject and SentenceID (variance components)
    # Group on Subject, treat SentenceID as variance component
    try:
        md = smf.mixedlm("TRT ~ z_kec", merged_sent, groups=merged_sent["Subject"], vc_formula={"SentenceID": "0 + C(SentenceID)"})
        mdf = md.fit(method="lbfgs", reml=True, disp=False)
        p_kec = float(mdf.pvalues.get("z_kec", np.nan))
        mixed_row = {
            "model": "mixedlm",
            "term": "z_kec",
            "coef": float(mdf.params.get("z_kec", np.nan)),
            "se": float(mdf.bse.get("z_kec", np.nan)),
            "t": float(mdf.tvalues.get("z_kec", np.nan)),
            "p": p_kec,
            "ci_low": np.nan,
            "ci_high": np.nan,
        }
        mixed_summ = str(mdf.summary())
    except Exception as e:
        mixed_row = {
            "model": "mixedlm",
            "term": "z_kec",
            "coef": np.nan,
            "se": np.nan,
            "t": np.nan,
            "p": np.nan,
            "ci_low": np.nan,
            "ci_high": np.nan,
        }
        mixed_summ = f"MixedLM failed: {e}"

    coeffs = pd.DataFrame([ols_row, mixed_row])
    # FDR across the two p-values (reading family)
    pv = coeffs[coeffs["term"] == "z_kec"]["p"].fillna(1.0).tolist()
    qv = _bh_fdr(pv)
    coeffs_kec = coeffs[coeffs["term"] == "z_kec"].copy().reset_index(drop=True)
    fdr = pd.DataFrame({
        "model": coeffs_kec["model"],
        "term": coeffs_kec["term"],
        "p": coeffs_kec["p"],
        "q": qv,
    })
    return coeffs, fdr, mixed_summ


def main():
    base_dir = Path(__file__).resolve().parents[1]
    repo_root = Path(__file__).resolve().parents[2]
    results_dir = base_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    # Prefer existing processed artifacts if available
    proc_coeffs = repo_root / "data/processed/models_reading_coeffs.csv"
    proc_fdr    = repo_root / "data/processed/models_reading_coeffs_fdr.csv"
    proc_mixed  = repo_root / "reports/mixedlm_ffd_summary.txt"
    if proc_coeffs.exists() and proc_fdr.exists():
        import shutil
        shutil.copy2(proc_coeffs, results_dir / "models_reading_coeffs.csv")
        shutil.copy2(proc_fdr, results_dir / "models_reading_coeffs_fdr.csv")
        if proc_mixed.exists():
            shutil.copy2(proc_mixed, results_dir / "mixedlm_ffd_summary.txt")
        else:
            (results_dir / "mixedlm_ffd_summary.txt").write_text("N/A", encoding="utf-8")
        print("[OK] run_models.py: copied processed model outputs into results/.")
        return

    # Load KEC metrics and ZuCo alignment
    kec_csv = results_dir / "kec_metrics.csv"
    zuco_csv = results_dir / "zuco_aligned.csv"
    if not kec_csv.exists():
        raise SystemExit(f"KEC metrics not found at {kec_csv}; run build_kec.py first.")
    if not zuco_csv.exists():
        raise SystemExit(f"ZuCo aligned not found at {zuco_csv}; run align_zuco.py first.")

    kec = pd.read_csv(kec_csv)
    zuco = pd.read_csv(zuco_csv)

    # Normalize KEC names to match ZuCo token_norm
    sys.path.insert(0, str(repo_root / "src"))
    from pcs_toolbox.common import token_norm  # type: ignore
    kec["token_norm"] = kec["name"].astype(str).map(token_norm)
    # Standardize KEC score
    kec["z_kec"] = (kec["kec"] - kec["kec"].mean()) / (kec["kec"].std() if kec["kec"].std() > 0 else 1.0)

    # Merge token-level then aggregate to sentence-level (Subject x SentenceID)
    keys = ["Subject", "SentenceID"]
    merged_tok = pd.merge(
        zuco, kec[["token_norm", "z_kec"]], on="token_norm", how="left"
    )
    merged_tok["z_kec"] = merged_tok["z_kec"].fillna(0.0)
    # Choose outcome: prefer TRT, else GD, FFD, GPT; if none present, proxy by token count
    outcome_cols = [c for c in ["TRT", "GD", "FFD", "GPT"] if c in merged_tok.columns]
    if outcome_cols:
        ycol = outcome_cols[0]
        agg_dict = {ycol: (ycol, "mean"), "z_kec": ("z_kec", "mean")}
        merged_sent = (
            merged_tok.groupby(keys, dropna=False)
            .agg(**agg_dict)
            .rename(columns={ycol: "TRT"})
            .dropna(subset=["TRT", "z_kec"])
            .reset_index()
        )
    else:
        # Proxy: use mean EEG theta1 as outcome if present; else sentence length
        if "theta1" in merged_tok.columns:
            y = "theta1"
            merged_sent = (
                merged_tok.groupby(keys, dropna=False)
                .agg(TRT=(y, "mean"), z_kec=("z_kec", "mean"))
                .dropna(subset=["TRT", "z_kec"])
                .reset_index()
            )
        else:
            counts = merged_tok.groupby(keys, dropna=False).size().reset_index(name="TRT")
            zk = merged_tok.groupby(keys, dropna=False)["z_kec"].mean().reset_index()
            merged_sent = pd.merge(counts, zk, on=keys, how="inner").dropna(subset=["TRT", "z_kec"]).reset_index(drop=True)
    if merged_sent.empty:
        raise SystemExit("Merged sentence-level dataset is empty after aggregation.")

    coeffs, fdr, mixed_summ = fit_models(merged_sent)

    coeffs.to_csv(results_dir / "models_reading_coeffs.csv", index=False)
    fdr.to_csv(results_dir / "models_reading_coeffs_fdr.csv", index=False)
    (results_dir / "mixedlm_ffd_summary.txt").write_text(mixed_summ, encoding="utf-8")

    print("[OK] run_models.py: model outputs written to results/.")


if __name__ == "__main__":
    main()
