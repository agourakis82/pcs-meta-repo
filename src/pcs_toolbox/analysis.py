from __future__ import annotations
from typing import List, Optional, Dict
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.multitest import multipletests
from joblib import Parallel, delayed


def fit_ols_clustered(df: pd.DataFrame, formula: str, cluster: Optional[str] = None):
    if cluster and cluster in df.columns:
        try:
            n_groups = int(pd.Series(df[cluster]).nunique())
        except Exception:
            n_groups = 0
        if n_groups >= 2:
            return smf.ols(formula, data=df).fit(cov_type="cluster", cov_kwds={"groups": df[cluster]})
    # Fallback to classical OLS when no/insufficient clusters
    return smf.ols(formula, data=df).fit()


def fit_mixedlm(df: pd.DataFrame, response: str, fixed: List[str], group: str = "Subject", vc: Optional[Dict[str, str]] = None):
    from statsmodels.regression.mixed_linear_model import MixedLM

    cols = [response] + fixed + [group]
    if vc:
        cols += [k for k in vc.keys() if k in df.columns]
    d = df[cols].dropna().copy()
    exog = sm.add_constant(d[fixed])
    endog = d[response]
    model = MixedLM(endog, exog, groups=d[group], vc_formula=vc or None)
    res = model.fit(reml=True, method="lbfgs")
    return res


def apply_fdr(df: pd.DataFrame, p_col: str = "p", group_col: Optional[str] = "response", alpha: float = 0.05) -> pd.DataFrame:
    if group_col and group_col in df.columns:
        outs = []
        for g, grp in df.groupby(group_col):
            p = grp[p_col].values
            rej, q, _, _ = multipletests(p, alpha=alpha, method="fdr_bh")
            gdf = grp.copy()
            gdf["p_fdr_bh"] = q
            gdf["rej_fdr_bh_0.05"] = rej
            outs.append(gdf)
        return pd.concat(outs, ignore_index=True)
    else:
        p = df[p_col].values
        rej, q, _, _ = multipletests(p, alpha=alpha, method="fdr_bh")
        out = df.copy()
        out["p_fdr_bh"] = q
        out["rej_fdr_bh_0.05"] = rej
        return out


def bootstrap_coeffs(df: pd.DataFrame, formula: str, group_col: str = "Subject", B: int = 1000, n_jobs: int = -1, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    groups = df[group_col].dropna().unique()
    seeds = rng.integers(0, 2**32 - 1, size=B, endpoint=True)

    def _fit_once(s: int):
        rs = np.random.default_rng(int(s))
        samp_groups = rs.choice(groups, size=len(groups), replace=True)
        samp_df = pd.concat([df[df[group_col] == g] for g in samp_groups], ignore_index=True)
        try:
            m = smf.ols(formula, data=samp_df).fit()
            return m.params
        except Exception:
            return None

    res = Parallel(n_jobs=n_jobs)(delayed(_fit_once)(int(s)) for s in seeds)
    return pd.DataFrame([r for r in res if r is not None])
