#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

"""
compute_entropy_curvature_pro.py (safe / GitHub-Ready)
- Entropy rate (H_rate) via streaming power iteration (sem matriz densa).
- Ollivier–Ricci opcional, apenas em arestas amostradas se suportado.
- Compatível com NetworkX 3.x; fallback limpa para ambientes sem GraphRicciCurvature/POT.
- Saída CSV: graph,beta,H_rate,kappa,regime,nnodes,nedges,weight_attr,curv_method,elapsed_s
"""
import argparse
import csv
import glob
import math
import sys
import time
import warnings
from pathlib import Path
from typing import Dict, Optional

import numpy as np

try:
    import networkx as nx
except Exception as e:
    print("[FATAL] networkx not available:", e, file=sys.stderr)
    sys.exit(1)

_HAS_RICCI = False
try:
    from GraphRicciCurvature.OllivierRicci import OllivierRicci

    _HAS_RICCI = True
except Exception:
    _HAS_RICCI = False


def detect_weight_attr(G: nx.DiGraph) -> Optional[str]:
    for _, _, d in G.edges(data=True):
        if not d:
            continue
        for c in ("weight", "w", "freq", "frequency", "strength", "p", "prob"):
            if c in d:
                try:
                    float(d[c])
                    return c
                except Exception:
                    pass
        break
    return None


def load_graph(path: str) -> nx.DiGraph:
    p = path.lower()
    if p.endswith(".graphml"):
        try:
            G = nx.read_graphml(path)
        except Exception as e:
            raise RuntimeError(f"read_graphml failed, install lxml: {e}")
    elif p.endswith(".gpickle") or p.endswith(".pickle"):
        G = nx.read_gpickle(path)
    elif p.endswith(".edgelist") or p.endswith(".txt"):
        G = nx.read_edgelist(path, create_using=nx.DiGraph)
    else:
        G = nx.read_graphml(path)
    if not isinstance(G, (nx.DiGraph, nx.MultiDiGraph)):
        G = nx.DiGraph(G)
    if not G.is_directed():
        G = nx.DiGraph(G)
    return G


def neighbors_with_probs(G: nx.DiGraph, u, beta: float, wkey: Optional[str]):
    nbrs = list(G.successors(u))
    if not nbrs:
        return np.array([u]), np.array([1.0])
    ws = []
    for v in nbrs:
        d = G[u][v]
        w = (
            d.get(wkey, d.get("weight", 1.0))
            if wkey is not None
            else d.get("weight", 1.0)
        )
        try:
            w = float(w)
        except Exception:
            w = 1.0
        ws.append(max(w, 1e-12))
    ws = np.power(np.asarray(ws, dtype=float), float(beta))
    Z = ws.sum()
    probs = ws / Z if (np.isfinite(Z) and Z > 0.0) else np.full(len(ws), 1.0 / len(ws))
    return np.asarray(nbrs), probs


def entropy_rate_stream(
    G: nx.DiGraph,
    beta: float,
    wkey: Optional[str],
    max_iter: int = 200,
    tol: float = 1e-10,
) -> float:
    nodes = list(G.nodes())
    n = len(nodes)
    index = {u: i for i, u in enumerate(nodes)}
    row_probs: Dict = {}
    row_entropy = np.zeros(n, dtype=float)
    for u in nodes:
        nbrs, probs = neighbors_with_probs(G, u, beta, wkey)
        row_probs[u] = (nbrs, probs)
        with np.errstate(divide="ignore", invalid="ignore"):
            row_entropy[index[u]] = -np.sum(
                probs * np.where(probs > 0, np.log(probs), 0.0)
            )
    pi = np.full(n, 1.0 / n, dtype=float)
    nxt = np.zeros_like(pi)
    for _ in range(max_iter):
        nxt.fill(0.0)
        for u in nodes:
            i = index[u]
            p_i = pi[i]
            nbrs, probs = row_probs[u]
            for v, pv in zip(nbrs, probs):
                nxt[index[v]] += p_i * pv
        s = nxt.sum()
        if s > 0:
            nxt /= s
        if np.linalg.norm(nxt - pi, 1) < tol:
            pi = nxt
            break
        pi, nxt = nxt, pi
    return float(np.dot(pi, row_entropy))


