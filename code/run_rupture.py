from mc_sim import run_sim
from box_count_dimension import box_count_dimension
import numpy as np, pandas as pd, pathlib

# ── parâmetros principais ───────────────────────────────────────────
N, steps = 10_000, 12_000
def Lambda(t):
    """Gaussian shock centred at t0=5000 (σ = 500)."""
    return 0.8 * np.exp(-((t - 5_000) / 500) ** 2)

# ── simulação ───────────────────────────────────────────────────────
G = run_sim(N, steps, alpha=0.3, beta=0.02, Lambda_func=Lambda, seed=42)

# ── análise em janelas deslizantes ──────────────────────────────────
window = 200
D_ts = []
for t in range(0, steps, window):
    sub = G.subgraph(list(G.nodes)[t:t + window])
    if sub.number_of_edges() == 0:
        D_ts.append(np.nan)
        continue                 # ← agora SÓ executa quando grafo vazio
    else:
        D1, _, _ = box_count_dimension(sub, q=1, bootstrap=100)
        D_ts.append(D1)
        print(f"t={t:5d}, D1={D1:.3f}")   # feedback opcional

# ── salvar série temporal ───────────────────────────────────────────
out = pathlib.Path(__file__).resolve().parent.parent / "paper_data" / "H2_timeseries.csv"
out.parent.mkdir(exist_ok=True)
pd.Series(D_ts).to_csv(out, index=False)
print("✅  Série temporal salva em", out.relative_to(out.parent.parent))