"""
Kahan Summation Algorithm

Implementação da soma de Kahan para reduzir erros de arredondamento
em somas de ponto flutuante com grande variação de magnitude.

Author: PCS-HELIO Team
License: MIT
"""

import numpy as np
from typing import Union, Optional
import logging

logger = logging.getLogger(__name__)

ArrayLike = Union[np.ndarray, list, tuple]


def kahan_sum(
    x: ArrayLike, axis: Optional[int] = None, dtype: Optional[np.dtype] = None
) -> Union[float, np.ndarray]:
    """
    Soma compensada de Kahan para reduzir erros de arredondamento.

    Algoritmo que mantém um termo de compensação para corrigir
    erros de arredondamento em somas de ponto flutuante.

    Parameters
    ----------
    x : array_like
        Array de entrada para soma
    axis : int, optional
        Eixo ao longo do qual somar. Se None, soma todos os elementos
    dtype : np.dtype, optional
        Tipo de dados para o resultado. Se None, usa tipo de x

    Returns
    -------
    sum : float ou np.ndarray
        Soma compensada

    Notes
    -----
    Algoritmo de Kahan:
    1. sum = 0, c = 0  (compensação)
    2. Para cada x[i]:
       - y = x[i] - c
       - t = sum + y
       - c = (t - sum) - y  (erro de arredondamento)
       - sum = t

    Reduz erro de O(n·ε) para O(ε) onde ε é precisão da máquina.

    Examples
    --------
    >>> # Caso adverso: somar 1.0 + muitos números pequenos
    >>> x = [1.0] + [1e-16] * 1000000
    >>> sum_naive = sum(x)
    >>> sum_kahan = kahan_sum(x)
    >>> abs(sum_kahan - (1.0 + 1e-10)) < abs(sum_naive - (1.0 + 1e-10))
    True

    >>> # Array multidimensional
    >>> A = np.random.randn(100, 50) * np.logspace(-10, 10, 5000).reshape(100, 50)
    >>> s1 = np.sum(A, axis=0)  # Soma ingênua
    >>> s2 = kahan_sum(A, axis=0)  # Soma de Kahan
    >>> np.allclose(s1, s2, rtol=1e-12)  # Kahan mais precisa
    True
    """
    x = np.asarray(x)

    if dtype is None:
        dtype = x.dtype
        # Promover para float64 se necessário para máxima precisão
        if not np.issubdtype(dtype, np.floating):
            dtype = np.float64
        elif dtype == np.float32:
            dtype = np.float64

    x = x.astype(dtype)

    if axis is None:
        # Soma de todos os elementos
        return _kahan_sum_1d(x.ravel())

    # Soma ao longo de um eixo específico
    if axis < 0:
        axis = x.ndim + axis

    if axis >= x.ndim:
        raise ValueError(
            f"axis {axis} está fora dos limites para array de dimensão {x.ndim}"
        )

    # Mover o eixo para a última posição
    x_moved = np.moveaxis(x, axis, -1)
    original_shape = x_moved.shape

    # Reshape para (..., n) onde n é o tamanho do eixo
    x_reshaped = x_moved.reshape(-1, original_shape[-1])

    # Aplicar Kahan sum em cada linha
    result = np.array([_kahan_sum_1d(row) for row in x_reshaped], dtype=dtype)

    # Reshape de volta para a forma original (sem o eixo somado)
    result_shape = original_shape[:-1]
    if result_shape:
        result = result.reshape(result_shape)
    else:
        result = result.item()  # Escalar se todas as dimensões foram somadas

    return result


def _kahan_sum_1d(x: np.ndarray) -> float:
    """
    Implementação 1D da soma de Kahan.

    Parameters
    ----------
    x : np.ndarray
        Array 1D para soma

    Returns
    -------
    sum : float
        Soma compensada
    """
    if len(x) == 0:
        return 0.0

    # Inicializar soma e compensação
    sum_val = float(x[0])
    c = 0.0

    # Aplicar algoritmo de Kahan
    for i in range(1, len(x)):
        y = float(x[i]) - c
        t = sum_val + y
        c = (t - sum_val) - y
        sum_val = t

    return sum_val


