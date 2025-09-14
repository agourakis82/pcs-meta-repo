#!/usr/bin/env python3
"""
Create mock datasets for testing PCS-Meta-Repo v4.4 pipeline
Research-grade test data following established data structures
"""

import logging
from pathlib import Path
from typing import Any, Dict

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_mock_zuco_rt_data(output_dir: Path) -> None:
    """
    Create mock ZuCo RT data following established eye-tracking paradigms.

    References:
    - Hollenstein et al. (2018). ZuCo, a simultaneous EEG and eye-tracking corpus
    - Rayner (2009). Eye movements and attention in reading, scene perception, and visual search
    """
    logger.info(f"Creating mock ZuCo RT data in {output_dir}")

    # Create realistic reading time data
    np.random.seed(42)  # Reproducible for testing

    n_subjects = 3
    n_sentences = 10
    words_per_sentence = 8

    records = []

    # Sample vocabulary with frequency estimates
    vocab = [
        ("the", 7.0),
        ("and", 6.5),
        ("of", 6.8),
        ("to", 6.2),
        ("a", 6.9),
        ("in", 6.1),
        ("is", 5.8),
        ("it", 5.9),
        ("you", 5.7),
        ("that", 5.6),
        ("was", 5.4),
        ("for", 5.5),
        ("on", 5.3),
        ("are", 5.2),
        ("as", 5.1),
        ("with", 5.0),
        ("his", 4.9),
        ("they", 4.8),
        ("be", 4.7),
        ("at", 4.6),
        ("reading", 3.5),
        ("comprehension", 2.8),
        ("cognitive", 2.9),
        ("processing", 3.1),
        ("attention", 3.2),
        ("memory", 3.4),
        ("semantic", 2.7),
        ("syntactic", 2.4),
        ("lexical", 2.3),
        ("neural", 2.6),
    ]

    word_id = 0

    for subj in range(1, n_subjects + 1):
        for sent in range(1, n_sentences + 1):
            for pos in range(1, words_per_sentence + 1):
                word, logfreq = vocab[np.random.randint(0, len(vocab))]

                # Simulate realistic reading times based on word properties
                # Following established models (e.g., E-Z Reader, SWIFT)
                base_rt = 200  # Base reading time
                freq_effect = max(0, (4.0 - logfreq) * 20)  # Frequency effect
                length_effect = len(word) * 15  # Length effect
                position_effect = pos * 5  # Position in sentence

                # Add individual differences and noise
                subj_factor = 1.0 + (subj - 2) * 0.1
                noise = np.random.normal(0, 30)

                # First fixation duration (FFD)
                ffd = max(80, base_rt + freq_effect + noise * 0.5) * subj_factor

                # Gaze duration (GD) - includes refixations
                gd = (
                    ffd + np.random.exponential(20) if np.random.random() < 0.3 else ffd
                )

                # Total reading time (TRT) - includes regressions
                trt = gd + np.random.exponential(50) if np.random.random() < 0.2 else gd

                # Number of fixations
                nfix = 1 + np.random.poisson(0.3)

                records.append(
                    {
                        "subject_id": f"S{subj:02d}",
                        "task_id": "normal_reading",
                        "doc_id": f"doc_{sent:02d}",
                        "sent_id": sent,
                        "word_id": pos,
                        "word": word,
                        "ffd_ms": round(ffd, 1),
                        "gd_ms": round(gd, 1),
                        "trt_ms": round(trt, 1),
                        "nfix": nfix,
                        "length": len(word),
                        "logfreq": logfreq,
                        "position": pos,
                        "lang": "en",
                    }
                )

                word_id += 1

    # Create DataFrame and save
    df = pd.DataFrame(records)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "reading_times.csv"
    df.to_csv(output_path, index=False)

    logger.info(f"Created {len(df)} RT records: {output_path}")
    return df


