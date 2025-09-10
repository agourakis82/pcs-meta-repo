"""
Tests for SVD-based solver and truncation heuristics.

Checks numerical stability on ill-conditioned systems and consistency with
NumPy least-squares on well-conditioned problems.

Author: PCS-HELIO Team
License: MIT
"""

import numpy as np
import pytest

try:
    from src.pcs_math.svd_solve import svd_solve, truncated_svd
except ImportError:
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from src.pcs_math.svd_solve import svd_solve, truncated_svd


def test_truncated_svd_rank_and_error():
    np.random.seed(123)
    m, n, r = 40, 25, 5
    U = np.random.randn(m, r)
    V = np.random.randn(r, n)
    A = U @ V  # rank r
    U_t, S_t, Vt_t, rank_eff = truncated_svd(A, rank=r)
    A_approx = U_t @ np.diag(S_t) @ Vt_t
    # Effective rank should be <= r
    assert rank_eff <= r
    # Reconstruction error should be small
    err = np.linalg.norm(A - A_approx)
    assert err < 1e-10


def test_svd_solve_well_conditioned_vs_lstsq():
    np.random.seed(42)
    m, n = 80, 30
    A = np.random.randn(m, n)
    x_true = np.random.randn(n)
    b = A @ x_true + 1e-10 * np.random.randn(m)
    x_svd, info = svd_solve(A, b, return_info=True)
    x_np = np.linalg.lstsq(A, b, rcond=None)[0]
    # Solutions should be very close
    assert np.linalg.norm(x_svd - x_np) / (np.linalg.norm(x_np) + 1e-16) < 1e-10
    # Residuals comparable
    r_svd = np.linalg.norm(A @ x_svd - b)
    r_np = np.linalg.norm(A @ x_np - b)
    assert abs(r_svd - r_np) < 1e-10


def test_svd_handles_ill_conditioning():
    np.random.seed(7)
    n = 20
    U = np.random.randn(n, n)
    V = np.random.randn(n, n)
    s = np.logspace(0, -12, n)
    A = U @ np.diag(s) @ V.T
    x_true = np.random.randn(n)
    b = A @ x_true

    x_svd, info = svd_solve(A, b, rcond=1e-10, return_info=True)
    # Check that residual is near machine precision
    assert info["residual_norm"] < 1e-8
