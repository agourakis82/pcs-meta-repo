import numpy as np, matplotlib.pyplot as plt, pathlib

root = pathlib.Path(__file__).resolve().parent.parent / "paper_model" / "figs"
root.mkdir(exist_ok=True)

# Fig 1 – density profile ---------------------------------------
r = np.logspace(-1, 2, 200)
D1 = 1.17            # exemplo
rho = r**(-(D1+1))
plt.loglog(r, rho)
plt.xlabel("r")
plt.ylabel(r"$\rho^\ast(r)$")
plt.title("Density profile (slope = -{:.2f})".format(D1+1))
plt.savefig(root / "Fig1_density.pdf", bbox_inches="tight")
plt.clf()

# Fig 2 – entropy landscape -------------------------------------
ratio = np.linspace(0.5, 2.0, 400)
H = 1.5*(1+np.log(np.pi/ratio))
plt.plot(ratio, H)
plt.axvline(np.sqrt(np.pi/2), linestyle="--")
plt.xlabel(r"$D_0/D_1$")
plt.ylabel("Shannon entropy H")
plt.title("Entropy vs. D0/D1")
plt.savefig(root / "Fig2_entropy.pdf", bbox_inches="tight")
plt.clf()

# Fig 3 – stability heatmap -------------------------------------
alpha = np.logspace(-1,1,50)
beta  = np.logspace(-3,0,50)
A,B = np.meshgrid(alpha, beta)
Hmap = 1.5*(1+np.log(np.pi*A/B))
plt.imshow(Hmap, origin="lower",
           extent=[alpha.min(), alpha.max(), beta.min(), beta.max()],
           aspect='auto')
plt.xscale("log"); plt.yscale("log")
plt.xlabel(r"$\alpha$")
plt.ylabel(r"$\beta$")
plt.title("Entropy landscape")
plt.colorbar(label="H")
plt.savefig(root / "Fig3_heatmap.pdf", bbox_inches="tight")
plt.clf()