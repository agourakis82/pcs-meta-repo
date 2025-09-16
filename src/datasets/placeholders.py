"""Real-mode lightweight dataset loaders.

These functions prioritize existing real L1_tidy artifacts when present, and
fall back to minimal raw parsing where feasible. No synthetic rows are created.
If neither L1_tidy nor parseable raw data exists locally, they raise with a
clear message to preserve the "tudo real" requirement.
"""

# pyright: reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnknownVariableType=false, reportGeneralTypeIssues=false

from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable, List, Optional, cast

import pandas as pd

logger = logging.getLogger(__name__)

# Common schema columns for RT / ET datasets
RT_COLUMNS = [
    "subject_id",
    "task_id",
    "doc_id",
    "sent_id",
    "word_id",
    "word",
    "ffd_ms",
    "gd_ms",
    "trt_ms",
    "nfix",
    "length",
    "position",
    "lang",
]

# Common schema columns for EEG datasets (simplified placeholder)
EEG_COLUMNS = [
    "subject_id",
    "task_id",
    "doc_id",
    "sent_id",
    "word_id",
    "word",
    "alpha",
    "beta",
    "gamma",
    "theta",
    "lang",
]


def _read_if_exists(p: Path) -> pd.DataFrame | None:
    if p.exists():
        try:
            df = pd.read_parquet(p)
            if not df.empty:
                logger.info(f"Loaded existing L1_tidy: {p} ({len(df)} rows)")
                return df
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Failed to read {p}: {e}")
    return None


def _simple_rt_from_csv(folder: Path) -> pd.DataFrame:
    """Attempt a lightweight, memory-safe CSV/TSV/TXT parse into RT schema.

    Strategy:
    - Detect columns from header only
    - Read selected columns in chunks
    - Concatenate to avoid OOM
    """
    # candidates: csv, tsv, txt
    patterns = ("*.csv", "*.tsv", "*.txt")
    cands: List[Path] = []
    for pat in patterns:
        for p in folder.glob(f"**/{pat}"):
            if "__MACOSX" in str(p) or p.name.startswith("._"):
                continue
            cands.append(p)

    for f in cands[:10]:
        try:
            # pick separator by extension
            sep = "\t" if f.suffix.lower() in {".tsv", ".txt"} else None
            # Read header only, with fallbacks
            try:
                hdr = pd.read_csv(f, nrows=0, sep=sep)  # type: ignore
            except Exception:
                try:
                    hdr = pd.read_csv(  # type: ignore
                        f, nrows=0, sep=sep, encoding="latin1", engine="python"
                    )
                except Exception:
                    hdr = pd.read_csv(f, nrows=0, sep=sep, engine="python")  # type: ignore

            cols = {c.lower(): c for c in hdr.columns}
            word_col = (
                cols.get("word")
                or cols.get("token")
                or cols.get("text")
                or cols.get("current_fix_interest_area_label")
                or cols.get("interest_area_label")
            )
            if not word_col:
                continue

            def pick(*names: str) -> Optional[str]:
                for n in names:
                    if n in cols:
                        return cols[n]
                return None

            ffd = pick(
                "ffd",
                "firstfix",
                "first_fix_dur",
                "first_fixation_duration",
                "current_fix_duration",
            )
            gd = pick("gd", "gazedur", "gaze_duration")
            trt = pick("trt", "totregdur", "total_reading_time", "total_duration")
            nfix = pick("nfix", "nfixations", "n_fix")

            usecols_candidates: List[Optional[str]] = [
                word_col,
                ffd,
                gd,
                trt,
                nfix,
                cols.get("subject_id") or cols.get("participant_id"),
                cols.get("subjid"),
                cols.get("doc_id") or cols.get("article_id"),
                cols.get("sent_id"),
                cols.get("word_id") or cols.get("current_fix_interest_area_index"),
            ]
            usecols: List[str] = [c for c in usecols_candidates if c is not None]

            parts: List[pd.DataFrame] = []
            try:
                reader = pd.read_csv(  # type: ignore
                    f,
                    usecols=usecols,
                    chunksize=200_000,
                    low_memory=True,
                    iterator=True,
                    sep=sep,
                )
            except Exception:
                reader = pd.read_csv(  # type: ignore
                    f,
                    usecols=usecols,
                    chunksize=200_000,
                    low_memory=True,
                    iterator=True,
                    encoding="latin1",
                    engine="python",
                    sep=sep,
                )

            for chunk in cast(Iterable[pd.DataFrame], reader):
                out = pd.DataFrame()
                out["word"] = chunk[word_col].astype(str)
                if ffd and ffd in chunk:
                    out["ffd_ms"] = pd.to_numeric(chunk[ffd], errors="coerce")  # type: ignore
                if gd and gd in chunk:
                    out["gd_ms"] = pd.to_numeric(chunk[gd], errors="coerce")  # type: ignore
                if trt and trt in chunk:
                    out["trt_ms"] = pd.to_numeric(chunk[trt], errors="coerce")  # type: ignore
                if nfix and nfix in chunk:
                    out["nfix"] = pd.to_numeric(chunk[nfix], errors="coerce")  # type: ignore

                subj_col = (
                    cols.get("subject_id")
                    or cols.get("participant_id")
                    or cols.get("subjid")
                )
                if subj_col and subj_col in chunk:
                    out["subject_id"] = chunk[subj_col].astype(str)
                else:
                    out["subject_id"] = "unk"

                doc_col = cols.get("doc_id") or cols.get("article_id")
                if doc_col and doc_col in chunk:
                    out["doc_id"] = chunk[doc_col].astype(str)
                else:
                    out["doc_id"] = f.stem

                sent_col = cols.get("sent_id")
                if sent_col and sent_col in chunk:
                    out["sent_id"] = pd.to_numeric(chunk[sent_col], errors="coerce")  # type: ignore

                word_col_id = cols.get("word_id") or cols.get(
                    "current_fix_interest_area_index"
                )
                if word_col_id and word_col_id in chunk:
                    out["word_id"] = pd.to_numeric(chunk[word_col_id], errors="coerce")  # type: ignore

                out["length"] = out["word"].str.len()
                out["position"] = out["word_id"]
                out["lang"] = "en"
                out = out.dropna(subset=["word"])  # type: ignore
                if not out.empty:
                    parts.append(out)

            if parts:
                df = pd.concat(parts, ignore_index=True)
                logger.info(f"Parsed RT from {f} -> {len(df)} rows (chunked)")
                return df
        except Exception as e:  # noqa: BLE001
            logger.warning(f"RT CSV parse failed for {f}: {e}")
            continue

    return pd.DataFrame(columns=RT_COLUMNS)


