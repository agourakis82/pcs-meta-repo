"""
PCS Wrappers - Unified Interfaces v4.3

High-level wrappers that route to numerically stable solvers based on
quality gates and lightweight diagnostics.

Author: PCS-HELIO Team
License: MIT
"""

from .least_squares import solve_least_squares

__all__ = ["solve_least_squares"]

