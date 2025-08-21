#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Symbolic regime profiles (Extended Data S1). Headless-safe.
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def main():
    outdir = Path("figs")
    outdir.mkdir(parents=True, exist_ok=True)
    x = np.linspace(0, 1, 200)
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(x, 0.3 + 0.2 * np.sin(6 * x), label="neurotypical")
    ax.plot(x, 0.6 + 0.25 * np.cos(5 * x), label="gifted")
    ax.plot(x, 0.45 + 0.4 * np.sin(4 * x) * np.cos(3 * x), label="twice-exceptional")
    ax.plot(x, 0.2 * np.exp(-8 * (x - 0.5) ** 2), label="collapse")
    ax.legend(frameon=False, ncols=2)
    ax.set_xlabel("latent dimension")
    ax.set_ylabel("activation")
    for ext in ("png", "pdf"):
        fig.savefig(outdir / f"Fig_gamma_profiles.{ext}", bbox_inches="tight", dpi=300)
    plt.close(fig)


if __name__ == "__main__":
    main()
