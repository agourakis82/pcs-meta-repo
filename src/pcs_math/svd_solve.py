"""
SVD-based Linear System Solver with Truncation

Implementação estável de solução de sistemas lineares via SVD com truncamento
automático para problemas mal-condicionados. Inclui heurísticas de rank.

Author: PCS-HELIO Team
License: MIT
"""

import numpy as np
from typing import Tuple, Union, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


def truncated_svd(
    A: np.ndarray,
    rank: Optional[int] = None,
    rcond: Optional[float] = None,
    return_info: bool = False,
) -> Union[
    Tuple[np.ndarray, np.ndarray, np.ndarray, int],
    Tuple[np.ndarray, np.ndarray, np.ndarray, int, Dict[str, Any]],
]:
    """
    SVD truncada com determinação automática de rank.

    Implementa truncamento Eckart-Young para aproximação de baixo rank.
    Usa heurísticas de scree plot e rcond para determinar rank efetivo.

    Parameters
    ----------
    A : np.ndarray, shape (m, n)
        Matriz de entrada
    rank : int, optional
        Rank máximo desejado. Se None, determina automaticamente
    rcond : float, optional
        Threshold relativo para valores singulares. Se None, usa eps * max(m,n)
    return_info : bool, default=False
        Se True, retorna informações de diagnóstico

    Returns
    -------
    U : np.ndarray, shape (m, k)
        Vetores singulares esquerdos truncados
    S : np.ndarray, shape (k,)
        Valores singulares truncados
    Vt : np.ndarray, shape (k, n)
        Vetores singulares direitos truncados
    rank_eff : int
        Rank efetivo usado
    info : dict, optional
        Informações de diagnóstico (se return_info=True)

    Notes
    -----
    Aproximação de Eckart-Young: min ||A - A_k||_F onde A_k tem rank k.
    Heurística scree: detecta "cotovelo" na curva de valores singulares.

    Examples
    --------
    >>> A = np.random.randn(100, 50)
    >>> U, S, Vt, rank_eff = truncated_svd(A, rank=10)
    >>> A_approx = U @ np.diag(S) @ Vt
    >>> np.linalg.matrix_rank(A_approx) <= 10
    True
    """
    A = np.asarray(A, dtype=np.float64)
    m, n = A.shape

    # SVD completa
    U_full, S_full, Vt_full = np.linalg.svd(A, full_matrices=False)

    # Determinar rcond padrão
    if rcond is None:
        rcond = np.finfo(A.dtype).eps * max(m, n)

    # Filtrar valores singulares muito pequenos
    S_nonzero = S_full[S_full > rcond * S_full[0]]
    max_rank = len(S_nonzero)

    # Determinar rank efetivo
    if rank is None:
        # Default: keep full numerical rank (conservative, matches lstsq behavior)
        rank_eff = max_rank if max_rank > 0 else 0
    else:
        rank_eff = min(rank, max_rank)

    # Truncar SVD
    U = U_full[:, :rank_eff]
    S = S_full[:rank_eff]
    Vt = Vt_full[:rank_eff, :]

    # Log informações
    logger.debug(
        f"SVD truncada: A{A.shape} -> rank_eff={rank_eff}/{min(m,n)}, "
        f"σ_max={S[0]:.2e}, σ_min={S[-1]:.2e}, cond={S[0]/S[-1]:.2e}"
    )

    if return_info:
        info = {
            "singular_values_full": S_full,
            "rank_full": len(S_nonzero),
            "condition_number": S[0] / S[-1] if len(S) > 0 else np.inf,
            "truncation_error": np.linalg.norm(S_full[rank_eff:])
            if rank_eff < len(S_full)
            else 0.0,
            "rcond_used": rcond,
        }
        return U, S, Vt, rank_eff, info

    return U, S, Vt, rank_eff


def _estimate_rank_scree(S: np.ndarray, threshold: float = 0.1) -> int:
    """
    Estima rank via análise de scree plot dos valores singulares.

    Detecta "cotovelo" na curva de decaimento dos valores singulares.

    Parameters
    ----------
    S : np.ndarray
        Valores singulares em ordem decrescente
    threshold : float, default=0.1
        Threshold para detecção do cotovelo

    Returns
    -------
    rank : int
        Rank estimado
    """
    if len(S) <= 1:
        return len(S)

    # Normalizar valores singulares
    S_norm = S / S[0]

    # Calcular segunda derivada (curvatura)
    if len(S_norm) >= 3:
        # Aproximação de diferenças finitas para segunda derivada
        d2 = np.diff(S_norm, n=2)

        # Encontrar ponto de máxima curvatura (cotovelo)
        cotovelo = np.argmax(np.abs(d2)) + 1

        # Verificar se o cotovelo é significativo
        if S_norm[cotovelo] / S_norm[0] > threshold:
            return cotovelo + 1

    # Fallback: usar threshold simples
    rank_threshold = np.sum(S_norm > threshold)
    return max(1, rank_threshold)


