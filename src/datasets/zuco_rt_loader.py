"""
ZuCo RT/ET loader - harmonized schema for v4.4
"""

import logging
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def validate_word_events_rt(df: pd.DataFrame) -> bool:
    """Validate RT schema compliance"""
    required_cols = [
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
    missing = set(required_cols) - set(df.columns)
    if missing:
        logger.error(f"Missing required columns: {missing}")
        return False
    return True


def normalize_word(word: str) -> str:
    """Normalize word: lowercase, strip, handle placeholders"""
    if pd.isna(word):
        return ""
    word = str(word).lower().strip()
    # Drop placeholder patterns
    if word.startswith("word_") and word[5:].isdigit():
        return ""
    return word


def load_zuco_rt(raw_dir: Path, output_path: Optional[Path] = None) -> pd.DataFrame:
    """Load ZuCo RT data with harmonized schema"""
    logger.info(f"Loading ZuCo RT from {raw_dir}")

    # Find mat/csv files
    data_files = list(raw_dir.glob("**/*.mat")) + list(raw_dir.glob("**/*.csv"))
    if not data_files:
        raise FileNotFoundError(f"No data files found in {raw_dir}")

    records = []

    for file_path in data_files:
        logger.debug(f"Processing {file_path}")

        if file_path.suffix == ".mat":
            # Handle MATLAB files (simplified - adjust to real ZuCo structure)
            try:
                import scipy.io

                mat_data = scipy.io.loadmat(file_path)
                # Extract reading times - adjust keys to real ZuCo structure
                for subj_key in mat_data.keys():
                    if not subj_key.startswith("_"):
                        continue
            except ImportError:
                logger.warning("scipy not available for .mat files, skipping")
                continue

        elif file_path.suffix == ".csv":
            df_raw = pd.read_csv(file_path)

            # Map columns to harmonized schema (adjust to real ZuCo)
            col_mapping = {
                "subject": "subject_id",
                "task": "task_id",
                "document": "doc_id",
                "sentence": "sent_id",
                "word_position": "word_id",
                "first_fixation_duration": "ffd_ms",
                "gaze_duration": "gd_ms",
                "total_reading_time": "trt_ms",
                "fixation_count": "nfix",
                "word_length": "length",
                "log_frequency": "logfreq",
                "sentence_position": "position",
            }

            for old_col, new_col in col_mapping.items():
                if old_col in df_raw.columns:
                    df_raw = df_raw.rename(columns={old_col: new_col})

            # Add defaults
            df_raw["lang"] = "en"

            # Normalize words
            if "word" in df_raw.columns:
                df_raw["word"] = df_raw["word"].apply(normalize_word)
                # Filter out empty words
                df_raw = df_raw[df_raw["word"] != ""]

            # Convert to numeric where needed
            numeric_cols = [
                "ffd_ms",
                "gd_ms",
                "trt_ms",
                "nfix",
                "length",
                "logfreq",
                "position",
            ]
            for col in numeric_cols:
                if col in df_raw.columns:
                    df_raw[col] = pd.to_numeric(df_raw[col], errors="coerce")

            records.append(df_raw)

    if not records:
        raise ValueError("No valid records found")

    df_final = pd.concat(records, ignore_index=True)

    # Ensure required columns exist with defaults
    required_defaults = {
        "lang": "en",
        "subject_id": "unknown",
        "task_id": "unknown",
        "doc_id": "unknown",
        "sent_id": 0,
        "word_id": 0,
        "word": "",
        "ffd_ms": np.nan,
        "gd_ms": np.nan,
        "trt_ms": np.nan,
        "nfix": np.nan,
        "length": np.nan,
        "logfreq": np.nan,
        "position": np.nan,
    }

    for col, default in required_defaults.items():
        if col not in df_final.columns:
            df_final[col] = default

    # Validate
    if not validate_word_events_rt(df_final):
        raise ValueError("Schema validation failed")

    logger.info(f"Loaded {len(df_final)} word events")

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df_final.to_parquet(output_path, index=False)
        logger.info(f"Saved to {output_path}")

    return df_final
