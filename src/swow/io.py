"""
SWOW I/O Module

Handles loading, saving, and validation of SWOW datasets across all supported languages.
Provides standardized interfaces for reading raw SWOW data and exporting processed results.

Author: PCS Meta-Repo
License: MIT
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple
import logging
import yaml
import json
from datetime import datetime

# Set up logging
logger = logging.getLogger(__name__)


class SWOWDataLoader:
    """Standardized loader for SWOW datasets across all languages"""

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize SWOW data loader with configuration."""
        self.config_path = (
            config_path
            or Path(__file__).parent.parent.parent / "config" / "swow_paths.yaml"
        )
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load SWOW configuration from YAML file."""
        try:
            with open(self.config_path, "r") as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.warning(f"Could not load config from {self.config_path}: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration if config file is not available."""
        return {
            "en": {
                "raw_dir": "data/raw_public/swow/en",
                "sources": ["SWOW-EN.complete.20180827.csv"],
            },
            "es": {
                "raw_dir": "data/raw_public/swow/es",
                "sources": ["SWOWRP.raw.20220426.csv"],
            },
            "zh": {
                "raw_dir": "data/raw_public/swow/zh",
                "sources": ["SWOWZH.raw.20230424.csv"],
            },
            "nl": {
                "raw_dir": "data/raw_public/swow/nl",
                "sources": ["associationData.csv"],
            },
        }


def load_swow_csv(
    language: str,
    data_path: Optional[Path] = None,
    sample_size: Optional[int] = None,
    validate: bool = True,
) -> pd.DataFrame:
    """
    Load SWOW CSV data for a specific language.

    Args:
        language: Language code (en, es, zh, nl)
        data_path: Optional path to specific CSV file
        sample_size: Optional sample size for testing
        validate: Whether to validate the loaded data

    Returns:
        DataFrame with standardized SWOW data
    """
    logger.info(f"Loading SWOW data for language: {language}")

    if language not in ["en", "es", "zh", "nl"]:
        raise ValueError(f"Unsupported language: {language}")

    # Determine data path
    if data_path is None:
        data_path = _find_swow_file(language)

    if not data_path.exists():
        raise FileNotFoundError(f"SWOW data file not found: {data_path}")

    # Load data with language-specific handling
    try:
        if language == "nl":
            # Dutch data may use different separator
            df = pd.read_csv(data_path, sep=";", quotechar='"', low_memory=False)
        else:
            df = pd.read_csv(data_path, low_memory=False)

        logger.info(f"Loaded {len(df):,} rows for {language}")

        # Apply sampling if requested
        if sample_size and len(df) > sample_size:
            df = df.sample(n=sample_size, random_state=42)
            logger.info(f"Sampled to {len(df):,} rows")

        # Standardize column names
        df = _standardize_columns(df, language)

        # Validate data if requested
        if validate:
            df = _validate_swow_data(df, language)

        return df

    except Exception as e:
        logger.error(f"Error loading SWOW data for {language}: {e}")
        raise


def _find_swow_file(language: str) -> Path:
    """Find SWOW data file for a given language."""
    base_path = (
        Path(__file__).parent.parent.parent / "data" / "raw_public" / "swow" / language
    )

    # Common file patterns by language
    patterns = {
        "en": ["*SWOW-EN*.csv", "*swow*en*.csv", "*english*.csv"],
        "es": ["*SWOW*RP*.csv", "*swow*es*.csv", "*spanish*.csv"],
        "zh": ["*SWOW*ZH*.csv", "*swow*zh*.csv", "*chinese*.csv"],
        "nl": ["*association*.csv", "*swow*nl*.csv", "*dutch*.csv"],
    }

    for pattern in patterns.get(language, ["*.csv"]):
        files = list(base_path.glob(pattern))
        if files:
            # Return the largest file (most complete dataset)
            return max(files, key=lambda f: f.stat().st_size)

    # Fallback: return first CSV file found
    csv_files = list(base_path.glob("*.csv"))
    if csv_files:
        return csv_files[0]

    raise FileNotFoundError(f"No SWOW CSV files found in {base_path}")


def _standardize_columns(df: pd.DataFrame, language: str) -> pd.DataFrame:
    """Standardize column names across languages."""

    # Common column mappings
    column_mappings = {
        "en": {
            "cue": ["cue", "Cue", "CUE", "word", "Word"],
            "response": ["response", "Response", "RESPONSE", "R1", "associate"],
            "frequency": ["frequency", "Frequency", "FREQ", "R1.Freq", "count"],
            "strength": ["strength", "Strength", "R1.Strength", "weight"],
        },
        "es": {
            "cue": ["cue", "Cue", "palabra", "estimulo"],
            "response": ["response", "Response", "respuesta", "R1"],
            "frequency": ["frequency", "frecuencia", "R1.Freq"],
            "strength": ["strength", "fuerza", "R1.Strength"],
        },
        "zh": {
            "cue": ["cue", "Cue", "词汇", "刺激词"],
            "response": ["response", "Response", "反应", "R1"],
            "frequency": ["frequency", "频率", "R1.Freq"],
            "strength": ["strength", "强度", "R1.Strength"],
        },
        "nl": {
            "cue": ["cue", "Cue", "woord", "stimulus"],
            "response": ["response", "Response", "reactie", "R1"],
            "frequency": ["frequency", "frequentie", "R1.Freq"],
            "strength": ["strength", "sterkte", "R1.Strength"],
        },
    }

    mappings = column_mappings.get(language, column_mappings["en"])

    # Create reverse mapping from actual columns to standard names
    reverse_mapping = {}
    for standard_name, possible_names in mappings.items():
        for possible_name in possible_names:
            if possible_name in df.columns:
                reverse_mapping[possible_name] = standard_name
                break

    # Apply mapping
    df = df.rename(columns=reverse_mapping)

    # Ensure required columns exist
    required_cols = ["cue", "response"]
    for col in required_cols:
        if col not in df.columns:
            logger.warning(f"Required column '{col}' not found for {language}")

    return df


