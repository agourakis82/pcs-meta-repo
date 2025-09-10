"""
Testes para módulo QR Householder

Testa decomposição QR, solução de sistemas lineares e estabilidade numérica.

Author: PCS-HELIO Team
License: MIT
"""

import pytest
import numpy as np
import logging

# Configurar logging para testes
logging.basicConfig(level=logging.WARNING)

try:
    from src.pcs_math.qr_householder import (
        householder_qr,
        solve_via_qr,
        qr_condition_number,
    )
except ImportError:
    # Fallback para execução direta
    import sys
    import os

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from src.pcs_math.qr_householder import (
        householder_qr,
        solve_via_qr,
        qr_condition_number,
    )


class TestHouseholderQR:
    """Testes para decomposição QR via Householder."""

    def test_qr_basic_square(self):
        """Teste básico com matriz quadrada."""
        np.random.seed(42)
        A = np.random.randn(5, 5).astype(np.float64)

        Q, R = householder_qr(A, mode="reduced")

        # Verificar dimensões
        assert Q.shape == (5, 5)
        assert R.shape == (5, 5)

        # Verificar decomposição: A = QR
        A_reconstructed = Q @ R
        assert np.allclose(A, A_reconstructed, rtol=1e-12)

        # Verificar ortogonalidade de Q
        I = np.eye(5)
        assert np.allclose(Q.T @ Q, I, rtol=1e-12)

        # Verificar que R é triangular superior
        R_lower = np.tril(R, k=-1)
        assert np.allclose(R_lower, 0, atol=1e-14)

    def test_qr_rectangular_tall(self):
        """Teste com matriz retangular alta (m > n)."""
        np.random.seed(123)
        A = np.random.randn(10, 6).astype(np.float64)

        Q, R = householder_qr(A, mode="reduced")

        # Verificar dimensões
        assert Q.shape == (10, 6)
        assert R.shape == (6, 6)

        # Verificar decomposição
        assert np.allclose(A, Q @ R, rtol=1e-12)

        # Verificar ortogonalidade
        I = np.eye(6)
        assert np.allclose(Q.T @ Q, I, rtol=1e-12)

    def test_qr_rectangular_wide(self):
        """Teste com matriz retangular larga (m < n)."""
        np.random.seed(456)
        A = np.random.randn(4, 7).astype(np.float64)

        Q, R = householder_qr(A, mode="reduced")

        # Verificar dimensões
        assert Q.shape == (4, 4)
        assert R.shape == (4, 7)

        # Verificar decomposição
        assert np.allclose(A, Q @ R, rtol=1e-12)

        # Verificar ortogonalidade
        I = np.eye(4)
        assert np.allclose(Q.T @ Q, I, rtol=1e-12)

    def test_qr_full_mode(self):
        """Teste modo 'full' vs 'reduced'."""
        np.random.seed(789)
        A = np.random.randn(8, 5).astype(np.float64)

        Q_red, R_red = householder_qr(A, mode="reduced")
        Q_full, R_full = householder_qr(A, mode="full")

        # Verificar dimensões
        assert Q_red.shape == (8, 5)
        assert R_red.shape == (5, 5)
        assert Q_full.shape == (8, 8)
        assert R_full.shape == (8, 5)

        # Ambos devem reconstruir A
        assert np.allclose(A, Q_red @ R_red, rtol=1e-12)
        assert np.allclose(A, Q_full @ R_full, rtol=1e-12)

        # Q_full deve ser ortogonal completa
        I_full = np.eye(8)
        assert np.allclose(Q_full.T @ Q_full, I_full, rtol=1e-12)

    def test_qr_ill_conditioned(self):
        """Teste com matriz mal-condicionada."""
        np.random.seed(20240910)
        # Criar matriz mal-condicionada
        U = np.random.randn(6, 6)
        s = np.array([1e0, 1e-1, 1e-2, 1e-3, 1e-12, 1e-14])  # Valores singulares
        V = np.random.randn(6, 6)
        # Ortonormalizar para controle do condicionamento
        U, _ = np.linalg.qr(U)
        V, _ = np.linalg.qr(V)
        A = U @ np.diag(s) @ V.T

        Q, R = householder_qr(A)

        # Mesmo mal-condicionada, QR deve ser estável
        assert np.allclose(A, Q @ R, rtol=1e-10)
        assert np.allclose(Q.T @ Q, np.eye(6), rtol=1e-12)

        # Verificar número de condição
        cond_A = np.linalg.cond(A)
        cond_R = qr_condition_number(A)

        # Condição de R deve ser similar à de A
        assert abs(np.log10(cond_A) - np.log10(cond_R)) < 1.0

    def test_qr_rank_deficient(self):
        """Teste com matriz rank-deficiente."""
        # Criar matriz rank 3 em espaço 5x5
        np.random.seed(999)
        U = np.random.randn(5, 3)
        V = np.random.randn(3, 5)
        A = U @ V  # rank = 3

        Q, R = householder_qr(A)

        # Decomposição deve funcionar
        assert np.allclose(A, Q @ R, rtol=1e-12)

        # R deve ter elementos pequenos nas últimas linhas
        R_diag = np.diag(R)
        assert np.sum(np.abs(R_diag) > 1e-12) <= 3  # Rank efetivo ≤ 3

    def test_qr_zero_matrix(self):
        """Teste com matriz zero."""
        A = np.zeros((4, 3))

        Q, R = householder_qr(A)

        # Deve retornar Q = I, R = 0
        assert np.allclose(Q, np.eye(4, 3), rtol=1e-14)
        assert np.allclose(R, np.zeros((3, 3)), atol=1e-14)
        assert np.allclose(A, Q @ R, atol=1e-14)

    def test_qr_single_column(self):
        """Teste com matriz de uma coluna."""
        np.random.seed(111)
        A = np.random.randn(6, 1).astype(np.float64)

        Q, R = householder_qr(A)

        assert Q.shape == (6, 1)
        assert R.shape == (1, 1)
        assert np.allclose(A, Q @ R, rtol=1e-12)
        assert np.allclose(Q.T @ Q, np.eye(1), rtol=1e-12)

    def test_qr_dtype_consistency(self):
        """Teste consistência de tipos de dados."""
        A_f32 = np.random.randn(4, 3).astype(np.float32)
        A_f64 = A_f32.astype(np.float64)

        Q32, R32 = householder_qr(A_f32, dtype=np.float32)
        Q64, R64 = householder_qr(A_f64, dtype=np.float64)

        # Resultados devem ser consistentes (dentro da precisão)
        assert np.allclose(Q32, Q64, rtol=1e-6)  # float32 tem menor precisão
        assert np.allclose(R32, R64, rtol=1e-6)


