"""
SWOW Multilingual Alignment Module

Provides functionality for aligning and comparing SWOW datasets across languages.
Supports cross-language semantic analysis and multilingual integration.

Author: PCS Meta-Repo
License: MIT
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple
import logging
from collections import defaultdict

# Set up logging
logger = logging.getLogger(__name__)


def align_multilingual_swow(
    datasets: Dict[str, pd.DataFrame],
    alignment_method: str = "translation",
    translation_dict: Optional[Dict[str, Dict[str, str]]] = None,
    min_overlap: int = 10,
) -> Dict[str, Any]:
    """
    Align SWOW datasets across multiple languages.

    Args:
        datasets: Dictionary of language -> DataFrame
        alignment_method: Method for alignment ("translation", "phonetic", "semantic")
        translation_dict: Optional translation dictionary
        min_overlap: Minimum overlap required for alignment

    Returns:
        Dictionary with alignment results
    """

    logger.info(f"Aligning SWOW datasets for languages: {list(datasets.keys())}")

    alignment_results = {
        "languages": list(datasets.keys()),
        "method": alignment_method,
        "alignments": {},
        "statistics": {},
        "overlaps": {},
    }

    # Compute pairwise alignments
    languages = list(datasets.keys())
    for i, lang1 in enumerate(languages):
        for j, lang2 in enumerate(languages[i + 1 :], i + 1):
            logger.info(f"Aligning {lang1} <-> {lang2}")

            alignment = _compute_pairwise_alignment(
                datasets[lang1],
                datasets[lang2],
                lang1,
                lang2,
                alignment_method,
                translation_dict,
            )

            alignment_results["alignments"][f"{lang1}_{lang2}"] = alignment
            alignment_results["overlaps"][f"{lang1}_{lang2}"] = len(
                alignment["aligned_pairs"]
            )

    # Compute overall statistics
    alignment_results["statistics"] = _compute_alignment_statistics(
        alignment_results, datasets
    )

    return alignment_results


def _compute_pairwise_alignment(
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    lang1: str,
    lang2: str,
    method: str,
    translation_dict: Optional[Dict[str, Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """Compute alignment between two SWOW datasets."""

    alignment = {
        "lang1": lang1,
        "lang2": lang2,
        "method": method,
        "aligned_pairs": [],
        "statistics": {},
    }

    if method == "translation" and translation_dict:
        alignment["aligned_pairs"] = _align_by_translation(
            df1, df2, lang1, lang2, translation_dict
        )
    elif method == "phonetic":
        alignment["aligned_pairs"] = _align_by_phonetic_similarity(df1, df2)
    elif method == "semantic":
        alignment["aligned_pairs"] = _align_by_semantic_similarity(df1, df2)
    else:
        # Fallback: exact string matching (for cognates)
        alignment["aligned_pairs"] = _align_by_exact_match(df1, df2)

    # Compute alignment statistics
    alignment["statistics"] = {
        "total_pairs": len(alignment["aligned_pairs"]),
        "coverage_lang1": len(set(p[0] for p in alignment["aligned_pairs"]))
        / len(set(df1["cue"]) | set(df1["response"])),
        "coverage_lang2": len(set(p[1] for p in alignment["aligned_pairs"]))
        / len(set(df2["cue"]) | set(df2["response"])),
    }

    return alignment


def _align_by_translation(
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    lang1: str,
    lang2: str,
    translation_dict: Dict[str, Dict[str, str]],
) -> List[Tuple[str, str]]:
    """Align words using translation dictionary."""

    aligned_pairs = []

    # Get translation mapping
    if lang1 in translation_dict and lang2 in translation_dict[lang1]:
        translations = translation_dict[lang1][lang2]
    elif lang2 in translation_dict and lang1 in translation_dict[lang2]:
        translations = {v: k for k, v in translation_dict[lang2][lang1].items()}
    else:
        logger.warning(f"No translation dictionary found for {lang1} -> {lang2}")
        return aligned_pairs

    # Get vocabularies
    vocab1 = set(df1["cue"]) | set(df1["response"])
    vocab2 = set(df2["cue"]) | set(df2["response"])

    # Find aligned pairs
    for word1 in vocab1:
        if word1 in translations:
            word2 = translations[word1]
            if word2 in vocab2:
                aligned_pairs.append((word1, word2))

    return aligned_pairs


def _align_by_exact_match(
    df1: pd.DataFrame, df2: pd.DataFrame
) -> List[Tuple[str, str]]:
    """Align words by exact string matching (for cognates)."""

    vocab1 = set(df1["cue"]) | set(df1["response"])
    vocab2 = set(df2["cue"]) | set(df2["response"])

    # Find exact matches
    common_words = vocab1 & vocab2
    aligned_pairs = [(word, word) for word in common_words]

    return aligned_pairs


def _align_by_phonetic_similarity(
    df1: pd.DataFrame, df2: pd.DataFrame
) -> List[Tuple[str, str]]:
    """Align words by phonetic similarity (placeholder implementation)."""

    # This is a simplified implementation
    # In practice, you would use phonetic algorithms like Soundex, Metaphone, etc.

    vocab1 = set(df1["cue"]) | set(df1["response"])
    vocab2 = set(df2["cue"]) | set(df2["response"])

    aligned_pairs = []

    for word1 in vocab1:
        for word2 in vocab2:
            # Simple similarity based on edit distance
            if _compute_edit_distance(word1, word2) <= 2 and len(word1) > 3:
                aligned_pairs.append((word1, word2))

    return aligned_pairs


def _align_by_semantic_similarity(
    df1: pd.DataFrame, df2: pd.DataFrame
) -> List[Tuple[str, str]]:
    """Align words by semantic similarity (placeholder implementation)."""

    # This would require semantic embeddings or other semantic similarity measures
    # For now, return empty list
    logger.warning("Semantic alignment not implemented - returning empty alignment")
    return []


def _compute_edit_distance(s1: str, s2: str) -> int:
    """Compute edit distance between two strings."""

    if len(s1) < len(s2):
        return _compute_edit_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def _compute_alignment_statistics(
    alignment_results: Dict[str, Any], datasets: Dict[str, pd.DataFrame]
) -> Dict[str, Any]:
    """Compute overall alignment statistics."""

    stats = {
        "total_languages": len(datasets),
        "total_alignments": len(alignment_results["alignments"]),
        "average_overlap": np.mean(list(alignment_results["overlaps"].values()))
        if alignment_results["overlaps"]
        else 0,
        "language_coverage": {},
    }

    # Compute coverage for each language
    for lang, df in datasets.items():
        vocab_size = len(set(df["cue"]) | set(df["response"]))
        aligned_words = set()

        for alignment_key, alignment in alignment_results["alignments"].items():
            if lang in alignment_key:
                if alignment["lang1"] == lang:
                    aligned_words.update(p[0] for p in alignment["aligned_pairs"])
                else:
                    aligned_words.update(p[1] for p in alignment["aligned_pairs"])

        coverage = len(aligned_words) / vocab_size if vocab_size > 0 else 0
        stats["language_coverage"][lang] = {
            "vocab_size": vocab_size,
            "aligned_words": len(aligned_words),
            "coverage": coverage,
        }

    return stats


def create_multilingual_graph(
    datasets: Dict[str, pd.DataFrame],
    alignment_results: Dict[str, Any],
    merge_aligned: bool = True,
) -> pd.DataFrame:
    """
    Create a multilingual graph by merging aligned datasets.

    Args:
        datasets: Dictionary of language -> DataFrame
        alignment_results: Results from align_multilingual_swow
        merge_aligned: Whether to merge aligned words into single nodes

    Returns:
        Multilingual graph as DataFrame
    """

    logger.info("Creating multilingual graph")

    multilingual_edges = []

    for lang, df in datasets.items():
        # Add language-specific edges
        for _, row in df.iterrows():
            edge = {
                "cue": row["cue"],
                "response": row["response"],
                "language": lang,
                "edge_type": "intra_language",
            }

            # Add frequency if available
            if "frequency" in row:
                edge["frequency"] = row["frequency"]

            multilingual_edges.append(edge)

    # Add cross-language edges if merging aligned words
    if merge_aligned:
        for alignment_key, alignment in alignment_results["alignments"].items():
            for word1, word2 in alignment["aligned_pairs"]:
                edge = {
                    "cue": word1,
                    "response": word2,
                    "language": f"{alignment['lang1']}_{alignment['lang2']}",
                    "edge_type": "cross_language",
                    "frequency": 1,  # Default frequency for alignment edges
                }
                multilingual_edges.append(edge)

    multilingual_df = pd.DataFrame(multilingual_edges)

    logger.info(f"Created multilingual graph with {len(multilingual_df)} edges")
    return multilingual_df


def compare_language_networks(
    datasets: Dict[str, pd.DataFrame],
    metrics: List[str] = ["density", "clustering", "centrality"],
) -> Dict[str, Any]:
    """
    Compare network properties across languages.

    Args:
        datasets: Dictionary of language -> DataFrame
        metrics: List of metrics to compute

    Returns:
        Comparison results
    """

    logger.info(f"Comparing network properties for {len(datasets)} languages")

    comparison = {"languages": list(datasets.keys()), "metrics": {}, "rankings": {}}

    # Compute basic network statistics for each language
    for lang, df in datasets.items():
        vocab = set(df["cue"]) | set(df["response"])
        n_nodes = len(vocab)
        n_edges = len(df)

        comparison["metrics"][lang] = {
            "nodes": n_nodes,
            "edges": n_edges,
            "density": n_edges / (n_nodes * (n_nodes - 1)) if n_nodes > 1 else 0,
            "avg_degree": (2 * n_edges) / n_nodes if n_nodes > 0 else 0,
        }

    # Create rankings
    for metric in ["nodes", "edges", "density", "avg_degree"]:
        ranking = sorted(
            comparison["metrics"].items(), key=lambda x: x[1][metric], reverse=True
        )
        comparison["rankings"][metric] = [lang for lang, _ in ranking]

    return comparison
