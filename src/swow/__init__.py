"""
SWOW (Small World of Words) Processing Module

This module provides comprehensive functionality for processing multilingual
SWOW datasets and computing KEC (Knowledge, Entropy, Curvature) metrics.

Supported Languages:
- EN (English)
- ES (Spanish)
- ZH (Chinese)
- NL (Dutch)

Main Components:
- Data loading and cleaning
- Graph construction
- KEC metrics computation
- Cross-language alignment
- Integration with neurophysiological datasets

Author: PCS Meta-Repo
License: MIT
"""

from pathlib import Path
from typing import Dict, List, Any, Optional

# Version information
__version__ = "1.0.0"
__author__ = "PCS Meta-Repo"
__license__ = "MIT"

# Supported languages
SUPPORTED_LANGUAGES = ["en", "es", "zh", "nl"]

# Language metadata
LANGUAGE_INFO = {
    "en": {
        "name": "English",
        "release_date": "2018-10-18",
        "participants_per_cue": 100,
        "description": "SWOW-EN: English word association norms",
    },
    "es": {
        "name": "Spanish",
        "release_date": "2022-09-17",
        "participants_per_cue": 70,
        "description": "SWOW-RP: Spanish word association norms",
    },
    "zh": {
        "name": "Chinese",
        "release_date": "2024-11-04",
        "participants_per_cue": 55,
        "description": "SWOW-ZH: Chinese word association norms",
    },
    "nl": {
        "name": "Dutch",
        "release_date": "2013-xx-xx",
        "participants_per_cue": "variable",
        "description": "SWOW-NL: Dutch word association norms",
    },
}


def get_supported_languages() -> List[str]:
    """Get list of supported SWOW languages."""
    return SUPPORTED_LANGUAGES.copy()


def get_language_info(language: str) -> Dict[str, Any]:
    """Get metadata for a specific language."""
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(
            f"Unsupported language: {language}. Supported: {SUPPORTED_LANGUAGES}"
        )
    return LANGUAGE_INFO[language].copy()


def validate_language(language: str) -> bool:
    """Validate if a language is supported."""
    return language in SUPPORTED_LANGUAGES


# Import main functionality (with error handling for optional dependencies)
try:
    from .io import load_swow_csv, save_swow_data
    from .graph import build_swow_graph, validate_graph
    from .metrics_kec import compute_swow_kec_metrics
    from .clean_en import clean_english_swow
    from .clean_es import clean_spanish_swow
    from .clean_zh import clean_chinese_swow
    from .clean_nl import clean_dutch_swow
    from .align import align_multilingual_swow
    from .api import SWOWProcessor, MultilingualSWOWAnalyzer

    __all__ = [
        # Core functions
        "load_swow_csv",
        "save_swow_data",
        "build_swow_graph",
        "validate_graph",
        "compute_swow_kec_metrics",
        # Language-specific cleaning
        "clean_english_swow",
        "clean_spanish_swow",
        "clean_chinese_swow",
        "clean_dutch_swow",
        # Cross-language functionality
        "align_multilingual_swow",
        # High-level APIs
        "SWOWProcessor",
        "MultilingualSWOWAnalyzer",
        # Utilities
        "get_supported_languages",
        "get_language_info",
        "validate_language",
        # Constants
        "SUPPORTED_LANGUAGES",
        "LANGUAGE_INFO",
    ]

except ImportError as e:
    # Graceful degradation if some modules are missing
    print(f"Warning: Some SWOW modules could not be imported: {e}")

    __all__ = [
        "get_supported_languages",
        "get_language_info",
        "validate_language",
        "SUPPORTED_LANGUAGES",
        "LANGUAGE_INFO",
    ]