class TestQRSolver:
    """Testes para solução de sistemas via QR."""

    def test_solve_square_system(self):
        """Teste sistema quadrado bem-condicionado."""
        np.random.seed(222)
        A = np.random.randn(5, 5).astype(np.float64)
        x_true = np.random.randn(5)
        b = A @ x_true

        x_qr = solve_via_qr(A, b)

        # Verificar solução
        assert np.allclose(x_qr, x_true, rtol=1e-12)
        assert np.allclose(A @ x_qr, b, rtol=1e-12)

    def test_solve_overdetermined(self):
        """Teste sistema sobredeterminado (mínimos quadrados)."""
        np.random.seed(333)
        A = np.random.randn(10, 6).astype(np.float64)
        x_true = np.random.randn(6)
        b = A @ x_true + 0.01 * np.random.randn(10)  # Ruído pequeno

        x_qr = solve_via_qr(A, b)

        # Comparar com solução NumPy
        x_numpy = np.linalg.lstsq(A, b, rcond=None)[0]
        assert np.allclose(x_qr, x_numpy, rtol=1e-10)

        # Verificar que é solução de mínimos quadrados
        residual_qr = np.linalg.norm(A @ x_qr - b)
        residual_numpy = np.linalg.norm(A @ x_numpy - b)
        assert abs(residual_qr - residual_numpy) < 1e-12

    def test_solve_underdetermined(self):
        """Teste sistema subdeterminado."""
        np.random.seed(444)
        A = np.random.randn(3, 5).astype(np.float64)
        b = np.random.randn(3)

        x_qr = solve_via_qr(A, b)

        # Verificar que satisfaz o sistema
        assert np.allclose(A @ x_qr, b, rtol=1e-12)

        # Comparar com NumPy
        x_numpy = np.linalg.lstsq(A, b, rcond=None)[0]
        assert np.allclose(x_qr, x_numpy, rtol=1e-10)

    def test_solve_multiple_rhs(self):
        """Teste múltiplos lados direitos."""
        np.random.seed(555)
        A = np.random.randn(6, 4).astype(np.float64)
        B = np.random.randn(6, 3)  # 3 sistemas

        # Resolver cada sistema individualmente
        X_individual = np.zeros((4, 3))
        for i in range(3):
            X_individual[:, i] = solve_via_qr(A, B[:, i])

        # Resolver todos de uma vez
        X_batch = solve_via_qr(A, B)

        assert np.allclose(X_individual, X_batch, rtol=1e-12)

    def test_solve_rank_deficient(self):
        """Teste sistema rank-deficiente."""
        # Criar matriz rank 2 em espaço 4x4
        np.random.seed(666)
        U = np.random.randn(4, 2)
        V = np.random.randn(2, 4)
        A = U @ V

        # b no espaço coluna de A
        x_true = np.random.randn(4)
        b = A @ x_true

        x_qr = solve_via_qr(A, b, rcond=1e-12)

        # Deve encontrar uma solução (não necessariamente x_true)
        assert np.allclose(A @ x_qr, b, rtol=1e-10)

    def test_solve_ill_conditioned_vs_normal_equations(self):
        """Comparar QR vs equações normais em problema mal-condicionado."""
        # Matriz mal-condicionada
        np.random.seed(777)
        A = np.random.randn(20, 10)
        A[:, -1] = A[:, 0] + 1e-12 * np.random.randn(20)  # Quase colinear

        x_true = np.random.randn(10)
        b = A @ x_true + 1e-14 * np.random.randn(20)  # Ruído pequeno

        # Solução QR
        x_qr = solve_via_qr(A, b)

        # Solução equações normais (instável)
        AtA = A.T @ A
        Atb = A.T @ b
        try:
            x_normal = np.linalg.solve(AtA, Atb)
        except np.linalg.LinAlgError:
            x_normal = np.linalg.lstsq(AtA, Atb, rcond=None)[0]

        # QR deve ser mais precisa
        error_qr = np.linalg.norm(x_qr - x_true)
        error_normal = np.linalg.norm(x_normal - x_true)

        # QR geralmente melhor, mas pelo menos não muito pior
        assert error_qr <= 10 * error_normal or error_qr < 1e-10


