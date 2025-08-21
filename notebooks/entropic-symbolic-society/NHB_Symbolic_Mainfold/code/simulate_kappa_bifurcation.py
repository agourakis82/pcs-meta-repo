#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
κ-bifurcation diagram (schematic). Headless-safe.
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def main():
    outdir = Path("figs")
    outdir.mkdir(parents=True, exist_ok=True)
    k = np.linspace(0, 3, 400)
    stable = np.tanh(1.2 * (k - 1)) + 0.2
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(k, stable, lw=2)
    ax.set_xlabel("κ control")
    ax.set_ylabel("Steady state")
    ax.set_title("κ-bifurcation (schematic)")
    for ext in ("png", "pdf"):
        fig.savefig(
            outdir / f"Fig_kappa_bifurcation.{ext}", bbox_inches="tight", dpi=300
        )
    plt.close(fig)


if __name__ == "__main__":
    main()
