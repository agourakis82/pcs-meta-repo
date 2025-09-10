"""
Preconditioners for Iterative Linear Solvers

Implementação de pré-condicionadores para acelerar convergência
de métodos iterativos como Gradiente Conjugado.

Author: PCS-HELIO Team
License: MIT
"""

import numpy as np
from typing import Union, Optional
import logging

try:
    import scipy.sparse as sp
    import scipy.sparse.linalg as spla
    from scipy.sparse.linalg import LinearOperator

    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

    # Fallback simples para LinearOperator
    class LinearOperator:
        def __init__(self, shape, matvec, dtype=np.float64):
            self.shape = shape
            self.dtype = dtype
            self._matvec = matvec

        def matvec(self, x):
            return self._matvec(x)

        def __matmul__(self, x):
            return self.matvec(x)


logger = logging.getLogger(__name__)


def jacobi_precond(A: Union[np.ndarray, "sp.spmatrix"]) -> LinearOperator:
    """
    Pré-condicionador de Jacobi (diagonal).

    M = diag(A), aplicação: M^(-1) x = x / diag(A)
    Simples e eficiente para matrizes com diagonal dominante.

    Parameters
    ----------
    A : np.ndarray ou scipy.sparse matrix
        Matriz do sistema linear

    Returns
    -------
    M_inv : LinearOperator
        Operador M^(-1) para pré-condicionamento

    Notes
    -----
    Complexidade: O(n) para construção e aplicação.
    Efetivo quando A tem diagonal forte comparada aos off-diagonais.

    Examples
    --------
    >>> A = np.diag([4, 3, 2, 1]) + 0.1 * np.random.randn(4, 4)
    >>> M_inv = jacobi_precond(A)
    >>> x = np.array([1, 2, 3, 4])
    >>> y = M_inv @ x  # Aplicar pré-condicionador
    """
    if HAS_SCIPY and sp.issparse(A):
        # Matriz esparsa
        diag_A = A.diagonal()
    else:
        # Matriz densa
        A = np.asarray(A)
        diag_A = np.diag(A)

    # Evitar divisão por zero
    diag_A = np.where(np.abs(diag_A) < np.finfo(A.dtype).eps, 1.0, diag_A)
    diag_inv = 1.0 / diag_A

    def matvec(x):
        return diag_inv * x

    n = len(diag_A)
    M_inv = LinearOperator(shape=(n, n), matvec=matvec, dtype=A.dtype)

    logger.debug(f"Jacobi preconditioner: n={n}, min_diag={np.min(np.abs(diag_A)):.2e}")

    return M_inv


def ichol0_precond(A: Union[np.ndarray, "sp.spmatrix"]) -> LinearOperator:
    """
    Pré-condicionador Cholesky Incompleto (IC0).

    Aproxima A ≈ L L^T onde L é triangular inferior esparsa.
    Usa padrão de esparsidade de A (nível 0 de fill-in).

    Parameters
    ----------
    A : np.ndarray ou scipy.sparse matrix
        Matriz simétrica positiva definida

    Returns
    -------
    M_inv : LinearOperator
        Operador M^(-1) = (L L^T)^(-1)

    Notes
    -----
    Requer SciPy para implementação completa.
    Fallback para Jacobi se SciPy não disponível ou A não SPD.

    Examples
    --------
    >>> # Matriz SPD esparsa
    >>> n = 100
    >>> A = sp.diags([1, -2, 1], [-1, 0, 1], shape=(n, n))
    >>> A = -A  # Tornar SPD
    >>> M_inv = ichol0_precond(A)
    """
    if not HAS_SCIPY:
        logger.warning("SciPy não disponível, usando Jacobi como fallback")
        return jacobi_precond(A)

    # Converter para formato CSC se necessário
    if sp.issparse(A):
        A_csc = A.tocsc()
    else:
        A = np.asarray(A)
        # Verificar se é simétrica
        if not np.allclose(A, A.T, rtol=1e-10):
            logger.warning("Matriz não simétrica, usando Jacobi")
            return jacobi_precond(A)
        A_csc = sp.csc_matrix(A)

    n = A_csc.shape[0]

    try:
        # Tentar fatoração Cholesky incompleta
        # Nota: scipy.sparse.linalg não tem spilu diretamente para Cholesky
        # Usar aproximação via LU incompleta
        ilu = spla.spilu(A_csc, fill_factor=1.0, drop_tol=0.0)

        def matvec(x):
            # Resolver M z = x onde M ≈ A
            # Usar ilu.solve que resolve L U z = x
            return ilu.solve(x)

        M_inv = LinearOperator(shape=(n, n), matvec=matvec, dtype=A_csc.dtype)

        logger.debug(f"ILU(0) preconditioner: n={n}, nnz={ilu.L.nnz + ilu.U.nnz}")

        return M_inv

    except Exception as e:
        logger.warning(f"Falha na fatoração ILU: {e}, usando Jacobi")
        return jacobi_precond(A)


