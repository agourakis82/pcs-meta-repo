"""
OneStop Eye-Tracking Loader for v4.4 modality separation.
Loads eye-tracking data for English from OneStop dataset.
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
    from ..contracts_v4.4 import validate_word_events_rt
except ImportError:
    import sys
    from pathlib import Path as P
    sys.path.append(str(P(__file__).parent.parent))
    from contracts_v4.4 import validate_word_events_rt

logger = logging.getLogger(__name__)


def normalize_word(word: str) -> str:
    if pd.isna(word) or word == "":
        return ""
    normalized = re.sub(r'[^\w]', '', str(word).lower())
    return normalized


def load_onestop_et_data(raw_dir: str) -> pd.DataFrame:
    """
    Load OneStop eye-tracking data with v4.4 schema.
    
    Args:
        raw_dir: Path to raw OneStop data
        
    Returns:
        DataFrame with word_events_rt schema
    """
    logger.info(f"Loading OneStop ET data from {raw_dir}")
    
    # Real-only policy: this loader must parse actual OneStop files.
    # Raise until implemented for your file layout.
    if not Path(raw_dir).exists():
        raise FileNotFoundError(f"OneStop raw_dir not found: {raw_dir}")
    raise NotImplementedError("Implement OneStop ET parsing for your data schema; no synthetic data allowed.")
    df["word_norm"] = df["word"].apply(normalize_word)
    
    # After implementing real parsing: normalize, validate, and return.


def process_onestop_et_to_parquet(raw_dir: str, output_path: str) -> None:
    """
    Process OneStop ET data and save to parquet format.
    
    Args:
        raw_dir: Path to raw OneStop data
        output_path: Path to save processed parquet file
    """
    df = load_onestop_et_data(raw_dir)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, compression="snappy", index=False)
    logger.info(f"OneStop ET data saved to {output_path}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Process OneStop ET data")
    parser.add_argument("--raw_dir", required=True, help="Path to raw OneStop data")
    parser.add_argument("--output", required=True, help="Output parquet file path")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.INFO)
    
    process_onestop_et_to_parquet(args.raw_dir, args.output)
    print(f"✅ OneStop ET processing completed")
