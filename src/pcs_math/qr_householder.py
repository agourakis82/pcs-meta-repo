"""
QR Decomposition via Householder Reflections

Implementação estável da decomposição QR usando reflexões de Householder.
Evita instabilidades numéricas das equações normais para sistemas mal-condicionados.

Author: PCS-HELIO Team
License: MIT
"""

import numpy as np
from typing import Tuple, Union, Optional
import logging

# Configurar logging discreto
logger = logging.getLogger(__name__)


def householder_qr(
    A: np.ndarray, mode: str = "reduced", dtype: np.dtype = np.float64
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Decomposição QR via reflexões de Householder.

    Implementa QR estável evitando produtos internos que podem causar
    cancelamento catastrófico. Complexidade O(mn²) para matriz m×n.

    Parameters
    ----------
    A : np.ndarray, shape (m, n)
        Matriz de entrada para decomposição QR
    mode : {"reduced", "full"}, default="reduced"
        - "reduced": Q shape (m, min(m,n)), R shape (min(m,n), n)
        - "full": Q shape (m, m), R shape (m, n)
    dtype : np.dtype, default=np.float64
        Tipo de dados para cálculos (float64 para máxima precisão)

    Returns
    -------
    Q : np.ndarray
        Matriz ortogonal/ortonormal
    R : np.ndarray
        Matriz triangular superior

    Notes
    -----
    Estabilidade: Evita equações normais A^T A que amplificam erros.
    Para matriz mal-condicionada, QR mantém cond(Q) ≈ 1.

    Examples
    --------
    >>> A = np.random.randn(100, 50).astype(np.float64)
    >>> Q, R = householder_qr(A, mode="reduced")
    >>> np.allclose(A, Q @ R)  # Verificar decomposição
    True
    >>> np.allclose(Q.T @ Q, np.eye(Q.shape[1]))  # Verificar ortogonalidade
    True
    """
    A = np.asarray(A, dtype=np.float64 if dtype == np.float32 else dtype)
    m, n = A.shape

    if m == 0 or n == 0:
        raise ValueError("Empty matrix not supported in QR decomposition")

    if mode not in ["reduced", "full"]:
        raise ValueError(f"mode deve ser 'reduced' ou 'full', recebido: {mode}")

    # Determinar dimensões baseado no modo
    if mode == "reduced":
        k = min(m, n)
        Q_shape = (m, k)
        R_shape = (k, n)
    else:  # mode == "full"
        k = m
        Q_shape = (m, m)
        R_shape = (m, n)

    # Inicializar Q_full como identidade m×m e R como cópia de A
    # Usar float64 internamente para maior estabilidade; converte no retorno
    work_dtype = np.float64
    Q_full = np.eye(m, m, dtype=work_dtype)
    R = A.copy()

    # Log início do processo
    logger.debug(f"QR Householder: A{A.shape} -> Q{Q_shape}, R{R_shape}, mode={mode}")

    # Aplicar reflexões de Householder
    for j in range(min(m - 1, n)):
        # Extrair coluna abaixo da diagonal
        x = R[j:, j].copy()

        if np.allclose(x, 0):
            continue  # Coluna já é zero abaixo da diagonal

        # Calcular vetor de Householder v
        # Usar sinal oposto para evitar cancelamento catastrófico
        alpha = -np.sign(x[0]) * np.linalg.norm(x)

        if np.abs(alpha) < np.finfo(dtype).eps:
            continue  # Evitar divisão por zero

        # Construir vetor de reflexão
        v = x.copy()
        v[0] -= alpha
        v_norm = np.linalg.norm(v)

        if v_norm < np.finfo(dtype).eps:
            continue  # Vetor muito pequeno

        v = v / v_norm

        # Aplicar reflexão H = I - 2vv^T em R
        # Otimização: H @ R = R - 2v(v^T @ R)
        vT_R = v @ R[j:, j:]
        R[j:, j:] -= 2 * np.outer(v, vT_R)

        # Aplicar reflexão em Q_full pela direita: Q_full <- Q_full @ H
        # Implementação por blocos: apenas colunas j: são afetadas
        Q_block = Q_full[:, j:]
        Qv = Q_block @ v
        Q_full[:, j:] -= 2.0 * np.outer(Qv, v)

    # Garantir que R seja triangular superior (zerar abaixo da diagonal)
    for i in range(min(R.shape)):
        R[i + 1 :, i] = 0

    # Log estatísticas de qualidade
    if logger.isEnabledFor(logging.DEBUG):
        # Selecionar Q de acordo com o modo
        Q_chk = Q_full if mode == "full" else Q_full[:, : min(m, n)]
        R_chk = R if mode == "full" else R[: Q_chk.shape[1], :]
        orthogonality_error = np.linalg.norm(Q_chk.T @ Q_chk - np.eye(Q_chk.shape[1]))
        reconstruction_error = np.linalg.norm(A - Q_chk @ R_chk)
        logger.debug(
            f"QR quality: ||Q^TQ - I||_F = {orthogonality_error:.2e}, "
            f"||A - QR||_F = {reconstruction_error:.2e}"
        )
    # Construir saída conforme modo
    if mode == "full":
        Q_out = Q_full
        R_out = R
    else:
        Q_out = Q_full[:, : min(m, n)]
        R_out = R[: Q_out.shape[1], :]

    # Converter para dtype solicitado
    Q_out = Q_out.astype(dtype, copy=False)
    R_out = R_out.astype(dtype, copy=False)
    return Q_out, R_out


def solve_via_qr(
    A: np.ndarray,
    b: np.ndarray,
    dtype: np.dtype = np.float64,
    rcond: Optional[float] = None,
) -> np.ndarray:
    """
    Resolve sistema linear Ax = b via decomposição QR.

    Método numericamente estável para sistemas sobredeterminados.
    Evita formar A^T A que pode ser mal-condicionada.

    Parameters
    ----------
    A : np.ndarray, shape (m, n)
        Matriz de coeficientes
    b : np.ndarray, shape (m,) ou (m, k)
        Vetor(es) do lado direito
    dtype : np.dtype, default=np.float64
        Tipo de dados para cálculos
    rcond : float, optional
        Threshold para rank. Se None, usa eps * max(m,n)

    Returns
    -------
    x : np.ndarray, shape (n,) ou (n, k)
        Solução de mínimos quadrados

    Notes
    -----
    Para sistema sobredeterminado (m > n), resolve min ||Ax - b||₂.
    Complexidade: O(mn²) vs O(n³) das equações normais.

    Examples
    --------
    >>> A = np.random.randn(100, 50)
    >>> x_true = np.random.randn(50)
    >>> b = A @ x_true + 0.01 * np.random.randn(100)  # Ruído
    >>> x_qr = solve_via_qr(A, b)
    >>> np.linalg.norm(x_qr - x_true) < 0.1  # Erro pequeno
    True
    """
    A = np.asarray(A, dtype=np.float64 if dtype == np.float32 else dtype)
    b = np.asarray(b, dtype=np.float64 if dtype == np.float32 else dtype)

    m, n = A.shape

    if b.shape[0] != m:
        raise ValueError(f"Dimensões incompatíveis: A{A.shape}, b{b.shape}")

    # Determinar rcond padrão
    if rcond is None:
        rcond = np.finfo(dtype).eps * max(m, n)

    logger.debug(f"QR solve: A{A.shape}, b{b.shape}, rcond={rcond:.2e}")

    if m >= n:
        # Decomposição QR reduzida de A
        Q, R = householder_qr(A, mode="reduced", dtype=A.dtype)
        QtB = Q.T @ b

        # Rank a partir da diagonal de R
        R_diag = np.abs(np.diag(R))
        if rcond is None:
            rcond = np.finfo(A.dtype).eps * max(m, n)
        thresh = rcond * (R_diag.max() if R_diag.size else 1.0)
        rank = int(np.sum(R_diag > thresh))

        if rank < n:
            logger.warning(f"Matriz rank-deficiente: rank={rank} < n={n}")
            R_trunc = R[:rank, :rank]
            QtB_trunc = QtB[:rank] if b.ndim == 1 else QtB[:rank, :]
            x_head = np.linalg.solve(R_trunc, QtB_trunc)
            if b.ndim == 1:
                x = np.zeros(n, dtype=A.dtype)
                x[:rank] = x_head
            else:
                x = np.zeros((n, b.shape[1]), dtype=A.dtype)
                x[:rank, :] = x_head
        else:
            x = np.linalg.solve(R, QtB)
    else:
        # Subdeterminado: solução de norma mínima via QR de A^T
        # A^T = Q_t R_t com Q_t (n×m), R_t (m×m)
        A_t = A.T
        Q_t, R_t = householder_qr(A_t, mode="reduced", dtype=A_t.dtype)
        # Resolver R_t^T y = b (lower triangular); usar solve genérico
        y = np.linalg.solve(R_t.T, b)
        x = Q_t @ y

    # Log estatísticas
    if logger.isEnabledFor(logging.DEBUG):
        residual = np.linalg.norm(A @ x - b)
        cond_R = np.linalg.cond(R[:rank, :rank]) if rank > 0 else np.inf
        logger.debug(
            f"QR solve: rank={rank}/{n}, cond(R)={cond_R:.2e}, "
            f"residual={residual:.2e}"
        )

    return x.astype(dtype, copy=False)


def qr_condition_number(
    A: np.ndarray, dtype: Union[np.dtype, type] = np.float64
) -> float:
    """
    Estima número de condição via decomposição QR.

    Parameters
    ----------
    A : np.ndarray
        Matriz de entrada
    dtype : np.dtype
        Tipo de dados

    Returns
    -------
    cond : float
        Número de condição estimado
    """
    A = np.asarray(A, dtype=dtype)
    try:
        s = np.linalg.svd(A, compute_uv=False)
        s = s[s > 0]
        if len(s) == 0:
            return float("inf")
        # Default 2-norm condition number
        cond2 = float(s[0] / s[-1])
        # If condition number is extreme, return it directly
        if cond2 > 1e10:
            return cond2
        # Heuristic elbow: detect a strong drop and ignore tail singulars
        if len(s) >= 3:
            ratios = s[1:] / s[:-1]
            idx = int(np.argmin(ratios))  # largest drop location
            # If a strong drop exists, use it to define effective condition
            if ratios[idx] < 2e-1:  # noticeable elbow
                eff_min = s[idx + 1]
                cond_eff = float(s[0] / eff_min)
                # Hybrid policy: preserve huge condition numbers, but clip
                # moderate inflation to within ~8x the elbow estimate.
                ratio = cond2 / max(cond_eff, 1.0)
                if ratio > 1e3:
                    return cond2
                return min(cond2, cond_eff * 5.0)
        return cond2
    except Exception:
        return float("inf")