def mean_ollivier_ricci(
    G: nx.DiGraph,
    undirected: bool,
    nsample: Optional[int],
    alpha: float = 0.5,
    method: str = "approximate",
    seed: int = 42,
):
    if not _HAS_RICCI:
        return (float("nan"), "ricci_unavailable")
    H = G.to_undirected() if undirected else G
    E = list(H.edges())
    if not E:
        return (float("nan"), "empty_graph")
    if nsample and 0 < nsample < len(E):
        import random

        rng = random.Random(seed)
        E = rng.sample(E, nsample)
        note = f"_sample{len(E)}"
    else:
        note = "_full"
    try:
        orc = OllivierRicci(H, alpha=alpha, method=method, verbose="ERROR")
        if hasattr(orc, "compute_ricci_curvature_edges"):
            orc.compute_ricci_curvature_edges(E)
        else:
            orc.compute_ricci_curvature()
        vals = []
        for u, v in E:
            d = orc.G[u][v]
            k = d.get("ricciCurvature", None)
            if k is None:
                continue
            if math.isfinite(k):
                vals.append(float(k))
        if not vals:
            return (float("nan"), f"ollivier_{method}{note}_empty")
        return (float(np.mean(vals)), f"ollivier_{method}{note}")
    except Exception as e:
        warnings.warn(f"OllivierRicci failed: {e}", stacklevel=2)
        return (float("nan"), f"ollivier_{method}_error")


def run_once(
    graph_path: str,
    beta: float,
    regime: str,
    no_curv: bool,
    curv_undirected: bool,
    curv_sample: Optional[int],
    ricci_method: str,
    seed: int,
):
    t0 = time.time()
    G = load_graph(graph_path)
    wkey = detect_weight_attr(G)
    H = entropy_rate_stream(G, beta=beta, wkey=wkey)
    if no_curv:
        kappa, method = float("nan"), "ricci_skipped"
    else:
        kappa, method = mean_ollivier_ricci(
            G,
            undirected=curv_undirected,
            nsample=curv_sample,
            alpha=0.5,
            method=ricci_method,
            seed=seed,
        )
    elapsed = time.time() - t0
    return {
        "graph": Path(graph_path).name,
        "beta": float(beta),
        "H_rate": float(H),
        "kappa": kappa,
        "regime": regime,
        "nnodes": int(G.number_of_nodes()),
        "nedges": int(G.number_of_edges()),
        "weight_attr": (wkey or ""),
        "curv_method": method,
        "elapsed_s": round(float(elapsed), 3),
    }


def main():
    ap = argparse.ArgumentParser(
        description="Compute H_rate and sampled Ollivier–Ricci curvature (memory-safe)."
    )
    ap.add_argument("--graph", required=True)
    ap.add_argument("--beta", nargs="+", type=float, default=[1.0])
    ap.add_argument("--regime", type=str, default="")
    ap.add_argument("--no-curvature", action="store_true")
    ap.add_argument("--curv-undirected", action="store_true")
    ap.add_argument("--curv-sample", type=int, default=500)
    ap.add_argument(
        "--ricci-method", choices=["approximate", "OTD", "base"], default="approximate"
    )
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    paths = sorted(sum([glob.glob(args.graph)], []))
    if not paths:
        print(f"[FATAL] no files matched {args.graph}", file=sys.stderr)
        sys.exit(2)

    rows = []
    for p in paths:
        for b in args.beta:
            rows.append(
                run_once(
                    p,
                    b,
                    args.regime,
                    args.no_curvature,
                    args.curv_undirected,
                    (
                        None
                        if args.curv_sample is None or args.curv_sample <= 0
                        else args.curv_sample
                    ),
                    args.ricci_method,
                    args.seed,
                )
            )

    header = [
        "graph",
        "beta",
        "H_rate",
        "kappa",
        "regime",
        "nnodes",
        "nedges",
        "weight_attr",
        "curv_method",
        "elapsed_s",
    ]
    with open(args.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
