"""
Spectral Embedding and Fiedler Vector

Numerically stable implementation of graph Laplacians, the Fiedler vector,
and spectral embeddings suitable for small to mid-size problems. Supports
dense and sparse affinity matrices, with symmetric normalization by default.

Author: PCS-HELIO Team
License: MIT
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional, Tuple, Dict, Any, Union
import logging
import numpy as np

logger = logging.getLogger(__name__)

try:  # SciPy is optional
    import scipy.sparse as sp
    import scipy.sparse.linalg as spla

    HAS_SCIPY = True
except Exception:  # pragma: no cover - optional dependency
    HAS_SCIPY = False
    sp = None  # type: ignore
    spla = None  # type: ignore


ArrayLike = Union[np.ndarray, "sp.spmatrix"]


def _to_symmetric(W: np.ndarray, tol: float = 1e-12) -> np.ndarray:
    """
    Ensure symmetry by averaging with its transpose if needed.

    Parameters
    ----------
    W : np.ndarray
        Weight/affinity matrix.
    tol : float
        Symmetry tolerance.

    Returns
    -------
    Wsym : np.ndarray
        Symmetrized matrix.
    """
    if np.allclose(W, W.T, rtol=1e-10, atol=tol):
        return W
    return 0.5 * (W + W.T)


def laplacian_matrix(
    W: ArrayLike, norm: Literal["none", "sym", "rw"] = "sym", dtype: np.dtype = np.float64
) -> ArrayLike:
    """
    Build graph Laplacian from an affinity/weight matrix.

    Parameters
    ----------
    W : array_like (n,n) dense or sparse
        Symmetric affinity/weight matrix (nonnegative weights). If not strictly
        symmetric, it will be symmetrized as (W+Wᵀ)/2.
    norm : {"none", "sym", "rw"}, default="sym"
        Laplacian normalization:
        - none: L = D - W
        - sym: L = I - D^{-1/2} W D^{-1/2}
        - rw:  L = I - D^{-1} W
    dtype : np.dtype
        Floating dtype (default float64).

    Returns
    -------
    L : array_like
        Laplacian matrix in the same density family as W.

    Notes
    -----
    For numerical stability, degrees smaller than eps are clipped.
    """
    if HAS_SCIPY and sp.issparse(W):
        W = W.tocsr().astype(dtype)
        d = np.asarray(W.sum(axis=1)).ravel()
        d = np.maximum(d, np.finfo(dtype).eps)
        if norm == "none":
            D = sp.diags(d, format="csr")
            L = D - W
        elif norm == "sym":
            d_inv_sqrt = 1.0 / np.sqrt(d)
            D_inv_sqrt = sp.diags(d_inv_sqrt, format="csr")
            # L = I - D^{-1/2} W D^{-1/2}
            I = sp.eye(W.shape[0], dtype=dtype, format="csr")
            L = I - (D_inv_sqrt @ W @ D_inv_sqrt)
        elif norm == "rw":
            d_inv = 1.0 / d
            D_inv = sp.diags(d_inv, format="csr")
            I = sp.eye(W.shape[0], dtype=dtype, format="csr")
            L = I - (D_inv @ W)
        else:
            raise ValueError("norm must be one of {'none','sym','rw'}")
        return L

    # Dense path
    W = np.asarray(W, dtype=dtype)
    W = _to_symmetric(W)
    d = np.sum(W, axis=1)
    d = np.maximum(d, np.finfo(dtype).eps)
    if norm == "none":
        D = np.diag(d)
        return D - W
    elif norm == "sym":
        D_inv_sqrt = np.diag(1.0 / np.sqrt(d))
        n = W.shape[0]
        return np.eye(n, dtype=dtype) - D_inv_sqrt @ W @ D_inv_sqrt
    elif norm == "rw":
        D_inv = np.diag(1.0 / d)
        n = W.shape[0]
        return np.eye(n, dtype=dtype) - D_inv @ W
    else:
        raise ValueError("norm must be one of {'none','sym','rw'}")


def _connected_components_dense(W: np.ndarray) -> np.ndarray:
    """
    Connected components labels for a dense symmetric adjacency matrix.
    Uses DFS on thresholded edges (W>0).
    """
    n = W.shape[0]
    visited = np.zeros(n, dtype=bool)
    comp = -np.ones(n, dtype=int)
    adj = W > 0

    cid = 0
    for i in range(n):
        if not visited[i]:
            stack = [i]
            while stack:
                u = stack.pop()
                if visited[u]:
                    continue
                visited[u] = True
                comp[u] = cid
                neighbors = np.where(adj[u])[0]
                for v in neighbors:
                    if not visited[v]:
                        stack.append(v)
            cid += 1
    return comp


def fiedler_vector(
    W: ArrayLike,
    norm: Literal["none", "sym", "rw"] = "sym",
    solver: Literal["eigsh", "eigh"] = "eigsh",
    k: int = 2,
    dtype: np.dtype = np.float64,
) -> np.ndarray:
    """
    Compute the Fiedler vector (second smallest eigenvector) of Laplacian.

    Parameters
    ----------
    W : array_like (n,n)
        Affinity/weight matrix (dense or sparse). If the graph has multiple
        connected components, the Fiedler vector is defined per component; the
        implementation returns a vector whose entries are concatenated by
        component order.
    norm : {"none", "sym", "rw"}, default="sym"
        Laplacian normalization.
    solver : {"eigsh", "eigh"}, default="eigsh"
        Eigen-solver. If SciPy is unavailable or W is small/dense, falls back
        to dense `eigh`.
    k : int, default=2
        Number of smallest eigenpairs to compute (>=2 to access Fiedler).
    dtype : np.dtype
        Floating dtype (default float64).

    Returns
    -------
    v2 : np.ndarray, shape (n,)
        The Fiedler vector (normalized to unit norm). Sign is arbitrary.

    Notes
    -----
    For stability, the eigenvectors are normalized to unit 2-norm and, when
    possible, oriented such that the majority of entries are positive.
    """
    if k < 2:
        raise ValueError("k must be >= 2 to extract the Fiedler vector")

    # Build Laplacian
    L = laplacian_matrix(W, norm=norm, dtype=dtype)

    # Choose solver path
    if HAS_SCIPY and sp.issparse(W) and solver == "eigsh":
        n = W.shape[0]
        # Smallest eigenpairs of symmetric positive semi-definite Laplacian
        vals, vecs = spla.eigsh(L, k=k, which="SM")  # type: ignore[arg-type]
    else:
        # Dense path
        Ld = L.toarray() if (HAS_SCIPY and sp.issparse(L)) else np.asarray(L)
        vals, vecs = np.linalg.eigh(Ld)
        # take k smallest
        idx = np.argsort(vals)[:k]
        vals = vals[idx]
        vecs = vecs[:, idx]

    # Fiedler is second eigenvector (skip the trivial all-ones/nullspace)
    v2 = np.asarray(vecs[:, 1], dtype=dtype)

    # Normalize and orient sign for determinism
    nrm = np.linalg.norm(v2)
    if nrm > 0:
        v2 = v2 / nrm
    if np.sum(v2) < 0:  # flip sign so that mean is non-negative
        v2 = -v2

    return v2


def spectral_embedding(
    W: ArrayLike,
    k: int = 2,
    norm: Literal["none", "sym", "rw"] = "sym",
    solver: Literal["eigsh", "eigh"] = "eigsh",
    return_info: bool = False,
    dtype: np.dtype = np.float64,
) -> Union[np.ndarray, Tuple[np.ndarray, Dict[str, Any]]]:
    """
    Compute a k-dimensional spectral embedding from the Laplacian.

    Parameters
    ----------
    W : array_like (n,n)
        Affinity/weight matrix. May be dense or sparse.
    k : int, default=2
        Number of embedding dimensions (smallest nontrivial eigenvectors).
    norm : {"none", "sym", "rw"}, default="sym"
        Laplacian normalization.
    solver : {"eigsh", "eigh"}, default="eigsh"
        Eigen-solver selection.
    return_info : bool, default=False
        If True, returns additional diagnostics.
    dtype : np.dtype
        Floating dtype (default float64).

    Returns
    -------
    Y : np.ndarray, shape (n, k)
        Embedding coordinates using the k smallest nontrivial eigenvectors.
    info : dict, optional
        Diagnostics including eigenvalues and condition hints.

    Notes
    -----
    - The trivial eigenvector (all-ones) is discarded; k refers to nontrivial
      vectors. For example, for k=2 the output contains the Fiedler vector as
      its first column.
    - For disconnected graphs, the Laplacian has multiple zero eigenvalues; in
      that case, useful embeddings are computed per component implicitly by the
      eigen-solver. This routine does not reorder nodes; it returns raw vectors
      aligned with the input ordering.
    """
    if k < 1:
        raise ValueError("k must be >= 1")

    L = laplacian_matrix(W, norm=norm, dtype=dtype)

    if HAS_SCIPY and sp.issparse(W) and solver == "eigsh":
        # Request (k+1) smallest to drop the trivial one
        vals, vecs = spla.eigsh(L, k=min(W.shape[0] - 1, k + 1), which="SM")  # type: ignore[arg-type]
        idx = np.argsort(vals)
        vals = vals[idx]
        vecs = vecs[:, idx]
        # Drop the first (trivial) eigenvector
        U = vecs[:, 1 : k + 1]
        evals = vals[1 : k + 1]
    else:
        Ld = L.toarray() if (HAS_SCIPY and sp.issparse(L)) else np.asarray(L)
        vals, vecs = np.linalg.eigh(Ld)
        idx = np.argsort(vals)
        vals = vals[idx]
        vecs = vecs[:, idx]
        U = vecs[:, 1 : k + 1]
        evals = vals[1 : k + 1]

    # Normalize columns, fix sign for determinism
    Y = np.asarray(U, dtype=dtype).copy()
    for j in range(Y.shape[1]):
        col = Y[:, j]
        nrm = np.linalg.norm(col)
        if nrm > 0:
            col = col / nrm
        if np.sum(col) < 0:
            col = -col
        Y[:, j] = col

    if return_info:
        info = {"eigenvalues": np.asarray(evals, dtype=dtype), "norm": norm, "solver": solver}
        return Y, info

    return Y

