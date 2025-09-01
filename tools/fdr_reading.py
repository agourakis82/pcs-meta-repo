import pandas as pd
from pathlib import Path
from statsmodels.stats.multitest import multipletests

proc = Path("data/processed")
inp  = proc / "models_reading_coeffs.csv"
out  = proc / "models_reading_coeffs_fdr.csv"

df = pd.read_csv(inp)
if not {'response','p'}.issubset(df.columns):
    raise SystemExit(f"Required cols not found in {inp}: got {df.columns}")
outs=[]
for resp, grp in df.groupby('response'):
    pvals = grp['p'].values
    rej, q, _, _ = multipletests(pvals, alpha=0.05, method="fdr_bh")
    g = grp.copy()
    g['p_fdr_bh'] = q
    g['rej_fdr_bh_0.05'] = rej
    outs.append(g)
fdr = pd.concat(outs, ignore_index=True)
fdr.to_csv(out, index=False)
print(f"[OK] Saved {out}")
