#!/usr/bin/env python
"""
Monte‑Carlo Bernoulli–fractal simulator (CLI + importable).
Usage example:
    python mc_sim.py --N 10000 --steps 10000 --alpha 0.3 --beta 0.02 --outcsv ../paper_data/run.csv
"""
import argparse, time, csv, pathlib, networkx as nx, numpy as np
from typing import Callable

# ── core step ───────────────────────────────────────────────────────
def bernoulli_step(G, alpha: float, beta: float, Lambda_func: Callable[[int], float], t: int, rng):
    for u in G.nodes:
        k = G.degree[u]
        if rng.random() < np.exp(-alpha * k):
            v = rng.choice(G.nodes)
            G.add_edge(u, v)
        if G.degree[u] and rng.random() < beta:
            v = rng.choice(list(G.neighbors(u)))
            G.remove_edge(u, v)
    # rupture term Λ
    Lambda = Lambda_func(t)
    for _ in range(int(Lambda * G.number_of_nodes())):
        u = rng.choice(G.nodes)
        if G.degree[u]:
            v = rng.choice(list(G.neighbors(u)))
            G.remove_edge(u, v)
    return G

# ── public function -------------------------------------------------
def run_sim(N: int, steps: int, alpha: float, beta: float,
            seed: int = 0, Lambda_func: Callable[[int], float] = lambda t: 0.):
    rng = np.random.default_rng(seed)
    G = nx.gnm_random_graph(N, N * 3, seed=seed)
    for t in range(steps):
        bernoulli_step(G, alpha, beta, Lambda_func, t, rng)
    return G

# ── CLI -------------------------------------------------------------
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--N", type=int, default=10000)
    p.add_argument("--steps", type=int, default=10000)
    p.add_argument("--alpha", type=float, default=0.3)
    p.add_argument("--beta", type=float, default=0.02)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--outcsv", default=None)
    args = p.parse_args()

    t0 = time.time()
    G = run_sim(args.N, args.steps, args.alpha, args.beta, args.seed)
    runtime = time.time() - t0

    from box_count_dimension import box_count_dimension
    D1, ci_low, ci_high = box_count_dimension(G, q=1, bootstrap=200)
    print(f"D1={D1:.3f}  CI=[{ci_low:.3f},{ci_high:.3f}]  runtime={runtime:.1f}s")

    if args.outcsv:
        path = pathlib.Path(args.outcsv)
        path.parent.mkdir(exist_ok=True)
        header = not path.exists()
        with path.open("a", newline="") as f:
            w = csv.writer(f)
            if header:
                w.writerow(["N","steps","alpha","beta","seed","D1","ci_low","ci_high","runtime"])
            w.writerow([args.N,args.steps,args.alpha,args.beta,args.seed,
                        f"{D1:.3f}",f"{ci_low:.3f}",f"{ci_high:.3f}",f"{runtime:.1f}"])

if __name__ == "__main__":
    main()