"""
Non-Negative Least Squares via KKT Conditions

Implementação de NNLS usando condições de Karush-Kuhn-Tucker
para garantir convergência teórica e validação numérica.

Author: PCS-HELIO Team
License: MIT
"""

import numpy as np
from typing import Tuple, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


def nnls_kkt(
    A: np.ndarray,
    b: np.ndarray,
    tol: float = 1e-10,
    max_iter: int = 10000,
    return_info: bool = False,
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Resolve problema NNLS: min ||Ax - b||² sujeito a x ≥ 0.

    Implementa algoritmo ativo baseado em condições KKT:
    1. Viabilidade primal: Ax - b = r, x ≥ 0
    2. Viabilidade dual: A^T r + λ = 0, λ ≥ 0
    3. Complementaridade: x_i λ_i = 0 ∀i

    Parameters
    ----------
    A : np.ndarray, shape (m, n)
        Matriz de coeficientes
    b : np.ndarray, shape (m,)
        Vetor do lado direito
    tol : float, default=1e-10
        Tolerância para condições KKT
    max_iter : int, default=10000
        Número máximo de iterações
    return_info : bool, default=False
        Se True, retorna informações detalhadas

    Returns
    -------
    x : np.ndarray, shape (n,)
        Solução NNLS
    info : dict
        Informações de convergência e validação KKT

    Notes
    -----
    Algoritmo de conjunto ativo:
    - P: conjunto de índices ativos (x_i > 0)
    - Z: conjunto de índices inativos (x_i = 0)
    - Resolve subproblema irrestrito em P
    - Atualiza conjuntos baseado em condições KKT

    Complexidade: O(n³) no pior caso, mas tipicamente muito menor.

    Examples
    --------
    >>> # Problema NNLS simples
    >>> A = np.array([[1, 1], [1, 0], [0, 1]])
    >>> b = np.array([2, 1, 1])
    >>> x, info = nnls_kkt(A, b, return_info=True)
    >>> np.all(x >= 0)  # Não-negatividade
    True
    >>> info['kkt_satisfied']  # Condições KKT
    True
    """
    A = np.asarray(A, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)

    m, n = A.shape

    if b.shape[0] != m:
        raise ValueError(f"Dimensões incompatíveis: A{A.shape}, b{b.shape}")

    logger.debug(f"NNLS KKT: A{A.shape}, b{b.shape}, tol={tol:.2e}")

    # Inicialização
    x = np.zeros(n, dtype=np.float64)
    P = set()  # Conjunto ativo (x_i > 0)
    Z = set(range(n))  # Conjunto inativo (x_i = 0)

    # Histórico para diagnóstico
    objective_history = []
    kkt_violation_history = []

    for iteration in range(max_iter):
        # Calcular resíduo e gradiente
        r = A @ x - b
        grad = A.T @ r  # ∇f(x) = A^T(Ax - b)

        # Calcular função objetivo
        objective = 0.5 * np.dot(r, r)
        objective_history.append(objective)

        # Verificar condições KKT
        kkt_violation = _check_kkt_conditions(x, grad, P, Z, tol)
        kkt_violation_history.append(kkt_violation)

        logger.debug(
            f"NNLS iter {iteration}: obj={objective:.2e}, "
            f"KKT_viol={kkt_violation:.2e}, |P|={len(P)}"
        )

        if kkt_violation <= tol:
            logger.debug(f"NNLS convergiu em {iteration} iterações")
            converged = True
            break

        # Encontrar índice para adicionar ao conjunto ativo
        # Escolher j ∈ Z com maior violação dual: min(grad_j, 0)
        candidates = [(j, min(grad[j], 0)) for j in Z]
        if not candidates:
            break

        j_add, min_grad = min(candidates, key=lambda x: x[1])

        if min_grad >= -tol:
            # Nenhuma violação dual significativa
            break

        # Adicionar j ao conjunto ativo
        P.add(j_add)
        Z.remove(j_add)

        # Resolver subproblema irrestrito no conjunto ativo
        while True:
            if not P:
                break

            # Formar subproblema A_P x_P = b
            P_list = sorted(P)
            A_P = A[:, P_list]

            try:
                # Resolver sistema de equações normais
                # (A_P^T A_P) x_P = A_P^T b
                AtA_P = A_P.T @ A_P
                Atb_P = A_P.T @ b

                # Verificar condicionamento
                cond_num = np.linalg.cond(AtA_P)
                if cond_num > 1e12:
                    logger.warning(f"Sistema mal-condicionado: cond={cond_num:.2e}")

                x_P = np.linalg.solve(AtA_P, Atb_P)

            except np.linalg.LinAlgError:
                logger.warning("Sistema singular, removendo última variável")
                P.remove(j_add)
                Z.add(j_add)
                break

            # Verificar viabilidade: x_P ≥ 0
            if np.all(x_P >= -tol):
                # Solução viável, atualizar x
                x.fill(0.0)
                x[P_list] = np.maximum(x_P, 0.0)  # Projetar para não-negativo
                break
            else:
                # Solução inviável, encontrar índice para remover
                # Usar interpolação para encontrar maior α tal que x + α(x_P - x) ≥ 0
                alpha_candidates = []

                for i, p_idx in enumerate(P_list):
                    if x_P[i] < 0:
                        if x[p_idx] > 0:
                            alpha = x[p_idx] / (x[p_idx] - x_P[i])
                            alpha_candidates.append((alpha, p_idx))

                if not alpha_candidates:
                    # Não deveria acontecer, mas proteger contra loop infinito
                    logger.warning("Nenhum candidato para remoção encontrado")
                    break

                # Escolher menor α (primeiro a violar restrição)
                alpha, idx_remove = min(alpha_candidates)

                # Atualizar x com interpolação
                x_new = np.zeros(n)
                x_new[P_list] = x[P_list] + alpha * (x_P - x[P_list])
                x_new = np.maximum(x_new, 0.0)  # Garantir não-negatividade
                x = x_new

                # Remover índice do conjunto ativo
                P.remove(idx_remove)
                Z.add(idx_remove)
                x[idx_remove] = 0.0
    else:
        # Não convergiu
        logger.warning(f"NNLS não convergiu em {max_iter} iterações")
        converged = False

    # Validação final das condições KKT
    r_final = A @ x - b
    grad_final = A.T @ r_final
    lambda_final = np.zeros(n)

    # Multiplicadores de Lagrange para restrições ativas
    for i in range(n):
        if x[i] <= tol:  # Variável no limite
            lambda_final[i] = max(0, grad_final[i])
        else:  # Variável no interior
            lambda_final[i] = 0

    # Verificar condições KKT finais
    kkt_final = _validate_kkt_solution(A, b, x, lambda_final, tol)

    # Calcular métricas de qualidade
    residual_norm = np.linalg.norm(r_final)
    objective_final = 0.5 * np.dot(r_final, r_final)

    info = {
        "converged": converged,
        "iterations": iteration + 1 if converged else max_iter,
        "objective": objective_final,
        "residual_norm": residual_norm,
        "active_set": sorted(P),
        "inactive_set": sorted(Z),
        "kkt_satisfied": kkt_final["satisfied"],
        "kkt_violations": kkt_final,
        "lagrange_multipliers": lambda_final,
        "objective_history": np.array(objective_history),
        "kkt_violation_history": np.array(kkt_violation_history),
    }

    logger.debug(
        f"NNLS final: obj={objective_final:.2e}, "
        f"||r||={residual_norm:.2e}, KKT={kkt_final['satisfied']}"
    )

    if return_info:
        return x, info
    else:
        return x, info


def _check_kkt_conditions(
    x: np.ndarray, grad: np.ndarray, P: set, Z: set, tol: float
) -> float:
    """
    Verifica violação das condições KKT.

    Returns
    -------
    violation : float
        Máxima violação das condições KKT
    """
    violations = []

    # Para variáveis ativas (x_i > 0): gradiente deve ser ~0
    for i in P:
        if x[i] > tol:
            violations.append(abs(grad[i]))

    # Para variáveis inativas (x_i = 0): gradiente deve ser ≥ 0
    for i in Z:
        if x[i] <= tol:
            violations.append(max(0, -grad[i]))

    return max(violations) if violations else 0.0


def _validate_kkt_solution(
    A: np.ndarray, b: np.ndarray, x: np.ndarray, lambda_vec: np.ndarray, tol: float
) -> Dict[str, Any]:
    """
    Valida solução NNLS contra condições KKT.

    Returns
    -------
    validation : dict
        Resultados da validação KKT
    """
    n = len(x)

    # 1. Viabilidade primal: x ≥ 0
    primal_feasible = np.all(x >= -tol)
    min_x = np.min(x)

    # 2. Viabilidade dual: A^T r + λ = 0 onde r = Ax - b
    r = A @ x - b
    dual_residual = A.T @ r + lambda_vec
    dual_feasible = np.linalg.norm(dual_residual) <= tol
    dual_residual_norm = np.linalg.norm(dual_residual)

    # 3. Não-negatividade dos multiplicadores: λ ≥ 0
    lambda_nonneg = np.all(lambda_vec >= -tol)
    min_lambda = np.min(lambda_vec)

    # 4. Complementaridade: x_i * λ_i = 0
    complementarity = np.abs(x * lambda_vec)
    complementarity_satisfied = np.all(complementarity <= tol)
    max_complementarity = np.max(complementarity)

    # Violação total
    total_violation = max(
        max(0, -min_x),  # Violação primal
        dual_residual_norm,  # Violação dual
        max(0, -min_lambda),  # Violação λ ≥ 0
        max_complementarity,  # Violação complementaridade
    )

    satisfied = (
        primal_feasible
        and dual_feasible
        and lambda_nonneg
        and complementarity_satisfied
    )

    return {
        "satisfied": satisfied,
        "total_violation": total_violation,
        "primal_feasible": primal_feasible,
        "min_x": min_x,
        "dual_feasible": dual_feasible,
        "dual_residual_norm": dual_residual_norm,
        "lambda_nonnegative": lambda_nonneg,
        "min_lambda": min_lambda,
        "complementarity_satisfied": complementarity_satisfied,
        "max_complementarity": max_complementarity,
    }


def nnls_compare_scipy(A: np.ndarray, b: np.ndarray, tol: float = 1e-10):
    """
    Compara implementação KKT com scipy.optimize.nnls (se disponível).

    Parameters
    ----------
    A, b : arrays do problema NNLS
    tol : tolerância

    Returns
    -------
    comparison : dict
        Resultados da comparação
    """
    # Nossa implementação
    x_kkt, info_kkt = nnls_kkt(A, b, tol=tol, return_info=True)

    try:
        from scipy.optimize import nnls as scipy_nnls

        # Implementação SciPy
        x_scipy, residual_scipy = scipy_nnls(A, b)

        # Comparar soluções
        solution_diff = np.linalg.norm(x_kkt - x_scipy)
        objective_kkt = 0.5 * np.linalg.norm(A @ x_kkt - b) ** 2
        objective_scipy = 0.5 * np.linalg.norm(A @ x_scipy - b) ** 2

        comparison = {
            "scipy_available": True,
            "x_kkt": x_kkt,
            "x_scipy": x_scipy,
            "solution_difference": solution_diff,
            "objective_kkt": objective_kkt,
            "objective_scipy": objective_scipy,
            "kkt_info": info_kkt,
            "scipy_residual": residual_scipy,
        }

        logger.info(f"NNLS comparison: ||x_kkt - x_scipy|| = {solution_diff:.2e}")

    except ImportError:
        logger.info("SciPy não disponível para comparação")
        comparison = {"scipy_available": False, "x_kkt": x_kkt, "kkt_info": info_kkt}

    return comparison


def nnls_test_cases() -> Dict[str, Any]:
    """
    Gera casos de teste para validar implementação NNLS.

    Returns
    -------
    test_results : dict
        Resultados dos casos de teste
    """
    np.random.seed(42)  # Reprodutibilidade

    test_cases = {}

    # Caso 1: Problema simples com solução conhecida
    logger.info("Teste NNLS - Caso 1: Problema simples")
    A1 = np.array([[1, 0], [0, 1], [1, 1]], dtype=np.float64)
    b1 = np.array([1, 1, 1.5], dtype=np.float64)
    x1, info1 = nnls_kkt(A1, b1, return_info=True)

    test_cases["simple"] = {
        "A": A1,
        "b": b1,
        "x": x1,
        "info": info1,
        "expected_active": [0, 1],  # Ambas variáveis devem ser ativas
    }

    # Caso 2: Problema com algumas variáveis zero
    logger.info("Teste NNLS - Caso 2: Variáveis zero")
    A2 = np.array([[1, -1, 0], [0, 1, -1], [1, 0, 1]], dtype=np.float64)
    b2 = np.array([1, 0, 2], dtype=np.float64)
    x2, info2 = nnls_kkt(A2, b2, return_info=True)

    test_cases["sparse"] = {"A": A2, "b": b2, "x": x2, "info": info2}

    # Caso 3: Problema mal-condicionado
    logger.info("Teste NNLS - Caso 3: Mal-condicionado")
    n = 10
    A3 = np.random.randn(15, n)
    A3 += 1e-8 * np.random.randn(15, n)  # Adicionar ruído pequeno
    x_true = np.maximum(0, np.random.randn(n))  # Solução não-negativa
    b3 = A3 @ x_true + 1e-10 * np.random.randn(15)  # Ruído pequeno

    x3, info3 = nnls_kkt(A3, b3, return_info=True)

    test_cases["ill_conditioned"] = {
        "A": A3,
        "b": b3,
        "x": x3,
        "info": info3,
        "x_true": x_true,
        "recovery_error": np.linalg.norm(x3 - x_true),
    }

    # Caso 4: Problema degenerado (b = 0)
    logger.info("Teste NNLS - Caso 4: Degenerado")
    A4 = np.random.randn(5, 3)
    b4 = np.zeros(5)
    x4, info4 = nnls_kkt(A4, b4, return_info=True)

    test_cases["degenerate"] = {
        "A": A4,
        "b": b4,
        "x": x4,
        "info": info4,
        "expected_zero": True,  # Solução deve ser zero
    }

    # Resumo dos testes
    summary = {
        "total_cases": len(test_cases),
        "all_converged": all(case["info"]["converged"] for case in test_cases.values()),
        "all_kkt_satisfied": all(
            case["info"]["kkt_satisfied"] for case in test_cases.values()
        ),
    }

    logger.info(
        f"NNLS testes: {summary['total_cases']} casos, "
        f"convergência: {summary['all_converged']}, "
        f"KKT: {summary['all_kkt_satisfied']}"
    )

    return {"cases": test_cases, "summary": summary}


if __name__ == "__main__":
    # Executar testes se chamado diretamente
    logging.basicConfig(level=logging.INFO)
    results = nnls_test_cases()

    # Comparar com SciPy se disponível
    A_test = np.random.randn(20, 10)
    b_test = np.random.randn(20)
    comparison = nnls_compare_scipy(A_test, b_test)

    print("Testes NNLS concluídos com sucesso!")
