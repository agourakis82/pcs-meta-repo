"""
editorial_preamble
====================

This module centralises common styling and figure-export utilities for the
*Symbolic Manifold* project.  Each figure-producing script in the suite
imports this module to ensure that all plots share a consistent look and
feel appropriate for publication in journals such as **Scientific Reports**.

Highlights:

* Global rcParams and a default colour palette tailored for clear
  scientific figures.  The palette can be overridden on a per-script
  basis but still falls back to sensible defaults.
* Directory helpers: figures are saved into a ``figs`` folder that is
  created relative to the script that generated them.
* Multi-format saving: figures are exported to ``.png``, ``.pdf`` and
  ``.svg`` by default to support screen viewing, high‑resolution print
  and vector formats.
* Panel labelling: when a figure has multiple subplots, each panel can
  automatically be tagged with a capital letter (A, B, …) in the upper
  left corner.
* Footers: captions can be appended below a figure; these are useful
  for Extended Data figures or for including concise descriptions
  directly in the exported image.

This file contains no executable logic when imported, but defines
functions for scripts to call.  See the docstrings of individual
functions for details.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List, Optional

import matplotlib.pyplot as plt

__all__ = [
    "DEFAULT_RC",
    "DEFAULT_PALETTE",
    "set_style",
    "ensure_figdir",
    "savefig_multi",
    "label_all_panels",
    "add_footer",
    "finalize",
]

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# rcParams that approximate the style used in many Nature family journals.
DEFAULT_RC: Dict[str, object] = {
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "font.size": 10,
    "axes.labelsize": 10,
    "axes.titlesize": 11,
    "legend.fontsize": 9,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "axes.linewidth": 0.8,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
}

# A simple palette providing primary and secondary colours.  Scripts may
# override keys in this dictionary when calling :func:`set_style` to
# customise colour choices while retaining defaults.
DEFAULT_PALETTE: Dict[str, str] = {
    "background": "white",
    "bars": "#1f77b4",  # muted blue
    "points": "#2ca02c",  # muted green
    "accent": "#111111",  # near black
    "line1": "#d62728",  # muted red
    "line2": "#9467bd",  # muted purple
    "line3": "#8c564b",  # muted brown
}

# ---------------------------------------------------------------------------
# Style utilities
# ---------------------------------------------------------------------------


def set_style(
    rc: Optional[Dict[str, object]] = None, palette: Optional[Dict[str, str]] = None
) -> Dict[str, str]:
    """Apply global matplotlib style settings.

    Parameters
    ----------
    rc: dict, optional
        Additional or overridden rcParams.  Any keys provided here
        override the defaults defined in :data:`DEFAULT_RC`.
    palette: dict, optional
        Colour palette overrides.  Keys not present fall back to
        :data:`DEFAULT_PALETTE`.

    Returns
    -------
    dict
        The palette actually used after merging defaults and overrides.

    Notes
    -----
    This function updates ``matplotlib.pyplot.rcParams`` in-place.  It
    should be called near the start of a script before any figures are
    created.  The returned palette can then be passed to plotting
    functions to obtain colours.
    """
    merged_rc: Dict[str, object] = {**DEFAULT_RC, **(rc or {})}
    merged_palette: Dict[str, str] = {**DEFAULT_PALETTE, **(palette or {})}
    plt.rcParams.update(merged_rc)
    plt.rcParams["figure.facecolor"] = merged_palette["background"]
    plt.rcParams["axes.facecolor"] = merged_palette["background"]
    return merged_palette


def ensure_figdir(file: str | Path) -> Path:
    """Determine and create the figures directory for a script.

    Given the path to a script, this function constructs a ``figs``
    directory one level above the script file.  It creates the
    directory if it does not already exist.

    Parameters
    ----------
    file: str or Path
        Path to the source file that will produce figures.

    Returns
    -------
    pathlib.Path
        The absolute path to the figures directory.
    """
    script_path = Path(file).resolve()
    outdir = script_path.parent.parent / "figs"
    outdir.mkdir(parents=True, exist_ok=True)
    return outdir


def savefig_multi(
    fig: plt.Figure,
    outdir: Path,
    basename: str,
    exts: Iterable[str] = ("png", "pdf", "svg"),
) -> List[Path]:
    """Save a figure in multiple formats.

    Parameters
    ----------
    fig: matplotlib.figure.Figure
        The figure to save.
    outdir: pathlib.Path
        Output directory in which to place the figure files.  The
        directory must already exist.
    basename: str
        Base filename (without extension) for the output files.
    exts: Iterable[str]
        Iterable of file extensions (without dots) to generate.  The
        default writes PNG, PDF and SVG.

    Returns
    -------
    list of pathlib.Path
        A list of the absolute paths to the saved files.
    """
    saved_paths: List[Path] = []
    for ext in exts:
        path = outdir / f"{basename}.{ext}"
        fig.savefig(path, bbox_inches="tight")
        saved_paths.append(path)
    return saved_paths


def label_all_panels(fig: plt.Figure, start: str = "A") -> None:
    """Label every axes in a figure with sequential capital letters.

    Panels are labelled in row-major order.  Each axes in the
    ``fig.axes`` list will receive a label placed at the top-left
    corner of the axes.  Colour is drawn from the ``accent`` entry of
    the current palette.

    Parameters
    ----------
    fig: matplotlib.figure.Figure
        The figure whose panels should be labelled.
    start: str, optional
        The starting letter.  Default is ``"A"``.
    """
    ascii_offset = ord(start.upper())
    palette = DEFAULT_PALETTE
    for idx, ax in enumerate(fig.axes):
        label = chr(ascii_offset + idx)
        ax.text(
            0.02,
            0.96,
            f"{label}",
            transform=ax.transAxes,
            fontsize=12,
            fontweight="bold",
            va="top",
            ha="left",
            color=palette.get("accent", "black"),
        )


def add_footer(
    fig: plt.Figure, text: str, fontsize: int = 9, y_offset: float = -0.05
) -> None:
    """Append a footer/caption below a figure.

    Parameters
    ----------
    fig: matplotlib.figure.Figure
        The figure to annotate.
    text: str
        The caption to add.
    fontsize: int, optional
        Font size of the caption.  Defaults to 9.
    y_offset: float, optional
        Vertical offset relative to the figure bottom.  Negative
        values move the caption downward.  Defaults to -0.05.
    """
    fig.text(0.5, y_offset, text, ha="center", fontsize=fontsize)


def finalize(
    fig: plt.Figure,
    outdir: Path,
    basename: str,
    footer: Optional[str] = None,
    exts: Iterable[str] = ("png", "pdf", "svg"),
) -> List[Path]:
    """Wrap up figure creation: label panels, append a footer and save.

    This function combines several helper routines into one:

    * Calls :func:`label_all_panels` to tag each subplot.
    * If ``footer`` is supplied, calls :func:`add_footer`.
    * Calls :func:`savefig_multi` to write the figure to disk.

    Parameters
    ----------
    fig: matplotlib.figure.Figure
        The figure to finalise and save.
    outdir: pathlib.Path
        Output directory for the saved files.
    basename: str
        Base filename (without extension) for output files.
    footer: str, optional
        Caption to append below the figure.  If ``None`` (default), no
        caption is added.
    exts: Iterable[str], optional
        File extensions to save.  Defaults to PNG, PDF and SVG.

    Returns
    -------
    list of pathlib.Path
        Paths to the saved files.
    """
    # Panel labels
    label_all_panels(fig)
    # Footer
    if footer:
        add_footer(fig, footer)
    # Save
    saved = savefig_multi(fig, outdir, basename, exts=exts)
    return saved
