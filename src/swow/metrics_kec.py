"""
SWOW KEC Metrics Module

Computes Knowledge, Entropy, and Curvature metrics for SWOW semantic networks.
Integrates with the main pcs_toolbox.kec module while providing SWOW-specific functionality.

Author: PCS Meta-Repo
License: MIT
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple
import logging
import sys

# Add parent directory to path for pcs_toolbox imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from pcs_toolbox.kec import (
        compute_kec_metrics,
        transition_entropy,
        ricci_curvature,
        meso_coherence,
    )

    KEC_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Could not import pcs_toolbox.kec: {e}")
    KEC_AVAILABLE = False

# Set up logging
logger = logging.getLogger(__name__)


def compute_swow_kec_metrics(
    graph,
    language: str = "unknown",
    output_dir: Optional[Path] = None,
    save_individual: bool = True,
    alpha: float = 0.5,
    resolution: float = 1.0,
) -> pd.DataFrame:
    """
    Compute comprehensive KEC metrics for SWOW graph.

    Args:
        graph: igraph.Graph object
        language: Language code for the dataset
        output_dir: Directory to save individual metric files
        save_individual: Whether to save individual metric files
        alpha: Alpha parameter for Ricci curvature
        resolution: Resolution parameter for community detection

    Returns:
        DataFrame with all KEC metrics
    """

    if not KEC_AVAILABLE:
        raise ImportError("pcs_toolbox.kec is required but not available")

    logger.info(f"Computing KEC metrics for {language} SWOW graph")
    logger.info(f"Graph: {graph.vcount()} nodes, {graph.ecount()} edges")

    try:
        # Compute all metrics using the main KEC module
        kec_df = compute_kec_metrics(graph)

        # Add language metadata
        kec_df["language"] = language
        kec_df["dataset"] = "SWOW"

        # Validate results
        validation = _validate_kec_results(kec_df, graph)
        if not validation["valid"]:
            logger.warning(f"KEC validation issues: {validation['issues']}")

        # Save individual metric files if requested
        if save_individual and output_dir:
            _save_individual_metrics(kec_df, output_dir, language)

        logger.info(f"Successfully computed KEC metrics for {len(kec_df)} nodes")
        return kec_df

    except Exception as e:
        logger.error(f"Error computing KEC metrics: {e}")
        raise


def compute_entropy_only(
    graph, language: str = "unknown", smoothing: str = "teleport", epsilon: float = 1e-6
) -> pd.DataFrame:
    """
    Compute only entropy metrics (faster alternative).

    Args:
        graph: igraph.Graph object
        language: Language code
        smoothing: Smoothing method for entropy computation
        epsilon: Small value for numerical stability

    Returns:
        DataFrame with entropy metrics
    """

    if not KEC_AVAILABLE:
        raise ImportError("pcs_toolbox.kec is required but not available")

    logger.info(f"Computing entropy metrics for {language} SWOW graph")

    try:
        entropy_df = transition_entropy(graph)
        entropy_df["language"] = language
        entropy_df["dataset"] = "SWOW"

        logger.info(f"Computed entropy for {len(entropy_df)} nodes")
        return entropy_df

    except Exception as e:
        logger.error(f"Error computing entropy: {e}")
        raise


def compute_curvature_only(
    graph, language: str = "unknown", alpha: float = 0.5, sample_fraction: float = 1.0
) -> pd.DataFrame:
    """
    Compute only curvature metrics.

    Args:
        graph: igraph.Graph object
        language: Language code
        alpha: Alpha parameter for Ricci curvature
        sample_fraction: Fraction of edges to sample for large graphs

    Returns:
        DataFrame with curvature metrics
    """

    if not KEC_AVAILABLE:
        raise ImportError("pcs_toolbox.kec is required but not available")

    logger.info(f"Computing curvature metrics for {language} SWOW graph")

    try:
        # Sample graph if too large
        if sample_fraction < 1.0 and graph.ecount() > 10000:
            logger.info(
                f"Sampling {sample_fraction:.1%} of edges for curvature computation"
            )
            # This would require implementing edge sampling - for now, use full graph

        curvature_df = ricci_curvature(graph, alpha=alpha)
        curvature_df["language"] = language
        curvature_df["dataset"] = "SWOW"

        logger.info(f"Computed curvature for {len(curvature_df)} nodes")
        return curvature_df

    except Exception as e:
        logger.error(f"Error computing curvature: {e}")
        raise


def compute_coherence_only(
    graph, language: str = "unknown", resolution: float = 1.0, method: str = "leiden"
) -> pd.DataFrame:
    """
    Compute only coherence metrics.

    Args:
        graph: igraph.Graph object
        language: Language code
        resolution: Resolution parameter for community detection
        method: Community detection method

    Returns:
        DataFrame with coherence metrics
    """

    if not KEC_AVAILABLE:
        raise ImportError("pcs_toolbox.kec is required but not available")

    logger.info(f"Computing coherence metrics for {language} SWOW graph")

    try:
        coherence_df = meso_coherence(graph, resolution=resolution)
        coherence_df["language"] = language
        coherence_df["dataset"] = "SWOW"

        logger.info(f"Computed coherence for {len(coherence_df)} nodes")
        return coherence_df

    except Exception as e:
        logger.error(f"Error computing coherence: {e}")
        raise


def _validate_kec_results(kec_df: pd.DataFrame, graph) -> Dict[str, Any]:
    """Validate KEC computation results."""

    validation = {"valid": True, "issues": [], "statistics": {}}

    try:
        # Check expected columns
        expected_cols = ["name", "entropy", "curvature", "coherence"]
        missing_cols = [col for col in expected_cols if col not in kec_df.columns]
        if missing_cols:
            validation["issues"].append(f"Missing columns: {missing_cols}")
            validation["valid"] = False

        # Check number of nodes matches
        if len(kec_df) != graph.vcount():
            validation["issues"].append(
                f"Node count mismatch: KEC={len(kec_df)}, Graph={graph.vcount()}"
            )
            validation["valid"] = False

        # Check for NaN values
        for col in ["entropy", "curvature", "coherence"]:
            if col in kec_df.columns:
                nan_count = kec_df[col].isna().sum()
                if nan_count > 0:
                    validation["issues"].append(f"{col}: {nan_count} NaN values")

                # Compute statistics
                validation["statistics"][col] = {
                    "mean": float(kec_df[col].mean()),
                    "std": float(kec_df[col].std()),
                    "min": float(kec_df[col].min()),
                    "max": float(kec_df[col].max()),
                    "nan_count": int(nan_count),
                }

        # Check value ranges
        if "entropy" in kec_df.columns:
            entropy_values = kec_df["entropy"].dropna()
            if len(entropy_values) > 0:
                if entropy_values.min() < 0:
                    validation["issues"].append("Negative entropy values found")
                if entropy_values.max() > 10:  # Reasonable upper bound
                    validation["issues"].append("Unusually high entropy values found")

        if "coherence" in kec_df.columns:
            coherence_values = kec_df["coherence"].dropna()
            if len(coherence_values) > 0:
                if coherence_values.min() < -1 or coherence_values.max() > 1:
                    validation["issues"].append(
                        "Coherence values outside expected range [-1, 1]"
                    )

    except Exception as e:
        validation["valid"] = False
        validation["issues"].append(f"Validation error: {e}")

    return validation


def _save_individual_metrics(
    kec_df: pd.DataFrame, output_dir: Path, language: str
) -> None:
    """Save individual metric files."""

    output_dir.mkdir(parents=True, exist_ok=True)

    # Save individual metrics as parquet files
    metrics = ["entropy", "curvature", "coherence"]

    for metric in metrics:
        if metric in kec_df.columns:
            # Create metric-specific DataFrame
            if metric == "entropy":
                metric_df = kec_df[["name", "entropy"]].copy()
                metric_df = metric_df.rename(columns={"entropy": "H"})
            elif metric == "curvature":
                metric_df = kec_df[["name", "curvature"]].copy()
                metric_df = metric_df.rename(columns={"curvature": "kappa"})
            elif metric == "coherence":
                metric_df = kec_df[["name", "coherence", "community"]].copy()
                metric_df = metric_df.rename(columns={"coherence": "Q"})

            # Add metadata columns
            metric_df["language"] = language
            metric_df["dataset"] = "SWOW"
            metric_df = metric_df.rename(columns={"name": "node"})

            # Save as parquet
            output_path = output_dir / f"{metric}.parquet"
            metric_df.to_parquet(output_path, index=False)

            logger.info(f"Saved {metric} metrics to {output_path}")


def load_kec_metrics(
    language: str, base_dir: Optional[Path] = None, format: str = "parquet"
) -> Dict[str, pd.DataFrame]:
    """
    Load previously computed KEC metrics.

    Args:
        language: Language code
        base_dir: Base directory for KEC files
        format: File format (parquet, csv)

    Returns:
        Dictionary with loaded metrics
    """

    if base_dir is None:
        base_dir = (
            Path(__file__).parent.parent.parent
            / "data"
            / "L2_derived"
            / "kec"
            / language
        )

    metrics = {}
    metric_names = ["entropy", "curvature", "coherence"]

    for metric in metric_names:
        if format == "parquet":
            file_path = base_dir / f"{metric}.parquet"
        else:
            file_path = base_dir / f"{metric}.csv"

        if file_path.exists():
            try:
                if format == "parquet":
                    metrics[metric] = pd.read_parquet(file_path)
                else:
                    metrics[metric] = pd.read_csv(file_path)

                logger.info(f"Loaded {metric} metrics: {len(metrics[metric])} nodes")

            except Exception as e:
                logger.error(f"Error loading {metric} metrics: {e}")
        else:
            logger.warning(f"KEC file not found: {file_path}")

    return metrics


def merge_kec_metrics(metrics_dict: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Merge individual KEC metrics into a single DataFrame.

    Args:
        metrics_dict: Dictionary with individual metric DataFrames

    Returns:
        Merged DataFrame with all metrics
    """

    if not metrics_dict:
        return pd.DataFrame()

    # Start with the first available metric
    base_metric = list(metrics_dict.keys())[0]
    merged_df = metrics_dict[base_metric].copy()

    # Standardize node column name
    node_col = "node" if "node" in merged_df.columns else "name"
    if node_col != "node":
        merged_df = merged_df.rename(columns={node_col: "node"})

    # Merge other metrics
    for metric_name, metric_df in metrics_dict.items():
        if metric_name == base_metric:
            continue

        # Standardize column names
        metric_df = metric_df.copy()
        if "name" in metric_df.columns and "node" not in metric_df.columns:
            metric_df = metric_df.rename(columns={"name": "node"})

        # Merge on node column
        merged_df = merged_df.merge(
            metric_df, on="node", how="outer", suffixes=("", f"_{metric_name}")
        )

    logger.info(f"Merged KEC metrics for {len(merged_df)} nodes")
    return merged_df


def compute_kec_statistics(kec_df: pd.DataFrame) -> Dict[str, Any]:
    """Compute summary statistics for KEC metrics."""

    stats = {"n_nodes": len(kec_df), "metrics": {}}

    for metric in ["entropy", "curvature", "coherence"]:
        if metric in kec_df.columns:
            values = kec_df[metric].dropna()
            if len(values) > 0:
                stats["metrics"][metric] = {
                    "count": len(values),
                    "mean": float(values.mean()),
                    "std": float(values.std()),
                    "min": float(values.min()),
                    "max": float(values.max()),
                    "median": float(values.median()),
                    "q25": float(values.quantile(0.25)),
                    "q75": float(values.quantile(0.75)),
                    "nan_count": int(kec_df[metric].isna().sum()),
                }

    return stats
