---
title: Numerical Core v4.3 — Stability, Solvers, and Quality Gates
author: PCS-HELIO Team
license: MIT
---

# Numerical Core v4.3

This guide summarizes the numerically stable linear algebra core added in v4.3. It provides practical recommendations, algorithmic rationale, and concise usage snippets that are deterministic and reproducible by default (float64).

## Why QR/Householder, When SVD, and When NNLS

- QR/Householder: Stable least-squares without squaring the condition number (avoid normal equations). Preferred on well-conditioned problems. Complexity O(m n^2).
- Truncated SVD: Robust against severe ill-conditioning; acts as an implicit regularizer by removing small singular directions (Eckart–Young). Complexity O(m n min(m, n)).
- NNLS via KKT: Enforces non-negativity constraints and validates KKT conditions numerically (primal, dual, complementary slackness). Complexity up to O(n^3) in worst case.

Rules of thumb:
- Use QR when cond(A) <= 1e3.
- Use truncated SVD when cond(A) > 1e3 or when numerical stability matters most.
- Use NNLS when constraints require x >= 0.

## Conjugate Gradient (CG) + Preconditioners

CG solves SPD systems Ax=b with per-iteration cost proportional to nnz(A). It is attractive for large sparse systems. Stopping criterion uses relative residual ||r||/||b|| <= tol.

Preconditioners (M ≈ A):
- Jacobi (diagonal): Cheap and robust; good when diagonal dominance holds.
- IC0 (incomplete Cholesky via ILU(0) fallback): Effective on sparse SPD matrices; requires SciPy.
- SSOR: Useful for banded structures; tunable with ω in (0, 2).

Heuristic: choose_preconditioner(auto) selects Jacobi for diagonal dominance, IC0 for SPD+sparse (SciPy), otherwise SSOR.

## Quality Gates for Linear Solvers

- condition_number(A, method="svd"): sigma_max / sigma_min (∞ if singular).
- choose_solver(A, prefer="qr", nonneg=False): returns one of {"qr", "svd_trunc", "nnls"}.

Routing logic:
- Nonnegativity -> NNLS.
- cond(A) > 1e3 -> truncated SVD.
- Otherwise -> QR (or SVD if prefer="svd").

## API Summary (float64 by default)

- QR (Householder): `householder_qr(A, mode)`; `solve_via_qr(A, b)`.
- SVD: `truncated_svd(A, rank, rcond)`; `svd_solve(A, b, rank, rcond)`.
- CG: `cg(A, b, M, tol, maxiter)` plus preconditioners in `preconditioners.py`.
- Kahan summation: `kahan_sum(x, axis, dtype)`; `kahan_dot`, `kahan_norm_squared`.
- NNLS: `nnls_kkt(A, b)` with KKT validation and optional SciPy comparison.
- Spectral embedding: `laplacian_matrix(W, norm)`; `fiedler_vector(W)`; `spectral_embedding(W, k)`.
- Wrapper: `solve_least_squares(A, b, constraints, prefer)` returns solution and diagnostics.

## Spectral Embedding (Fiedler Vector)

- Laplacians: unnormalized (L=D-W), symmetric-normalized (L=I-D^{-1/2}WD^{-1/2}), and random-walk.
- Fiedler vector: second smallest eigenvector of L; useful for partitioning/ordering. Implementation normalizes columns and fixes sign for determinism.
- Supports dense and sparse matrices; uses SciPy eigsh when available, otherwise NumPy eigh.

## Determinism and Precision

- All routines use float64 unless overridden.
- Randomness only used for test/demo data; set seeds for reproducibility.
- Kahan summation reduces accumulation error in wide-dynamic-range sums.

## Examples

QR vs SVD (ill-conditioned):

```python
import numpy as np
from src.pcs_wrappers.least_squares import solve_least_squares

np.random.seed(0)
A = np.random.randn(50, 10)
A[:, -1] = A[:, 0] + 1e-12 * np.random.randn(50)  # near-collinear
x_true = np.random.randn(10)
b = A @ x_true

x, diag = solve_least_squares(A, b, prefer="qr")
print(diag.method, diag.condition, diag.residual_norm)
```

Spectral embedding (two blocks):

```python
import numpy as np
from src.pcs_graph.spectral_embedding import spectral_embedding

W = np.zeros((10+10, 20))
W[:10, :10] = 1.0
W[10:, 10:] = 1.0
np.fill_diagonal(W, 0.0)
Y, info = spectral_embedding(W, k=2, return_info=True)
```

## FAQ (for clinical team)

- Why avoid normal equations? They square the condition number and can destroy accuracy.
- Why truncated SVD? It automatically dampens directions dominated by noise.
- Why preconditioning? It reshapes the problem so CG converges in fewer steps.
- Why Kahan summation? It keeps track of lost low-order bits to reduce rounding error.

## Performance Notes

- QR/SVD are O(n^3) for dense problems; prefer CG with preconditioning for large, sparse SPD systems (O(k·nnz)).
- Spectral methods rely on eigen-solves; for sparse graphs, `eigsh` is preferred.

All code avoids exotic dependencies and runs with NumPy alone; SciPy, when present, accelerates sparse paths and NNLS comparison.

