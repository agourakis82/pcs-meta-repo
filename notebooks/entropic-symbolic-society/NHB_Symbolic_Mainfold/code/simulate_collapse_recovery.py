#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Collapse and recovery time-series (Extended Data S6). Headless-safe.
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def main():
    outdir = Path("figs")
    outdir.mkdir(parents=True, exist_ok=True)
    t = np.linspace(0, 10, 600)
    a = 0.25 + 0.55 * (1 / (1 + np.exp(-(t - 5))))  # recovery
    k = 0.6 - 0.35 * np.exp(-(((t - 5) / 2.0) ** 2))  # dip + recover
    e = (
        0.3
        + 0.3 * np.exp(-(((t - 2) / 0.8) ** 2))
        + 0.15 * np.sin(0.7 * t) * np.exp(-0.1 * t)
    )
    fig, ax = plt.subplots(1, 1, figsize=(7, 4))
    ax.plot(t, a, label="α", lw=2)
    ax.plot(t, k, label="κ", lw=2)
    ax.plot(t, e, label="E_r", lw=2)
    ax.legend(frameon=False, ncols=3)
    ax.set_xlabel("time")
    ax.set_ylabel("state")
    for ext in ("png", "pdf"):
        fig.savefig(
            outdir / f"Fig_collapse_recovery.{ext}", bbox_inches="tight", dpi=300
        )
    plt.close(fig)


if __name__ == "__main__":
    main()
