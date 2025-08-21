from pathlib import Path
from mc_sim import run_sim
from box_count_dimension import box_count_dimension
import pandas as pd

# --- Monte Carlo mínimo -----------------------------------------------------
G  = run_sim(1000, 500, alpha=0.3, beta=0.02)
D1 = box_count_dimension(G, q=1)

# --- Saída reprodutível ------------------------------------------------------
root_dir   = Path(__file__).resolve().parent.parent        # raiz do repo
data_dir   = root_dir / "paper_data"
data_dir.mkdir(exist_ok=True)                              # cria se faltar
csv_path   = data_dir / "demo_metrics.csv"

df = pd.DataFrame({"alpha":[0.3], "beta":[0.02], "D1":[D1]})
df.to_csv(csv_path, index=False)

print("Metrics written to", csv_path)
print("D1 =", D1)