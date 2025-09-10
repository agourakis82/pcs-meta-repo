"""
Linear Solver Quality Gates

Condition number estimation and solver routing for least-squares problems.
Prefers QR on well-conditioned systems; routes to truncated SVD when the
condition number is large; NNLS is suggested when constraints are nonnegative.

Author: PCS-HELIO Team
License: MIT
"""

from __future__ import annotations

from typing import Literal
import numpy as np


def condition_number(A: np.ndarray, method: Literal["svd", "qr"] = "svd") -> float:
    """
    Estimate the condition number of A.

    Parameters
    ----------
    A : np.ndarray
        Matrix.
    method : {"svd", "qr"}, default="svd"
        Estimation method. "svd" uses full SVD; "qr" uses an approximation via R.

    Returns
    -------
    cond : float
        Condition number estimate (sigma_max / sigma_min). np.inf if singular.
    """
    A = np.asarray(A, dtype=np.float64)

    if method == "svd":
        s = np.linalg.svd(A, compute_uv=False)
        s = s[s > 0]
        if len(s) == 0:
            return float("inf")
        return float(s[0] / s[-1])
    elif method == "qr":
        # Import locally to avoid hard dependency chain
        from src.pcs_math.qr_householder import householder_qr

        _, R = householder_qr(A, mode="reduced", dtype=np.float64)
        diag = np.abs(np.diag(R))
        diag = diag[diag > 0]
        if len(diag) == 0:
            return float("inf")
        return float(diag[0] / diag[-1])
    else:
        raise ValueError("method must be 'svd' or 'qr'")


def choose_solver(
    A: np.ndarray,
    prefer: Literal["qr", "svd"] = "qr",
    kmax: int | None = None,
    nonneg: bool = False,
) -> Literal["qr", "svd_trunc", "nnls"]:
    """
    Decide which solver to use for a least-squares problem.

    Parameters
    ----------
    A : np.ndarray
        Coefficient matrix.
    prefer : {"qr", "svd"}, default="qr"
        Preferred unconstrained solver when the system is well-conditioned.
    kmax : int, optional
        Max rank to consider for truncated SVD (advisory only).
    nonneg : bool, default=False
        If True, route to NNLS.

    Returns
    -------
    solver : {"qr", "svd_trunc", "nnls"}
        Suggested solver.

    Notes
    -----
    - If cond(A) > 1e3, route to truncated SVD.
    - If nonneg=True, route to NNLS regardless of conditioning.
    """
    if nonneg:
        return "nnls"

    cond = condition_number(A, method="svd")
    if cond > 1e3:
        return "svd_trunc"
    return "qr" if prefer == "qr" else "svd_trunc"

