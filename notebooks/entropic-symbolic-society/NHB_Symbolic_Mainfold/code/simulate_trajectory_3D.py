#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
3D trajectory in (α, κ, E_r) space (Extended Data S4). Headless-safe.
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D  # noqa


def main():
    outdir = Path("figs")
    outdir.mkdir(parents=True, exist_ok=True)
    t = np.linspace(0, 2 * np.pi, 300)
    a = 0.5 + 0.3 * np.cos(t)
    k = 0.4 + 0.25 * np.sin(2 * t)
    e = 0.6 + 0.2 * np.sin(t + np.pi / 4)
    fig = plt.figure(figsize=(6, 5))
    ax = fig.add_subplot(111, projection="3d")
    ax.plot(a, k, e, lw=1.8)
    ax.set_xlabel("α")
    ax.set_ylabel("κ")
    ax.set_zlabel("E_r")
    ax.set_title("Trajectory in symbolic manifold (schematic)")
    for ext in ("png", "pdf"):
        fig.savefig(outdir / f"Fig_trajectory_3D.{ext}", bbox_inches="tight", dpi=300)
    plt.close(fig)


if __name__ == "__main__":
    main()
