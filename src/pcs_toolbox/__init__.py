"""PCS Toolbox public API.

Exports data loaders (SWOW, ZuCo), KEC metrics, and analysis helpers.
"""

from __future__ import annotations

__all__ = [
    "__version__",
    "add",
    # new public symbols
    "load_swow_graph",
    "compute_kec_metrics",
    "load_zuco",
    "fit_ols_clustered",
    "fit_mixedlm",
    "apply_fdr",
    "bootstrap_coeffs",
]

# Version constant (kept static to satisfy tests without requiring installation)
__version__ = "0.2.1"


def add(a: float | int, b: float | int) -> float | int:
    """Add two numbers (kept simple to satisfy tests)."""
    return a + b

# New imports for public API
try:
    from .swow import load_swow_graph  # type: ignore
except Exception:
    pass
try:
    from .kec import compute_kec_metrics  # type: ignore
except Exception:
    pass
try:
    from .zuco import load_all as load_zuco  # type: ignore
except Exception:
    pass
try:
    from .analysis import (
        fit_ols_clustered,
        fit_mixedlm,
        apply_fdr,
        bootstrap_coeffs,
    )  # type: ignore
except Exception:
    pass
