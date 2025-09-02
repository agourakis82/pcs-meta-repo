#!/usr/bin/env python3
"""
Headless PCS-HELIO v4.3 pipeline for ZuCo x KEC:
- enforce KEC schema (token_norm, curvature alias)
- load ZuCo multi-subject if present, else aligned
- merge on token_norm, harmonize categories, create log_TRT if needed
- fit OLS for available ET responses vs KEC predictors
- apply BH-FDR per response
- write outputs & QA

Intended for CI but safe to run locally.
"""
import json, re, sys, warnings
from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from statsmodels.stats.multitest import multipletests

SEED = 42
np.random.seed(SEED)

ROOT = Path(__file__).resolve().parents[1]
NB_DIR = ROOT / 'notebooks'
PROC = ROOT / 'data' / 'processed'
FIG_DIR = ROOT / 'notebooks' / 'figures' / 'metrics'
RPT_DIR = ROOT / 'notebooks' / 'reports'
for p in (PROC, FIG_DIR, RPT_DIR):
    p.mkdir(parents=True, exist_ok=True)


def norm_token(s):
    if not isinstance(s, str):
        return s
    s = s.lower()
    s = re.sub(r"[\W_]+", "", s)
    return s


def finalize_kec_schema(kec_path: Path) -> pd.DataFrame:
    if not kec_path.exists():
        print(f"[v4.3] KEC file missing: {kec_path}")
        return pd.DataFrame(columns=['token_norm', 'entropy', 'curvature', 'coherence'])
    df = pd.read_csv(kec_path)
    # curvature alias
    if 'curvature' not in df.columns and 'avg_curvature' in df.columns:
        df = df.rename(columns={'avg_curvature': 'curvature'})
    # token normalization
    if 'token_norm' not in df.columns:
        src = (
            'token_norm' if 'token_norm' in df.columns else (
            'node' if 'node' in df.columns else (
            'word' if 'word' in df.columns else (
            'Word' if 'Word' in df.columns else None)))
        )
        if src is not None:
            df['token_norm'] = df[src].astype(str).map(norm_token)
    # build view
    need = ['token_norm', 'entropy', 'curvature', 'coherence']
    for c in need:
        if c not in df.columns:
            df[c] = pd.NA
    out = df[need].copy()
    # rewrite file to ensure downstream stability
    out.to_csv(kec_path, index=False)
    print(f"[v4.3] KEC schema enforced -> {kec_path}")
    return out


def load_zuco(proc: Path) -> pd.DataFrame:
    z_alt = proc / 'zuco_word_level_all_subjects.csv'
    z_def = proc / 'zuco_aligned.csv'
    if z_alt.exists():
        z = pd.read_csv(z_alt, low_memory=False)
    elif z_def.exists():
        z = pd.read_csv(z_def, low_memory=False)
    else:
        print(f"[v4.3] No ZuCo files found in {proc}")
        return pd.DataFrame()
    # Harmonize
    if 'subject' in z.columns and 'Subject' not in z.columns:
        z['Subject'] = z['subject'].astype(str)
    if 'Task' not in z.columns:
        if 'task' in z.columns:
            z['Task'] = z['task'].astype(str)
        elif 'tsr' in z.columns:
            z['Task'] = z['tsr'].map({1: 'TSR', 0: 'NR'}).fillna('Unknown').astype(str)
    if 'Dataset' not in z.columns:
        z['Dataset'] = 'v1'
    wsrc = 'Word' if 'Word' in z.columns else ('word' if 'word' in z.columns else None)
    if wsrc:
        z['token_norm'] = z[wsrc].astype(str).map(norm_token)
    return z


