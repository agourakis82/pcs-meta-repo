"""
analyze_swow.py
================

This script analyses the SWOW (Small World of Words) semantic network by
computing the degree distribution and its complementary cumulative distribution
function (CCDF).  It uses a command line interface and the shared
``editorial_preamble`` module to produce a two–panel figure that is saved
in multiple formats.  The left panel shows the histogram of node degrees on
a logarithmic frequency axis, while the right panel shows the CCDF on a
log–log scale.  A caption is appended to the figure consistent with
Extended Data Fig. S3 in the accompanying manuscript.

The script can load graphs in either GraphML (.graphml) or pickle
(.gpickle/.pickle) formats.  It includes a check for file existence and
provides helpful error messages when the graph cannot be loaded.
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Tuple

import editorial_preamble as ep
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from matplotlib.ticker import ScalarFormatter


def load_graph(path: Path) -> nx.Graph:
    """Load a graph from a .graphml or .gpickle file.

    Parameters
    ----------
    path : Path
        Path to the graph file.  Supported suffixes: ``.graphml``, ``.gpickle`` and ``.pickle``.

    Returns
    -------
    nx.Graph
        The loaded graph.  Directed graphs are converted to undirected for degree computation.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    ValueError
        If the suffix is unsupported.
    """
    if not path.exists():
        raise FileNotFoundError(f"Graph file not found: {path}")
    suffix = path.suffix.lower()
    if suffix == ".graphml":
        G = nx.read_graphml(path)
    elif suffix in {".gpickle", ".pickle"}:
        G = nx.read_gpickle(path)
    else:
        raise ValueError(
            f"Unsupported graph format: {suffix}. Use .graphml or .gpickle."
        )
    return G.to_undirected()


def compute_degree_array(G: nx.Graph) -> np.ndarray:
    """Return the array of degrees for all nodes in G."""
    return np.array([d for _, d in G.degree()], dtype=float)


def ccdf(values: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Compute the complementary cumulative distribution function for positive values."""
    v = values[values >= 1]
    if v.size == 0:
        return np.array([]), np.array([])
    sorted_v = np.sort(v)
    unique_vals = np.unique(sorted_v)
    ccdf_vals = (
        1.0 - np.searchsorted(sorted_v, unique_vals, side="right") / sorted_v.size
    )
    return unique_vals, ccdf_vals


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyse a semantic network by plotting its degree distribution and CCDF."
    )
    parser.add_argument(
        "--graph",
        type=Path,
        default=Path("NHB_Symbolic_Mainfold/results/word_network.graphml"),
        help="Path to the graph file (.graphml, .gpickle or .pickle).",
    )
    parser.add_argument(
        "--bins", type=int, default=100, help="Number of histogram bins (default: 100)."
    )
    parser.add_argument(
        "--min-degree",
        type=int,
        default=1,
        help="Minimum degree to include in the histogram (default: 1).",
    )
    parser.add_argument(
        "--outdir",
        type=Path,
        default=Path("NHB_Symbolic_Mainfold/figs"),
        help="Directory for saving figures.",
    )
    parser.add_argument(
        "--basename",
        type=str,
        default="ext_S3_degree_distribution",
        help="Base filename for output files.",
    )
    parser.add_argument(
        "--log-level", type=str, default="INFO", help="Logging level (default: INFO)."
    )
    args = parser.parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    palette = ep.set_style()
    try:
        G = load_graph(args.graph)
    except Exception as exc:
        logging.error(str(exc))
        return
    degrees = compute_degree_array(G)
    # Filter degrees for histogram
    degrees_hist = degrees[degrees >= args.min_degree]
    # Compute CCDF
    unique_deg, ccdf_vals = ccdf(degrees_hist)
    # Prepare figure
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    # Histogram (log‐scaled frequency)
    axes[0].hist(
        degrees_hist,
        bins=args.bins,
        color=palette["bars"],
        edgecolor="black",
        linewidth=0.6,
        alpha=0.85,
    )
    axes[0].set_xlabel("Degree")
    axes[0].set_ylabel("Frequency")
    axes[0].set_title("Degree distribution")
    axes[0].set_yscale("log")
    axes[0].set_xlim(left=args.min_degree)
    axes[0].grid(True, linestyle="--", alpha=0.4)
    # CCDF
    axes[1].loglog(
        unique_deg,
        ccdf_vals,
        marker="o",
        linestyle="none",
        markersize=3.5,
        color=palette["points"],
        alpha=0.85,
    )
    axes[1].set_xlabel("Degree")
    axes[1].set_ylabel("P(X \u2265 x)")
    axes[1].set_title("Complementary CDF")
    axes[1].grid(True, linestyle="--", which="both", alpha=0.4)
    axes[1].yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
    ep.label_all_panels(fig, start="A")
    footer = (
        "Extended Data Fig. S3 | Degree distribution and CCDF of the SWOW‐EN semantic graph. "
        "Panel (A) shows the histogram of node degrees on a log frequency scale. Panel (B) shows "
        "the complementary cumulative distribution on a log–log scale. Graph is loaded from "
        f"{args.graph.name} and analysed as undirected."
    )
    ep.finalize(fig, args.outdir, args.basename, footer)


if __name__ == "__main__":
    main()
