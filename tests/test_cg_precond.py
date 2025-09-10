"""
Tests for Conjugate Gradient with preconditioning.

Validates convergence on SPD matrices and demonstrates reduced iterations
with Jacobi preconditioner on tridiagonal Laplacian.

Author: PCS-HELIO Team
License: MIT
"""

import numpy as np
import pytest

try:
    from src.pcs_math.cg_precond import cg
    from src.pcs_math.preconditioners import jacobi_precond
except ImportError:
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from src.pcs_math.cg_precond import cg
    from src.pcs_math.preconditioners import jacobi_precond


def make_tridiag_spd(n: int) -> np.ndarray:
    d = 2.0 * np.ones(n)
    e = -1.0 * np.ones(n - 1)
    A = np.diag(d) + np.diag(e, 1) + np.diag(e, -1)
    return A


def test_cg_converges_on_spd():
    np.random.seed(0)
    n = 200
    A = make_tridiag_spd(n)
    x_true = np.random.randn(n)
    b = A @ x_true
    x, info = cg(A, b, tol=1e-10, maxiter=500, return_info=True)
    assert info["converged"]
    # Solution accurate
    rel_err = np.linalg.norm(x - x_true) / (np.linalg.norm(x_true) + 1e-16)
    assert rel_err < 1e-8


def test_cg_preconditioning_reduces_iterations():
    np.random.seed(1)
    n = 300
    A = make_tridiag_spd(n)
    b = np.random.randn(n)

    # Without preconditioning
    _, info_no = cg(A, b, tol=1e-8, maxiter=2000, return_info=True)

    # With Jacobi preconditioning
    M = jacobi_precond(A)
    _, info_j = cg(A, b, M=M, tol=1e-8, maxiter=2000, return_info=True)

    assert info_j["converged"]
    assert info_no["converged"]
    # Preconditioning should not increase iterations
    assert info_j["iterations"] <= info_no["iterations"]
