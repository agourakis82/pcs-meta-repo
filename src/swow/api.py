"""
SWOW High-Level API Module

Provides high-level classes and functions for SWOW data processing and analysis.
Integrates all SWOW functionality into easy-to-use interfaces.

Author: PCS Meta-Repo
License: MIT
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple
import logging
from datetime import datetime

# Import SWOW modules
from .io import load_swow_csv, save_swow_data, get_swow_statistics
from .graph import build_swow_graph, validate_graph, save_graph, load_graph
from .metrics_kec import compute_swow_kec_metrics, load_kec_metrics
from .clean_en import clean_english_swow
from .clean_es import clean_spanish_swow
from .clean_zh import clean_chinese_swow
from .clean_nl import clean_dutch_swow
from .align import align_multilingual_swow, create_multilingual_graph

# Set up logging
logger = logging.getLogger(__name__)


class SWOWProcessor:
    """
    High-level processor for individual SWOW datasets.

    Provides a complete pipeline from raw data to KEC metrics.
    """

    def __init__(self, language: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize SWOW processor for a specific language.

        Args:
            language: Language code (en, es, zh, nl)
            config: Optional configuration dictionary
        """

        if language not in ["en", "es", "zh", "nl"]:
            raise ValueError(f"Unsupported language: {language}")

        self.language = language
        self.config = config or {}

        # Set up cleaning function
        self.cleaning_functions = {
            "en": clean_english_swow,
            "es": clean_spanish_swow,
            "zh": clean_chinese_swow,
            "nl": clean_dutch_swow,
        }

        # Initialize data containers
        self.raw_data = None
        self.cleaned_data = None
        self.graph = None
        self.kec_metrics = None

        logger.info(f"Initialized SWOW processor for language: {language}")

    def load_data(self, data_path: Optional[Path] = None, **kwargs) -> pd.DataFrame:
        """Load raw SWOW data."""

        logger.info(f"Loading {self.language} SWOW data")

        self.raw_data = load_swow_csv(
            language=self.language, data_path=data_path, **kwargs
        )

        logger.info(f"Loaded {len(self.raw_data):,} associations")
        return self.raw_data

    def clean_data(self, **kwargs) -> pd.DataFrame:
        """Clean and preprocess the data."""

        if self.raw_data is None:
            raise ValueError("No raw data loaded. Call load_data() first.")

        logger.info(f"Cleaning {self.language} SWOW data")

        cleaning_func = self.cleaning_functions[self.language]
        self.cleaned_data = cleaning_func(self.raw_data, **kwargs)

        logger.info(f"Cleaned data: {len(self.cleaned_data):,} associations")
        return self.cleaned_data

    def build_graph(self, **kwargs) -> Any:
        """Build semantic graph from cleaned data."""

        if self.cleaned_data is None:
            raise ValueError("No cleaned data available. Call clean_data() first.")

        logger.info(f"Building {self.language} SWOW graph")

        self.graph = build_swow_graph(self.cleaned_data, **kwargs)

        # Validate graph
        validation = validate_graph(self.graph)
        if not validation["valid"]:
            logger.warning(f"Graph validation issues: {validation['issues']}")

        logger.info(
            f"Built graph: {self.graph.vcount()} nodes, {self.graph.ecount()} edges"
        )
        return self.graph

    def compute_kec_metrics(self, **kwargs) -> pd.DataFrame:
        """Compute KEC metrics for the graph."""

        if self.graph is None:
            raise ValueError("No graph available. Call build_graph() first.")

        logger.info(f"Computing KEC metrics for {self.language}")

        self.kec_metrics = compute_swow_kec_metrics(
            self.graph, language=self.language, **kwargs
        )

        logger.info(f"Computed KEC metrics for {len(self.kec_metrics)} nodes")
        return self.kec_metrics

    def run_complete_pipeline(
        self,
        data_path: Optional[Path] = None,
        output_dir: Optional[Path] = None,
        save_intermediate: bool = True,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Run the complete SWOW processing pipeline.

        Args:
            data_path: Path to raw SWOW data
            output_dir: Directory to save outputs
            save_intermediate: Whether to save intermediate results
            **kwargs: Additional arguments for processing steps

        Returns:
            Dictionary with processing results
        """

        logger.info(f"Running complete SWOW pipeline for {self.language}")

        results = {
            "language": self.language,
            "timestamp": datetime.now().isoformat(),
            "steps_completed": [],
            "statistics": {},
        }

        try:
            # Step 1: Load data
            self.load_data(data_path, **kwargs.get("load_kwargs", {}))
            results["steps_completed"].append("load_data")
            results["statistics"]["raw_associations"] = len(self.raw_data)

            # Step 2: Clean data
            self.clean_data(**kwargs.get("clean_kwargs", {}))
            results["steps_completed"].append("clean_data")
            results["statistics"]["cleaned_associations"] = len(self.cleaned_data)

            # Step 3: Build graph
            self.build_graph(**kwargs.get("graph_kwargs", {}))
            results["steps_completed"].append("build_graph")
            results["statistics"]["graph_nodes"] = self.graph.vcount()
            results["statistics"]["graph_edges"] = self.graph.ecount()

            # Step 4: Compute KEC metrics
            self.compute_kec_metrics(**kwargs.get("kec_kwargs", {}))
            results["steps_completed"].append("compute_kec_metrics")
            results["statistics"]["kec_nodes"] = len(self.kec_metrics)

            # Save intermediate results if requested
            if save_intermediate and output_dir:
                self.save_results(output_dir)
                results["steps_completed"].append("save_results")

            results["success"] = True
            logger.info(f"Pipeline completed successfully for {self.language}")

        except Exception as e:
            results["success"] = False
            results["error"] = str(e)
            logger.error(f"Pipeline failed for {self.language}: {e}")

        return results

    def save_results(self, output_dir: Path) -> None:
        """Save all processing results."""

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save cleaned data
        if self.cleaned_data is not None:
            save_swow_data(
                self.cleaned_data, output_dir / f"swow_{self.language}_cleaned.csv"
            )

        # Save graph
        if self.graph is not None:
            save_graph(self.graph, output_dir / f"swow_{self.language}_graph.graphml")

        # Save KEC metrics
        if self.kec_metrics is not None:
            save_swow_data(
                self.kec_metrics, output_dir / f"swow_{self.language}_kec.csv"
            )

        logger.info(f"Saved results to {output_dir}")

    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics about the processed data."""

        stats = {
            "language": self.language,
            "processing_status": {
                "raw_data_loaded": self.raw_data is not None,
                "data_cleaned": self.cleaned_data is not None,
                "graph_built": self.graph is not None,
                "kec_computed": self.kec_metrics is not None,
            },
        }

        if self.raw_data is not None:
            stats["raw_data"] = get_swow_statistics(self.raw_data)

        if self.cleaned_data is not None:
            stats["cleaned_data"] = get_swow_statistics(self.cleaned_data)

        if self.graph is not None:
            validation = validate_graph(self.graph)
            stats["graph"] = validation["statistics"]

        if self.kec_metrics is not None:
            stats["kec_metrics"] = {
                "n_nodes": len(self.kec_metrics),
                "metrics_available": [
                    col
                    for col in ["entropy", "curvature", "coherence"]
                    if col in self.kec_metrics.columns
                ],
            }

        return stats


class MultilingualSWOWAnalyzer:
    """
    High-level analyzer for multilingual SWOW datasets.

    Provides functionality for cross-language analysis and comparison.
    """

    def __init__(self, languages: List[str], config: Optional[Dict[str, Any]] = None):
        """
        Initialize multilingual SWOW analyzer.

        Args:
            languages: List of language codes to analyze
            config: Optional configuration dictionary
        """

        self.languages = languages
        self.config = config or {}

        # Initialize processors for each language
        self.processors = {}
        for lang in languages:
            self.processors[lang] = SWOWProcessor(lang, config.get(lang, {}))

        # Initialize containers for multilingual analysis
        self.alignment_results = None
        self.multilingual_graph = None
        self.comparison_results = None

        logger.info(f"Initialized multilingual analyzer for languages: {languages}")

    def process_all_languages(
        self, data_paths: Optional[Dict[str, Path]] = None, **kwargs
    ) -> Dict[str, Any]:
        """Process all languages using their individual processors."""

        logger.info("Processing all languages")

        results = {}

        for lang in self.languages:
            logger.info(f"Processing {lang}")

            data_path = data_paths.get(lang) if data_paths else None
            lang_kwargs = kwargs.get(lang, kwargs)

            results[lang] = self.processors[lang].run_complete_pipeline(
                data_path=data_path, **lang_kwargs
            )

        return results

    def align_languages(self, **kwargs) -> Dict[str, Any]:
        """Align datasets across languages."""

        logger.info("Aligning languages")

        # Get cleaned datasets
        datasets = {}
        for lang in self.languages:
            if self.processors[lang].cleaned_data is not None:
                datasets[lang] = self.processors[lang].cleaned_data
            else:
                logger.warning(f"No cleaned data available for {lang}")

        if len(datasets) < 2:
            raise ValueError(
                "At least 2 languages with cleaned data required for alignment"
            )

        self.alignment_results = align_multilingual_swow(datasets, **kwargs)

        logger.info(f"Aligned {len(datasets)} languages")
        return self.alignment_results

    def create_multilingual_network(self, **kwargs) -> pd.DataFrame:
        """Create a multilingual semantic network."""

        if self.alignment_results is None:
            raise ValueError(
                "No alignment results available. Call align_languages() first."
            )

        logger.info("Creating multilingual network")

        datasets = {}
        for lang in self.languages:
            if self.processors[lang].cleaned_data is not None:
                datasets[lang] = self.processors[lang].cleaned_data

        self.multilingual_graph = create_multilingual_graph(
            datasets, self.alignment_results, **kwargs
        )

        logger.info(
            f"Created multilingual network with {len(self.multilingual_graph)} edges"
        )
        return self.multilingual_graph

    def compare_languages(self, **kwargs) -> Dict[str, Any]:
        """Compare network properties across languages."""

        logger.info("Comparing languages")

        datasets = {}
        for lang in self.languages:
            if self.processors[lang].cleaned_data is not None:
                datasets[lang] = self.processors[lang].cleaned_data

        from .align import compare_language_networks

        self.comparison_results = compare_language_networks(datasets, **kwargs)

        logger.info(f"Compared {len(datasets)} languages")
        return self.comparison_results

    def run_complete_multilingual_analysis(
        self,
        data_paths: Optional[Dict[str, Path]] = None,
        output_dir: Optional[Path] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Run complete multilingual analysis pipeline."""

        logger.info("Running complete multilingual analysis")

        results = {
            "languages": self.languages,
            "timestamp": datetime.now().isoformat(),
            "steps_completed": [],
            "individual_results": {},
            "multilingual_results": {},
        }

        try:
            # Step 1: Process individual languages
            results["individual_results"] = self.process_all_languages(
                data_paths, **kwargs
            )
            results["steps_completed"].append("process_languages")

            # Step 2: Align languages
            self.align_languages(**kwargs.get("align_kwargs", {}))
            results["multilingual_results"]["alignment"] = self.alignment_results
            results["steps_completed"].append("align_languages")

            # Step 3: Create multilingual network
            self.create_multilingual_network(**kwargs.get("network_kwargs", {}))
            results["multilingual_results"]["network_size"] = len(
                self.multilingual_graph
            )
            results["steps_completed"].append("create_network")

            # Step 4: Compare languages
            self.compare_languages(**kwargs.get("compare_kwargs", {}))
            results["multilingual_results"]["comparison"] = self.comparison_results
            results["steps_completed"].append("compare_languages")

            # Save results if output directory provided
            if output_dir:
                self.save_multilingual_results(output_dir)
                results["steps_completed"].append("save_results")

            results["success"] = True
            logger.info("Multilingual analysis completed successfully")

        except Exception as e:
            results["success"] = False
            results["error"] = str(e)
            logger.error(f"Multilingual analysis failed: {e}")

        return results

    def save_multilingual_results(self, output_dir: Path) -> None:
        """Save multilingual analysis results."""

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save individual language results
        for lang in self.languages:
            lang_dir = output_dir / lang
            self.processors[lang].save_results(lang_dir)

        # Save multilingual results
        if self.multilingual_graph is not None:
            save_swow_data(
                self.multilingual_graph, output_dir / "multilingual_network.csv"
            )

        # Save alignment and comparison results as JSON
        import json

        if self.alignment_results is not None:
            with open(output_dir / "alignment_results.json", "w") as f:
                json.dump(self.alignment_results, f, indent=2, default=str)

        if self.comparison_results is not None:
            with open(output_dir / "comparison_results.json", "w") as f:
                json.dump(self.comparison_results, f, indent=2, default=str)

        logger.info(f"Saved multilingual results to {output_dir}")
