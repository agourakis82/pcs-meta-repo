from __future__ import annotations
try:
    from importlib.metadata import PackageNotFoundError, version
    __version__ = version("pcs_toolbox")
except Exception:
    __version__ = "0.0.0"
def add(a, b):
    return a + b
__all__ = ["__version__", "add"]