def process_merge(zuco: pd.DataFrame, kec_view: pd.DataFrame) -> pd.DataFrame:
    if len(zuco) == 0 or 'token_norm' not in zuco.columns:
        return pd.DataFrame()
    if len(kec_view) == 0 or 'token_norm' not in kec_view.columns:
        # create empty columns to allow safe merge
        kec_view = pd.DataFrame({
            'token_norm': [],
            'entropy': [],
            'curvature': [],
            'coherence': [],
        })
    merged = zuco.merge(kec_view, on='token_norm', how='left', suffixes=('', '_kec'))
    if 'LogFreq' in merged.columns and 'log_freq' not in merged.columns:
        merged = merged.rename(columns={'LogFreq': 'log_freq'})
    # Map duration_ms to TRT if TRT missing
    if 'TRT' not in merged.columns and 'duration_ms' in merged.columns:
        merged['TRT'] = merged['duration_ms']
    # Logs
    for resp in ('TRT', 'GPT'):
        if resp in merged.columns:
            merged[f'log_{resp}'] = np.log1p(merged[resp])
    # Categorical types
    for cat in ('Dataset', 'Task', 'Subject', 'SentenceID'):
        if cat in merged.columns:
            merged[cat] = merged[cat].astype(str)
    return merged


def fit_ols_and_fdr(df: pd.DataFrame, outdir: Path) -> dict:
    summary = {
        'reading_coeffs_csv': None,
        'reading_coeffs_fdr_csv': None,
    }
    if len(df) == 0:
        print('[v4.3] No merged data; skip OLS/FDR')
        return summary
    # Identify vars
    et_candidates = ('FFD', 'GD', 'log_TRT', 'log_GPT', 'TRT', 'duration_ms')
    predictors = [c for c in ('entropy', 'curvature', 'coherence') if c in df.columns]
    reading_results = []
    for resp in [r for r in et_candidates if r in df.columns]:
        if len(predictors) == 0:
            continue
        need_cols = [resp] + predictors
        d = df.dropna(subset=need_cols)
        if len(d) < 100:
            # keep CI budget small and avoid spurious fits
            continue
        formula = f"{resp} ~ " + ' + '.join(predictors)
        try:
            m = smf.ols(formula, data=d).fit()
            coefs = m.params.rename('coef').to_frame()
            coefs['se'] = m.bse
            coefs['t'] = m.tvalues
            coefs['p'] = m.pvalues
            coefs['response'] = resp
            reading_results.append(coefs.reset_index().rename(columns={'index': 'term'}))
        except Exception as e:
            warnings.warn(f'OLS failed for {resp}: {e}')
    if reading_results:
        tbl = pd.concat(reading_results, ignore_index=True)
        coeffs_path = outdir / 'models_reading_coeffs.csv'
        tbl.to_csv(coeffs_path, index=False)
        summary['reading_coeffs_csv'] = str(coeffs_path)
        # FDR per response
        outs = []
        for resp, grp in tbl.groupby('response'):
            p = grp['p'].values
            rej, q, _, _ = multipletests(p, alpha=0.05, method='fdr_bh')
            g = grp.copy()
            g['p_fdr_bh'] = q
            g['rej_fdr_bh_0.05'] = rej
            outs.append(g)
        fdr = pd.concat(outs, ignore_index=True)
        fdr_path = outdir / 'models_reading_coeffs_fdr.csv'
        fdr.to_csv(fdr_path, index=False)
        summary['reading_coeffs_fdr_csv'] = str(fdr_path)
        print('[v4.3] Wrote OLS and FDR tables')
    else:
        print('[v4.3] No OLS results produced')
    return summary


def write_qa(df: pd.DataFrame, summary: dict, rpt_dir: Path):
    qa = {
        'merged_rows': int(len(df)) if len(df) > 0 else 0,
        'et_cols': [c for c in ('FFD','GD','log_TRT','log_GPT') if c in (df.columns if len(df)>0 else [])],
        'kec_cols': [c for c in ('entropy','curvature','coherence') if c in (df.columns if len(df)>0 else [])],
        'cat_covs': [c for c in ('Dataset','Task') if c in (df.columns if len(df)>0 else [])],
        **summary,
    }
    (rpt_dir / 'qa_kec_models_ci.json').write_text(json.dumps(qa, indent=2))
    print('[v4.3] Wrote QA JSON')


def main() -> int:
    kec_path = PROC / 'kec' / 'metrics_en.csv'
    kec_view = finalize_kec_schema(kec_path)
    zuco = load_zuco(PROC)
    merged = process_merge(zuco, kec_view)
    summary = fit_ols_and_fdr(merged, PROC)
    write_qa(merged, summary, RPT_DIR)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
