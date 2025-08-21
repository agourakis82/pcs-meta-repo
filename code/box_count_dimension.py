import numpy as np

# ──────────────────────────────────────────────────────────────────────
def _shannon_entropy(freq):
    """Shannon entropy for a normalized histogram (freq ≥ 0, sum = 1)."""
    p = freq[freq > 0]
    return -np.sum(p * np.log(p))

# ──────────────────────────────────────────────────────────────────────
def box_count_dimension(G, q: float = 1, bootstrap: int = 200):
    """
    Multiscale box‑count estimate of D_q with bootstrap CI.
    Returns (D_q, CI_low, CI_high).  NaN if graph is edgeless.
    """
    deg = np.fromiter((d for _, d in G.degree()), dtype=int)
    maxdeg = deg.max(initial=0)

    # edgeless or single‑degree graphs → não definimos dimensão
    if maxdeg < 2:
        return float("nan"), float("nan"), float("nan")

    # malha log‑espalhada (6 pontos) entre 1 e maxdeg, sem zeros
    eps_float = np.geomspace(1.0, float(maxdeg), num=6)
    eps = np.unique(np.clip(eps_float.round().astype(int), 1, None))

    S = []  # entropias/geradores multifractais para cada escala
    for e in eps:
        hist, _ = np.histogram(deg, bins=range(0, maxdeg + e, e), density=True)
        if q == 1:
            S.append(_shannon_entropy(hist))
        else:
            p = hist[hist > 0]
            S.append(np.log(np.sum(p ** q)) / (1 - q))

    # regressão linear: S = –D_q · log ε   ⇒   slope = –D_q
    slope, _ = np.polyfit(np.log(eps), S, deg=1)
    Dq = -slope

    # ── bootstrap ------------------------------------------------------
    boots = []
    rng = np.random.default_rng(42)
    for _ in range(bootstrap):
        sample = rng.choice(deg, size=len(deg), replace=True)
        max_s = sample.max()
        if max_s < 2:
            continue  # pula amostra degenerada
        S_b = []
        for e in eps:
            h, _ = np.histogram(sample, bins=range(0, max_s + e, e), density=True)
            if q == 1:
                S_b.append(_shannon_entropy(h))
            else:
                p = h[h > 0]
                S_b.append(np.log(np.sum(p ** q)) / (1 - q))
        slope_b, _ = np.polyfit(np.log(eps), S_b, deg=1)
        boots.append(-slope_b)

    if len(boots) < 10:
        return Dq, float("nan"), float("nan")  # CI pouco confiável

    ci_low, ci_high = np.percentile(boots, [2.5, 97.5])
    return Dq, ci_low, ci_high