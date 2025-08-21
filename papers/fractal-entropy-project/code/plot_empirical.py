import pandas as pd, matplotlib.pyplot as plt, pathlib, sys

# ── localizar CSV mais recente ─────────────────────────────────────
data_dir = pathlib.Path(__file__).resolve().parent.parent / "paper_data"
csvs = sorted(data_dir.glob("run_*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
if not csvs:
    sys.exit("❌  Nenhum run_*.csv encontrado em paper_data/")
csv = csvs[0]
print("Usando:", csv.name)

# ── ler dados e pivotar ────────────────────────────────────────────
df = pd.read_csv(csv)
pivot = df.pivot(index="beta", columns="alpha", values="D1")
if pivot.isna().all().all():
    sys.exit("❌  DataFrame vazio – verifique se D1 foi salvo no CSV")

# ── plotar e salvar ────────────────────────────────────────────────
fig_dir = pathlib.Path(__file__).resolve().parent.parent / "paper_model" / "figs"
fig_dir.mkdir(parents=True, exist_ok=True)
out = fig_dir / "Fig4_heatmap_empirical.pdf"

plt.imshow(pivot, origin="lower", aspect="auto",
           extent=[pivot.columns.min(), pivot.columns.max(),
                   pivot.index.min(), pivot.index.max()])
plt.xscale("log"); plt.yscale("log")
plt.xlabel(r"$\alpha$"); plt.ylabel(r"$\beta$")
plt.colorbar(label=r"$D_1$ empirical")
plt.title("Empirical fractal dimension $D_1$")
plt.savefig(out, bbox_inches="tight")
plt.close()
print("✅  Figura salva em", out.relative_to(fig_dir.parent.parent))