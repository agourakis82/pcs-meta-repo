from __future__ import annotations
from typing import Optional
import numpy as np
import pandas as pd

# Optional deps guarded to avoid import-time failures
try:  # igraph is optional but recommended
    import igraph as ig  # type: ignore
except Exception:  # pragma: no cover - allow import of module without igraph
    ig = None  # type: ignore

try:  # GraphRicciCurvature is optional
    from GraphRicciCurvature.OllivierRicci import OllivierRicci  # type: ignore
except Exception:  # pragma: no cover
    OllivierRicci = None  # type: ignore


def _entropy_row(probs: np.ndarray) -> float:
    # Stable entropy computation without numba
    p = probs[(probs > 0) & np.isfinite(probs)]
    if p.size == 0:
        return 0.0
    return float(-(p * np.log(p)).sum())


def transition_entropy(g) -> pd.DataFrame:
    """Compute transition entropy per node using outgoing edge weights as probabilities.
    Robust to missing/NaN/negative weights; falls back to uniform when invalid.
    """
    n = g.vcount()
    ent = np.zeros(n, dtype=np.float64)
    has_weight_attr = "weight" in g.es.attributes()
    for v in range(n):
        nbrs = g.successors(v)
        if not nbrs:
            ent[v] = 0.0
            continue
        # Collect weights robustly
        w_list = []
        for u in nbrs:
            try:
                if has_weight_attr:
                    eid = g.get_eid(v, u)
                    w = g.es[eid].get("weight", 1.0)
                else:
                    w = 1.0
                w = float(w)
            except Exception:
                w = 1.0
            if not np.isfinite(w) or w < 0:
                w = 0.0
            w_list.append(w)
        weights = np.asarray(w_list, dtype=np.float64)
        wsum = float(np.nansum(weights))
        if wsum <= 0:
            # Fallback to uniform distribution over neighbors
            probs = np.full(len(nbrs), 1.0 / len(nbrs), dtype=np.float64)
        else:
            probs = weights / wsum
        ent[v] = _entropy_row(probs)
    names = g.vs["name"] if "name" in g.vs.attributes() else list(range(n))
    return pd.DataFrame({"name": names, "entropy": ent})


def ricci_curvature(g, alpha: float = 0.5) -> pd.DataFrame:
    """Compute Ollivier-Ricci curvature and return per-node average of incident edges."""
    # If ORC lib unavailable, return NaNs
    if OllivierRicci is None:
        return pd.DataFrame({"name": g.vs["name"], "curvature": np.nan})

    # Convert to networkx for ORC library
    import networkx as nx  # type: ignore

    H = nx.DiGraph()
    H.add_nodes_from(g.vs["name"])  # type: ignore[index]
    for e in g.es:
        u = g.vs[e.tuple[0]]["name"]
        v = g.vs[e.tuple[1]]["name"]
        w = e["weight"] if "weight" in g.es.attributes() else 1.0
        H.add_edge(u, v, weight=float(w))
    # Undirected for curvature stability
    UG = nx.Graph()
    for u, v, d in H.edges(data=True):
        w = float(d.get("weight", 1.0))
        if UG.has_edge(u, v):
            UG[u][v]["weight"] += w
        else:
            UG.add_edge(u, v, weight=w)
    # Force single-process to avoid sandboxed multiprocessing errors
    orc = OllivierRicci(UG, alpha=alpha, verbose="ERROR", proc=1)
    try:
        orc.compute_ricci_curvature()
    except Exception:
        # In restricted environments where multiprocessing locks are unavailable,
        # return NaN curvature to keep pipeline functional.
        return pd.DataFrame({"name": list(UG.nodes), "curvature": np.nan})
    # Average incident edge curvature per node
    curv = {n: [] for n in UG.nodes}
    for u, v, d in UG.edges(data=True):
        k = d.get("ricciCurvature", 0.0)
        curv[u].append(k)
        curv[v].append(k)
    node_curv = {n: (float(np.mean(v)) if v else 0.0) for n, v in curv.items()}
    return pd.DataFrame({"name": list(node_curv.keys()), "curvature": list(node_curv.values())})


def meso_coherence(g, resolution: float = 1.0) -> pd.DataFrame:
    """Community coherence via Leiden clustering modularity as a proxy.
    Returns per-node community label and graph-level modularity copied to each node as 'coherence'.
    """
    try:
        import leidenalg as la  # optional
    except Exception:
        la = None
    ug = g.as_undirected()
    if la is None:
        parts = ug.community_multilevel()
        membership = parts.membership
        mod = ug.modularity(membership)
    else:
        part = la.find_partition(ug, la.RBConfigurationVertexPartition, resolution_parameter=resolution)
        membership = part.membership  # type: ignore[attr-defined]
        mod = float(part.quality())
    return pd.DataFrame({"name": ug.vs["name"], "community": membership, "coherence": mod})


def compute_kec_metrics(g) -> pd.DataFrame:
    """Compute entropy, curvature, and coherence for an igraph graph."""
    if ig is None:
        raise ImportError("igraph is required for compute_kec_metrics; please install python-igraph")
    ent = transition_entropy(g)
    curv = ricci_curvature(g)
    coh = meso_coherence(g)
    out = ent.merge(curv, on="name", how="left").merge(coh, on="name", how="left")
    return out
