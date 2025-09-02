import igraph as ig
from pcs_toolbox import compute_kec_metrics


def test_kec_metrics_shapes():
    g = ig.Graph(directed=True)
    g.add_vertices(["a", "b", "c"]) 
    g.add_edges([(0, 1), (1, 2), (2, 0)])
    g.es["weight"] = [1.0, 2.0, 3.0]
    df = compute_kec_metrics(g)
    assert set(["name", "entropy", "curvature", "community", "coherence"]) <= set(df.columns)
    assert len(df) == 3