class TestQRConditionNumber:
    """Testes para estimativa de número de condição."""

    def test_condition_well_conditioned(self):
        """Teste matriz bem-condicionada."""
        A = np.eye(5) + 0.1 * np.random.randn(5, 5)

        cond_qr = qr_condition_number(A)
        cond_numpy = np.linalg.cond(A)

        # Deve ser próximo de 1 e consistente com NumPy
        assert cond_qr < 10
        assert abs(np.log10(cond_qr) - np.log10(cond_numpy)) < 0.5

    def test_condition_ill_conditioned(self):
        """Teste matriz mal-condicionada."""
        np.random.seed(20240910)
        # Criar matriz com número de condição conhecido
        U = np.random.randn(4, 4)
        s = np.array([1, 1e-2, 1e-4, 1e-6])
        V = np.random.randn(4, 4)
        U, _ = np.linalg.qr(U)
        V, _ = np.linalg.qr(V)
        A = U @ np.diag(s) @ V.T

        cond_qr = qr_condition_number(A)
        cond_expected = s[0] / s[-1]  # 1e6

        # Deve detectar mal-condicionamento
        assert cond_qr > 1e5
        assert abs(np.log10(cond_qr) - np.log10(cond_expected)) < 1.0

    def test_condition_singular(self):
        """Teste matriz singular."""
        A = np.array([[1, 2], [2, 4]], dtype=np.float64)  # rank 1

        cond_qr = qr_condition_number(A)

        # Deve ser muito grande ou infinito
        assert cond_qr > 1e12 or np.isinf(cond_qr)


class TestQREdgeCases:
    """Testes para casos extremos."""

    def test_empty_matrix(self):
        """Teste matriz vazia."""
        A = np.array([]).reshape(0, 0)

        with pytest.raises((ValueError, IndexError)):
            householder_qr(A)

    def test_single_element(self):
        """Teste matriz 1x1."""
        A = np.array([[5.0]])

        Q, R = householder_qr(A)

        assert Q.shape == (1, 1)
        assert R.shape == (1, 1)
        assert np.allclose(Q @ R, A)
        assert np.allclose(Q.T @ Q, np.eye(1))

    def test_very_small_elements(self):
        """Teste com elementos muito pequenos."""
        A = 1e-15 * np.random.randn(3, 3)

        Q, R = householder_qr(A)

        # Deve funcionar sem overflow/underflow
        assert np.allclose(A, Q @ R, rtol=1e-10)
        assert np.allclose(Q.T @ Q, np.eye(3), rtol=1e-12)

    def test_very_large_elements(self):
        """Teste com elementos muito grandes."""
        A = 1e10 * np.random.randn(3, 3)

        Q, R = householder_qr(A)

        # Deve funcionar sem overflow
        assert np.allclose(A, Q @ R, rtol=1e-12)
        assert np.allclose(Q.T @ Q, np.eye(3), rtol=1e-12)


if __name__ == "__main__":
    # Executar testes se chamado diretamente
    pytest.main([__file__, "-v"])
