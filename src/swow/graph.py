"""
SWOW Graph Construction Module

Builds semantic networks from SWOW association data and provides graph analysis utilities.
Supports all SWOW languages (EN, ES, ZH, NL) with standardized graph construction.

Author: PCS Meta-Repo
License: MIT
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple
import logging
import networkx as nx
import igraph as ig
from collections import defaultdict, Counter

# Set up logging
logger = logging.getLogger(__name__)


def build_swow_graph(
    df: pd.DataFrame,
    graph_type: str = "igraph",
    directed: bool = True,
    weight_column: Optional[str] = None,
    min_weight: float = 0.0,
    max_nodes: Optional[int] = None,
) -> Union[ig.Graph, nx.Graph]:
    """
    Build a graph from SWOW association data.

    Args:
        df: DataFrame with cue-response pairs
        graph_type: Type of graph to build ("igraph" or "networkx")
        directed: Whether to build directed graph
        weight_column: Column to use for edge weights
        min_weight: Minimum weight threshold
        max_nodes: Maximum number of nodes (for sampling)

    Returns:
        Graph object (igraph.Graph or networkx.Graph)
    """

    logger.info(f"Building {graph_type} graph from {len(df):,} associations")

    # Validate input
    required_cols = ["cue", "response"]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Required column '{col}' not found in DataFrame")

    # Clean data
    df_clean = df.dropna(subset=required_cols).copy()
    df_clean = df_clean[df_clean["cue"] != df_clean["response"]]  # Remove self-loops

    # Apply weight filtering if specified
    if weight_column and weight_column in df_clean.columns:
        df_clean = df_clean[df_clean[weight_column] >= min_weight]
        logger.info(
            f"Filtered to {len(df_clean):,} associations with weight >= {min_weight}"
        )

    # Sample nodes if requested
    if max_nodes:
        all_nodes = set(df_clean["cue"]) | set(df_clean["response"])
        if len(all_nodes) > max_nodes:
            # Sample most frequent nodes
            node_counts = Counter(list(df_clean["cue"]) + list(df_clean["response"]))
            top_nodes = set([node for node, _ in node_counts.most_common(max_nodes)])
            df_clean = df_clean[
                df_clean["cue"].isin(top_nodes) & df_clean["response"].isin(top_nodes)
            ]
            logger.info(f"Sampled to {max_nodes} most frequent nodes")

    # Build graph based on type
    if graph_type.lower() == "igraph":
        return _build_igraph(df_clean, directed, weight_column)
    elif graph_type.lower() == "networkx":
        return _build_networkx_graph(df_clean, directed, weight_column)
    else:
        raise ValueError(f"Unsupported graph type: {graph_type}")


def _build_igraph(
    df: pd.DataFrame, directed: bool, weight_column: Optional[str]
) -> ig.Graph:
    """Build igraph.Graph from SWOW data."""

    # Create edge list
    edges = list(zip(df["cue"], df["response"]))

    # Get unique nodes
    nodes = sorted(set(df["cue"]) | set(df["response"]))

    # Create graph
    g = ig.Graph(directed=directed)
    g.add_vertices(nodes)
    g.add_edges(edges)

    # Add edge weights if specified
    if weight_column and weight_column in df.columns:
        # Create weight mapping
        weight_map = {}
        for _, row in df.iterrows():
            edge_key = (row["cue"], row["response"])
            if edge_key in weight_map:
                weight_map[edge_key] += row[weight_column]
            else:
                weight_map[edge_key] = row[weight_column]

        # Apply weights to edges
        weights = []
        for edge in g.es:
            source = g.vs[edge.source]["name"]
            target = g.vs[edge.target]["name"]
            weight = weight_map.get((source, target), 1.0)
            weights.append(float(weight))

        g.es["weight"] = weights
    else:
        # Count multiple edges as weights
        edge_counts = defaultdict(int)
        for edge in edges:
            edge_counts[edge] += 1

        weights = []
        for edge in g.es:
            source = g.vs[edge.source]["name"]
            target = g.vs[edge.target]["name"]
            weight = edge_counts.get((source, target), 1)
            weights.append(float(weight))

        g.es["weight"] = weights

    # Add metadata
    g["language"] = "unknown"
    g["dataset"] = "SWOW"
    g["directed"] = directed
    g["n_associations"] = len(df)

    logger.info(f"Built igraph with {g.vcount()} nodes and {g.ecount()} edges")

    return g


def _build_networkx_graph(
    df: pd.DataFrame, directed: bool, weight_column: Optional[str]
) -> nx.Graph:
    """Build NetworkX graph from SWOW data."""

    # Create appropriate graph type
    if directed:
        G = nx.DiGraph()
    else:
        G = nx.Graph()

    # Add edges with weights
    for _, row in df.iterrows():
        cue = row["cue"]
        response = row["response"]

        if weight_column and weight_column in df.columns:
            weight = row[weight_column]
        else:
            weight = 1.0

        if G.has_edge(cue, response):
            G[cue][response]["weight"] += weight
        else:
            G.add_edge(cue, response, weight=weight)

    # Add metadata
    G.graph["language"] = "unknown"
    G.graph["dataset"] = "SWOW"
    G.graph["directed"] = directed
    G.graph["n_associations"] = len(df)

    logger.info(
        f"Built NetworkX graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges"
    )

    return G


def validate_graph(graph: Union[ig.Graph, nx.Graph]) -> Dict[str, Any]:
    """
    Validate and analyze a SWOW graph.

    Args:
        graph: Graph to validate

    Returns:
        Dictionary with validation results and basic statistics
    """

    validation = {"valid": True, "issues": [], "statistics": {}, "recommendations": []}

    try:
        if isinstance(graph, ig.Graph):
            validation["statistics"] = _analyze_igraph(graph)
        elif isinstance(graph, (nx.Graph, nx.DiGraph)):
            validation["statistics"] = _analyze_networkx_graph(graph)
        else:
            validation["valid"] = False
            validation["issues"].append(f"Unsupported graph type: {type(graph)}")
            return validation

        # Check for common issues
        stats = validation["statistics"]

        # Check connectivity
        if stats.get("n_components", 1) > 1:
            validation["issues"].append(
                f"Graph has {stats['n_components']} disconnected components"
            )
            validation["recommendations"].append(
                "Consider filtering to largest connected component"
            )

        # Check for isolated nodes
        if stats.get("isolated_nodes", 0) > 0:
            validation["issues"].append(
                f"Graph has {stats['isolated_nodes']} isolated nodes"
            )
            validation["recommendations"].append("Consider removing isolated nodes")

        # Check density
        density = stats.get("density", 0)
        if density < 0.001:
            validation["issues"].append(
                f"Graph is very sparse (density: {density:.6f})"
            )
            validation["recommendations"].append(
                "Consider increasing minimum weight threshold"
            )
        elif density > 0.1:
            validation["issues"].append(f"Graph is very dense (density: {density:.3f})")
            validation["recommendations"].append("Consider applying stronger filtering")

        # Check for self-loops
        if stats.get("self_loops", 0) > 0:
            validation["issues"].append(f"Graph has {stats['self_loops']} self-loops")
            validation["recommendations"].append("Consider removing self-loops")

    except Exception as e:
        validation["valid"] = False
        validation["issues"].append(f"Error during validation: {e}")

    return validation


def _analyze_igraph(graph: ig.Graph) -> Dict[str, Any]:
    """Analyze igraph.Graph and return statistics."""

    stats = {
        "n_nodes": graph.vcount(),
        "n_edges": graph.ecount(),
        "directed": graph.is_directed(),
        "density": graph.density(),
        "n_components": len(graph.components()),
        "isolated_nodes": sum(1 for v in graph.vs if graph.degree(v) == 0),
        "self_loops": sum(1 for e in graph.es if e.source == e.target),
    }

    # Add degree statistics
    degrees = graph.degree()
    stats["degree_stats"] = {
        "mean": np.mean(degrees),
        "std": np.std(degrees),
        "min": min(degrees),
        "max": max(degrees),
        "median": np.median(degrees),
    }

    # Add weight statistics if available
    if "weight" in graph.es.attributes():
        weights = graph.es["weight"]
        stats["weight_stats"] = {
            "mean": np.mean(weights),
            "std": np.std(weights),
            "min": min(weights),
            "max": max(weights),
            "median": np.median(weights),
        }

    return stats


def _analyze_networkx_graph(graph: nx.Graph) -> Dict[str, Any]:
    """Analyze NetworkX graph and return statistics."""

    stats = {
        "n_nodes": graph.number_of_nodes(),
        "n_edges": graph.number_of_edges(),
        "directed": graph.is_directed(),
        "density": nx.density(graph),
        "isolated_nodes": len(list(nx.isolates(graph))),
        "self_loops": nx.number_of_selfloops(graph),
    }

    # Component analysis
    if graph.is_directed():
        stats["n_components"] = nx.number_weakly_connected_components(graph)
    else:
        stats["n_components"] = nx.number_connected_components(graph)

    # Degree statistics
    if graph.number_of_nodes() > 0:
        degrees = [d for n, d in graph.degree()]
        stats["degree_stats"] = {
            "mean": np.mean(degrees),
            "std": np.std(degrees),
            "min": min(degrees),
            "max": max(degrees),
            "median": np.median(degrees),
        }

    # Weight statistics if available
    weights = [d.get("weight", 1.0) for u, v, d in graph.edges(data=True)]
    if weights:
        stats["weight_stats"] = {
            "mean": np.mean(weights),
            "std": np.std(weights),
            "min": min(weights),
            "max": max(weights),
            "median": np.median(weights),
        }

    return stats


def save_graph(
    graph: Union[ig.Graph, nx.Graph], output_path: Path, format: str = "auto"
) -> None:
    """
    Save graph to file.

    Args:
        graph: Graph to save
        output_path: Output file path
        format: Output format (auto, graphml, gml, pickle)
    """

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Determine format from extension if auto
    if format == "auto":
        suffix = output_path.suffix.lower()
        if suffix == ".graphml":
            format = "graphml"
        elif suffix == ".gml":
            format = "gml"
        elif suffix in [".pkl", ".pickle"]:
            format = "pickle"
        else:
            format = "graphml"  # Default

    try:
        if isinstance(graph, ig.Graph):
            if format == "graphml":
                graph.write_graphml(str(output_path))
            elif format == "gml":
                graph.write_gml(str(output_path))
            elif format == "pickle":
                graph.write_pickle(str(output_path))
            else:
                raise ValueError(f"Unsupported format for igraph: {format}")

        elif isinstance(graph, (nx.Graph, nx.DiGraph)):
            if format == "graphml":
                nx.write_graphml(graph, output_path)
            elif format == "gml":
                nx.write_gml(graph, output_path)
            elif format == "pickle":
                import pickle

                with open(output_path, "wb") as f:
                    pickle.dump(graph, f)
            else:
                raise ValueError(f"Unsupported format for NetworkX: {format}")

        logger.info(f"Saved graph to {output_path}")

    except Exception as e:
        logger.error(f"Error saving graph: {e}")
        raise


def load_graph(input_path: Path, graph_type: str = "auto") -> Union[ig.Graph, nx.Graph]:
    """
    Load graph from file.

    Args:
        input_path: Input file path
        graph_type: Type of graph to load (auto, igraph, networkx)

    Returns:
        Loaded graph
    """

    if not input_path.exists():
        raise FileNotFoundError(f"Graph file not found: {input_path}")

    suffix = input_path.suffix.lower()

    try:
        if graph_type == "igraph" or (
            graph_type == "auto" and suffix in [".gml", ".graphml"]
        ):
            if suffix == ".graphml":
                return ig.Graph.Read_GraphML(str(input_path))
            elif suffix == ".gml":
                return ig.Graph.Read_GML(str(input_path))
            elif suffix in [".pkl", ".pickle"]:
                return ig.Graph.Read_Pickle(str(input_path))

        elif graph_type == "networkx" or graph_type == "auto":
            if suffix == ".graphml":
                return nx.read_graphml(input_path)
            elif suffix == ".gml":
                return nx.read_gml(input_path)
            elif suffix in [".pkl", ".pickle"]:
                import pickle

                with open(input_path, "rb") as f:
                    return pickle.load(f)

        raise ValueError(f"Cannot determine how to load {input_path}")

    except Exception as e:
        logger.error(f"Error loading graph: {e}")
        raise


def get_largest_component(
    graph: Union[ig.Graph, nx.Graph],
) -> Union[ig.Graph, nx.Graph]:
    """Extract the largest connected component from a graph."""

    if isinstance(graph, ig.Graph):
        components = graph.components()
        if len(components) == 1:
            return graph

        largest_component = max(components, key=len)
        return graph.subgraph(largest_component)

    elif isinstance(graph, (nx.Graph, nx.DiGraph)):
        if graph.is_directed():
            components = list(nx.weakly_connected_components(graph))
        else:
            components = list(nx.connected_components(graph))

        if len(components) == 1:
            return graph

        largest_component = max(components, key=len)
        return graph.subgraph(largest_component).copy()

    else:
        raise ValueError(f"Unsupported graph type: {type(graph)}")
