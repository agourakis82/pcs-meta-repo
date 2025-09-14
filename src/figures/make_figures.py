#!/usr/bin/env python3
"""Figure generation for v4.4 - Modal split & multilingual KEC"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set style
plt.style.use("seaborn-v0_8")
sns.set_palette("husl")


def load_kec_data(lang: str, kec_base: Path) -> Optional[pd.DataFrame]:
    """Load KEC data for a language"""
    lang_dir = kec_base / lang
    if not lang_dir.exists():
        logger.warning(f"KEC data for {lang} not found")
        return None

    try:
        # Load main KEC components
        entropy_path = lang_dir / "entropy.parquet"
        if entropy_path.exists():
            return pd.read_parquet(entropy_path)
    except Exception as e:
        logger.error(f"Failed to load KEC for {lang}: {e}")
    return None


def make_f1_kec_distributions(kec_base: Path, output_dir: Path, version: str) -> None:
    """F1: KEC distributions per language"""
    logger.info("Generating F1: KEC distributions")

    fig_dir = output_dir / version / "kec_distributions"
    fig_dir.mkdir(parents=True, exist_ok=True)

    languages = ["en", "es", "nl", "zh"]

    for lang in languages:
        kec_df = load_kec_data(lang, kec_base)
        if kec_df is None:
            continue

        # Create figure
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        fig.suptitle(f"KEC Distributions - {lang.upper()}", fontsize=16)

        # Assume KEC metrics are in columns
        metrics = ["entropy", "curvature", "coherence", "components"]

        for i, metric in enumerate(metrics):
            ax = axes[i // 2, i % 2]

            if metric in kec_df.columns:
                # Remove outliers for ES if needed
                data = kec_df[metric].dropna()
                if lang == "es":
                    q1, q3 = data.quantile([0.25, 0.75])
                    iqr = q3 - q1
                    data = data[(data >= q1 - 1.5 * iqr) & (data <= q3 + 1.5 * iqr)]

                ax.hist(data, bins=50, alpha=0.7, density=True)
                ax.set_title(f"{metric.title()}")
                ax.set_xlabel("Value")
                ax.set_ylabel("Density")
            else:
                ax.text(
                    0.5,
                    0.5,
                    f"{metric}\nNot Available",
                    ha="center",
                    va="center",
                    transform=ax.transAxes,
                )
                ax.set_title(f"{metric.title()} (N/A)")

        plt.tight_layout()

        # Save
        output_path = fig_dir / f"F1_kec_distributions_{lang}.png"
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        logger.info(f"Saved {output_path}")
        plt.close()


def make_f2_reading_vs_kec(
    integration_dir: Path, output_dir: Path, version: str
) -> None:
    """F2: Reading times vs KEC"""
    logger.info("Generating F2: Reading vs KEC")

    fig_dir = output_dir / version
    fig_dir.mkdir(parents=True, exist_ok=True)

    # Try to load integrated RT data
    rt_files = list(integration_dir.glob("*_kec_rt.parquet"))
    if not rt_files:
        logger.warning("No integrated RT data found")
        return

    # Use first available dataset
    rt_path = rt_files[0]
    try:
        df = pd.read_parquet(rt_path)
        logger.info(f"Loaded RT data from {rt_path}: {len(df)} records")
    except Exception as e:
        logger.error(f"Failed to load RT data: {e}")
        return

    # Create figure
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle("Reading Times vs KEC Metrics", fontsize=16)

    # RT measures
    rt_measures = ["ffd_ms", "gd_ms", "trt_ms"]
    rt_labels = ["First Fixation Duration", "Gaze Duration", "Total Reading Time"]

    # KEC measure (assume entropy is available)
    kec_col = "entropy" if "entropy" in df.columns else None

    if kec_col is None:
        logger.warning("No KEC metrics found in RT data")
        return

    for i, (rt_col, label) in enumerate(zip(rt_measures, rt_labels)):
        ax = axes[i]

        if rt_col in df.columns:
            # Filter valid data
            valid_data = df.dropna(subset=[rt_col, kec_col])

            if len(valid_data) > 0:
                # Scatter plot with regression line
                ax.scatter(valid_data[kec_col], valid_data[rt_col], alpha=0.6, s=20)

                # Add regression line
                z = np.polyfit(valid_data[kec_col], valid_data[rt_col], 1)
                p = np.poly1d(z)
                ax.plot(valid_data[kec_col], p(valid_data[kec_col]), "r--", alpha=0.8)

                ax.set_xlabel("KEC Entropy")
                ax.set_ylabel(f"{label} (ms)")
                ax.set_title(label)
            else:
                ax.text(
                    0.5,
                    0.5,
                    "No valid data",
                    ha="center",
                    va="center",
                    transform=ax.transAxes,
                )
        else:
            ax.text(
                0.5,
                0.5,
                f"{rt_col}\nNot Available",
                ha="center",
                va="center",
                transform=ax.transAxes,
            )

    plt.tight_layout()

    # Save
    output_path = fig_dir / "F2_reading_vs_KEC.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    logger.info(f"Saved {output_path}")
    plt.close()


def make_f3_eeg_vs_kec(integration_dir: Path, output_dir: Path, version: str) -> None:
    """F3: EEG vs KEC"""
    logger.info("Generating F3: EEG vs KEC")

    fig_dir = output_dir / version
    fig_dir.mkdir(parents=True, exist_ok=True)

    # Try to load integrated EEG data
    eeg_files = list(integration_dir.glob("*_kec_eeg.parquet"))
    if not eeg_files:
        logger.warning("No integrated EEG data found")
        return

    # Use first available dataset
    eeg_path = eeg_files[0]
    try:
        df = pd.read_parquet(eeg_path)
        logger.info(f"Loaded EEG data from {eeg_path}: {len(df)} records")
    except Exception as e:
        logger.error(f"Failed to load EEG data: {e}")
        return

    # Create figure
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle("EEG Metrics vs KEC", fontsize=16)

    # EEG bands
    eeg_bands = ["theta", "alpha", "beta", "eeg_metric"]
    band_labels = ["Theta Power", "Alpha Power", "Beta Power", "EEG Metric"]

    # KEC measure
    kec_col = "entropy" if "entropy" in df.columns else None

    if kec_col is None:
        logger.warning("No KEC metrics found in EEG data")
        return

    for i, (band, label) in enumerate(zip(eeg_bands, band_labels)):
        ax = axes[i // 2, i % 2]

        if band in df.columns:
            # Filter valid data
            valid_data = df.dropna(subset=[band, kec_col])

            if len(valid_data) > 0:
                # Box plot by KEC quartiles
                valid_data["kec_quartile"] = pd.qcut(
                    valid_data[kec_col], 4, labels=["Q1", "Q2", "Q3", "Q4"]
                )

                sns.boxplot(data=valid_data, x="kec_quartile", y=band, ax=ax)
                ax.set_xlabel("KEC Entropy Quartile")
                ax.set_ylabel(label)
                ax.set_title(label)
            else:
                ax.text(
                    0.5,
                    0.5,
                    "No valid data",
                    ha="center",
                    va="center",
                    transform=ax.transAxes,
                )
        else:
            ax.text(
                0.5,
                0.5,
                f"{band}\nNot Available",
                ha="center",
                va="center",
                transform=ax.transAxes,
            )

    plt.tight_layout()

    # Save
    output_path = fig_dir / "F3_EEG_vs_KEC.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    logger.info(f"Saved {output_path}")
    plt.close()


def main():
    parser = argparse.ArgumentParser(description="Generate figures for v4.4")
    parser.add_argument("--version", default="v4.4", help="Version tag")
    parser.add_argument("--compat", action="store_true", help="Use legacy merged file")

    args = parser.parse_args()

    # Set up paths
    repo_root = Path(__file__).parent.parent
    data_dir = repo_root / "data"
    kec_base = data_dir / "L2_derived" / "kec"
    integration_dir = data_dir / "processed" / args.version / "integration"
    output_dir = repo_root / "figures"

    try:
        # Generate all figures
        make_f1_kec_distributions(kec_base, output_dir, args.version)
        make_f2_reading_vs_kec(integration_dir, output_dir, args.version)
        make_f3_eeg_vs_kec(integration_dir, output_dir, args.version)

        logger.info(f"All figures generated for {args.version}")

    except Exception as e:
        logger.error(f"Figure generation failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
