"""
Tests for quality gates and solver routing.

Author: PCS-HELIO Team
License: MIT
"""

import numpy as np

try:
    from src.pcs_qc.quality_gate_linear import condition_number, choose_solver
except ImportError:
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from src.pcs_qc.quality_gate_linear import condition_number, choose_solver


def test_condition_number_matches_expectation():
    U = np.random.randn(6, 6)
    V = np.random.randn(6, 6)
    s = np.array([1.0, 1e-2, 1e-3, 1e-4, 1e-6, 1e-8])
    A = U @ np.diag(s) @ V.T
    cond = condition_number(A, method="svd")
    expected = s[0] / s[-1]
    assert abs(np.log10(cond) - np.log10(expected)) < 1.0


def test_choose_solver_routes_correctly():
    # Well-conditioned
    A_well = np.eye(10)
    assert choose_solver(A_well, prefer="qr", nonneg=False) == "qr"
    # Ill-conditioned
    A_ill = np.diag([1.0, 1e-8, 1e-12, 1e-16])
    assert choose_solver(A_ill, prefer="qr", nonneg=False) == "svd_trunc"
    # Nonnegative constraint
    assert choose_solver(A_well, prefer="qr", nonneg=True) == "nnls"
