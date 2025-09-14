#!/usr/bin/env python3
"""
KEC Compiler CLI for v4.4 - Multilingual, Resumable, GPU-aware
Compiles Knowledge Edge Curvature (KEC) metrics from SWOW data
"""

import argparse
import json
import logging
import warnings
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from tqdm import tqdm

# Suppress warnings
warnings.filterwarnings("ignore")

import yaml  # noqa: E402
from src.config.paths import ensure_dir, get_paths  # noqa: E402

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class KECCompiler:
    """Multilingual KEC compiler with checkpointing and GPU support."""

    def __init__(self, languages: List[str], device: str = "auto", resume: bool = True):
        self.languages = languages
        self.device = self._setup_device(device)
        self.resume = resume
        self.paths = get_paths()
        # Load KEC/SWOW params if available
        try:
            cfg_file = Path(__file__).parent.parent.parent / "config" / "swow.yaml"
            with open(cfg_file) as f:
                self._cfg = yaml.safe_load(f)
        except Exception:
            self._cfg = {}

        # Setup output directories
        for lang in languages:
            ensure_dir(f"@data_root.L2_derived/kec/{lang}")

    def _setup_device(self, device: str) -> str:
        """Setup computation device (CPU/GPU)."""
        if device == "auto":
            try:
                import torch

                device = "cuda" if torch.cuda.is_available() else "cpu"
                logger.info(f"Auto-detected device: {device}")
            except ImportError:
                device = "cpu"
                logger.info("PyTorch not available, using CPU")
        return device

    def _get_checkpoint_path(self, lang: str) -> Path:
        """Get checkpoint file path for a language."""
        output_dir = ensure_dir(f"@data_root.L2_derived/kec/{lang}")
        return output_dir / ".status.json"

    def _load_checkpoint(self, lang: str) -> Dict[str, Any]:
        """Load processing status for a language."""
        checkpoint_path = self._get_checkpoint_path(lang)
        if checkpoint_path.exists():
            with open(checkpoint_path) as f:
                data = json.load(f)
                # Robustness: ensure 'completed_steps' key exists
                if not isinstance(data, dict):
                    data = {"completed_steps": []}
                else:
                    data.setdefault("completed_steps", [])
                return data
        # Default when checkpoint does not exist
        return {"completed_steps": []}

    def _save_checkpoint(self, lang: str, step: str):
        """Save processing step completion."""
        checkpoint_path = self._get_checkpoint_path(lang)
        status = self._load_checkpoint(lang)
        if step not in status["completed_steps"]:
            status["completed_steps"].append(step)

        with open(checkpoint_path, "w") as f:
            json.dump(status, f, indent=2)

    def _is_step_complete(self, lang: str, step: str) -> bool:
        """Check if a step is already completed."""
        if not self.resume:
            return False
        status = self._load_checkpoint(lang)
        return step in status.get("completed_steps", [])

    def load_swow_data(self, lang: str) -> pd.DataFrame:
        """Load SWOW data for a language."""
        swow_paths = self.paths.get_dataset_paths("swow")
        tidy_dir = Path(swow_paths["tidy_dir"])

        # Look for language-specific file
        possible_files = [
            tidy_dir / f"swow_{lang}.csv",
            tidy_dir / f"swow_{lang}.tsv",
            tidy_dir / f"{lang}" / "swow.csv",
            tidy_dir / f"{lang}" / "swow.tsv",
        ]

        for file_path in possible_files:
            if file_path.exists():
                logger.info(f"Loading SWOW data for {lang} from {file_path}")
                if file_path.suffix == ".csv":
                    return pd.read_csv(file_path)
                else:
                    return pd.read_csv(file_path, sep="\t")

        raise FileNotFoundError(
            f"SWOW data for language '{lang}' not found in {tidy_dir}"
        )

    def build_graph(self, lang: str) -> pd.DataFrame:
        """Build word association graph from SWOW data."""
        step = "build"
        if self._is_step_complete(lang, step):
            logger.info(f"Step '{step}' already completed for {lang}, skipping")
            return self._load_edges(lang)

        logger.info(f"Building graph for {lang}")
        swow_data = self.load_swow_data(lang)

        # Build edges from SWOW data
        # Assuming columns: cue, response, strength/weight
        if "cue" in swow_data.columns and "response" in swow_data.columns:
            edges = swow_data[["cue", "response"]].copy()

            # Add weight if available
            if "strength" in swow_data.columns:
                edges["weight"] = swow_data["strength"]
            elif "weight" in swow_data.columns:
                edges["weight"] = swow_data["weight"]
            else:
                edges["weight"] = 1.0
        else:
            # Handle different column formats
            logger.warning(
                (
                    "Standard columns not found for %s, "
                    "inferring from available columns"
                )
                % lang
            )
            edges = pd.DataFrame()
            # Add fallback logic here based on actual SWOW format

        # Clean and normalize
        edges = edges.dropna()
        edges["cue"] = edges["cue"].str.lower().str.strip()
        edges["response"] = edges["response"].str.lower().str.strip()
        edges = edges[edges["cue"] != edges["response"]]  # Remove self-loops

        # Save edges
        output_path = ensure_dir(f"@data_root.L2_derived/kec/{lang}") / "edges.parquet"
        edges.to_parquet(output_path, index=False)

        self._save_checkpoint(lang, step)
        logger.info(f"Graph built for {lang}: {len(edges)} edges")
        return edges

    def _load_edges(self, lang: str) -> pd.DataFrame:
        """Load pre-computed edges."""
        output_path = ensure_dir(f"@data_root.L2_derived/kec/{lang}") / "edges.parquet"
        return pd.read_parquet(output_path)

    def compute_entropy(self, lang: str) -> pd.DataFrame:
        """Compute entropy metrics for nodes."""
        step = "entropy"
        if self._is_step_complete(lang, step):
            logger.info(f"Step '{step}' already completed for {lang}, skipping")
            return self._load_entropy(lang)

        logger.info(f"Computing entropy for {lang}")
        edges = self._load_edges(lang)

        # Group by cue to compute entropy
        entropy_data = []
        for cue, group in tqdm(edges.groupby("cue"), desc="Computing entropy"):
            weights = group["weight"].values
            weights = weights / weights.sum()  # Normalize to probabilities

            # Shannon entropy
            entropy = -np.sum(weights * np.log2(weights + 1e-10))

            entropy_data.append(
                {
                    "word": cue,
                    "entropy": entropy,
                    "out_degree": len(group),
                    "total_weight": group["weight"].sum(),
                }
            )

        entropy_df = pd.DataFrame(entropy_data)

        # Save entropy
        output_path = (
            ensure_dir(f"@data_root.L2_derived/kec/{lang}") / "entropy.parquet"
        )
        entropy_df.to_parquet(output_path, index=False)

        self._save_checkpoint(lang, step)
        logger.info(f"Entropy computed for {lang}: {len(entropy_df)} nodes")
        return entropy_df

    def _load_entropy(self, lang: str) -> pd.DataFrame:
        """Load pre-computed entropy."""
        output_path = (
            ensure_dir(f"@data_root.L2_derived/kec/{lang}") / "entropy.parquet"
        )
        return pd.read_parquet(output_path)

    def compute_curvature(self, lang: str) -> pd.DataFrame:
        """Compute curvature metrics."""
        step = "curvature"
        if self._is_step_complete(lang, step):
            logger.info(f"Step '{step}' already completed for {lang}, skipping")
            return self._load_curvature(lang)

        logger.info(f"Computing curvature for {lang}")
        edges = self._load_edges(lang)

        # Build adjacency information
        graph_dict = {}
        for _, row in edges.iterrows():
            cue, response = row["cue"], row["response"]
            if cue not in graph_dict:
                graph_dict[cue] = set()
            graph_dict[cue].add(response)

        # Compute Ollivier-Ricci curvature approximation
        curvature_data = []
        for word in tqdm(graph_dict.keys(), desc="Computing curvature"):
            neighbors = graph_dict[word]

            # Simple curvature approximation based on neighborhood overlap
            curvatures = []
            for neighbor in neighbors:
                if neighbor in graph_dict:
                    neighbor_neighbors = graph_dict[neighbor]
                    overlap = len(neighbors.intersection(neighbor_neighbors))
                    total = len(neighbors.union(neighbor_neighbors))
                    if total > 0:
                        curvatures.append(overlap / total)

            avg_curvature = np.mean(curvatures) if curvatures else 0.0

            curvature_data.append(
                {
                    "word": word,
                    "curvature": avg_curvature,
                    "neighborhood_size": len(neighbors),
                }
            )

        curvature_df = pd.DataFrame(curvature_data)

        # Save curvature
        output_path = (
            ensure_dir(f"@data_root.L2_derived/kec/{lang}") / "curvature.parquet"
        )
        curvature_df.to_parquet(output_path, index=False)

        self._save_checkpoint(lang, step)
        logger.info(f"Curvature computed for {lang}: {len(curvature_df)} nodes")
        return curvature_df

    def _load_curvature(self, lang: str) -> pd.DataFrame:
        """Load pre-computed curvature."""
        output_path = (
            ensure_dir(f"@data_root.L2_derived/kec/{lang}") / "curvature.parquet"
        )
        return pd.read_parquet(output_path)

    def compute_coherence(self, lang: str) -> pd.DataFrame:
        """Compute coherence metrics using real graph-based embeddings.

        Approach: local neighbor-distribution cosine coherence.
        For each node, build a probability vector over its top-K outgoing
        neighbors (by edge weight). The node's coherence is the average cosine
        similarity between this vector and the corresponding vectors of each
        neighbor. This yields a stable, embedding-like local coherence that
        correlates with community structure and semantic tightness.

        References:
        - Belkin & Niyogi (2003), Laplacian Eigenmaps for dimensionality reduction
        - Ollivier (2009), Ricci curvature of Markov chains on metric spaces
        - Newman (2010), Networks: An Introduction (local similarity and assortativity)
        """
        step = "coherence"
        if self._is_step_complete(lang, step):
            logger.info(f"Step '{step}' already completed for {lang}, skipping")
            return self._load_coherence(lang)

        logger.info(f"Computing coherence for {lang}")

        edges = self._load_edges(lang)

        # Hyperparameters (read from config if present)
        TOP_K = self._cfg.get("params", {}).get("coherence", {}).get("top_k", 20)
        METHOD = (
            self._cfg.get("params", {})
            .get("coherence", {})
            .get("method", "neighbor_cosine_topk")
        )

        # Build neighbor dict with top-K by weight and normalized weights
        logger.info("Building neighbor distributions (top-K)...")
        edges = edges.copy()
        if "weight" not in edges.columns:
            edges["weight"] = 1.0

        # sort by cue and weight desc, then take top-K
        edges["rank"] = edges.groupby("cue")["weight"].rank(
            method="first", ascending=False
        )
        edges_top = edges[edges["rank"] <= TOP_K].drop(columns=["rank"])  # type: ignore[call-arg]
        # normalize per cue
        wsum = edges_top.groupby("cue")["weight"].transform("sum")
        edges_top["p"] = edges_top["weight"] / wsum.replace(0, np.nan)
        edges_top = edges_top.dropna(subset=["p"])  # remove nodes with zero sum

        # Build dict: node -> {neighbor: p}
        nbr_dist: dict[str, dict[str, float]] = {}
        for row in edges_top.itertuples(index=False):
            cue = getattr(row, "cue")
            resp = getattr(row, "response")
            p = float(getattr(row, "p"))
            if cue not in nbr_dist:
                nbr_dist[cue] = {}
            nbr_dist[cue][resp] = p

        # (Optional) vector norms could be cached if needed for speed.

        def cosine_over_dicts(a: dict[str, float], b: dict[str, float]) -> float:
            # dot over intersection
            if not a or not b:
                return 0.0
            if len(a) > len(b):
                a, b = b, a
            dot = 0.0
            for k, va in a.items():
                vb = b.get(k)
                if vb is not None:
                    dot += va * vb
            na = float(np.sqrt(np.sum(np.square(list(a.values())))))
            nb = float(np.sqrt(np.sum(np.square(list(b.values())))))
            if na == 0.0 or nb == 0.0:
                return 0.0
            return float(dot / (na * nb))

        # Compute coherence per node: average cosine with neighbors' distributions
        logger.info("Aggregating cosine coherence per node...")
        words = set(edges_top["cue"].unique()) | set(edges_top["response"].unique())
        results = []
        for word in tqdm(words, desc="Computing coherence"):
            base = nbr_dist.get(word)
            if not base:
                results.append(
                    {
                        "word": word,
                        "coherence": 0.0,
                        "neighbors_evaluated": 0,
                    }
                )
                continue
            coss = []
            for nbr in base.keys():
                nbv = nbr_dist.get(nbr)
                if nbv:
                    coss.append(cosine_over_dicts(base, nbv))
            coh = float(np.mean(coss)) if coss else 0.0
            results.append(
                {
                    "word": word,
                    "coherence": coh,
                    "neighbors_evaluated": len(coss),
                }
            )

        coherence_df = pd.DataFrame(results)
        coherence_df["method"] = METHOD
        coherence_df["top_k"] = TOP_K

        # Save coherence
        output_path = (
            ensure_dir(f"@data_root.L2_derived/kec/{lang}") / "coherence.parquet"
        )
        coherence_df.to_parquet(output_path, index=False)

        self._save_checkpoint(lang, step)
        logger.info(f"Coherence computed for {lang}: {len(coherence_df)} nodes")
        return coherence_df

    def _load_coherence(self, lang: str) -> pd.DataFrame:
        """Load pre-computed coherence."""
        output_path = (
            ensure_dir(f"@data_root.L2_derived/kec/{lang}") / "coherence.parquet"
        )
        return pd.read_parquet(output_path)

    def compose_kec(self, lang: str) -> pd.DataFrame:
        """Compose final KEC metrics from components."""
        step = "compose"
        if self._is_step_complete(lang, step):
            logger.info(f"Step '{step}' already completed for {lang}, skipping")
            return self._load_kec_nodes(lang)

        logger.info(f"Composing KEC for {lang}")

        # Load all components
        entropy_df = self._load_entropy(lang)
        curvature_df = self._load_curvature(lang)
        coherence_df = self._load_coherence(lang)

        # Merge all metrics
        kec_df = entropy_df.merge(curvature_df, on="word", how="outer")
        kec_df = kec_df.merge(coherence_df, on="word", how="outer")

        # Fill missing values
        kec_df = kec_df.fillna(0)

        # Add language column
        kec_df["lang"] = lang

        # Save final KEC nodes
        output_path = (
            ensure_dir(f"@data_root.L2_derived/kec/{lang}") / "kec_nodes.parquet"
        )
        kec_df.to_parquet(output_path, index=False)

        # Also save components separately
        components_df = kec_df[
            ["word", "lang", "entropy", "curvature", "coherence"]
        ].copy()
        output_path = (
            ensure_dir(f"@data_root.L2_derived/kec/{lang}") / "components.parquet"
        )
        components_df.to_parquet(output_path, index=False)

        self._save_checkpoint(lang, step)
        logger.info(f"KEC composed for {lang}: {len(kec_df)} nodes")
        return kec_df

    def _load_kec_nodes(self, lang: str) -> pd.DataFrame:
        """Load final KEC nodes."""
        output_path = (
            ensure_dir(f"@data_root.L2_derived/kec/{lang}") / "kec_nodes.parquet"
        )
        return pd.read_parquet(output_path)

    def run_step(self, step: str, lang: str):
        """Run a specific processing step for a language."""
        if step == "build":
            self.build_graph(lang)
        elif step == "entropy":
            self.compute_entropy(lang)
        elif step == "curvature":
            self.compute_curvature(lang)
        elif step == "coherence":
            self.compute_coherence(lang)
        elif step == "compose":
            self.compose_kec(lang)
        elif step == "all":
            self.build_graph(lang)
            self.compute_entropy(lang)
            self.compute_curvature(lang)
            self.compute_coherence(lang)
            self.compose_kec(lang)
        else:
            raise ValueError(f"Unknown step: {step}")

    def run(self, step: str = "all"):
        """Run processing for all languages."""
        logger.info(f"Starting KEC compilation for languages: {self.languages}")
        logger.info(f"Device: {self.device}, Resume: {self.resume}")

        for lang in self.languages:
            logger.info(f"Processing language: {lang}")
            try:
                self.run_step(step, lang)
                logger.info(f"Completed processing for {lang}")
            except Exception as e:
                logger.error(f"Error processing {lang}: {e}")
                raise


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="KEC Compiler v4.4")
    parser.add_argument(
        "--lang", required=True, help="Comma-separated languages (e.g., en,es,nl,zh)"
    )
    parser.add_argument(
        "--step",
        default="all",
        choices=["build", "entropy", "curvature", "coherence", "compose", "all"],
        help="Processing step to run",
    )
    parser.add_argument(
        "--device",
        default="auto",
        choices=["auto", "cpu", "cuda"],
        help="Computation device",
    )
    parser.add_argument(
        "--resume", action="store_true", default=True, help="Resume from checkpoints"
    )
    parser.add_argument(
        "--no-resume", dest="resume", action="store_false", help="Start from scratch"
    )

    args = parser.parse_args()

    # Parse languages
    languages = [lang.strip() for lang in args.lang.split(",")]

    # Initialize and run compiler
    compiler = KECCompiler(languages=languages, device=args.device, resume=args.resume)
    compiler.run(args.step)

    logger.info("KEC compilation completed successfully!")


if __name__ == "__main__":
    main()
