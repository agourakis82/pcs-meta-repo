#!/usr/bin/env python3
"""
Simplified v4.4 pipeline execution with direct path resolution
Research-grade pipeline with proper error handling
"""

import argparse
import logging
from pathlib import Path

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_test_data():
    """Create test data directly"""
    logger.info("Creating test data for pipeline validation")

    repo_path = Path("/home/agourakis82/workspace/pcs-meta-repo")

    # Create directory structure
    dirs = [
        "data/raw_public/zuco",
        "data/raw_public/swow",
        "data/L1_tidy/zuco_rt",
        "data/L1_tidy/zuco_eeg",
        "data/L2_derived/kec/en",
        "data/processed/v4.4/integration",
    ]

    for dir_path in dirs:
        (repo_path / dir_path).mkdir(parents=True, exist_ok=True)

    # Create mock ZuCo RT data
    rt_data = []
    for i in range(100):
        rt_data.append(
            {
                "subject_id": f"S{(i//20)+1:02d}",
                "task_id": "reading",
                "doc_id": f"doc_{(i//10)+1:02d}",
                "sent_id": (i // 10) + 1,
                "word_id": (i % 10) + 1,
                "word": [
                    "the",
                    "cat",
                    "sat",
                    "on",
                    "mat",
                    "and",
                    "dog",
                    "ran",
                    "fast",
                    "home",
                ][i % 10],
                "ffd_ms": 200 + np.random.normal(0, 50),
                "gd_ms": 250 + np.random.normal(0, 75),
                "trt_ms": 300 + np.random.normal(0, 100),
                "nfix": 1 + np.random.poisson(0.3),
                "length": len(
                    [
                        "the",
                        "cat",
                        "sat",
                        "on",
                        "mat",
                        "and",
                        "dog",
                        "ran",
                        "fast",
                        "home",
                    ][i % 10]
                ),
                "logfreq": 5.0 + np.random.normal(0, 1),
                "position": (i % 10) + 1,
                "lang": "en",
            }
        )

    rt_df = pd.DataFrame(rt_data)
    rt_output = repo_path / "data/raw_public/zuco/reading_times.csv"
    rt_df.to_csv(rt_output, index=False)
    logger.info(f"Created RT data: {rt_output}")

    # Create mock EEG data
    eeg_data = []
    for i in range(100):
        eeg_data.append(
            {
                "subject_id": f"S{(i//20)+1:02d}",
                "task_id": "reading",
                "doc_id": f"doc_{(i//10)+1:02d}",
                "sent_id": (i // 10) + 1,
                "word_id": (i % 10) + 1,
                "word": [
                    "the",
                    "cat",
                    "sat",
                    "on",
                    "mat",
                    "and",
                    "dog",
                    "ran",
                    "fast",
                    "home",
                ][i % 10],
                "eeg_metric": -2.5 + np.random.normal(0, 0.5),
                "theta": 2.5 + np.random.normal(0, 0.3),
                "alpha": 3.2 + np.random.normal(0, 0.4),
                "beta": 1.8 + np.random.normal(0, 0.2),
                "onset_ms": ((i % 10) + 1) * 600,
                "offset_ms": ((i % 10) + 1) * 600 + 500,
                "length": len(
                    [
                        "the",
                        "cat",
                        "sat",
                        "on",
                        "mat",
                        "and",
                        "dog",
                        "ran",
                        "fast",
                        "home",
                    ][i % 10]
                ),
                "logfreq": 5.0 + np.random.normal(0, 1),
                "position": (i % 10) + 1,
                "lang": "en",
            }
        )

    eeg_df = pd.DataFrame(eeg_data)
    eeg_output = repo_path / "data/raw_public/zuco/eeg_data.csv"
    eeg_df.to_csv(eeg_output, index=False)
    logger.info(f"Created EEG data: {eeg_output}")

    return True


def process_rt_data():
    """Process RT data to L1 tidy format"""
    logger.info("Processing RT data")

    repo_path = Path("/home/agourakis82/workspace/pcs-meta-repo")
    input_file = repo_path / "data/raw_public/zuco/reading_times.csv"
    output_file = repo_path / "data/L1_tidy/zuco_rt/word_events_rt.parquet"

    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        return False

    try:
        # Load and process data
        df = pd.read_csv(input_file)

        # Ensure output directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Save as parquet
        df.to_parquet(output_file, index=False)

        logger.info(f"Processed {len(df)} RT records -> {output_file}")
        return True

    except Exception as e:
        logger.error(f"RT processing failed: {e}")
        return False


def process_eeg_data():
    """Process EEG data to L1 tidy format"""
    logger.info("Processing EEG data")

    repo_path = Path("/home/agourakis82/workspace/pcs-meta-repo")
    input_file = repo_path / "data/raw_public/zuco/eeg_data.csv"
    output_file = repo_path / "data/L1_tidy/zuco_eeg/word_events_eeg.parquet"

    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        return False

    try:
        # Load and process data
        df = pd.read_csv(input_file)

        # Ensure output directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Save as parquet
        df.to_parquet(output_file, index=False)

        logger.info(f"Processed {len(df)} EEG records -> {output_file}")
        return True

    except Exception as e:
        logger.error(f"EEG processing failed: {e}")
        return False


def create_mock_kec():
    """Create mock KEC data for testing integration"""
    logger.info("Creating mock KEC data")

    repo_path = Path("/home/agourakis82/workspace/pcs-meta-repo")

    # Create KEC for common words
    words = ["the", "cat", "sat", "on", "mat", "and", "dog", "ran", "fast", "home"]

    kec_data = []
    for word in words:
        kec_data.append(
            {
                "word": word,
                "entropy": 2.5 + np.random.normal(0, 0.5),
                "curvature": 1.8 + np.random.normal(0, 0.3),
                "coherence": 0.7 + np.random.normal(0, 0.1),
                "components": 5 + np.random.poisson(2),
            }
        )

    kec_df = pd.DataFrame(kec_data)

    # Save KEC files
    kec_dir = repo_path / "data/L2_derived/kec/en"
    kec_dir.mkdir(parents=True, exist_ok=True)

    kec_df[["word", "entropy"]].to_parquet(kec_dir / "entropy.parquet", index=False)
    kec_df[["word", "curvature"]].to_parquet(kec_dir / "curvature.parquet", index=False)
    kec_df[["word", "coherence"]].to_parquet(kec_dir / "coherence.parquet", index=False)
    kec_df[["word", "components"]].to_parquet(
        kec_dir / "components.parquet", index=False
    )

    logger.info(f"Created KEC data for {len(kec_df)} words")
    return True


def integrate_data():
    """Integrate RT/EEG with KEC data"""
    logger.info("Integrating RT/EEG with KEC data")

    repo_path = Path("/home/agourakis82/workspace/pcs-meta-repo")

    try:
        # Load RT data
        rt_file = repo_path / "data/L1_tidy/zuco_rt/word_events_rt.parquet"
        if rt_file.exists():
            rt_df = pd.read_parquet(rt_file)

            # Load KEC data
            kec_file = repo_path / "data/L2_derived/kec/en/entropy.parquet"
            if kec_file.exists():
                kec_df = pd.read_parquet(kec_file)

                # Merge RT with KEC
                rt_kec = rt_df.merge(kec_df, on="word", how="left")

                # Save integrated data
                output_dir = repo_path / "data/processed/v4.4/integration"
                output_dir.mkdir(parents=True, exist_ok=True)

                rt_kec.to_parquet(output_dir / "zuco_kec_rt.parquet", index=False)
                logger.info(f"Created RT-KEC integration: {len(rt_kec)} records")

        # Load EEG data
        eeg_file = repo_path / "data/L1_tidy/zuco_eeg/word_events_eeg.parquet"
        if eeg_file.exists():
            eeg_df = pd.read_parquet(eeg_file)

            # Load KEC data
            kec_file = repo_path / "data/L2_derived/kec/en/entropy.parquet"
            if kec_file.exists():
                kec_df = pd.read_parquet(kec_file)

                # Merge EEG with KEC
                eeg_kec = eeg_df.merge(kec_df, on="word", how="left")

                # Save integrated data
                output_dir = repo_path / "data/processed/v4.4/integration"
                eeg_kec.to_parquet(output_dir / "zuco_kec_eeg.parquet", index=False)
                logger.info(f"Created EEG-KEC integration: {len(eeg_kec)} records")

        return True

    except Exception as e:
        logger.error(f"Integration failed: {e}")
        return False


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(description="Simple v4.4 pipeline")
    parser.add_argument(
        "--step",
        choices=["all", "data", "tidy-rt", "tidy-eeg", "kec", "integrate"],
        default="all",
    )

    args = parser.parse_args()

    logger.info("🧠 PCS-Meta-Repo v4.4 - Simplified Pipeline")
    logger.info("=" * 50)

    success = True

    if args.step in ["all", "data"]:
        logger.info("Step 1: Creating test data")
        success &= create_test_data()

    if args.step in ["all", "tidy-rt"]:
        logger.info("Step 2: Processing RT data")
        success &= process_rt_data()

    if args.step in ["all", "tidy-eeg"]:
        logger.info("Step 3: Processing EEG data")
        success &= process_eeg_data()

    if args.step in ["all", "kec"]:
        logger.info("Step 4: Creating KEC data")
        success &= create_mock_kec()

    if args.step in ["all", "integrate"]:
        logger.info("Step 5: Integrating data")
        success &= integrate_data()

    if success:
        logger.info("🎉 Pipeline completed successfully!")

        # Show outputs
        repo_path = Path("/home/agourakis82/workspace/pcs-meta-repo")
        outputs = [
            "data/L1_tidy/zuco_rt/word_events_rt.parquet",
            "data/L1_tidy/zuco_eeg/word_events_eeg.parquet",
            "data/L2_derived/kec/en/entropy.parquet",
            "data/processed/v4.4/integration/zuco_kec_rt.parquet",
            "data/processed/v4.4/integration/zuco_kec_eeg.parquet",
        ]

        logger.info("\n📊 Created outputs:")
        for output in outputs:
            file_path = repo_path / output
            if file_path.exists():
                size = file_path.stat().st_size
                logger.info(f"  ✅ {output} ({size} bytes)")
            else:
                logger.info(f"  ❌ {output}")

    else:
        logger.error("❌ Pipeline failed")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
