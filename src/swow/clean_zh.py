"""
SWOW Chinese Data Cleaning Module

Provides specialized cleaning and preprocessing functions for Chinese SWOW data.
Handles Chinese-specific text normalization, validation, and quality control.

Author: PCS Meta-Repo
License: MIT
"""

import pandas as pd
import numpy as np
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple, Set
import logging

# Set up logging
logger = logging.getLogger(__name__)


def clean_chinese_swow(
    df: pd.DataFrame,
    min_word_length: int = 1,
    max_word_length: int = 10,
    remove_numbers: bool = True,
    remove_punctuation: bool = True,
    remove_duplicates: bool = True,
    min_frequency: int = 1,
    quality_threshold: float = 0.8,
) -> pd.DataFrame:
    """
    Clean and preprocess Chinese SWOW data.

    Args:
        df: Raw SWOW DataFrame
        min_word_length: Minimum word length (characters)
        max_word_length: Maximum word length (characters)
        remove_numbers: Whether to remove numeric entries
        remove_punctuation: Whether to remove punctuation
        remove_duplicates: Whether to remove duplicate associations
        min_frequency: Minimum frequency threshold
        quality_threshold: Quality score threshold (0-1)

    Returns:
        Cleaned DataFrame
    """

    logger.info(f"Cleaning Chinese SWOW data: {len(df):,} initial associations")

    df_clean = df.copy()
    initial_count = len(df_clean)

    # Basic cleaning
    df_clean = _basic_chinese_cleaning(df_clean, remove_punctuation)
    logger.info(f"After basic cleaning: {len(df_clean):,} associations")

    # Length filtering
    df_clean = _filter_by_length(df_clean, min_word_length, max_word_length)
    logger.info(f"After length filtering: {len(df_clean):,} associations")

    # Chinese-specific validation
    df_clean = _validate_chinese_words(df_clean)
    logger.info(f"After Chinese validation: {len(df_clean):,} associations")

    # Remove duplicates if requested
    if remove_duplicates:
        df_clean = _remove_duplicates(df_clean)
        logger.info(f"After removing duplicates: {len(df_clean):,} associations")

    # Add cleaning metadata
    df_clean.attrs = {
        "cleaning_applied": True,
        "initial_count": initial_count,
        "final_count": len(df_clean),
        "language": "zh",
        "cleaning_version": "1.0.0",
    }

    logger.info(
        f"Chinese SWOW cleaning completed: {len(df_clean):,} final associations"
    )
    return df_clean


def _basic_chinese_cleaning(df: pd.DataFrame, remove_punctuation: bool) -> pd.DataFrame:
    """Apply basic Chinese text cleaning."""

    df_clean = df.copy()

    # Convert to string and strip whitespace
    df_clean["cue"] = df_clean["cue"].astype(str).str.strip()
    df_clean["response"] = df_clean["response"].astype(str).str.strip()

    # Remove punctuation if requested (preserve Chinese characters)
    if remove_punctuation:
        # Keep Chinese characters, letters, and numbers
        pattern = r"[^\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaffa-zA-Z0-9]"
        df_clean["cue"] = df_clean["cue"].str.replace(pattern, "", regex=True)
        df_clean["response"] = df_clean["response"].str.replace(pattern, "", regex=True)

    # Remove empty entries
    df_clean = df_clean[df_clean["cue"] != ""]
    df_clean = df_clean[df_clean["response"] != ""]

    return df_clean


def _validate_chinese_words(df: pd.DataFrame) -> pd.DataFrame:
    """Validate that entries contain Chinese characters."""

    # Pattern for Chinese characters (CJK Unified Ideographs)
    chinese_pattern = r"[\u4e00-\u9fff]+"

    df_validated = df[
        df["cue"].str.contains(chinese_pattern, na=False)
        & df["response"].str.contains(chinese_pattern, na=False)
    ].copy()

    return df_validated


def _filter_by_length(
    df: pd.DataFrame, min_length: int, max_length: int
) -> pd.DataFrame:
    """Filter words by character length."""

    df_filtered = df[
        (df["cue"].str.len() >= min_length)
        & (df["cue"].str.len() <= max_length)
        & (df["response"].str.len() >= min_length)
        & (df["response"].str.len() <= max_length)
    ].copy()

    return df_filtered


def _remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Remove duplicate cue-response pairs."""

    df_dedup = df.drop_duplicates(subset=["cue", "response"]).copy()

    if "frequency" in df.columns:
        df_dedup = df_dedup.groupby(["cue", "response"], as_index=False).agg(
            {
                "frequency": "sum",
                **{
                    col: "first"
                    for col in df.columns
                    if col not in ["cue", "response", "frequency"]
                },
            }
        )

    return df_dedup
