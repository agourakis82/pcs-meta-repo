import pandas as pd, statsmodels.formula.api as smf, numpy as np
from pathlib import Path

PROC = Path("data/processed")
inp  = PROC / "zuco_word_level_all_subjects.csv"  # Use the file with actual words
kec  = PROC / "kec" / "metrics_en.csv"
out  = PROC / "delta_r2_reading.csv"

zuco = pd.read_csv(inp)
kdf  = pd.read_csv(kec)

# normaliza colunas e merge esperto (Word/word)
for d in (zuco, kdf):
    d.columns = [c.strip() for c in d.columns]
z_word = "word" if "word" in zuco.columns else ("Word" if "Word" in zuco.columns else None)
k_word = "node" if "node" in kdf.columns else ("word" if "word" in kdf.columns else ("Word" if "Word" in kdf.columns else None))
if not (z_word and k_word):
    raise SystemExit("No Word/word column to merge.")
df = zuco.merge(kdf, left_on=z_word, right_on=k_word, how="left")

# prepara respostas/covariáveis
df = df.rename(columns={"LogFreq":"log_freq"})
for resp in ("TRT","GPT"):
    if resp in df: df[f"log_{resp}"] = (df[resp]+1).apply(np.log)
covs = [c for c in ("length","log_freq","surprisal") if c in df.columns]
kecs = [c for c in ("entropy","curvature","coherence") if c in df.columns]

rows=[]
for resp in [r for r in ("duration_ms","fixation_samples","avg_gaze_x","avg_gaze_y","avg_pupil_area") if r in df.columns]:
    base = resp + " ~ " + " + ".join(covs) if covs else resp + " ~ 1"
    full = base + " + " + " + ".join(kecs) if kecs else base
    try:
        m0 = smf.ols(base, data=df.dropna(subset=[resp]+covs)).fit()
        m1 = smf.ols(full, data=df.dropna(subset=[resp]+covs+kecs)).fit()
        # R² ajustado ou simples?
        rows.append({"response": resp,
                     "r2_base": m0.rsquared_adj,
                     "r2_full": m1.rsquared_adj,
                     "delta_r2_adj_pp": 100*(m1.rsquared_adj - m0.rsquared_adj)})
    except Exception as e:
        rows.append({"response": resp, "error": str(e)})

pd.DataFrame(rows).to_csv(out, index=False)
print("[OK] Saved", out)
