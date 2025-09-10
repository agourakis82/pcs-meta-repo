"""
PCS QC - Quality Gates v4.3

Lightweight quality checks and routing for linear solvers.

Author: PCS-HELIO Team
License: MIT
"""

from .quality_gate_linear import condition_number, choose_solver

__all__ = ["condition_number", "choose_solver"]

