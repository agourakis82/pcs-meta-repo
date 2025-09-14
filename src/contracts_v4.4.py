"""
Data contracts and validation schemas for the PCS project v4.4.
This module defines the expected structure and validation rules for datasets with modality separation.
"""

import pandas as pd
from typing import Dict, List, Optional, Any
import numpy as np


def validate_word_events_rt(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate RT/ET (Reading Time/Eye-Tracking) DataFrame schema for v4.4.

    Args:
        df: DataFrame to validate

    Returns:
        Dict with validation results
    """
    results = {"valid": True, "errors": [], "warnings": [], "stats": {}}

    # Required columns for RT/ET data
    required_columns = [
        "lang",
        "subject_id",
        "task_id",
        "doc_id",
        "sent_id",
        "word_id",
        "word",
        "ffd_ms",
        "gd_ms",
        "trt_ms",
        "nfix",
        "length",
        "logfreq",
        "position",
    ]

    # Check for required columns
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        results["valid"] = False
        results["errors"].append(f"Missing required RT columns: {missing_columns}")

    # Validate RT ranges (plausible eye-tracking values)
    if "ffd_ms" in df.columns:
        invalid_ffd = df[(df["ffd_ms"] < 50) | (df["ffd_ms"] > 800)].shape[0]
        if invalid_ffd > 0:
            results["warnings"].append(
                f"Found {invalid_ffd} records with FFD outside 50-800ms range"
            )

        # Check for constant values (like the ZuCo problem)
        if df["ffd_ms"].nunique() == 1:
            results["errors"].append(
                f"FFD has constant value: {df['ffd_ms'].iloc[0]} (degeneracy detected)"
            )

    if "gd_ms" in df.columns:
        invalid_gd = df[(df["gd_ms"] < 50) | (df["gd_ms"] > 1200)].shape[0]
        if invalid_gd > 0:
            results["warnings"].append(
                f"Found {invalid_gd} records with GD outside 50-1200ms range"
            )

        if df["gd_ms"].nunique() == 1:
            results["errors"].append(
                f"GD has constant value: {df['gd_ms'].iloc[0]} (degeneracy detected)"
            )

    if "trt_ms" in df.columns:
        invalid_trt = df[(df["trt_ms"] < 80) | (df["trt_ms"] > 1200)].shape[0]
        if invalid_trt > 0:
            results["warnings"].append(
                f"Found {invalid_trt} records with TRT outside 80-1200ms range"
            )

        if df["trt_ms"].nunique() == 1:
            results["errors"].append(
                f"TRT has constant value: {df['trt_ms'].iloc[0]} (degeneracy detected)"
            )

    if "nfix" in df.columns:
        invalid_nfix = df[(df["nfix"] < 1) | (df["nfix"] > 20)].shape[0]
        if invalid_nfix > 0:
            results["warnings"].append(
                f"Found {invalid_nfix} records with NFIX outside 1-20 range"
            )

    # Check for placeholder words
    if "word" in df.columns:
        placeholder_pattern = df["word"].str.match(r"^word_?\d+$", na=False)
        placeholder_count = placeholder_pattern.sum()
        if placeholder_count > 0:
            results["warnings"].append(
                f"Found {placeholder_count} placeholder words (word_N pattern)"
            )

    # Basic statistics
    results["stats"] = {
        "total_records": len(df),
        "unique_subjects": df["subject_id"].nunique()
        if "subject_id" in df.columns
        else 0,
        "unique_words": df["word"].nunique() if "word" in df.columns else 0,
        "languages": df["lang"].unique().tolist() if "lang" in df.columns else [],
        "missing_values": df.isnull().sum().to_dict(),
        "rt_variability": {
            "ffd_std": df["ffd_ms"].std() if "ffd_ms" in df.columns else None,
            "gd_std": df["gd_ms"].std() if "gd_ms" in df.columns else None,
            "trt_std": df["trt_ms"].std() if "trt_ms" in df.columns else None,
        },
    }

    return results


def validate_word_events_eeg(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate EEG DataFrame schema for v4.4.

    Args:
        df: DataFrame to validate

    Returns:
        Dict with validation results
    """
    results = {"valid": True, "errors": [], "warnings": [], "stats": {}}

    # Required columns for EEG data
    required_columns = [
        "lang",
        "subject_id",
        "task_id",
        "doc_id",
        "sent_id",
        "word_id",
        "word",
        "eeg_metric",
        "theta",
        "alpha",
        "beta",
        "onset_ms",
        "offset_ms",
        "length",
        "logfreq",
        "position",
    ]

    # Check for required columns
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        results["valid"] = False
        results["errors"].append(f"Missing required EEG columns: {missing_columns}")

    # Validate EEG ranges (microvolts typically)
    eeg_bands = ["theta", "alpha", "beta", "gamma", "delta"]
    for band in eeg_bands:
        if band in df.columns:
            invalid_eeg = df[(df[band] < -10) | (df[band] > 10)].shape[0]
            if invalid_eeg > 0:
                results["warnings"].append(
                    f"Found {invalid_eeg} records with {band} outside -10 to 10 range"
                )

            # Check for constant values
            if df[band].nunique() == 1:
                results["errors"].append(
                    f"{band} has constant value: {df[band].iloc[0]} (degeneracy detected)"
                )

    # Validate timing
    if "onset_ms" in df.columns:
        invalid_onset = df[(df["onset_ms"] < 0) | (df["onset_ms"] > 10000)].shape[0]
        if invalid_onset > 0:
            results["warnings"].append(
                f"Found {invalid_onset} records with onset_ms outside 0-10000ms range"
            )

    if "offset_ms" in df.columns:
        invalid_offset = df[(df["offset_ms"] < 0) | (df["offset_ms"] > 10000)].shape[0]
        if invalid_offset > 0:
            results["warnings"].append(
                f"Found {invalid_offset} records with offset_ms outside 0-10000ms range"
            )

    # Check for sufficient non-null EEG data
    eeg_columns = [col for col in eeg_bands if col in df.columns]
    if eeg_columns:
        non_null_percentage = (1 - df[eeg_columns].isnull().all(axis=1).mean()) * 100
        if non_null_percentage < 50:
            results["warnings"].append(
                f"Only {non_null_percentage:.1f}% of records have EEG data"
            )

    # Basic statistics
    results["stats"] = {
        "total_records": len(df),
        "unique_subjects": df["subject_id"].nunique()
        if "subject_id" in df.columns
        else 0,
        "unique_words": df["word"].nunique() if "word" in df.columns else 0,
        "languages": df["lang"].unique().tolist() if "lang" in df.columns else [],
        "missing_values": df.isnull().sum().to_dict(),
        "eeg_variability": {
            f"{band}_std": df[band].std() if band in df.columns else None
            for band in eeg_bands
        },
    }

    return results


def validate_integration_quality(
    merged_df: pd.DataFrame, kec_df: pd.DataFrame = None
) -> Dict[str, Any]:
    """
    Validate the quality of KEC integration with neurophysiological data.

    Args:
        merged_df: Integrated DataFrame
        kec_df: Original KEC DataFrame (optional)

    Returns:
        Dict with integration quality metrics
    """
    results = {"valid": True, "errors": [], "warnings": [], "stats": {}}

    # Calculate coverage
    total_words = len(merged_df)
    kec_columns = ["entropy", "curvature", "coherence"]
    available_kec_columns = [col for col in kec_columns if col in merged_df.columns]

    if available_kec_columns:
        words_with_kec = merged_df[available_kec_columns].notna().all(axis=1).sum()
        coverage = words_with_kec / total_words if total_words > 0 else 0

        if coverage < 0.5:
            results["errors"].append(
                f"Low KEC coverage: {coverage:.2%} (minimum 50% required)"
            )
        elif coverage < 0.7:
            results["warnings"].append(
                f"Moderate KEC coverage: {coverage:.2%} (70% recommended)"
            )
    else:
        results["errors"].append("No KEC columns found in merged dataset")
        words_with_kec = 0
        coverage = 0

    # Check for systematic missing patterns
    if available_kec_columns:
        missing_pattern = merged_df[available_kec_columns].isnull()
        if missing_pattern.all(axis=1).sum() > 0:
            systematic_missing = missing_pattern.all(axis=1).sum()
            results["warnings"].append(
                f"Found {systematic_missing} words with no KEC metrics"
            )

    results["stats"] = {
        "total_words": total_words,
        "words_with_kec": words_with_kec,
        "kec_coverage": coverage,
        "available_kec_columns": available_kec_columns,
        "unique_kec_words": len(kec_df) if kec_df is not None else 0,
        "join_efficiency": words_with_kec / len(kec_df)
        if kec_df is not None and len(kec_df) > 0
        else 0,
    }

    return results


def validate_target_degeneracy(
    df: pd.DataFrame, target_columns: List[str]
) -> Dict[str, Any]:
    """
    Specifically validate for target variable degeneracy (constant values).
    This addresses the ZuCo fixation_duration problem identified in diagnostics.

    Args:
        df: DataFrame to validate
        target_columns: List of columns to check for degeneracy

    Returns:
        Dict with degeneracy validation results
    """
    results = {"valid": True, "errors": [], "warnings": [], "stats": {}}

    degeneracy_stats = {}

    for col in target_columns:
        if col in df.columns:
            unique_values = df[col].nunique()
            total_values = df[col].notna().sum()
            unique_ratio = unique_values / total_values if total_values > 0 else 0
            std_dev = df[col].std()

            degeneracy_stats[col] = {
                "unique_values": unique_values,
                "total_values": total_values,
                "unique_ratio": unique_ratio,
                "std_dev": std_dev,
                "is_degenerate": unique_ratio < 0.01 or std_dev == 0,
            }

            # Check for degeneracy
            if unique_ratio < 0.01:
                results["valid"] = False
                results["errors"].append(
                    f"{col} has very low variability: {unique_ratio:.4%} unique values"
                )

            if std_dev == 0:
                results["valid"] = False
                results["errors"].append(
                    f"{col} has zero variability (constant value: {df[col].iloc[0]})"
                )

            if unique_values == 1:
                results["valid"] = False
                results["errors"].append(
                    f"{col} has only one unique value: {df[col].iloc[0]}"
                )

    results["stats"] = {
        "degeneracy_analysis": degeneracy_stats,
        "degenerate_columns": [
            col for col, stats in degeneracy_stats.items() if stats["is_degenerate"]
        ],
        "healthy_columns": [
            col for col, stats in degeneracy_stats.items() if not stats["is_degenerate"]
        ],
    }

    return results


# Schema definitions v4.4
WORD_EVENTS_RT_SCHEMA = {
    "required_columns": [
        "lang",
        "subject_id",
        "task_id",
        "doc_id",
        "sent_id",
        "word_id",
        "word",
        "ffd_ms",
        "gd_ms",
        "trt_ms",
        "nfix",
        "length",
        "logfreq",
        "position",
    ],
    "optional_columns": ["cloze_prob", "surprisal", "frequency"],
    "validation_rules": {
        "ffd_ms": {"min": 50, "max": 800, "unit": "milliseconds"},
        "gd_ms": {"min": 50, "max": 1200, "unit": "milliseconds"},
        "trt_ms": {"min": 80, "max": 1200, "unit": "milliseconds"},
        "nfix": {"min": 1, "max": 20},
    },
}

WORD_EVENTS_EEG_SCHEMA = {
    "required_columns": [
        "lang",
        "subject_id",
        "task_id",
        "doc_id",
        "sent_id",
        "word_id",
        "word",
        "eeg_metric",
        "theta",
        "alpha",
        "beta",
        "onset_ms",
        "offset_ms",
        "length",
        "logfreq",
        "position",
    ],
    "optional_columns": ["gamma", "delta", "unit_level"],
    "validation_rules": {
        "theta": {"min": -10, "max": 10, "unit": "microvolts"},
        "alpha": {"min": -10, "max": 10, "unit": "microvolts"},
        "beta": {"min": -10, "max": 10, "unit": "microvolts"},
        "onset_ms": {"min": 0, "max": 10000, "unit": "milliseconds"},
    },
}

KEC_SCHEMA_V44 = {
    "required_columns": ["word", "entropy", "curvature", "coherence"],
    "optional_columns": ["lang", "frequency", "length"],
    "data_types": {
        "word": "object",
        "entropy": "float64",
        "curvature": "float64",
        "coherence": "float64",
    },
    "validation_rules": {
        "entropy": {"min": 0, "max": 10},
        "coherence": {"min": -1, "max": 1},
    },
}

# Quality gate definitions
QUALITY_GATES_V44 = {
    "rt_datasets": {
        "min_records": 5000,
        "required_subjects": 2,
        "required_metrics": ["ffd_ms", "gd_ms", "trt_ms"],
        "max_degeneracy_ratio": 0.01,  # Maximum 1% constant values
    },
    "eeg_datasets": {
        "min_records": 1000,
        "required_subjects": 1,
        "required_metrics": ["theta", "alpha", "beta"],
        "min_non_null_percentage": 50,  # Minimum 50% non-null EEG data
    },
    "kec_integration": {
        "min_coverage": 0.7,  # 70% of tokens must have KEC metrics
        "required_languages": ["en"],
        "required_kec_metrics": ["entropy", "curvature", "coherence"],
    },
}
