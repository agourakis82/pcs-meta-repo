#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generates entropic-curvature heatmap (Fig. 2). Headless-safe (no plt.show()).
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def main():
    outdir = Path("figs")
    outdir.mkdir(parents=True, exist_ok=True)
    x = np.linspace(-2, 2, 200)
    y = np.linspace(-2, 2, 200)
    X, Y = np.meshgrid(x, y)
    Z = np.exp(-(X**2 + (Y * 1.2) ** 2))
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(
        Z, extent=[x.min(), x.max(), y.min(), y.max()], origin="lower", aspect="auto"
    )
    ax.set_xlabel("Entropy proxy (α)")
    ax.set_ylabel("Curvature proxy (κ)")
    cbar = fig.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label("Stability index")
    for ext in ("png", "pdf"):
        fig.savefig(
            outdir / f"Fig_symbolic_heatmap.{ext}", bbox_inches="tight", dpi=300
        )
    plt.close(fig)


if __name__ == "__main__":
    main()