def _validate_swow_data(df: pd.DataFrame, language: str) -> pd.DataFrame:
    """Validate and clean SWOW data."""

    initial_rows = len(df)

    # Remove rows with missing cue or response
    df = df.dropna(subset=["cue", "response"])

    # Remove empty strings
    df = df[df["cue"].str.strip() != ""]
    df = df[df["response"].str.strip() != ""]

    # Convert to string and strip whitespace
    df["cue"] = df["cue"].astype(str).str.strip()
    df["response"] = df["response"].astype(str).str.strip()

    # Remove very short or very long entries (likely errors)
    df = df[df["cue"].str.len().between(1, 50)]
    df = df[df["response"].str.len().between(1, 50)]

    # Language-specific validation
    if language == "zh":
        # For Chinese, ensure we have valid characters
        df = df[df["cue"].str.contains(r"[\u4e00-\u9fff]", na=False)]
        df = df[df["response"].str.contains(r"[\u4e00-\u9fff]", na=False)]

    final_rows = len(df)
    removed_rows = initial_rows - final_rows

    if removed_rows > 0:
        logger.info(
            f"Removed {removed_rows:,} invalid rows ({removed_rows/initial_rows:.1%})"
        )

    return df


def save_swow_data(
    df: pd.DataFrame,
    output_path: Path,
    format: str = "csv",
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Save SWOW data with optional metadata.

    Args:
        df: DataFrame to save
        output_path: Output file path
        format: Output format (csv, parquet, json)
        metadata: Optional metadata to save alongside
    """

    output_path.parent.mkdir(parents=True, exist_ok=True)

    if format.lower() == "csv":
        df.to_csv(output_path, index=False)
    elif format.lower() == "parquet":
        df.to_parquet(output_path, index=False)
    elif format.lower() == "json":
        df.to_json(output_path, orient="records", indent=2)
    else:
        raise ValueError(f"Unsupported format: {format}")

    logger.info(f"Saved {len(df):,} rows to {output_path}")

    # Save metadata if provided
    if metadata:
        metadata_path = output_path.with_suffix(".metadata.json")
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2, default=str)
        logger.info(f"Saved metadata to {metadata_path}")


def load_processed_kec_data(
    language: str, base_path: Optional[Path] = None
) -> Dict[str, pd.DataFrame]:
    """
    Load processed KEC data for a language.

    Args:
        language: Language code
        base_path: Base path for processed data

    Returns:
        Dictionary with entropy, curvature, coherence DataFrames
    """

    if base_path is None:
        base_path = (
            Path(__file__).parent.parent.parent
            / "data"
            / "L2_derived"
            / "kec"
            / language
        )

    kec_data = {}

    for metric in ["entropy", "curvature", "coherence"]:
        file_path = base_path / f"{metric}.parquet"
        if file_path.exists():
            kec_data[metric] = pd.read_parquet(file_path)
            logger.info(f"Loaded {metric} data: {len(kec_data[metric]):,} rows")
        else:
            logger.warning(f"KEC file not found: {file_path}")

    return kec_data


def get_swow_statistics(df: pd.DataFrame) -> Dict[str, Any]:
    """Get basic statistics for SWOW dataset."""

    stats = {
        "total_associations": len(df),
        "unique_cues": df["cue"].nunique(),
        "unique_responses": df["response"].nunique(),
        "unique_words": len(set(df["cue"].unique()) | set(df["response"].unique())),
        "avg_responses_per_cue": len(df) / df["cue"].nunique()
        if df["cue"].nunique() > 0
        else 0,
        "most_common_cues": df["cue"].value_counts().head(10).to_dict(),
        "most_common_responses": df["response"].value_counts().head(10).to_dict(),
    }

    # Add frequency/strength statistics if available
    if "frequency" in df.columns:
        stats["frequency_stats"] = {
            "mean": float(df["frequency"].mean()),
            "std": float(df["frequency"].std()),
            "min": float(df["frequency"].min()),
            "max": float(df["frequency"].max()),
        }

    if "strength" in df.columns:
        stats["strength_stats"] = {
            "mean": float(df["strength"].mean()),
            "std": float(df["strength"].std()),
            "min": float(df["strength"].min()),
            "max": float(df["strength"].max()),
        }

    return stats


def create_swow_manifest(
    language: str, df: pd.DataFrame, source_path: Path, output_path: Path
) -> Dict[str, Any]:
    """Create a manifest file for SWOW dataset."""

    manifest = {
        "dataset": "SWOW",
        "language": language,
        "timestamp": datetime.now().isoformat(),
        "source_file": str(source_path),
        "output_file": str(output_path),
        "statistics": get_swow_statistics(df),
        "processing": {
            "loader_version": "1.0.0",
            "validation_applied": True,
            "standardization_applied": True,
        },
    }

    return manifest