def load_geco_et(raw_dir: Path, output_path: Path) -> pd.DataFrame:  # pragma: no cover
    """Load GECO ET data in real-mode.

    Priority: existing L1_tidy -> simple raw CSV parse -> error.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    # 1) If already materialized, reuse
    existing = _read_if_exists(output_path)
    if existing is not None:
        return existing
    # 2) Try canonical L1_tidy location
    l1_default = output_path
    if l1_default.exists():
        df = pd.read_parquet(l1_default)
        if not df.empty:
            return df
    # 3) Try raw parse
    if not raw_dir.exists():
        raise FileNotFoundError(f"GECO raw_dir not found: {raw_dir}")
    if (
        any(raw_dir.glob("**/*.csv"))
        or any(raw_dir.glob("**/*.tsv"))
        or any(raw_dir.glob("**/*.txt"))
    ):
        df = _simple_rt_from_csv(raw_dir)
        if not df.empty:
            df.to_parquet(output_path, index=False)
            return df
    # If a zip is present but not extracted, instruct the user
    if any(raw_dir.glob("**/*.zip")):
        raise RuntimeError(
            f"GECO data is zipped under {raw_dir}. Please extract to enable parsing."
        )
    raise RuntimeError("GECO: no real data found to parse and no L1_tidy available.")


def load_onestop_et(
    raw_dir: Path, output_path: Path
) -> pd.DataFrame:  # pragma: no cover
    """Load OneStop ET data in real-mode.

    Priority: existing L1_tidy -> simple raw CSV parse from project's outputs
    under raw_dir -> error.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    existing = _read_if_exists(output_path)
    if existing is not None:
        return existing
    if not raw_dir.exists():
        raise FileNotFoundError(f"OneStop raw_dir not found: {raw_dir}")
    # Onestop repo includes scripts, but we look for CSVs if present
    df = _simple_rt_from_csv(raw_dir)
    if not df.empty:
        df.to_parquet(output_path, index=False)
        return df
    raise RuntimeError(
        "OneStop: no parsed CSVs found. Run preprocessing to generate CSVs, "
        "or place them under raw_dir."
    )


def load_derco_eeg(
    raw_dir: Path, output_path: Path
) -> pd.DataFrame:  # pragma: no cover
    """Load DERCo EEG real data when available.

    If an L1_tidy parquet already exists, reuse it; otherwise, instruct to use the
    dedicated DERCo loader which reads FIF epochs (heavy dependency on MNE).
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    existing = _read_if_exists(output_path)
    if existing is not None:
        return existing
    # Defer to dedicated loader to avoid duplicating heavy logic
    from .derco_eeg_loader import run as derco_run  # local import

    # Build a minimal config compatible with derco_eeg_loader.run
    config = {
        "raw_dir": str(raw_dir),
        "processed_dir": str(output_path.parent),
    }
    out = derco_run(config)
    return pd.read_parquet(out)


def load_lpp_eeg(raw_dir: Path, output_path: Path) -> pd.DataFrame:  # pragma: no cover
    """Load LPP EEG data in real-mode.

    Reuse existing L1_tidy if present; otherwise, raise until raw parsing is
    implemented.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    existing = _read_if_exists(output_path)
    if existing is not None:
        return existing
    if not raw_dir.exists():
        raise FileNotFoundError(f"LPP raw_dir not found: {raw_dir}")
    raise RuntimeError(
        "LPP: raw parsing not yet implemented. Place processed parquet at "
        "L1_tidy to proceed."
    )
