#!/usr/bin/env python3
"""
Integrate KEC with modality‑specific datasets (v4.4)

Produces separate integrated artifacts:
- EEG: data/processed/v4.4/integration/<dataset>_kec_eeg.parquet
- RT:  data/processed/v4.4/integration/<dataset>_kec_rt.parquet

Joins are done on normalized word form (lower + [A-Za-z0-9_]).
Requires real KEC in FASTDATA (L2_derived/kec/<lang>/) and real tidy L1 files.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from config.paths import load_paths


def normalize_word(word: str) -> str:
    if pd.isna(word) or word == "":
        return ""
    return re.sub(r"[^\w]", "", str(word).lower())


def compose_kec_table(lang: str = "en") -> pd.DataFrame:
    dr, _ = load_paths()
    l2 = Path(dr["layout"]["L2_derived"].format(data_root=dr["data_root"]))
    base = l2 / "kec" / lang
    parts: Dict[str, Path] = {
        "entropy": base / "entropy.parquet",
        "curvature": base / "curvature.parquet",
        "coherence": base / "coherence.parquet",
    }
    missing = [k for k, p in parts.items() if not p.exists()]
    if missing:
        raise FileNotFoundError(f"Missing KEC parts for {lang}: {missing} under {base}")
    df = pd.read_parquet(parts["entropy"]).rename(columns={"name": "word"})
    for k in ("curvature", "coherence"):
        d = pd.read_parquet(parts[k]).rename(columns={"name": "word"})
        df = df.merge(d, on="word", how="outer")
    df["word_norm"] = df["word"].apply(normalize_word)
    # Drop duplicates on word_norm keeping first
    df = df.drop_duplicates(subset=["word_norm"])  # conservative
    return df[["word_norm", "entropy", "curvature", "coherence"]]


def integrate_eeg(ds_name: str, lang: str = "en") -> Optional[Path]:
    dr, ds = load_paths()
    conf = ds.get(ds_name, {})
    proc_dir = Path(conf.get("processed_dir", "")).expanduser()
    in_file = proc_dir / "word_events_eeg.parquet"
    if not in_file.exists():
        return None
    out_dir = Path("data/processed/v4.4/integration")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{ds_name.split('_')[0]}_kec_eeg.parquet"

    df = pd.read_parquet(in_file)
    if "word_norm" not in df.columns:
        if "word" not in df.columns:
            raise ValueError(f"{ds_name}: missing 'word' column in {in_file}")
        df["word_norm"] = df["word"].apply(normalize_word)
    kec = compose_kec_table(lang)
    merged = df.merge(kec, on="word_norm", how="left")
    merged.to_parquet(out_file, index=False, compression="snappy")
    return out_file


def integrate_rt(ds_name: str, lang: str = "en") -> Optional[Path]:
    # Expect tidy path structure L1_tidy/<ds>_rt/word_events_rt.parquet or datasets.yaml processed_dir
    dr, ds = load_paths()
    conf = ds.get(ds_name, {})
    proc_dir = Path(conf.get("processed_dir", "")).expanduser()
    # Try common tidy name first
    in_file = proc_dir / "word_events_rt.parquet"
    if not in_file.exists():
        # Legacy fallback
        in_file = Path(f"data/L1_tidy/{ds_name}/word_events_rt.parquet")
    if not in_file.exists():
        return None
    out_dir = Path("data/processed/v4.4/integration")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{ds_name.split('_')[0]}_kec_rt.parquet"

    df = pd.read_parquet(in_file)
    if "word_norm" not in df.columns:
        if "word" not in df.columns:
            raise ValueError(f"{ds_name}: missing 'word' column in {in_file}")
        df["word_norm"] = df["word"].apply(normalize_word)
    kec = compose_kec_table(lang)
    merged = df.merge(kec, on="word_norm", how="left")
    merged.to_parquet(out_file, index=False, compression="snappy")
    return out_file


def run(lang: str = "en") -> Dict[str, Optional[Path]]:
    results: Dict[str, Optional[Path]] = {}
    # EEG datasets we know about
    for ds_name in ("derco_eeg", "lpp_eeg", "zuco_eeg"):
        try:
            p = integrate_eeg(ds_name, lang)
            if p:
                print(f"[integrate] EEG OK: {ds_name} -> {p}")
            results[f"{ds_name}_eeg"] = p
        except Exception as e:
            print(f"[integrate] EEG FAIL {ds_name}: {e}")
            results[f"{ds_name}_eeg"] = None
    # RT datasets
    for ds_name in ("zuco_rt", "geco_et", "onestop_et"):
        try:
            p = integrate_rt(ds_name, lang)
            if p:
                print(f"[integrate] RT OK: {ds_name} -> {p}")
            results[f"{ds_name}_rt"] = p
        except Exception as e:
            print(f"[integrate] RT FAIL {ds_name}: {e}")
            results[f"{ds_name}_rt"] = None
    return results


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Integrate KEC with EEG/RT (v4.4)")
    ap.add_argument("--lang", default="en")
    args = ap.parse_args()
    run(args.lang)


if __name__ == "__main__":
    main()

