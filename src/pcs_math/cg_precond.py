"""
Conjugate Gradient Method with Preconditioning

Implementação do método do Gradiente Conjugado com pré-condicionadores
para sistemas lineares simétricos positivos definidos.

Author: PCS-HELIO Team
License: MIT
"""

import numpy as np
from typing import Union, Optional, Dict, Any, Tuple
import logging

try:
    import scipy.sparse as sp
    from scipy.sparse.linalg import LinearOperator

    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    # Usar fallback do módulo preconditioners
    from .preconditioners import LinearOperator

logger = logging.getLogger(__name__)


def cg(
    A: Union[np.ndarray, LinearOperator],
    b: np.ndarray,
    x0: Optional[np.ndarray] = None,
    M: Optional[LinearOperator] = None,
    tol: float = 1e-8,
    maxiter: Optional[int] = None,
    return_info: bool = False,
) -> Union[np.ndarray, Tuple[np.ndarray, Dict[str, Any]]]:
    """
    Método do Gradiente Conjugado com pré-condicionamento.

    Resolve Ax = b onde A é simétrica positiva definida.
    Opcionalmente usa pré-condicionador M ≈ A para acelerar convergência.

    Parameters
    ----------
    A : np.ndarray, scipy.sparse matrix, ou LinearOperator
        Matriz do sistema (deve ser SPD)
    b : np.ndarray, shape (n,)
        Vetor do lado direito
    x0 : np.ndarray, optional
        Estimativa inicial. Se None, usa vetor zero
    M : LinearOperator, optional
        Pré-condicionador M^(-1). Se None, sem pré-condicionamento
    tol : float, default=1e-8
        Tolerância para convergência: ||r||/||b|| <= tol
    maxiter : int, optional
        Número máximo de iterações. Se None, usa n
    return_info : bool, default=False
        Se True, retorna informações de convergência

    Returns
    -------
    x : np.ndarray
        Solução aproximada
    info : dict, optional
        Informações de convergência (se return_info=True)

    Notes
    -----
    Algoritmo CG pré-condicionado:
    1. r₀ = b - Ax₀, z₀ = M⁻¹r₀, p₀ = z₀
    2. Para k = 0, 1, 2, ...:
       - αₖ = (rₖᵀzₖ) / (pₖᵀApₖ)
       - xₖ₊₁ = xₖ + αₖpₖ
       - rₖ₊₁ = rₖ - αₖApₖ
       - zₖ₊₁ = M⁻¹rₖ₊₁
       - βₖ = (rₖ₊₁ᵀzₖ₊₁) / (rₖᵀzₖ)
       - pₖ₊₁ = zₖ₊₁ + βₖpₖ

    Complexidade: O(k·nnz(A)) onde k é número de iterações.

    Examples
    --------
    >>> # Sistema SPD simples
    >>> A = np.array([[4, 1], [1, 3]])
    >>> b = np.array([1, 2])
    >>> x = cg(A, b)
    >>> np.allclose(A @ x, b)
    True

    >>> # Com pré-condicionador
    >>> from .preconditioners import jacobi_precond
    >>> M_inv = jacobi_precond(A)
    >>> x, info = cg(A, b, M=M_inv, return_info=True)
    >>> info['iterations'] <= 2  # Converge rapidamente
    True
    """
    b = np.asarray(b, dtype=np.float64)
    n = len(b)

    # Estimativa inicial
    if x0 is None:
        x = np.zeros(n, dtype=np.float64)
    else:
        x = np.asarray(x0, dtype=np.float64).copy()

    # Número máximo de iterações
    if maxiter is None:
        maxiter = n

    # Função para multiplicação matriz-vetor
    if hasattr(A, "matvec"):
        matvec = A.matvec
    elif HAS_SCIPY and sp.issparse(A):
        matvec = lambda v: A @ v
    else:
        A_array = np.asarray(A)
        matvec = lambda v: A_array @ v

    # Função para pré-condicionamento
    if M is None:
        precond = lambda v: v  # Identidade
    else:
        precond = M.matvec if hasattr(M, "matvec") else lambda v: M @ v

    # Inicialização
    r = b - matvec(x)  # Resíduo inicial
    z = precond(r)  # Resíduo pré-condicionado
    p = z.copy()  # Direção de busca inicial

    # Norma inicial para critério de parada
    b_norm = np.linalg.norm(b)
    if b_norm == 0:
        # Lado direito é zero
        if return_info:
            info = {
                "iterations": 0,
                "residual_norm": 0.0,
                "relative_residual": 0.0,
                "converged": True,
            }
            return np.zeros(n), info
        return np.zeros(n)

    # Histórico de convergência
    residual_norms = []

    # Produto interno inicial
    rz_old = np.dot(r, z)

    logger.debug(f"CG: n={n}, tol={tol:.2e}, maxiter={maxiter}")

    # Iterações CG
    for k in range(maxiter):
        # Calcular Ap
        Ap = matvec(p)

        # Produto interno p^T A p
        pAp = np.dot(p, Ap)

        if pAp <= 0:
            logger.warning(f"CG: pAp={pAp:.2e} <= 0, matriz não é SPD")
            break

        # Tamanho do passo
        alpha = rz_old / pAp

        # Atualizar solução
        x += alpha * p

        # Atualizar resíduo
        r -= alpha * Ap

        # Verificar convergência
        r_norm = np.linalg.norm(r)
        rel_residual = r_norm / b_norm
        residual_norms.append(r_norm)

        logger.debug(f"CG iter {k}: ||r||={r_norm:.2e}, rel={rel_residual:.2e}")

        if rel_residual <= tol:
            logger.debug(f"CG convergiu em {k+1} iterações")
            converged = True
            break

        # Pré-condicionar novo resíduo
        z = precond(r)

        # Produto interno para β
        rz_new = np.dot(r, z)

        # Coeficiente β
        beta = rz_new / rz_old

        # Atualizar direção de busca
        p = z + beta * p

        # Preparar para próxima iteração
        rz_old = rz_new
    else:
        # Não convergiu
        logger.warning(
            f"CG não convergiu em {maxiter} iterações, "
            f"resíduo relativo: {rel_residual:.2e}"
        )
        converged = False

    if return_info:
        info = {
            "iterations": k + 1 if converged else maxiter,
            "residual_norm": r_norm,
            "relative_residual": rel_residual,
            "converged": converged,
            "residual_history": np.array(residual_norms),
        }
        return x, info

    return x


