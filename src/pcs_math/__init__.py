"""
PCS Math - Núcleo Numérico Estável v4.3

Módulo de métodos numéricos estáveis e reproduzíveis para o projeto PCS.
Implementa QR Householder, SVD, Gradiente Conjugado com pré-condicionadores,
e soma de Kahan para máxima estabilidade numérica.

Author: PCS-HELIO Team
License: MIT
"""

from .qr_householder import householder_qr, solve_via_qr
from .svd_solve import svd_solve, truncated_svd
from .cg_precond import cg
from .preconditioners import jacobi_precond, ichol0_precond
from .kahan import kahan_sum

__version__ = "4.3.0"
__all__ = [
    "householder_qr",
    "solve_via_qr",
    "svd_solve",
    "truncated_svd",
    "cg",
    "jacobi_precond",
    "ichol0_precond",
    "kahan_sum",
]
