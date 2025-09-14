"""
GECO Eye-Tracking Loader for v4.4 modality separation.
Loads eye-tracking data for English and Dutch from GECO dataset.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
import re

try:
    from .validation_utils import get_contracts_import
success, contracts = get_contracts_import()
validate_word_events_rt = contracts.get('validate_word_events_rt') if success else None
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


def load_geco_et_data(raw_dir: str) -> pd.DataFrame:
    """
    Load GECO eye-tracking data with v4.4 schema.
    
    Args:
        raw_dir: Path to raw GECO data
        
    Returns:
        DataFrame with word_events_rt schema
    """
    logger.info(f"Loading GECO ET data from {raw_dir}")
    
    # Real-only policy: this loader must parse actual GECO files.
    # Raise until implemented for your file layout.
    if not Path(raw_dir).exists():
        raise FileNotFoundError(f"GECO raw_dir not found: {raw_dir}")
    raise NotImplementedError("Implement GECO ET parsing for your data schema; no synthetic data allowed.")
    df["word_norm"] = df["word"].apply(normalize_word)
    
    # After implementing real parsing: normalize, validate, and return.


def process_geco_et_to_parquet(raw_dir: str, output_path: str) -> None:
    """
    Process GECO ET data and save to parquet format.
    
    Args:
        raw_dir: Path to raw GECO data
        output_path: Path to save processed parquet file
    """
    df = load_geco_et_data(raw_dir)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, compression="snappy", index=False)
    logger.info(f"GECO ET data saved to {output_path}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Process GECO ET data")
    parser.add_argument("--raw_dir", required=True, help="Path to raw GECO data")
    parser.add_argument("--output", required=True, help="Output parquet file path")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.INFO)
    
    process_geco_et_to_parquet(args.raw_dir, args.output)
    print(f"✅ GECO ET processing completed")
