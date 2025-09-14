"""
SWOW Spanish Data Cleaning Module

Provides specialized cleaning and preprocessing functions for Spanish SWOW data.
Handles Spanish-specific text normalization, validation, and quality control.

Author: PCS Meta-Repo
License: MIT
"""

import pandas as pd
import numpy as np
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple, Set
import logging
import string
from collections import Counter

# Set up logging
logger = logging.getLogger(__name__)

# Spanish-specific constants
SPANISH_STOPWORDS = {
    "el",
    "la",
    "de",
    "que",
    "y",
    "a",
    "en",
    "un",
    "es",
    "se",
    "no",
    "te",
    "lo",
    "le",
    "da",
    "su",
    "por",
    "son",
    "con",
    "para",
    "al",
    "del",
    "los",
    "las",
    "una",
    "pero",
    "sus",
    "le",
    "ya",
    "o",
    "fue",
    "este",
    "ha",
    "si",
    "porque",
    "esta",
    "son",
    "entre",
    "cuando",
    "muy",
    "sin",
    "sobre",
    "ser",
    "tiene",
    "también",
    "me",
    "hasta",
    "hay",
    "donde",
    "han",
    "quien",
    "están",
    "estado",
    "desde",
    "todo",
    "nos",
    "durante",
    "todos",
    "uno",
    "les",
    "ni",
    "contra",
    "otros",
    "fueron",
    "ese",
    "eso",
    "había",
    "ante",
}

COMMON_SPANISH_WORDS = {
    "ser",
    "estar",
    "tener",
    "hacer",
    "poder",
    "decir",
    "ir",
    "ver",
    "dar",
    "saber",
    "querer",
    "llegar",
    "pasar",
    "deber",
    "poner",
    "parecer",
    "quedar",
    "creer",
    "hablar",
    "llevar",
    "dejar",
    "seguir",
    "encontrar",
    "llamar",
    "venir",
    "pensar",
    "salir",
    "volver",
    "tomar",
    "conocer",
    "vivir",
    "sentir",
    "tratar",
    "mirar",
    "contar",
    "empezar",
    "esperar",
    "buscar",
    "existir",
    "entrar",
    "trabajar",
    "escribir",
    "perder",
    "producir",
    "ocurrir",
    "entender",
    "pedir",
    "recibir",
    "recordar",
    "terminar",
    "permitir",
    "aparecer",
    "conseguir",
    "comenzar",
    "servir",
    "sacar",
    "necesitar",
    "mantener",
    "resultar",
    "leer",
    "caer",
    "cambiar",
    "presentar",
    "crear",
    "abrir",
    "considerar",
    "oír",
    "acabar",
    "convertir",
    "ganar",
    "formar",
    "traer",
    "partir",
    "morir",
    "aceptar",
    "realizar",
    "suponer",
}

# Spanish accent mappings for normalization
SPANISH_ACCENTS = {
    "á": "a",
    "é": "e",
    "í": "i",
    "ó": "o",
    "ú": "u",
    "ü": "u",
    "Á": "A",
    "É": "E",
    "Í": "I",
    "Ó": "O",
    "Ú": "U",
    "Ü": "U",
    "ñ": "n",
    "Ñ": "N",
}


