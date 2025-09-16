"""
SWOW Dutch Data Cleaning Module

Provides specialized cleaning and preprocessing functions for Dutch SWOW data.
Handles Dutch-specific text normalization, validation, and quality control.

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

# Dutch-specific constants
DUTCH_STOPWORDS = {
    "de",
    "het",
    "een",
    "en",
    "van",
    "te",
    "dat",
    "die",
    "in",
    "is",
    "hij",
    "niet",
    "zijn",
    "op",
    "aan",
    "met",
    "als",
    "voor",
    "had",
    "er",
    "maar",
    "om",
    "hem",
    "dan",
    "zou",
    "of",
    "wat",
    "mijn",
    "men",
    "dit",
    "zo",
    "door",
    "over",
    "ze",
    "zich",
    "bij",
    "ook",
    "tot",
    "je",
    "mij",
    "uit",
    "der",
    "daar",
    "haar",
    "naar",
    "heb",
    "hoe",
    "heeft",
    "aan",
    "want",
    "ben",
    "nog",
    "was",
    "waren",
    "veel",
    "meer",
    "doen",
    "moet",
    "wel",
    "ik",
    "jij",
    "wij",
    "zij",
    "hun",
    "ons",
    "jullie",
}


def clean_dutch_swow(
    df: pd.DataFrame,
    remove_stopwords: bool = False,
    min_word_length: int = 2,
    max_word_length: int = 30,
    remove_numbers: bool = True,
    remove_punctuation: bool = True,
    normalize_case: bool = True,
    remove_duplicates: bool = True,
    min_frequency: int = 1,
    quality_threshold: float = 0.8,
) -> pd.DataFrame:
    """
    Clean and preprocess Dutch SWOW data.

    Args:
        df: Raw SWOW DataFrame
        remove_stopwords: Whether to remove Dutch stopwords
        min_word_length: Minimum word length
        max_word_length: Maximum word length
        remove_numbers: Whether to remove numeric entries
        remove_punctuation: Whether to remove punctuation
        normalize_case: Whether to convert to lowercase
        remove_duplicates: Whether to remove duplicate associations
        min_frequency: Minimum frequency threshold
        quality_threshold: Quality score threshold (0-1)

    Returns:
        Cleaned DataFrame
    """

    logger.info(f"Cleaning Dutch SWOW data: {len(df):,} initial associations")

    df_clean = df.copy()
    initial_count = len(df_clean)

    # Basic cleaning
    df_clean = _basic_dutch_cleaning(df_clean, normalize_case, remove_punctuation)
    logger.info(f"After basic cleaning: {len(df_clean):,} associations")

    # Length filtering
    df_clean = _filter_by_length(df_clean, min_word_length, max_word_length)
    logger.info(f"After length filtering: {len(df_clean):,} associations")

    # Dutch-specific validation
    df_clean = _validate_dutch_words(df_clean)
    logger.info(f"After Dutch validation: {len(df_clean):,} associations")

    # Remove stopwords if requested
    if remove_stopwords:
        df_clean = _remove_dutch_stopwords(df_clean)
        logger.info(f"After removing stopwords: {len(df_clean):,} associations")

    # Remove duplicates if requested
    if remove_duplicates:
        df_clean = _remove_duplicates(df_clean)
        logger.info(f"After removing duplicates: {len(df_clean):,} associations")

    # Add cleaning metadata
    df_clean.attrs = {
        "cleaning_applied": True,
        "initial_count": initial_count,
        "final_count": len(df_clean),
        "language": "nl",
        "cleaning_version": "1.0.0",
    }

    logger.info(f"Dutch SWOW cleaning completed: {len(df_clean):,} final associations")
    return df_clean


def _basic_dutch_cleaning(
    df: pd.DataFrame, normalize_case: bool, remove_punctuation: bool
) -> pd.DataFrame:
    """Apply basic Dutch text cleaning."""

    df_clean = df.copy()

    # Convert to string and strip whitespace
    df_clean["cue"] = df_clean["cue"].astype(str).str.strip()
    df_clean["response"] = df_clean["response"].astype(str).str.strip()

    # Normalize case if requested
    if normalize_case:
        df_clean["cue"] = df_clean["cue"].str.lower()
        df_clean["response"] = df_clean["response"].str.lower()

    # Remove punctuation if requested
    if remove_punctuation:
        pattern = r"[^a-zA-Z0-9\s\-]"
        df_clean["cue"] = df_clean["cue"].str.replace(pattern, "", regex=True)
        df_clean["response"] = df_clean["response"].str.replace(pattern, "", regex=True)

        # Clean up multiple spaces
        df_clean["cue"] = (
            df_clean["cue"].str.replace(r"\s+", " ", regex=True).str.strip()
        )
        df_clean["response"] = (
            df_clean["response"].str.replace(r"\s+", " ", regex=True).str.strip()
        )

    # Remove empty entries
    df_clean = df_clean[df_clean["cue"] != ""]
    df_clean = df_clean[df_clean["response"] != ""]

    return df_clean


def _validate_dutch_words(df: pd.DataFrame) -> pd.DataFrame:
    """Validate that entries look like Dutch words."""

    dutch_pattern = r"^[a-zA-Z]+(?:[\-\'][a-zA-Z]+)*$"

    df_validated = df[
        df["cue"].str.match(dutch_pattern, na=False)
        & df["response"].str.match(dutch_pattern, na=False)
    ].copy()

    return df_validated


def _remove_dutch_stopwords(df: pd.DataFrame) -> pd.DataFrame:
    """Remove Dutch stopwords."""

    df_filtered = df[
        ~df["cue"].isin(DUTCH_STOPWORDS) & ~df["response"].isin(DUTCH_STOPWORDS)
    ].copy()

    return df_filtered


def _filter_by_length(
    df: pd.DataFrame, min_length: int, max_length: int
) -> pd.DataFrame:
    """Filter words by length."""

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
