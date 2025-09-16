"""
DERCo EEG Dataset Loader
========================

Loads DERCo EEG data (FIF epochs) and behavioural files,
harmonises to word_events.parquet, and validates schema.

Expected directories under data_root/raw_external/derco:
 - EEG_data/{preprocessed,raw}/<SUBJ>/article_<N>/*.fif
 - or EEG-based Reading Experiment/EEG_data/{preprocessed,raw}/...
 - Behavioural Word-Prediction Experiment/**/*.csv (optional)
 - answers/answers.csv (optional)
"""

from pathlib import Path
from typing import Dict, List, Optional
import re

import numpy as np
import pandas as pd

from config.paths import load_paths
from contracts import validate_word_events, optional_pandera_validate, check_dataset_quality


def _collect_files(raw_dir: Path) -> Dict[str, List[Path]]:
    out = {"eeg": [], "behav": []}
    # Primary
    for base in [raw_dir / "EEG_data", raw_dir / "EEG-based Reading Experiment" / "EEG_data"]:
        for sub in ["preprocessed", "raw"]:
            p = base / sub
            if p.exists():
                out["eeg"] += list(p.glob("**/*.fif"))
    # Behavioural
    if (raw_dir / "behavioural").exists():
        out["behav"] += list((raw_dir / "behavioural").glob("**/*.csv"))
    for bdir in [raw_dir / "Behavioural Word-Prediction Experiment", raw_dir / "answers"]:
        if bdir.exists():
            out["behav"] += list(bdir.glob("**/*.csv"))
    return out


def _read_epochs(file_path: Path) -> pd.DataFrame:
    try:
        import mne
        epochs = mne.read_epochs(str(file_path), preload=True, verbose=False)
        meta = epochs.metadata.copy() if epochs.metadata is not None else pd.DataFrame(index=range(len(epochs)))
        # Infer subject/article from path
        subj = None; art = None
        m = re.search(r"EEG_data/(?:preprocessed|raw)/([^/]+)/([^/]+)/", str(file_path))
        if m:
            subj, art = m.group(1), m.group(2)
        else:
            try:
                art = file_path.parent.name; subj = file_path.parent.parent.name
            except Exception:
                pass
        if subj is not None:
            meta["subject_id"] = subj
        if art is not None and "doc_id" not in meta.columns:
            meta["doc_id"] = art
        data = epochs.get_data()
        meta["eeg_metric"] = data.mean(axis=(1, 2))
        meta["theta"] = data[:, :, : max(1, data.shape[2] // 10)].mean(axis=(1, 2))
        meta["alpha"] = data[:, :, data.shape[2] // 10 : data.shape[2] // 5].mean(axis=(1, 2))
        meta["beta"] = data[:, :, data.shape[2] // 5 : data.shape[2] // 3].mean(axis=(1, 2))
        return meta
    except Exception as e:
        print(f"⚠ Failed to read epochs {file_path.name}: {e}")
        return pd.DataFrame()


def _harmonize(eeg_df: pd.DataFrame, beh_df: Optional[pd.DataFrame], fname: str) -> pd.DataFrame:
    if eeg_df is None or eeg_df.empty:
        base = beh_df.copy() if beh_df is not None else pd.DataFrame()
    else:
        base = eeg_df.copy()
    if base.empty:
        return pd.DataFrame()
    # Column remap
    colmap = {
        "participant_id": "subject_id",
        "SubjID": "subject_id",
        "article_id": "doc_id",
        "sent_id": "sent_id",
        "sentence_id": "sent_id",
        "word_id": "word_id",
        "word": "word",
        "token": "word",
        "cloze": "cloze_prob",
        "cloze_prob": "cloze_prob",
    }
    for k, v in colmap.items():
        if k in base.columns:
            base = base.rename(columns={k: v})
    # Build output
    cols = [
        "subject_id", "doc_id", "sent_id", "word_id", "word", "lang",
        "eeg_metric", "theta", "alpha", "beta", "onset_ms", "offset_ms",
        "cloze_prob", "length", "logfreq", "position",
    ]
    out = pd.DataFrame()
    for c in cols:
        if c in base.columns:
            out[c] = base[c]
        else:
            if c == "lang":
                out[c] = "en"
            elif c == "doc_id":
                out[c] = fname
            else:
                out[c] = pd.NA
    # Clean
    if "word" in out.columns and out["word"].notna().any():
        out = out[out["word"].notna()]
        out["word"] = out["word"].astype(str)
    # Types
    for c in ["eeg_metric","theta","alpha","beta","onset_ms","offset_ms","cloze_prob"]:
        if c in out.columns:
            out[c] = pd.to_numeric(out[c], errors="coerce")
    for c in ["length","sent_id","word_id"]:
        if c in out.columns:
            out[c] = pd.to_numeric(out[c], errors="coerce").astype("Int64")
    out["task_id"] = "derco_reading"
    return out


def run(config: Optional[Dict] = None) -> Path:
    print("🔄 Loading DERCo EEG data...")
    if config is None:
        _, datasets = load_paths()
        config = datasets["derco_eeg"]
    raw_dir = Path(config["raw_dir"]).expanduser()
    proc_dir = Path(config["processed_dir"]).expanduser()
    proc_dir.mkdir(parents=True, exist_ok=True)
    if not raw_dir.exists():
        raise FileNotFoundError(f"DERCo raw dir not found: {raw_dir}")
    files = _collect_files(raw_dir)
    print(f"📁 EEG files: {len(files['eeg'])}; behavioural: {len(files['behav'])}")

    all_parts: List[pd.DataFrame] = []
    # Process up to a reasonable number first; you can raise this as needed
    for eeg in files["eeg"][:20]:
        df_eeg = _read_epochs(eeg)
        if df_eeg.empty:
            continue
        # naive match to a behav file by article id substring
        beh = None
        stem = eeg.stem
        for b in files["behav"]:
            if any(tok in b.name for tok in [stem, stem.split("_")[0]]):
                try:
                    beh = pd.read_csv(b)
                    break
                except Exception:
                    pass
        h = _harmonize(df_eeg, beh, eeg.stem)
        if not h.empty:
            all_parts.append(h)
            print(f"✓ Harmonised {len(h)} rows from {eeg.name}")

    if not all_parts:
        raise RuntimeError("DERCo strict mode: no usable EEG/behavioural data found")

    df = pd.concat(all_parts, ignore_index=True)
    print(f"🔍 Validating {len(df)} total words/epochs…")
    # Drop missing essentials
    if {"word","subject_id"}.issubset(df.columns):
        df = df.dropna(subset=["word","subject_id"])
    validate_word_events(df, "DERCo")
    optional_pandera_validate(df, "word")
    if len(df) >= 1000:
        check_dataset_quality(df, "DERCo", min_rows=1000)
    out = proc_dir / "word_events_eeg.parquet"
    df.to_parquet(out, index=False, compression="snappy")
    print(f"💾 Saved DERCo word events (EEG) to {out}")
    print(f"📊 Final dataset: {len(df):,} rows; subjects: {df['subject_id'].nunique() if 'subject_id' in df.columns else 'NA'}")
    return out


if __name__ == "__main__":
    run()
