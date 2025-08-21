#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Plot symbolic regimes translational map (Fig. 4).
Headless-safe: salva arquivo; não usa plt.show() em batch.
"""
import argparse
from pathlib import Path

import matplotlib.pyplot as plt


def build_example_figure():
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.scatter([0, 1, 2], [0, 1, 0.2], alpha=0.7)
    ax.set_xlabel("UMAP-1")
    ax.set_ylabel("UMAP-2")
    ax.set_title("Symbolic Regimes (schematic)")
    return fig


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--outdir", type=Path, default=Path("figs"))
    p.add_argument("--basename", default="Fig_symbolic_regimes_map")
    args = p.parse_args()

    fig = build_example_figure()
    fig.suptitle(
        "Fig. 4 | Translational map of symbolic regimes. "
        "Panels illustrate the embedding of regimes and the clinical mapping."
    )
    args.outdir.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(
            args.outdir / f"{args.basename}.{ext}", bbox_inches="tight", dpi=300
        )
    plt.close(fig)


if __name__ == "__main__":
    main()