def ssor_precond(
    A: Union[np.ndarray, "sp.spmatrix"], omega: float = 1.0
) -> LinearOperator:
    """
    Pré-condicionador SSOR (Symmetric Successive Over-Relaxation).

    M = (D + ω L) D^(-1) (D + ω U) / ω(2-ω)
    onde D = diag(A), L = parte triangular inferior, U = superior.

    Parameters
    ----------
    A : np.ndarray ou scipy.sparse matrix
        Matriz do sistema
    omega : float, default=1.0
        Parâmetro de relaxação (0 < ω < 2)

    Returns
    -------
    M_inv : LinearOperator
        Operador de pré-condicionamento

    Notes
    -----
    Efetivo para matrizes com estrutura de banda.
    ω = 1.0 corresponde ao método de Gauss-Seidel simétrico.
    """
    if not (0 < omega < 2):
        logger.warning(f"ω={omega} fora do intervalo (0,2), usando ω=1.0")
        omega = 1.0

    if HAS_SCIPY and sp.issparse(A):
        A_csr = A.tocsr()
        D = sp.diags(A.diagonal(), format="csr")
        L = sp.tril(A_csr, k=-1)
        U = sp.triu(A_csr, k=1)
    else:
        A = np.asarray(A)
        D = np.diag(np.diag(A))
        L = np.tril(A, k=-1)
        U = np.triu(A, k=1)

    # Construir M = (D + ω L) D^(-1) (D + ω U) / [ω(2-ω)]
    # Para aplicar M^(-1), resolver o sistema em duas etapas

    def matvec(x):
        # Resolver M z = x
        # Etapa 1: (D + ω L) y = x
        # Etapa 2: (D + ω U) z = D y / [ω(2-ω)]

        if HAS_SCIPY and sp.issparse(A):
            # Versão esparsa
            M1 = D + omega * L
            M2 = D + omega * U

            # Resolver sistemas triangulares
            y = spla.spsolve_triangular(M1, x, lower=True)
            rhs = D @ y / (omega * (2 - omega))
            z = spla.spsolve_triangular(M2, rhs, lower=False)
        else:
            # Versão densa
            M1 = D + omega * L
            M2 = D + omega * U

            y = np.linalg.solve(M1, x)
            rhs = D @ y / (omega * (2 - omega))
            z = np.linalg.solve(M2, rhs)

        return z

    n = A.shape[0]
    M_inv = LinearOperator(shape=(n, n), matvec=matvec, dtype=A.dtype)

    logger.debug(f"SSOR preconditioner: n={n}, ω={omega}")

    return M_inv


