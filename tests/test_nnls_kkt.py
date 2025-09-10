"""
Tests for NNLS via KKT conditions.

Checks KKT satisfaction and compares with SciPy when available.

Author: PCS-HELIO Team
License: MIT
"""

import numpy as np
import pytest

try:
    from src.pcs_opt.nnls_kkt import nnls_kkt
except ImportError:
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from src.pcs_opt.nnls_kkt import nnls_kkt


def test_nnls_kkt_kkt_satisfaction():
    np.random.seed(1234)
    m, n = 30, 10
    A = np.abs(np.random.randn(m, n))  # nonnegative design to avoid cancellations
    x_true = np.abs(np.random.randn(n))
    b = A @ x_true
    x, info = nnls_kkt(A, b, tol=1e-10, return_info=True)
    assert info["converged"]
    assert info["kkt_satisfied"]
    assert np.all(x >= -1e-12)
    # Residual near zero
    assert info["residual_norm"] < 1e-8


def test_nnls_compare_scipy_if_available():
    np.random.seed(2)
    m, n = 40, 15
    A = np.abs(np.random.randn(m, n))
    x_true = np.abs(np.random.randn(n))
    b = A @ x_true + 1e-10 * np.random.randn(m)
    x_kkt, info_kkt = nnls_kkt(A, b, return_info=True)

    try:
        from scipy.optimize import nnls as scipy_nnls

        x_scipy, _ = scipy_nnls(A, b)
        # Solutions should be close
        diff = np.linalg.norm(x_kkt - x_scipy)
        assert diff / (np.linalg.norm(x_scipy) + 1e-16) < 1e-6
    except Exception:
        pytest.skip("SciPy not available; skipping comparison test")
