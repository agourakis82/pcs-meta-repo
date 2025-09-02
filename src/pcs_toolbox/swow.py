from __future__ import annotations
"""SWOW ingestion and graph construction (igraph backend).

Functions:
- load_swow_graph(csv_path: Path) -> igraph.Graph

Notes:
- Keeps provenance: stores path in graph['provenance'].
"""
from pathlib import Path
import pandas as pd

try:
    import igraph as ig  # type: ignore
except Exception as e:  # pragma: no cover
    ig = None  # type: ignore


def load_swow_graph(csv_path: Path):
    if ig is None:
        raise ImportError("igraph is required for SWOW graph construction")
    df = pd.read_csv(csv_path)
    # Expect columns: cue, response, weight/frequency
    cols = {c.lower(): c for c in df.columns}
    cue = cols.get("cue") or cols.get("source") or list(df.columns)[0]
    resp = cols.get("response") or cols.get("target") or list(df.columns)[1]
    w = cols.get("weight") or cols.get("frequency")
    edges = list(zip(df[cue].astype(str), df[resp].astype(str)))
    g = ig.Graph(directed=True)
    g.add_vertices(sorted(set([v for e in edges for v in e])))
    g.add_edges(edges)
    if w:
        g.es["weight"] = pd.to_numeric(df[w], errors="coerce").fillna(1.0).tolist()
    g["provenance"] = str(csv_path)
    return g
