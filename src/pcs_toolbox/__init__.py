"""Minimal public API for tests and simple utils."""

from __future__ import annotations

__all__ = ["__version__", "add"]

# Single-source version for tests; fallback if package metadata is unavailable.
try:
    from importlib.metadata import (
        version as _dist_version,  # type: ignore[attr-defined]
    )

    __version__ = _dist_version("pcs-toolbox")
except Exception:
    __version__ = "0.1.0"


def add(a: float | int, b: float | int) -> float | int:
    """Add two numbers (kept simple to satisfy tests)."""
    return a + b