def cg_solve_multiple(
    A: Union[np.ndarray, LinearOperator],
    B: np.ndarray,
    M: Optional[LinearOperator] = None,
    tol: float = 1e-8,
    maxiter: Optional[int] = None,
) -> np.ndarray:
    """
    Resolve múltiplos sistemas AX = B usando CG.

    Parameters
    ----------
    A : matriz do sistema
    B : np.ndarray, shape (n, k)
        Múltiplos lados direitos
    M : pré-condicionador opcional
    tol, maxiter : parâmetros CG

    Returns
    -------
    X : np.ndarray, shape (n, k)
        Soluções para cada sistema
    """
    B = np.asarray(B)
    if B.ndim == 1:
        return cg(A, B, M=M, tol=tol, maxiter=maxiter)

    n, k = B.shape
    X = np.zeros((n, k))

    for i in range(k):
        X[:, i] = cg(A, B[:, i], M=M, tol=tol, maxiter=maxiter)

    return X


def cg_least_squares(
    A: np.ndarray,
    b: np.ndarray,
    M: Optional[LinearOperator] = None,
    tol: float = 1e-8,
    maxiter: Optional[int] = None,
) -> np.ndarray:
    """
    Resolve problema de mínimos quadrados min ||Ax - b||² usando CG.

    Transforma em sistema normal A^T A x = A^T b e aplica CG.

    Parameters
    ----------
    A : np.ndarray, shape (m, n)
        Matriz de coeficientes
    b : np.ndarray, shape (m,)
        Vetor do lado direito
    M : pré-condicionador para A^T A
    tol, maxiter : parâmetros CG

    Returns
    -------
    x : np.ndarray, shape (n,)
        Solução de mínimos quadrados

    Notes
    -----
    Cuidado: A^T A pode ser mal-condicionada mesmo se A for bem-condicionada.
    Para problemas mal-condicionados, prefira QR ou SVD.
    """
    A = np.asarray(A)
    b = np.asarray(b)

    # Formar sistema normal
    AtA = A.T @ A
    Atb = A.T @ b

    logger.debug(f"CG least squares: A{A.shape} -> AtA{AtA.shape}")

    # Resolver usando CG
    return cg(AtA, Atb, M=M, tol=tol, maxiter=maxiter)


def estimate_condition_number_cg(
    A: Union[np.ndarray, LinearOperator], n_samples: int = 10, maxiter: int = 50
) -> float:
    """
    Estima número de condição usando iterações CG.

    Usa o fato de que CG converge em O(√κ) iterações onde κ = cond(A).

    Parameters
    ----------
    A : matriz do sistema
    n_samples : número de vetores aleatórios para teste
    maxiter : máximo de iterações CG

    Returns
    -------
    cond_est : float
        Estimativa do número de condição
    """
    if hasattr(A, "shape"):
        n = A.shape[0]
    else:
        raise ValueError("Não é possível determinar tamanho de A")

    convergence_rates = []

    for _ in range(n_samples):
        # Vetor aleatório
        b = np.random.randn(n)

        # Executar CG com informações
        try:
            _, info = cg(A, b, tol=1e-12, maxiter=maxiter, return_info=True)

            if info["converged"] and len(info["residual_history"]) > 1:
                # Estimar taxa de convergência
                residuals = info["residual_history"]
                # Taxa média de redução por iteração
                rate = (residuals[-1] / residuals[0]) ** (1.0 / len(residuals))
                convergence_rates.append(rate)
        except:
            continue

    if not convergence_rates:
        return np.inf

    # Estimar número de condição baseado na taxa de convergência
    avg_rate = np.mean(convergence_rates)

    # Heurística: κ ≈ ((1 + rate) / (1 - rate))²
    if avg_rate >= 1:
        return np.inf

    cond_est = ((1 + avg_rate) / (1 - avg_rate)) ** 2

    return cond_est
