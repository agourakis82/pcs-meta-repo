#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Two synthetic figures: (1) collapse snapshot; (2) bifurcation-like response.
Saves Fig1_collapse.png and Fig2_bifurcation.png in figs/.
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def fig1(outdir: Path):
    x = np.linspace(-2, 2, 300)
    y = np.exp(-(((x - 0.5) / 0.35) ** 2))  # simple collapse-like bump
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(x, y, lw=2)
    ax.axvline(0.5, ls="--", lw=1, color="k")
    ax.set_title("Collapse signature")
    ax.set_xlabel("latent")
    ax.set_ylabel("response")
    fig.savefig(outdir / "Fig1_collapse.png", bbox_inches="tight", dpi=300)
    plt.close(fig)


def fig2(outdir: Path):
    k = np.linspace(0, 3, 300)
    y = np.tanh(2 * (k - 1.2)) + 0.4
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(k, y, lw=2)
    ax.set_title("Bifurcation-like curve")
    ax.set_xlabel("κ")
    ax.set_ylabel("steady state")
    fig.savefig(outdir / "Fig2_bifurcation.png", bbox_inches="tight", dpi=300)
    plt.close(fig)


def main():
    outdir = Path("figs")
    outdir.mkdir(parents=True, exist_ok=True)
    fig1(outdir)
    fig2(outdir)


if __name__ == "__main__":
    main()
