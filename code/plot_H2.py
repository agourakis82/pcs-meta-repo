import pandas as pd, matplotlib.pyplot as plt, numpy as np, pathlib

# localizar CSV
root = pathlib.Path(__file__).resolve().parent.parent / "paper_data"
csv = root / "H2_timeseries.csv"
if not csv.exists():
    raise FileNotFoundError(f"{csv} não encontrado – rode run_rupture.py antes.")

# ler como DataFrame e converter para Series
ts = pd.read_csv(csv, header=None).iloc[:, 0]   # primeira coluna
plt.axvline(5000, linestyle="--", label=r"peak $\Lambda$")
plt.xlabel("t")
plt.ylabel(r"$D_1$")
plt.title("Recovery of $D_1$ after symbolic rupture")
plt.legend()
out = pathlib.Path(__file__).resolve().parent.parent / "paper_model/figs/Fig5_H2_decay.pdf"
out.parent.mkdir(parents=True, exist_ok=True)
plt.savefig(out, bbox_inches="tight")
print("Figura salva em", out)