def clean_spanish_swow(
    df: pd.DataFrame,
    remove_stopwords: bool = False,
    normalize_accents: bool = False,
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
    Clean and preprocess Spanish SWOW data.

    Args:
        df: Raw SWOW DataFrame
        remove_stopwords: Whether to remove Spanish stopwords
        normalize_accents: Whether to normalize Spanish accents
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

    logger.info(f"Cleaning Spanish SWOW data: {len(df):,} initial associations")

    # Make a copy to avoid modifying original
    df_clean = df.copy()

    # Ensure required columns exist
    if "cue" not in df_clean.columns or "response" not in df_clean.columns:
        raise ValueError("DataFrame must contain 'cue' and 'response' columns")

    initial_count = len(df_clean)

    # Step 1: Basic text cleaning
    df_clean = _basic_spanish_cleaning(
        df_clean, normalize_case, remove_punctuation, normalize_accents
    )
    logger.info(f"After basic cleaning: {len(df_clean):,} associations")

    # Step 2: Length filtering
    df_clean = _filter_by_length(df_clean, min_word_length, max_word_length)
    logger.info(f"After length filtering: {len(df_clean):,} associations")

    # Step 3: Remove numbers if requested
    if remove_numbers:
        df_clean = _remove_numeric_entries(df_clean)
        logger.info(f"After removing numbers: {len(df_clean):,} associations")

    # Step 4: Spanish-specific validation
    df_clean = _validate_spanish_words(df_clean)
    logger.info(f"After Spanish validation: {len(df_clean):,} associations")

    # Step 5: Remove stopwords if requested
    if remove_stopwords:
        df_clean = _remove_spanish_stopwords(df_clean)
        logger.info(f"After removing stopwords: {len(df_clean):,} associations")

    # Step 6: Remove duplicates if requested
    if remove_duplicates:
        df_clean = _remove_duplicates(df_clean)
        logger.info(f"After removing duplicates: {len(df_clean):,} associations")

    # Step 7: Frequency filtering
    if min_frequency > 1:
        df_clean = _filter_by_frequency(df_clean, min_frequency)
        logger.info(f"After frequency filtering: {len(df_clean):,} associations")

    # Step 8: Quality assessment and filtering
    df_clean = _assess_and_filter_quality(df_clean, quality_threshold)
    logger.info(f"After quality filtering: {len(df_clean):,} associations")

    # Add cleaning metadata
    df_clean = _add_cleaning_metadata(df_clean, initial_count)

    final_count = len(df_clean)
    removed_count = initial_count - final_count
    removal_rate = removed_count / initial_count if initial_count > 0 else 0

    logger.info(f"Spanish SWOW cleaning completed:")
    logger.info(f"  Initial: {initial_count:,} associations")
    logger.info(f"  Final: {final_count:,} associations")
    logger.info(f"  Removed: {removed_count:,} ({removal_rate:.1%})")

    return df_clean


def _basic_spanish_cleaning(
    df: pd.DataFrame,
    normalize_case: bool,
    remove_punctuation: bool,
    normalize_accents: bool,
) -> pd.DataFrame:
    """Apply basic Spanish text cleaning operations."""

    df_clean = df.copy()

    # Convert to string and strip whitespace
    df_clean["cue"] = df_clean["cue"].astype(str).str.strip()
    df_clean["response"] = df_clean["response"].astype(str).str.strip()

    # Normalize case if requested
    if normalize_case:
        df_clean["cue"] = df_clean["cue"].str.lower()
        df_clean["response"] = df_clean["response"].str.lower()

    # Normalize accents if requested
    if normalize_accents:
        for accented, unaccented in SPANISH_ACCENTS.items():
            df_clean["cue"] = df_clean["cue"].str.replace(accented, unaccented)
            df_clean["response"] = df_clean["response"].str.replace(
                accented, unaccented
            )

    # Remove punctuation if requested (preserve ñ and accented characters)
    if remove_punctuation:
        if normalize_accents:
            pattern = r"[^a-zA-Z0-9\s\-]"
        else:
            pattern = r"[^a-zA-ZáéíóúüñÁÉÍÓÚÜÑ0-9\s\-]"

        df_clean["cue"] = df_clean["cue"].str.replace(pattern, "", regex=True)
        df_clean["response"] = df_clean["response"].str.replace(pattern, "", regex=True)

        # Clean up multiple spaces and strip again
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


def _validate_spanish_words(df: pd.DataFrame) -> pd.DataFrame:
    """Validate that entries look like Spanish words."""

    # Pattern for valid Spanish words (including ñ and accented characters)
    spanish_pattern = r"^[a-zA-ZáéíóúüñÁÉÍÓÚÜÑ]+(?:[\-\'][a-zA-ZáéíóúüñÁÉÍÓÚÜÑ]+)*$"

    df_validated = df[
        df["cue"].str.match(spanish_pattern, na=False)
        & df["response"].str.match(spanish_pattern, na=False)
    ].copy()

    # Additional validation: check for reasonable character patterns
    # Remove entries with too many repeated characters
    df_validated = df_validated[
        ~df_validated["cue"].str.match(r".*(.)\1{3,}.*")
        & ~df_validated["response"].str.match(r".*(.)\1{3,}.*")
    ]

    return df_validated


def _remove_spanish_stopwords(df: pd.DataFrame) -> pd.DataFrame:
    """Remove Spanish stopwords."""

    df_filtered = df[
        ~df["cue"].isin(SPANISH_STOPWORDS) & ~df["response"].isin(SPANISH_STOPWORDS)
    ].copy()

    return df_filtered


def _remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Remove duplicate cue-response pairs."""

    # Remove exact duplicates
    df_dedup = df.drop_duplicates(subset=["cue", "response"]).copy()

    # If frequency column exists, aggregate frequencies for remaining duplicates
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


def _remove_numeric_entries(df: pd.DataFrame) -> pd.DataFrame:
    """Remove entries that are purely numeric."""

    df_filtered = df[
        ~df["cue"].str.match(r"^\d+$") & ~df["response"].str.match(r"^\d+$")
    ].copy()

    return df_filtered


def _filter_by_frequency(df: pd.DataFrame, min_frequency: int) -> pd.DataFrame:
    """Filter associations by minimum frequency."""

    if "frequency" in df.columns:
        df_filtered = df[df["frequency"] >= min_frequency].copy()
    else:
        # If no frequency column, compute frequency from duplicates
        freq_counts = (
            df.groupby(["cue", "response"])
            .size()
            .reset_index(name="computed_frequency")
        )
        df_with_freq = df.merge(freq_counts, on=["cue", "response"])
        df_filtered = df_with_freq[
            df_with_freq["computed_frequency"] >= min_frequency
        ].copy()
        df_filtered = df_filtered.drop("computed_frequency", axis=1)

    return df_filtered


def _assess_and_filter_quality(df: pd.DataFrame, threshold: float) -> pd.DataFrame:
    """Assess and filter associations by quality score."""

    quality_scores = []

    for _, row in df.iterrows():
        score = _compute_spanish_quality_score(row["cue"], row["response"])
        quality_scores.append(score)

    df_with_quality = df.copy()
    df_with_quality["quality_score"] = quality_scores

    # Filter by threshold
    df_filtered = df_with_quality[df_with_quality["quality_score"] >= threshold].copy()

    return df_filtered


def _compute_spanish_quality_score(cue: str, response: str) -> float:
    """Compute quality score for a Spanish cue-response pair."""

    score = 1.0

    # Penalize very short words
    if len(cue) < 3 or len(response) < 3:
        score -= 0.2

    # Penalize very long words (likely errors)
    if len(cue) > 15 or len(response) > 15:
        score -= 0.3

    # Penalize identical cue and response
    if cue == response:
        score -= 0.5

    # Bonus for common Spanish words
    if cue in COMMON_SPANISH_WORDS or response in COMMON_SPANISH_WORDS:
        score += 0.1

    # Penalize words with unusual character patterns for Spanish
    if _has_unusual_spanish_pattern(cue) or _has_unusual_spanish_pattern(response):
        score -= 0.2

    return max(0.0, min(1.0, score))


def _has_unusual_spanish_pattern(word: str) -> bool:
    """Check if word has unusual character patterns for Spanish."""

    # Spanish vowels including accented ones
    vowels = set("aeiouáéíóúü")
    consonants = set("bcdfghjklmnpqrstvwxyzñ")

    vowel_count = sum(1 for c in word.lower() if c in vowels)
    consonant_count = sum(1 for c in word.lower() if c in consonants)

    total_letters = vowel_count + consonant_count

    if total_letters == 0:
        return True

    vowel_ratio = vowel_count / total_letters
    consonant_ratio = consonant_count / total_letters

    # Flag words with extreme vowel/consonant ratios
    if vowel_ratio > 0.8 or consonant_ratio > 0.9:
        return True

    # Check for repeated character patterns
    if re.search(r"(.{2,})\1{2,}", word.lower()):
        return True

    return False


def _add_cleaning_metadata(df: pd.DataFrame, initial_count: int) -> pd.DataFrame:
    """Add metadata about the cleaning process."""

    df_with_meta = df.copy()

    df_with_meta.attrs = {
        "cleaning_applied": True,
        "initial_count": initial_count,
        "final_count": len(df),
        "removal_rate": (initial_count - len(df)) / initial_count
        if initial_count > 0
        else 0,
        "language": "es",
        "cleaning_version": "1.0.0",
    }

    return df_with_meta


def get_spanish_cleaning_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """Get statistics about Spanish SWOW data."""

    stats = {
        "total_associations": len(df),
        "unique_cues": df["cue"].nunique(),
        "unique_responses": df["response"].nunique(),
        "unique_words": len(set(df["cue"]) | set(df["response"])),
        "avg_cue_length": df["cue"].str.len().mean(),
        "avg_response_length": df["response"].str.len().mean(),
        "stopword_ratio": {
            "cues": df["cue"].isin(SPANISH_STOPWORDS).mean(),
            "responses": df["response"].isin(SPANISH_STOPWORDS).mean(),
        },
        "common_word_ratio": {
            "cues": df["cue"].isin(COMMON_SPANISH_WORDS).mean(),
            "responses": df["response"].isin(COMMON_SPANISH_WORDS).mean(),
        },
        "accented_word_ratio": {
            "cues": df["cue"].str.contains(r"[áéíóúüñ]", na=False).mean(),
            "responses": df["response"].str.contains(r"[áéíóúüñ]", na=False).mean(),
        },
    }

    # Add frequency statistics if available
    if "frequency" in df.columns:
        stats["frequency_stats"] = {
            "mean": df["frequency"].mean(),
            "std": df["frequency"].std(),
            "min": df["frequency"].min(),
            "max": df["frequency"].max(),
            "median": df["frequency"].median(),
        }

    return stats
