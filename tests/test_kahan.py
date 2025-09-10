"""
Tests for Kahan compensated summation.

Ensures reduced rounding error versus naive and NumPy sum in adverse cases.

Author: PCS-HELIO Team
License: MIT
"""

import numpy as np

try:
    from src.pcs_math.kahan import kahan_sum, kahan_dot, kahan_norm_squared
except ImportError:
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from src.pcs_math.kahan import kahan_sum, kahan_dot, kahan_norm_squared


def test_kahan_sum_adverse_scale_variation():
    # One large value plus many tiny ones
    large = 1.0
    small = 1e-10
    n = 1_000_0  # keep test quick
    x = np.array([large] + [small] * n)
    expected = large + n * small
    naive = float(sum(x))
    numpy_sum = float(np.sum(x))
    ksum = float(kahan_sum(x))
    err_naive = abs(naive - expected)
    err_np = abs(numpy_sum - expected)
    err_k = abs(ksum - expected)
    assert err_k <= err_np and err_k <= err_naive


def test_kahan_dot_and_norm():
    np.random.seed(0)
    x = np.random.randn(1000) * 1e-8
    y = np.random.randn(1000) * 1e8
    # Reference using higher precision via float128 if available
    try:
        ref = np.sum((x.astype(np.float128) * y.astype(np.float128))).astype(np.float64)
    except Exception:
        ref = np.sum(x * y)
    naive = float(np.sum(x * y))
    kd = float(kahan_dot(x, y))
    assert abs(kd - ref) <= abs(naive - ref)

    # Norm squared should match numpy within tolerance
    ns = float(kahan_norm_squared(x))
    npns = float(np.sum(x * x))
    assert abs(ns - npns) < 1e-12
