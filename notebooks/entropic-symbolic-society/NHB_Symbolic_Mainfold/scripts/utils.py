"""
utils.py — Shared utilities for the Symbolic Manifolds analysis pipeline.

This module centralizes common functionality used across notebooks:
- Robust project root discovery and path management
- Reproducibility helpers (random seeds)
- Safe I/O for DataFrames and GraphML
- Metadata helpers (embedding columns, optimal clusters)
"""

from __future__ import annotations

import json
import logging
import os
import random
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

try:
    import networkx as nx
except Exception:  # pragma: no cover
    nx = None  # type: ignore

__all__ = [
    "get_root_path",
    "resolve_paths",
    "set_seeds",
    "ensure_dir",
    "save_dataframe",
    "load_csv",
    "load_graphml",
    "save_graphml",
    "find_embedding_columns",
    "read_optimal_clusters",
]

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------

_log = logging.getLogger("symbolic_utils")
if not _log.handlers:
    _handler = logging.StreamHandler(stream=sys.stdout)
    _fmt = logging.Formatter("[%(levelname)s] %(message)s")
    _handler.setFormatter(_fmt)
    _log.addHandler(_handler)
    _log.setLevel(logging.INFO)


# -----------------------------------------------------------------------------
# Paths & Environment
# -----------------------------------------------------------------------------


def get_root_path() -> Path:
    """
    Discover the project root directory.

    Strategy:
      1) Respect explicit override via ENV: PROJECT_ROOT
      2) Walk upwards from CWD looking for a sentinel: README.md
      3) Fallback to CWD if nothing else found

    Returns
    -------
    Path
        Path to the project root directory.
    """
    env_override = os.getenv("PROJECT_ROOT")
    if env_override:
        p = Path(env_override).expanduser().resolve()
        if p.exists():
            return p

    current = Path.cwd().resolve()
    sentinel = "README.md"
    while current != current.parent:
        if (current / sentinel).exists():
            return current
        current = current.parent
    return Path.cwd().resolve()


def ensure_dir(p: Path) -> Path:
    """Create directory if it does not exist and return the path."""
    p.mkdir(parents=True, exist_ok=True)
    return p


def resolve_paths() -> Tuple[Path, Path, Path]:
    """
    Resolve and (if necessary) create ROOT, DATA, RESULTS directories.

    Returns
    -------
    (ROOT, DATA, RESULTS): tuple of Paths
    """
    root = get_root_path()
    data = ensure_dir(root / "data")
    results = ensure_dir(root / "results")
    _log.info(f"ROOT: {root}")
    _log.info(f"DATA: {data}")
    _log.info(f"RESULTS: {results}")
    return root, data, results


# -----------------------------------------------------------------------------
# Reproducibility
# -----------------------------------------------------------------------------


def set_seeds(seed: int = 42) -> None:
    """
    Set global random seeds for reproducibility across common libraries.
    """
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)
    np.random.seed(seed)
    try:
        import torch  # type: ignore

        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)  # type: ignore[attr-defined]
    except Exception:
        pass
    _log.info(f"Seeds set to {seed}.")


# -----------------------------------------------------------------------------
# Data I/O
# -----------------------------------------------------------------------------


def save_dataframe(df: pd.DataFrame, path: Path, index: bool = False) -> None:
    """
    Save a DataFrame to CSV with safe defaults and logging.
    """
    path = Path(path)
    ensure_dir(path.parent)
    df.to_csv(path, index=index)
    _log.info(f"DataFrame saved: {path}")


def load_csv(path: Path, **kwargs) -> pd.DataFrame:
    """
    Load a CSV file with pandas and basic validation.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"CSV not found: {path}")
    df = pd.read_csv(path, **kwargs)
    _log.info(f"Loaded CSV: {path} shape={df.shape}")
    return df


def load_graphml(path: Path):
    """
    Load a GraphML file with networkx. Ensures weight attribute is float if present.
    """
    if nx is None:
        raise ImportError("networkx is required to load GraphML files.")
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"GraphML not found: {path}")
    G = nx.read_graphml(path)
    # Coerce weights to float if present
    for u, v, d in G.edges(data=True):
        if "weight" in d:
            try:
                d["weight"] = float(d["weight"])
            except Exception:
                pass
    _log.info(
        f"Loaded graph: {path} | nodes={G.number_of_nodes()} edges={G.number_of_edges()}"
    )
    return G


def save_graphml(G, path: Path) -> None:
    """
    Save a graph to GraphML with networkx.
    """
    if nx is None:
        raise ImportError("networkx is required to save GraphML files.")
    path = Path(path)
    ensure_dir(path.parent)
    nx.write_graphml(G, path)
    _log.info(f"Graph saved: {path}")


# -----------------------------------------------------------------------------
# Metadata helpers
# -----------------------------------------------------------------------------


def find_embedding_columns(df: pd.DataFrame, prefix: str = "emb_") -> List[str]:
    """
    Return a list of embedding columns with a given prefix. Raise if none found.
    """
    cols = [c for c in df.columns if c.startswith(prefix)]
    if not cols:
        raise RuntimeError(f"No embedding columns found with prefix '{prefix}'.")
    return cols


def read_optimal_clusters(path: Path) -> Dict[str, object]:
    """
    Read optimal cluster metadata JSON produced by Notebook 05.
    Returns an empty dict if file does not exist.
    """
    path = Path(path)
    if not path.exists():
        _log.warning(f"Optimal clusters metadata not found: {path}")
        return {}
    with open(path, "r") as f:
        meta = json.load(f)
    _log.info(f"Loaded optimal cluster metadata from {path}: {meta}")
    return meta
