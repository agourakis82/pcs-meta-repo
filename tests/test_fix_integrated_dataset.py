import pandas as pd
import numpy as np
import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from scripts.fix_integrated_dataset import IntegratedDatasetFixer


def test_clean_numeric_column_basic():
    fixer = IntegratedDatasetFixer()
    series = pd.Series(["1.0", "2", "nan", "None", "false", "true", "-1", "0", "5"])
    cleaned = fixer.clean_numeric_column(series, "fixation_duration")
    # "false", "true", "nan", "None" should become NaN
    # negative and zero values should become NaN for fixation_duration
    expected = pd.Series(
        [1.0, 2.0, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, 5.0]
    )
    pd.testing.assert_series_equal(
        cleaned.reset_index(drop=True), expected.reset_index(drop=True)
    )


def test_fix_dataset_creates_backup(tmp_path):
    # Create a sample CSV file
    df = pd.DataFrame(
        {
            "fixation_duration": ["1", "2", "false", "true", "nan"],
            "entropy": ["0.1", "0.2", "nan", "none", "0.3"],
        }
    )
    input_file = tmp_path / "input.csv"
    df.to_csv(input_file, index=False)

    fixer = IntegratedDatasetFixer()
    fixed_df = fixer.fix_dataset(input_file)

    # Check backup file exists
    backup_file = tmp_path / "input_backup.csv"
    assert backup_file.exists()

    # Check cleaned data
    assert fixed_df["fixation_duration"].isna().sum() == 3  # false, true, nan -> NaN
    assert fixed_df["entropy"].isna().sum() == 2  # nan, none -> NaN


def test_validate_fix_returns_stats():
    fixer = IntegratedDatasetFixer()
    df = pd.DataFrame(
        {
            "fixation_duration": [1.0, 2.0, np.nan, 4.0],
            "entropy": [0.1, 0.2, 0.3, 0.4],
            "curvature": [np.nan, 0.5, 0.6, 0.7],
            "coherence": [0.1, np.nan, 0.3, 0.4],
        }
    )
    results = fixer.validate_fix(df)
    assert "fixation_duration" in results
    assert results["fixation_duration"]["valid_count"] == 3
    assert results["entropy"]["valid_count"] == 4


if __name__ == "__main__":
    pytest.main()
