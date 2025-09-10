"""
Unified Least-Squares Solver Wrapper

Routes to Householder-QR, truncated-SVD, or NNLS (KKT) based on quality gates
and user preferences. Provides lightweight diagnostics and deterministic runs.

Author: PCS-HELIO Team
License: MIT
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple, Literal
import numpy as np

from src.pcs_qc.quality_gate_linear import condition_number, choose_solver
from src.pcs_math.qr_householder import solve_via_qr
from src.pcs_math.svd_solve import svd_solve
from src.pcs_opt.nnls_kkt import nnls_kkt


@dataclass
class LSQDiagnostics:
    method: Literal["qr", "svd_trunc", "nnls"]
    condition: float
    time_ms: float
    residual_norm: float
    rank_used: Optional[int] = None
    notes: Optional[str] = None


def solve_least_squares(
    A: np.ndarray,
    b: np.ndarray,
    constraints: Optional[Dict[str, Any]] = None,
    prefer: Literal["qr", "svd"] = "qr",
    rcond: Optional[float] = None,
    rank: Optional[int] = None,
    quiet: bool = True,
) -> Tuple[np.ndarray, LSQDiagnostics]:
    """
    Solve least-squares with automatic solver selection and diagnostics.

    Parameters
    ----------
    A : np.ndarray (m,n)
        Coefficient matrix.
    b : np.ndarray (m,) or (m,k)
        Right-hand side vector(s).
    constraints : dict, optional
        If {"nonneg": True}, solves NNLS via KKT.
    prefer : {"qr","svd"}, default="qr"
        Preferred unconstrained solver when well-conditioned.
    rcond : float, optional
        Relative tolerance for rank determination (SVD/QR).
    rank : int, optional
        Target or max rank (SVD truncation hint).
    quiet : bool, default=True
        If False, prints a short informational log line.

    Returns
    -------
    x : np.ndarray
        Solution vector or matrix (n,) or (n,k).
    diag : LSQDiagnostics
        Diagnostics including method, condition, residual norm, and time.

    Notes
    -----
    - Uses float64 computations for numerical stability.
    - QR is preferred when cond(A) <= 1e3; otherwise, SVD truncation.
    - NNLS is routed when constraints specify nonnegativity.
    """
    A = np.asarray(A, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)

    nonneg = bool(constraints.get("nonneg")) if isinstance(constraints, dict) else False
    c = condition_number(A, method="svd")
    route = choose_solver(A, prefer=prefer, kmax=rank, nonneg=nonneg)

    t0 = time.perf_counter()
    if route == "nnls":
        if b.ndim != 1:
            raise ValueError("NNLS wrapper expects a 1D right-hand side (m,)")
        x, info = nnls_kkt(A, b, tol=rcond or 1e-10, max_iter=10000, return_info=True)
        residual_norm = float(np.linalg.norm(A @ x - b))
        diag = LSQDiagnostics(
            method="nnls",
            condition=c,
            time_ms=1000.0 * (time.perf_counter() - t0),
            residual_norm=residual_norm,
            rank_used=None,
            notes="routed by nonnegativity"
        )
        if not quiet:
            print(f"method=nnls | cond={c:.2e} | time={diag.time_ms:.1f}ms | res={residual_norm:.2e}")
        return x, diag

    if route == "qr":
        x = solve_via_qr(A, b, dtype=np.float64, rcond=rcond)
        residual_norm = float(np.linalg.norm(A @ x - b))
        diag = LSQDiagnostics(
            method="qr",
            condition=c,
            time_ms=1000.0 * (time.perf_counter() - t0),
            residual_norm=residual_norm,
            rank_used=None,
            notes=None,
        )
        if not quiet:
            print(f"method=qr | cond={c:.2e} | time={diag.time_ms:.1f}ms | res={residual_norm:.2e}")
        return x, diag

    # route == 'svd_trunc'
    if b.ndim == 1:
        x, info = svd_solve(A, b, rank=rank, rcond=rcond, return_info=True)
        residual_norm = float(info.get("residual_norm", np.linalg.norm(A @ x - b)))
        rank_used = int(info.get("rank_used", 0))
    else:
        # Solve per column for matrix RHS to avoid writing a batched SVD path
        X = np.zeros((A.shape[1], b.shape[1]), dtype=A.dtype)
        rank_used = None
        for j in range(b.shape[1]):
            X[:, j], info = svd_solve(A, b[:, j], rank=rank, rcond=rcond, return_info=True)
            if rank_used is None:
                rank_used = int(info.get("rank_used", 0))
        x = X
        residual_norm = float(np.linalg.norm(A @ x - b))

    diag = LSQDiagnostics(
        method="svd_trunc",
        condition=c,
        time_ms=1000.0 * (time.perf_counter() - t0),
        residual_norm=residual_norm,
        rank_used=rank_used,
        notes="routed by condition number",
    )
    if not quiet:
        print(
            f"method=svd_trunc | cond={c:.2e} | time={diag.time_ms:.1f}ms | "
            f"res={residual_norm:.2e} | rank={rank_used}"
        )
    return x, diag

