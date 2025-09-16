"""
Data contracts for DX-CODEX word-level event schemas.
Provides basic validation and quality checks used by loaders.
"""

from typing import Dict
import warnings
import pandas as pd


WORD_EVENTS_SCHEMA = {
    "required": ["subject_id", "doc_id", "sent_id", "word_id", "word", "lang"],
    "et_optional": ["ffd_ms", "gd_ms", "trt_ms", "nfix"],
    "eeg_optional": ["eeg_metric", "theta", "alpha", "beta", "onset_ms", "offset_ms"],
}


def validate_word_events(df: pd.DataFrame, dataset_name: str = "") -> Dict[str, any]:
    results = {"valid": True, "errors": [], "warnings": [], "stats": {}}
    missing = [c for c in WORD_EVENTS_SCHEMA["required"] if c not in df.columns]
    if missing:
        results["valid"] = False
        results["errors"].append(f"Missing required columns for {dataset_name}: {missing}")
        return results
    # Stats
    results["stats"] = {
        "n_rows": len(df),
        "n_subjects": df["subject_id"].nunique() if "subject_id" in df.columns else 0,
        "n_words_unique": df["word"].nunique() if "word" in df.columns else 0,
        "et_columns": [c for c in WORD_EVENTS_SCHEMA["et_optional"] if c in df.columns],
        "eeg_columns": [c for c in WORD_EVENTS_SCHEMA["eeg_optional"] if c in df.columns],
    }
    return results


def optional_pandera_validate(df: pd.DataFrame, schema_type: str = "word"):
    try:
        import pandera as pa  # noqa: F401
    except Exception:
        return


def check_dataset_quality(df: pd.DataFrame, dataset_name: str, min_rows: int = 1000) -> bool:
    res = validate_word_events(df, dataset_name)
    if not res.get("valid", True):
        for e in res.get("errors", []):
            print("❌", e)
        return False
    if res["stats"]["n_rows"] < min_rows:
        print(f"❌ {dataset_name} has {res['stats']['n_rows']} rows, minimum {min_rows} required")
        return False
    print(f"✅ {dataset_name} validation passed: rows={res['stats']['n_rows']:,}")
    return True