def kahan_dot(x: ArrayLike, y: ArrayLike) -> float:
    """
    Produto interno usando soma de Kahan.

    Calcula x · y = Σ x[i] * y[i] usando soma compensada
    para reduzir erros de arredondamento.

    Parameters
    ----------
    x, y : array_like
        Vetores de entrada

    Returns
    -------
    dot : float
        Produto interno compensado

    Examples
    --------
    >>> x = np.random.randn(1000) * 1e-8
    >>> y = np.random.randn(1000) * 1e8
    >>> dot_naive = np.sum(x * y)
    >>> dot_kahan = kahan_dot(x, y)
    >>> # Kahan geralmente mais preciso para casos extremos
    """
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)

    if x.shape != y.shape:
        raise ValueError(f"Formas incompatíveis: x{x.shape}, y{y.shape}")

    products = x * y
    return kahan_sum(products)


def kahan_norm_squared(x: ArrayLike) -> float:
    """
    Norma ao quadrado usando soma de Kahan.

    Calcula ||x||² = Σ x[i]² usando soma compensada.

    Parameters
    ----------
    x : array_like
        Vetor de entrada

    Returns
    -------
    norm_sq : float
        Norma ao quadrado compensada
    """
    x = np.asarray(x, dtype=np.float64)
    return kahan_sum(x * x)


def demonstrate_kahan_precision():
    """
    Demonstra a melhoria de precisão da soma de Kahan.

    Cria casos adversos onde a soma ingênua perde precisão
    e mostra como Kahan mantém maior precisão.

    Returns
    -------
    results : dict
        Resultados da demonstração
    """
    results = {}

    # Caso 1: Somar 1.0 + muitos números pequenos
    logger.info("Demonstração Kahan - Caso 1: 1.0 + números pequenos")

    large = 1.0
    small_count = 1000000
    small_value = 1e-7
    expected = large + small_count * small_value

    # Lista com 1.0 seguido de muitos números pequenos
    x1 = [large] + [small_value] * small_count

    sum_naive = sum(x1)
    sum_numpy = np.sum(x1)
    sum_kahan = kahan_sum(x1)

    error_naive = abs(sum_naive - expected)
    error_numpy = abs(sum_numpy - expected)
    error_kahan = abs(sum_kahan - expected)

    results["case1"] = {
        "expected": expected,
        "naive": sum_naive,
        "numpy": sum_numpy,
        "kahan": sum_kahan,
        "error_naive": error_naive,
        "error_numpy": error_numpy,
        "error_kahan": error_kahan,
        "improvement_vs_naive": error_naive / error_kahan
        if error_kahan > 0
        else np.inf,
        "improvement_vs_numpy": error_numpy / error_kahan
        if error_kahan > 0
        else np.inf,
    }

    logger.info(f"Erro ingênuo: {error_naive:.2e}")
    logger.info(f"Erro NumPy: {error_numpy:.2e}")
    logger.info(f"Erro Kahan: {error_kahan:.2e}")
    logger.info(f"Melhoria vs ingênuo: {results['case1']['improvement_vs_naive']:.1f}x")

    # Caso 2: Soma alternada com cancelamento
    logger.info("Demonstração Kahan - Caso 2: Cancelamento catastrófico")

    n = 100000
    # Criar sequência que deveria somar para ~0 mas tem cancelamento
    x2 = []
    for i in range(n):
        if i % 2 == 0:
            x2.append(1.0 + 1e-15)
        else:
            x2.append(-1.0)

    expected2 = n // 2 * 1e-15  # Valor esperado pequeno mas não zero

    sum_naive2 = sum(x2)
    sum_numpy2 = np.sum(x2)
    sum_kahan2 = kahan_sum(x2)

    error_naive2 = abs(sum_naive2 - expected2)
    error_numpy2 = abs(sum_numpy2 - expected2)
    error_kahan2 = abs(sum_kahan2 - expected2)

    results["case2"] = {
        "expected": expected2,
        "naive": sum_naive2,
        "numpy": sum_numpy2,
        "kahan": sum_kahan2,
        "error_naive": error_naive2,
        "error_numpy": error_numpy2,
        "error_kahan": error_kahan2,
    }

    logger.info(f"Esperado: {expected2:.2e}")
    logger.info(f"Erro ingênuo: {error_naive2:.2e}")
    logger.info(f"Erro NumPy: {error_numpy2:.2e}")
    logger.info(f"Erro Kahan: {error_kahan2:.2e}")

    return results


if __name__ == "__main__":
    # Executar demonstração se chamado diretamente
    logging.basicConfig(level=logging.INFO)
    demonstrate_kahan_precision()
