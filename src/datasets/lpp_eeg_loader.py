"""
LPP EEG Loader for v4.4 modality separation.
Loads EEG data from Le Petit Prince dataset.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
import re

# Standardized validation imports
try:
    from .validation_utils import get_contracts_import
    success, contracts = get_contracts_import()
    if success:
        validate_word_events_rt = contracts.get('validate_word_events_rt')
        validate_word_events_eeg = contracts.get('validate_word_events_eeg')
        validate_target_degeneracy = contracts.get('validate_target_degeneracy')
    else:
        # Fallback - validation will be limited
        validate_word_events_rt = None
        validate_word_events_eeg = None
        validate_target_degeneracy = None
except ImportError:
    # Ultimate fallback
    validate_word_events_rt = None
    validate_word_events_eeg = None
    validate_target_degeneracy = None
    logger.warning("Validation functions not available - imports failed")


try:
    from src.contracts_v4_4 import validate_word_events_eeg
except ImportError:
    import sys
    from pathlib import Path as P

    sys.path.append(str(P(__file__).parent.parent))
    from contracts_v4_4 import validate_word_events_eeg

logger = logging.getLogger(__name__)


def normalize_word(word: str) -> str:
    if pd.isna(word) or word == "":
        return ""
    normalized = re.sub(r"[^\w]", "", str(word).lower())
    return normalized


def load_lpp_eeg_data(raw_dir: str) -> pd.DataFrame:
    """
    Load LPP EEG data with v4.4 schema.

    Args:
        raw_dir: Path to raw LPP data

    Returns:
        DataFrame with word_events_eeg schema
    """
    logger.info(f"Loading LPP EEG data from {raw_dir}")

    # Real-only policy: must parse actual LPP files.
    if not Path(raw_dir).exists():
        raise FileNotFoundError(f"LPP raw_dir not found: {raw_dir}")
    raise NotImplementedError("Implement LPP EEG parsing; no synthetic data allowed.")
    df["word_norm"] = df["word"].apply(normalize_word)

    # After implementing real parsing: normalize, validate, and return.


def process_lpp_eeg_to_parquet(raw_dir: str, output_path: str) -> None:
    """
    Process LPP EEG data and save to parquet format.

    Args:
        raw_dir: Path to raw LPP data
        output_path: Path to save processed parquet file
    """
    df = load_lpp_eeg_data(raw_dir)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, compression="snappy", index=False)
    logger.info(f"LPP EEG data saved to {output_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Process LPP EEG data")
    parser.add_argument("--raw_dir", required=True, help="Path to raw LPP data")
    parser.add_argument("--output", required=True, help="Output parquet file path")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.INFO)

    process_lpp_eeg_to_parquet(args.raw_dir, args.output)
    print(f"✅ LPP EEG processing completed")
