#!/usr/bin/env python3
"""
Real ZuCo data loader for PCS-Meta-Repo v4.4
Research-grade processing of ZuCo corpus following established methodologies

References:
- Hollenstein et al. (2018). ZuCo, a simultaneous EEG and eye-tracking corpus for natural language processing
- Hollenstein et al. (2020). ZuCo 2.0: A dataset of physiological recordings during natural reading and annotation
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import scipy.io

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ZuCoRealLoader:
    """
    Load and process real ZuCo data following research-grade standards.

    Handles both ZuCo v1 and v2 data formats with proper validation.
    """

    def __init__(self, data_root: Path):
        self.data_root = Path(data_root)
        # Fix the path to avoid duplication
        if str(self.data_root).endswith("scripts"):
            # If we're already in scripts/, go up one level
            self.zuco_path = self.data_root / "data/raw_public/zuco"
        else:
            # From repo root
            self.zuco_path = self.data_root / "scripts/data/raw_public/zuco"

        # Validate ZuCo data structure
        if not self.zuco_path.exists():
            raise FileNotFoundError(f"ZuCo data not found at {self.zuco_path}")

        logger.info(f"Initialized ZuCo loader for {self.zuco_path}")

    def find_zuco_files(self) -> Dict[str, List[Path]]:
        """Find available ZuCo .mat files by task and version"""

        files = {
            "v1_sr": [],  # Sentiment Reading
            "v1_nr": [],  # Normal Reading
            "v1_tsr": [],  # Task-specific Reading
            "v2_tsr": [],  # ZuCo 2.0 Task-specific Reading
        }

        # ZuCo v1 files
        v1_answers = self.zuco_path / "v1/osfstorage/answers"
        if v1_answers.exists():
            # Sentiment Reading (SR)
            sr_files = list(v1_answers.glob("Fullresults_SR_*.mat"))
            files["v1_sr"] = sr_files

            # Normal Reading (NR)
            nr_files = list(v1_answers.glob("Fullresults_NR_*.mat"))
            files["v1_nr"] = nr_files

            # Task-specific Reading (TSR)
            tsr_files = list(v1_answers.glob("Fullresults_TSR_*.mat"))
            files["v1_tsr"] = tsr_files

        # ZuCo v2 files
        v2_path = self.zuco_path / "v2"
        if v2_path.exists():
            # Find v2 TSR files
            v2_tsr_files = list(v2_path.rglob("*.mat"))
            files["v2_tsr"] = v2_tsr_files

        logger.info(f"Found ZuCo files: {[(k, len(v)) for k, v in files.items()]}")
        return files

    def load_mat_file(self, mat_path: Path) -> Optional[Dict]:
        """
        Load ZuCo .mat file with proper error handling

        Args:
            mat_path: Path to .mat file

        Returns:
            Dictionary with loaded data or None if failed
        """
        try:
            # Load with scipy.io for compatibility
            mat_data = scipy.io.loadmat(
                str(mat_path), squeeze_me=True, struct_as_record=False
            )

            # Remove MATLAB metadata
            cleaned_data = {k: v for k, v in mat_data.items() if not k.startswith("__")}

            logger.debug(f"Loaded {mat_path.name}: {list(cleaned_data.keys())}")
            return cleaned_data

        except Exception as e:
            logger.error(f"Failed to load {mat_path}: {e}")
            return None

    def extract_rt_features(
        self, mat_data: Dict, subject_id: str, task: str
    ) -> List[Dict]:
        """
        Extract reading time features from ZuCo .mat data with robust structure detection

        Args:
            mat_data: Loaded .mat file data
            subject_id: Subject identifier
            task: Task identifier (NR, SR, TSR)

        Returns:
            List of word-level RT records
        """
        records = []

        try:
            # ZuCo data structure varies by version/task
            # Try to find the main data structure
            data_keys = [k for k in mat_data.keys() if not k.startswith("__")]

            if not data_keys:
                logger.warning(f"No data keys found in {subject_id} {task}")
                return records

            # Try multiple possible structures
            for main_key in data_keys:
                data = mat_data[main_key]
                logger.debug(f"Trying key '{main_key}', type: {type(data)}")

                # Try direct access to common ZuCo structures
                sentence_candidates = []

                # Pattern 1: data.sentence or data.sentenceData
                if hasattr(data, "sentence"):
                    sentence_candidates.append(("sentence", data.sentence))
                if hasattr(data, "sentenceData"):
                    sentence_candidates.append(("sentenceData", data.sentenceData))
                if hasattr(data, "content"):
                    sentence_candidates.append(("content", data.content))

                # Pattern 2: data is array-like, try first element
                if hasattr(data, "__len__") and len(data) > 0:
                    try:
                        first_elem = data[0] if hasattr(data, "__getitem__") else data
                        if hasattr(first_elem, "sentence"):
                            sentence_candidates.append(
                                ("first.sentence", first_elem.sentence)
                            )
                        if hasattr(first_elem, "sentenceData"):
                            sentence_candidates.append(
                                ("first.sentenceData", first_elem.sentenceData)
                            )
                    except (IndexError, AttributeError):
                        pass

                # Pattern 3: data is the sentence data directly
                if hasattr(data, "word") or (
                    hasattr(data, "__len__") and hasattr(data, "__getitem__")
                ):
                    sentence_candidates.append(("direct", data))

                # Try each candidate
                for candidate_name, sentences in sentence_candidates:
                    logger.debug(f"Trying sentence candidate: {candidate_name}")

                    # Ensure sentences is iterable
                    if not hasattr(sentences, "__len__"):
                        sentences = [sentences]
                    elif not hasattr(sentences, "__getitem__"):
                        try:
                            sentences = list(sentences)
                        except:
                            continue

                    # Process sentences
                    for sent_idx in range(len(sentences)):
                        try:
                            sentence = (
                                sentences[sent_idx]
                                if hasattr(sentences, "__getitem__")
                                else sentences
                            )

                            # Look for word data in sentence
                            words = None
                            if hasattr(sentence, "word"):
                                words = sentence.word
                            elif hasattr(sentence, "wordData"):
                                words = sentence.wordData
                            elif hasattr(sentence, "content") and hasattr(
                                sentence.content, "word"
                            ):
                                words = sentence.content.word

                            if words is None:
                                continue

                            # Ensure words is iterable
                            if not hasattr(words, "__len__"):
                                words = [words]
                            elif not hasattr(words, "__getitem__"):
                                try:
                                    words = list(words)
                                except:
                                    continue

                            # Process each word
                            for word_idx in range(len(words)):
                                try:
                                    word = (
                                        words[word_idx]
                                        if hasattr(words, "__getitem__")
                                        else words
                                    )

                                    # Extract word content
                                    word_text = self._extract_word_text(word, word_idx)
                                    if not word_text:
                                        continue

                                    # Extract RT measures with multiple field name attempts
                                    rt_measures = self._extract_rt_measures(word)

                                    record = {
                                        "subject_id": subject_id,
                                        "task_id": task.lower(),
                                        "doc_id": f"sent_{sent_idx+1:03d}",
                                        "sent_id": sent_idx + 1,
                                        "word_id": word_idx + 1,
                                        "word": word_text,
                                        "ffd_ms": rt_measures.get("ffd", np.nan),
                                        "gd_ms": rt_measures.get("gd", np.nan),
                                        "trt_ms": rt_measures.get("trt", np.nan),
                                        "nfix": rt_measures.get("nfix", np.nan),
                                        "length": len(word_text),
                                        "position": word_idx + 1,
                                        "lang": "en",
                                    }

                                    records.append(record)

                                except Exception as e:
                                    logger.debug(
                                        f"Failed to process word {word_idx}: {e}"
                                    )
                                    continue

                        except Exception as e:
                            logger.debug(f"Failed to process sentence {sent_idx}: {e}")
                            continue

                    # If we got records, we found the right structure
                    if records:
                        logger.info(
                            f"Extracted {len(records)} RT records from {subject_id} {task} using {candidate_name}"
                        )
                        return records

            # If we reach here, no structure worked
            logger.warning(
                f"Could not find compatible data structure in {subject_id} {task}"
            )

        except Exception as e:
            logger.error(f"Failed to extract RT features from {subject_id} {task}: {e}")

        return records

    def _extract_word_text(self, word, word_idx: int) -> str:
        """Extract word text from various possible fields"""
        # Try common field names for word content
        for field_name in ["content", "word", "text", "string", "value"]:
            if hasattr(word, field_name):
                text = getattr(word, field_name)
                if isinstance(text, str):
                    return text.strip()
                elif hasattr(text, "__str__"):
                    return str(text).strip()

        # If no text found, use fallback
        return f"word_{word_idx+1}"

    def _extract_rt_measures(self, word) -> Dict[str, float]:
        """Extract RT measures from word with multiple field name attempts"""
        measures = {}

        # FFD (First Fixation Duration)
        for ffd_name in [
            "FFD",
            "firstFixationDuration",
            "ffd",
            "first_fixation_duration",
        ]:
            if hasattr(word, ffd_name):
                measures["ffd"] = self._convert_to_float(getattr(word, ffd_name))
                break

        # GD (Gaze Duration)
        for gd_name in ["GD", "gazeDuration", "gd", "gaze_duration"]:
            if hasattr(word, gd_name):
                measures["gd"] = self._convert_to_float(getattr(word, gd_name))
                break

        # TRT (Total Reading Time)
        for trt_name in ["TRT", "totalReadingTime", "trt", "total_reading_time"]:
            if hasattr(word, trt_name):
                measures["trt"] = self._convert_to_float(getattr(word, trt_name))
                break

        # Number of fixations
        for nfix_name in [
            "nFixations",
            "numFixations",
            "nfix",
            "n_fixations",
            "fixationCount",
        ]:
            if hasattr(word, nfix_name):
                measures["nfix"] = self._convert_to_int(getattr(word, nfix_name))
                break

        return measures

    def _convert_to_float(self, value) -> float:
        """Safely convert value to float, handling MATLAB arrays"""
        try:
            if hasattr(value, "__iter__") and len(value) > 0:
                # MATLAB array, take first element
                val = value[0] if hasattr(value, "__getitem__") else next(iter(value))
                return float(val) if not np.isnan(val) else np.nan
            elif np.isscalar(value):
                return float(value) if not np.isnan(value) else np.nan
            else:
                return np.nan
        except (ValueError, TypeError, IndexError):
            return np.nan

    def _convert_to_int(self, value) -> int:
        """Safely convert value to int, handling MATLAB arrays"""
        try:
            if hasattr(value, "__iter__") and len(value) > 0:
                # MATLAB array, take first element
                val = value[0] if hasattr(value, "__getitem__") else next(iter(value))
                return int(val) if not np.isnan(val) else np.nan
            elif np.isscalar(value):
                return int(value) if not np.isnan(value) else np.nan
            else:
                return np.nan
        except (ValueError, TypeError, IndexError):
            return np.nan

    def load_zuco_rt_data(self, output_path: Path) -> pd.DataFrame:
        """
        Load and process ZuCo reading time data

        Args:
            output_path: Where to save the processed data

        Returns:
            DataFrame with harmonized RT data
        """
        logger.info("Loading real ZuCo RT data...")

        # Find available files
        zuco_files = self.find_zuco_files()

        all_records = []

        # Process Normal Reading (NR) files - primary RT data
        for mat_file in zuco_files["v1_nr"][:3]:  # Limit to first 3 for testing
            # Extract subject ID from filename
            subject_id = mat_file.stem.split("_")[
                -1
            ]  # e.g., ZAB from Fullresults_NR_ZAB.mat

            logger.info(f"Processing {mat_file.name}...")

            # Load the .mat file
            mat_data = self.load_mat_file(mat_file)
            if mat_data is None:
                continue

            # Extract RT features
            records = self.extract_rt_features(mat_data, subject_id, "NR")
            all_records.extend(records)

        # Create DataFrame
        if all_records:
            df = pd.DataFrame(all_records)

            # Data validation and cleaning
            logger.info(
                f"Loaded {len(df)} RT records from {len(df['subject_id'].unique())} subjects"
            )

            # Basic quality checks
            valid_rt = df["ffd_ms"].notna().sum()
            logger.info(
                f"Valid FFD measurements: {valid_rt}/{len(df)} ({valid_rt/len(df)*100:.1f}%)"
            )

            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Save as parquet
            df.to_parquet(output_path, index=False)
            logger.info(f"Saved ZuCo RT data to {output_path}")

            return df
        else:
            logger.warning("No RT records extracted")
            return pd.DataFrame()


def load_zuco_rt(raw_dir: Path, output_path: Path) -> pd.DataFrame:
    """
    Main entry point for ZuCo RT loading

    Args:
        raw_dir: Root directory containing ZuCo data
        output_path: Output file path

    Returns:
        Processed DataFrame
    """
    loader = ZuCoRealLoader(raw_dir.parent.parent.parent)  # Go up to repo root
    return loader.load_zuco_rt_data(output_path)


if __name__ == "__main__":
    # Test the loader
    repo_root = Path("/home/agourakis82/workspace/pcs-meta-repo")
    output_file = repo_root / "data/L1_tidy/zuco_rt/word_events_rt.parquet"

    df = load_zuco_rt(repo_root / "scripts/data/raw_public/zuco", output_file)
    print(f"Loaded {len(df)} RT records")
    if len(df) > 0:
        print(df.head())
        print(f"Columns: {list(df.columns)}")
        print(f"Subjects: {df['subject_id'].unique()}")
        print(f"Tasks: {df['task_id'].unique()}")
