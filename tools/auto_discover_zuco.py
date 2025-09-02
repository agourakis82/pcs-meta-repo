#!/usr/bin/env python3
"""
auto_discover_zuco.py — v4.3
Harmonize ZuCo v1/v2 exports into data/processed/zuco_aligned.csv with canonical columns and token_norm.
Also writes reports/zuco_loader_qa.json.
"""
from __future__ import annotations
import json, sys, warnings, re
from pathlib import Path
from typing import Dict, List
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
RPTS = ROOT / "reports"
PROC.mkdir(parents=True, exist_ok=True)
RPTS.mkdir(parents=True, exist_ok=True)

# Reuse local token normalization
sys.path.insert(0, str((ROOT/"tools").resolve()))
from token_norm import token_norm

CANDIDATES = [
    PROC / "zuco_aligned.csv",
    PROC / "zuco_word_level_all_subjects.csv",
    PROC / "zuco_word_level_ZKW.csv",
    PROC / "zuco_v1_aligned.csv",
]

# Column mapping to canonical
MAPS = {
    # tokens
    "Word": "Word",
    "word": "Word",
    "token": "Word",
    # subject
    "Subject": "Subject",
    "subject": "Subject",
    # sentence id
    "SentenceID": "SentenceID",
    "sentence_id": "SentenceID",
    "Sentence_ID": "SentenceID",
    # dataset/task
    "Dataset": "Dataset",
    "dataset": "Dataset",
    "Task": "Task",
    "task": "Task",
    # reading metrics
    "FirstFixationDuration": "FFD",
    "first_fix_dur": "FFD",
    "FFD": "FFD",
    "GazeDuration": "GD",
    "gaze_duration": "GD",
    "GD": "GD",
    "TotalReadingTime": "TRT",
    "total_reading_time": "TRT",
    "TRT": "TRT",
    "GoPastTime": "GPT",
    "go_past_time": "GPT",
    "GPT": "GPT",
    # freq/length (if present)
    "LogFreq": "log_freq",
    "log_freq": "log_freq",
    "Zipf": "log_freq",
    "length": "length",
    "Length": "length",
}

KEEP_ORDER = [
    "Subject","Dataset","Task","SentenceID","Word",
    "FFD","GD","TRT","GPT",
    "ThetaPower","AlphaPower","BetaPower","GammaPower",
    "length","log_freq","token_norm"
]

def load_first_existing(paths: List[Path]) -> pd.DataFrame:
    for p in paths:
        if p.exists():
            try:
                df = pd.read_csv(p)
                print(f"[info] Loaded: {p} -> {df.shape}")
                return df
            except Exception as e:
                warnings.warn(f"Failed to read {p}: {e}")
    return pd.DataFrame()


def harmonize(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    # strip col names
    df.columns = [c.strip() for c in df.columns]
    # rename known columns
    rename = {c: MAPS[c] for c in df.columns if c in MAPS}
    df = df.rename(columns=rename)
    # build token_norm
    if "token_norm" not in df.columns:
        if "Word" in df.columns:
            df["token_norm"] = df["Word"].astype(str).map(token_norm)
        else:
            # try any candidate token column
            for c in ("token","word"):
                if c in df.columns:
                    df["token_norm"] = df[c].astype(str).map(token_norm)
                    break
    # coerce types
    for cat in ("Subject","Dataset","Task","SentenceID"):
        if cat in df.columns:
            df[cat] = df[cat].astype(str)
    # ensure floats
    for m in ("FFD","GD","TRT","GPT","ThetaPower","AlphaPower","BetaPower","GammaPower"):
        if m in df.columns:
            df[m] = pd.to_numeric(df[m], errors="coerce")
    # prefer canonical column order
    cols = [c for c in KEEP_ORDER if c in df.columns]
    # append any extras
    extras = [c for c in df.columns if c not in cols]
    return df[cols + extras]


def main() -> int:
    df = load_first_existing(CANDIDATES)
    if df.empty:
        print("[warn] No ZuCo candidate files found. Nothing to do.")
        return 0
    out = harmonize(df)
    out_path = PROC / "zuco_aligned.csv"
    out.to_csv(out_path, index=False)
    print(f"[ok] Wrote: {out_path} ({len(out)} rows, {len(out.columns)} cols)")
    # QA
    qa = {
        "rows": int(len(out)),
        "cols": list(out.columns),
        "has_et": [c for c in ("FFD","GD","TRT","GPT") if c in out.columns],
        "has_eeg": [c for c in ("ThetaPower","AlphaPower","BetaPower","GammaPower") if c in out.columns],
        "token_norm_coverage": int(out["token_norm"].notna().sum()) if "token_norm" in out.columns else 0,
    }
    (RPTS/"zuco_loader_qa.json").write_text(json.dumps(qa, indent=2))
    print(f"[ok] Wrote QA: {RPTS/'zuco_loader_qa.json'}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