def create_mock_zuco_eeg_data(output_dir: Path) -> None:
    """
    Create mock ZuCo EEG data following established ERP paradigms.

    References:
    - Kutas & Hillyard (1984). Brain potentials during reading reflect word expectancy
    - Hagoort et al. (2004). Integration of word meaning and world knowledge
    """
    logger.info(f"Creating mock ZuCo EEG data in {output_dir}")

    np.random.seed(42)

    n_subjects = 3
    n_sentences = 10
    words_per_sentence = 8

    records = []

    vocab = [
        ("the", 7.0),
        ("and", 6.5),
        ("of", 6.8),
        ("to", 6.2),
        ("a", 6.9),
        ("reading", 3.5),
        ("comprehension", 2.8),
        ("cognitive", 2.9),
        ("processing", 3.1),
        ("attention", 3.2),
        ("semantic", 2.7),
    ]

    for subj in range(1, n_subjects + 1):
        for sent in range(1, n_sentences + 1):
            for pos in range(1, words_per_sentence + 1):
                word, logfreq = vocab[np.random.randint(0, len(vocab))]

                # Simulate EEG power in different frequency bands
                # Based on established findings in reading research

                # Theta (4-8 Hz) - associated with working memory
                theta_base = 2.5 + np.random.normal(0, 0.3)

                # Alpha (8-12 Hz) - associated with attention
                alpha_base = 3.2 + np.random.normal(0, 0.4)

                # Beta (12-30 Hz) - associated with processing effort
                beta_base = 1.8 + np.random.normal(0, 0.2)

                # Frequency effects on EEG
                freq_effect = (4.0 - logfreq) * 0.1

                # Individual differences
                subj_factor = 1.0 + (subj - 2) * 0.05

                # Primary EEG metric (e.g., N400 amplitude)
                n400_amplitude = -2.5 + freq_effect + np.random.normal(0, 0.5)

                records.append(
                    {
                        "subject_id": f"S{subj:02d}",
                        "task_id": "normal_reading",
                        "doc_id": f"doc_{sent:02d}",
                        "sent_id": sent,
                        "word_id": pos,
                        "word": word,
                        "eeg_metric": round(n400_amplitude * subj_factor, 3),
                        "theta": round(theta_base * subj_factor, 3),
                        "alpha": round(alpha_base * subj_factor, 3),
                        "beta": round(beta_base * subj_factor, 3),
                        "onset_ms": pos * 600,  # 600ms per word
                        "offset_ms": pos * 600 + 500,
                        "length": len(word),
                        "logfreq": logfreq,
                        "position": pos,
                        "lang": "en",
                    }
                )

    # Create DataFrame and save
    df = pd.DataFrame(records)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "eeg_data.csv"
    df.to_csv(output_path, index=False)

    logger.info(f"Created {len(df)} EEG records: {output_path}")
    return df


def create_mock_swow_data(output_dir: Path, lang: str = "en") -> None:
    """
    Create mock SWOW data following established word association norms.

    References:
    - De Deyne et al. (2019). The "Small World of Words" English word association norms
    - Nelson et al. (2004). The University of South Florida free association norms
    """
    logger.info(f"Creating mock SWOW data for {lang} in {output_dir}")

    np.random.seed(42)

    # Sample word associations based on semantic networks
    associations = [
        ("cat", "dog", 0.8),
        ("dog", "cat", 0.7),
        ("car", "drive", 0.9),
        ("read", "book", 0.85),
        ("book", "read", 0.75),
        ("happy", "sad", 0.6),
        ("big", "small", 0.9),
        ("hot", "cold", 0.95),
        ("love", "hate", 0.7),
        ("memory", "remember", 0.8),
        ("attention", "focus", 0.75),
        ("cognitive", "thinking", 0.85),
        ("processing", "compute", 0.7),
        ("semantic", "meaning", 0.9),
        ("neural", "brain", 0.85),
    ]

    records = []
    for cue, response, strength in associations:
        records.append(
            {"cue": cue, "response": response, "strength": strength, "language": lang}
        )

    # Create DataFrame and save
    df = pd.DataFrame(records)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"swow_{lang}.csv"
    df.to_csv(output_path, index=False)

    logger.info(f"Created {len(df)} SWOW records for {lang}: {output_path}")
    return df


def setup_mock_datasets():
    """Setup complete mock dataset structure for testing."""
    logger.info("Setting up mock datasets for v4.4 testing")

    base_path = Path("/home/agourakis82/workspace/pcs-meta-repo")
    raw_data_path = base_path / "data" / "raw_public"

    # Create ZuCo mock data
    zuco_path = raw_data_path / "zuco"
    create_mock_zuco_rt_data(zuco_path)
    create_mock_zuco_eeg_data(zuco_path)

    # Create SWOW mock data
    swow_path = raw_data_path / "swow"
    for lang in ["en", "es", "nl", "zh"]:
        create_mock_swow_data(swow_path, lang)

    logger.info("Mock datasets created successfully!")
    logger.info("You can now run: make tidy-rt")


if __name__ == "__main__":
    setup_mock_datasets()