def svd_solve(
    A: np.ndarray,
    b: np.ndarray,
    rank: Optional[int] = None,
    rcond: Optional[float] = None,
    return_info: bool = False,
) -> Union[np.ndarray, Tuple[np.ndarray, Dict[str, Any]]]:
    """
    Resolve sistema linear via SVD com truncamento automático.

    Método robusto para sistemas mal-condicionados usando pseudoinversa
    truncada. Implementa regularização automática via truncamento SVD.

    Parameters
    ----------
    A : np.ndarray, shape (m, n)
        Matriz de coeficientes
    b : np.ndarray, shape (m,) ou (m, k)
        Vetor(es) do lado direito
    rank : int, optional
        Rank máximo. Se None, determina automaticamente
    rcond : float, optional
        Threshold para valores singulares
    return_info : bool, default=False
        Se True, retorna informações de diagnóstico

    Returns
    -------
    x : np.ndarray, shape (n,) ou (n, k)
        Solução de mínimos quadrados regularizada
    info : dict, optional
        Informações de diagnóstico

    Notes
    -----
    Solução: x = V @ diag(1/σ) @ U^T @ b (truncada)
    Regularização automática via truncamento de valores singulares pequenos.
    Complexidade: O(mn min(m,n)) para SVD + O(rank * k) para solução.

    Examples
    --------
    >>> A = np.random.randn(100, 50)
    >>> A += 1e-10 * np.random.randn(100, 50)  # Ruído pequeno
    >>> x_true = np.random.randn(50)
    >>> b = A @ x_true
    >>> x_svd = svd_solve(A, b, rcond=1e-12)
    >>> np.linalg.norm(x_svd - x_true) < 1e-10
    True
    """
    A = np.asarray(A, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)

    m, n = A.shape

    if b.shape[0] != m:
        raise ValueError(f"Dimensões incompatíveis: A{A.shape}, b{b.shape}")

    logger.debug(f"SVD solve: A{A.shape}, b{b.shape}")

    # SVD truncada
    if return_info:
        U, S, Vt, rank_eff, svd_info = truncated_svd(A, rank, rcond, return_info=True)
    else:
        U, S, Vt, rank_eff = truncated_svd(A, rank, rcond, return_info=False)

    if rank_eff == 0:
        # Matriz nula
        if b.ndim == 1:
            x = np.zeros(n, dtype=A.dtype)
        else:
            x = np.zeros((n, b.shape[1]), dtype=A.dtype)

        if return_info:
            info = {"rank_used": 0, "residual_norm": np.linalg.norm(b)}
            if "svd_info" in locals():
                info.update(svd_info)
            return x, info
        return x

    # Resolver via pseudoinversa truncada: x = V @ diag(1/S) @ U^T @ b
    UtB = U.T @ b  # shape (rank_eff, ...)

    # Aplicar inversa dos valores singulares
    if b.ndim == 1:
        SinvUtB = UtB / S  # Broadcasting
    else:
        SinvUtB = UtB / S[:, np.newaxis]  # Broadcasting

    # Multiplicar por V^T
    x = Vt.T @ SinvUtB

    # Calcular informações de diagnóstico
    if return_info:
        residual = A @ x - b
        residual_norm = np.linalg.norm(residual)

        info = {
            "rank_used": rank_eff,
            "residual_norm": residual_norm,
            "solution_norm": np.linalg.norm(x),
        }

        if "svd_info" in locals():
            info.update(svd_info)

        logger.debug(
            f"SVD solve: rank={rank_eff}, residual={residual_norm:.2e}, "
            f"||x||={info['solution_norm']:.2e}"
        )

        return x, info

    return x


def svd_condition_number(A: np.ndarray) -> float:
    """
    Calcula número de condição via SVD.

    Parameters
    ----------
    A : np.ndarray
        Matriz de entrada

    Returns
    -------
    cond : float
        Número de condição σ_max / σ_min
    """
    A = np.asarray(A, dtype=np.float64)
    S = np.linalg.svd(A, compute_uv=False)

    # Filtrar valores singulares não-zero
    S_nonzero = S[S > 0]

    if len(S_nonzero) == 0:
        return np.inf

    return S_nonzero[0] / S_nonzero[-1]


def svd_rank(A: np.ndarray, rcond: Optional[float] = None) -> int:
    """
    Estima rank numérico via SVD.

    Parameters
    ----------
    A : np.ndarray
        Matriz de entrada
    rcond : float, optional
        Threshold relativo

    Returns
    -------
    rank : int
        Rank numérico estimado
    """
    A = np.asarray(A, dtype=np.float64)

    if rcond is None:
        rcond = np.finfo(A.dtype).eps * max(A.shape)

    S = np.linalg.svd(A, compute_uv=False)

    if len(S) == 0:
        return 0

    return np.sum(S > rcond * S[0])
