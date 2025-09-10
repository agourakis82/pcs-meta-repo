"""
Tests for spectral embedding and Fiedler vector.

Validates orthogonality, sign consistency, and basic cluster separability.

Author: PCS-HELIO Team
License: MIT
"""

import numpy as np

try:
    from src.pcs_graph.spectral_embedding import (
        laplacian_matrix,
        fiedler_vector,
        spectral_embedding,
    )
except ImportError:
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from src.pcs_graph.spectral_embedding import (
        laplacian_matrix,
        fiedler_vector,
        spectral_embedding,
    )


def make_block_graph(n1: int, n2: int, w_intra: float = 1.0, w_inter: float = 0.05) -> np.ndarray:
    n = n1 + n2
    W = np.zeros((n, n), dtype=np.float64)
    # Intra-block dense weights
    W[:n1, :n1] = w_intra
    W[n1:, n1:] = w_intra
    # Small inter-block connections
    W[:n1, n1:] = w_inter
    W[n1:, :n1] = w_inter
    np.fill_diagonal(W, 0.0)
    return W


def test_fiedler_vector_basic_properties():
    n = 20
    # Path graph (line)
    W = np.zeros((n, n))
    for i in range(n - 1):
        W[i, i + 1] = 1.0
        W[i + 1, i] = 1.0
    v2 = fiedler_vector(W, norm="sym", solver="eigh", k=2)
    # Orthogonal to constant vector in normalized sense
    c = np.ones(n)
    dot = float(np.dot(v2, c))
    # Not strictly zero for finite n, but should be small
    assert abs(dot) < 1e-6
    # Unit norm
    assert abs(np.linalg.norm(v2) - 1.0) < 1e-12


def test_spectral_embedding_separates_blocks():
    n1, n2 = 10, 12
    W = make_block_graph(n1, n2, w_intra=1.0, w_inter=0.01)
    Y, info = spectral_embedding(W, k=2, norm="sym", solver="eigh", return_info=True)
    # Use first nontrivial component (Fiedler) to separate
    v = Y[:, 0]
    # Classify by sign (robust to scaling)
    cut = np.median(v)
    labels = (v > cut).astype(int)
    # Expect clear separation: all in first block similar sign
    purity_1 = max(np.mean(labels[:n1] == 0), np.mean(labels[:n1] == 1))
    purity_2 = max(np.mean(labels[n1:] == 0), np.mean(labels[n1:] == 1))
    assert purity_1 > 0.8 and purity_2 > 0.8