def choose_preconditioner(
    A: Union[np.ndarray, "sp.spmatrix"], method: str = "auto"
) -> LinearOperator:
    """
    Escolhe pré-condicionador automaticamente baseado nas propriedades de A.

    Parameters
    ----------
    A : np.ndarray ou scipy.sparse matrix
        Matriz do sistema
    method : {"auto", "jacobi", "ichol0", "ssor"}, default="auto"
        Método de pré-condicionamento

    Returns
    -------
    M_inv : LinearOperator
        Pré-condicionador escolhido

    Notes
    -----
    Heurísticas para "auto":
    - Se diagonal dominante: Jacobi
    - Se SPD e esparsa: IC0
    - Caso contrário: SSOR
    """
    if method != "auto":
        if method == "jacobi":
            return jacobi_precond(A)
        elif method == "ichol0":
            return ichol0_precond(A)
        elif method == "ssor":
            return ssor_precond(A)
        else:
            raise ValueError(f"Método desconhecido: {method}")

    # Análise automática
    if HAS_SCIPY and sp.issparse(A):
        A_dense = A.toarray() if A.nnz < 10000 else None
    else:
        A = np.asarray(A)
        A_dense = A

    n = A.shape[0]

    # Verificar dominância diagonal
    if A_dense is not None:
        diag_A = np.diag(A_dense)
        off_diag_sum = np.sum(np.abs(A_dense), axis=1) - np.abs(diag_A)
        diag_dominant = np.all(np.abs(diag_A) >= off_diag_sum)

        # Verificar se é SPD (aproximadamente)
        is_symmetric = np.allclose(A_dense, A_dense.T, rtol=1e-10)
        eigenvals = None
        if is_symmetric and n <= 1000:  # Evitar eigendecomposição cara
            try:
                eigenvals = np.linalg.eigvals(A_dense)
                is_spd = np.all(eigenvals > 1e-12)
            except:
                is_spd = False
        else:
            is_spd = False
    else:
        # Matriz muito grande, usar heurísticas simples
        diag_dominant = False
        is_spd = False

    # Escolher método
    if diag_dominant:
        logger.debug("Escolhendo Jacobi (diagonal dominante)")
        return jacobi_precond(A)
    elif is_spd and HAS_SCIPY:
        logger.debug("Escolhendo IC0 (SPD)")
        return ichol0_precond(A)
    else:
        logger.debug("Escolhendo SSOR (caso geral)")
        return ssor_precond(A)


def preconditioner_quality(
    A: Union[np.ndarray, "sp.spmatrix"], M_inv: LinearOperator, n_samples: int = 10
) -> dict:
    """
    Avalia qualidade do pré-condicionador.

    Parameters
    ----------
    A : matriz do sistema
    M_inv : pré-condicionador
    n_samples : int
        Número de vetores aleatórios para teste

    Returns
    -------
    metrics : dict
        Métricas de qualidade
    """
    n = A.shape[0]

    # Estimar número de condição de M^(-1) A
    eigenvals = []

    for _ in range(n_samples):
        # Método da potência para estimar autovalores extremos
        x = np.random.randn(n)
        x = x / np.linalg.norm(x)

        # Aplicar M^(-1) A
        if HAS_SCIPY and sp.issparse(A):
            Ax = A @ x
        else:
            Ax = np.asarray(A) @ x

        MAx = M_inv @ Ax

        # Aproximar autovalor via quociente de Rayleigh
        eigenval = np.dot(x, MAx) / np.dot(x, x)
        eigenvals.append(eigenval)

    eigenvals = np.array(eigenvals)
    eigenvals = eigenvals[eigenvals > 0]  # Filtrar não-positivos

    if len(eigenvals) > 0:
        cond_est = np.max(eigenvals) / np.min(eigenvals)
    else:
        cond_est = np.inf

    # Número de condição original
    if HAS_SCIPY and sp.issparse(A):
        # Estimativa grosseira para matriz esparsa
        cond_orig = np.inf
    else:
        try:
            cond_orig = np.linalg.cond(np.asarray(A))
        except:
            cond_orig = np.inf

    metrics = {
        "condition_number_estimate": cond_est,
        "condition_number_original": cond_orig,
        "improvement_factor": cond_orig / cond_est if cond_est > 0 else 1.0,
        "eigenvalue_range": (np.min(eigenvals), np.max(eigenvals))
        if len(eigenvals) > 0
        else (0, 0),
    }

    return metrics
