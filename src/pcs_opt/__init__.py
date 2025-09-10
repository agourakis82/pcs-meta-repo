"""
PCS Optimization - Métodos de Otimização Numérica v4.3

Módulo de otimização com foco em problemas de mínimos quadrados
não-negativos e métodos baseados em condições KKT.

Author: PCS-HELIO Team
License: MIT
"""

from .nnls_kkt import nnls_kkt

__version__ = "4.3.0"
__all__ = [
    "nnls_kkt",
]
