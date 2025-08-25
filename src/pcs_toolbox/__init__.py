from __future__ import annotations

# __version__ com fallback quando o pacote não está instalado no ambiente
try:
    from importlib.metadata import PackageNotFoundError, version

    __version__ = version("pcs_toolbox")
except (PackageNotFoundError, Exception):  # pacote não instalado ou metadados ausentes
    __version__ = "0.0.0"


def add(a, b):
    """Somador mínimo usado nos testes."""
    return a + b


__all__ = ["__version__", "add"]
