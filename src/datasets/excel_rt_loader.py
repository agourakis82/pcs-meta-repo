from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional, Set

import pandas as pd

# pyright: reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnknownVariableType=false, reportGeneralTypeIssues=false


logger = logging.getLogger(__name__)


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


def _pick(cols: dict[str, str], *names: str) -> Optional[str]:
    for n in names:
        if n in cols:
            return cols[n]
    return None


def _parse_excel(path: Path) -> pd.DataFrame:
    try:
        df = pd.read_excel(path, engine="openpyxl")
    except Exception as e:
        msg = (
            f"Falha ao ler Excel {path}. Instale 'openpyxl' (pip install openpyxl). "
            f"Erro: {e}"
        )
        raise RuntimeError(msg)
    cols = {c.lower(): c for c in df.columns}
    word_col = _pick(cols, "word", "token", "text")
    if not word_col:
        # tentar colunas comuns de interesse visual
        word_col = _pick(cols, "interest_area_label", "current_fix_interest_area_label")
    if not word_col:
        return pd.DataFrame(columns=RT_COLUMNS)

    ffd = _pick(
        cols,
        "ffd",
        "firstfix",
        "first_fix_dur",
        "firstfixationduration",
        "first_fixation_duration",
    )
    gd = _pick(cols, "gd", "gazedur", "gaze_duration")
    trt = _pick(cols, "trt", "totregdur", "total_reading_time", "totalduration")
    nfix = _pick(cols, "nfix", "nfixations", "n_fix")

    out = pd.DataFrame()
    # Clean words: strip whitespace and filter out empty/invalid words
    words = df[word_col].astype(str).str.strip()
    words = words[words.notna() & (words != "") & (words != "nan")]
    out["word"] = words
    if ffd and ffd in df:
        out["ffd_ms"] = pd.to_numeric(df[ffd], errors="coerce")
    if gd and gd in df:
        out["gd_ms"] = pd.to_numeric(df[gd], errors="coerce")
    if trt and trt in df:
        out["trt_ms"] = pd.to_numeric(df[trt], errors="coerce")
    if nfix and nfix in df:
        out["nfix"] = pd.to_numeric(df[nfix], errors="coerce")

    subj = _pick(cols, "subject_id", "subject", "participant", "participant_id")
    out["subject_id"] = df[subj].astype(str) if subj and subj in df else "unk"
    doc = _pick(cols, "doc_id", "article", "article_id", "text_id")
    out["doc_id"] = df[doc].astype(str) if doc and doc in df else path.stem
    sent = _pick(cols, "sent_id", "sentence_id")
    out["sent_id"] = (
        pd.to_numeric(df[sent], errors="coerce") if sent and sent in df else pd.NA
    )
    wid = _pick(cols, "word_id", "position", "current_fix_interest_area_index")
    out["word_id"] = (
        pd.to_numeric(df[wid], errors="coerce") if wid and wid in df else pd.NA
    )

    out["length"] = out["word"].str.len()
    out["position"] = out["word_id"]

    # Detect language based on common words
    if not out.empty:
        # Sample some words to detect language
        sample_words = out["word"].str.lower().head(100).tolist()

        # Dutch indicators
        dutch_words = {
            "de",
            "het",
            "een",
            "en",
            "van",
            "dat",
            "die",
            "voor",
            "met",
            "op",
            "zijn",
            "bij",
            "werd",
            "wordt",
        }
        # English indicators
        english_words = {
            "the",
            "and",
            "of",
            "to",
            "in",
            "that",
            "for",
            "with",
            "on",
            "was",
            "is",
            "are",
            "were",
        }

        dutch_count = sum(1 for w in sample_words if w in dutch_words)
        english_count = sum(1 for w in sample_words if w in english_words)

        if dutch_count > english_count:
            detected_lang = "nl"
        else:
            detected_lang = "en"

        logger.info(
            f"Detected language: {detected_lang} "
            f"(Dutch: {dutch_count}, English: {english_count})"
        )
        out["lang"] = detected_lang
    else:
        out["lang"] = "en"
    out["task_id"] = pd.NA
    out = out.dropna(subset=["word"]).reset_index(drop=True)
    return out


def load_excel_rt(raw_dir: Path, output_path: Path) -> pd.DataFrame:
    """Load RT/ET style data from Excel files under raw_dir.

    - Accepts multiple .xlsx files (e.g., L1ReadingData.xlsx, L2ReadingData.xlsx)
    - Concatenates into the common RT schema and writes parquet
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw dir not found: {raw_dir}")

    xls: List[Path] = [
        *raw_dir.glob("**/*ReadingData*.xlsx"),
        *raw_dir.glob("**/*.xlsx"),
    ]
    # keep unique while preserving order
    seen: Set[Path] = set()
    files: List[Path] = []
    for p in xls:
        if p not in seen:
            files.append(p)
            seen.add(p)

    if not files:
        raise RuntimeError(
            "Nenhum .xlsx encontrado em "
            f"{raw_dir}. Coloque L1/L2ReadingData.xlsx nesta pasta."
        )

    parts: List[pd.DataFrame] = []
    for f in files:
        try:
            df = _parse_excel(f)
            if not df.empty:
                parts.append(df)
                logger.info(f"Lido Excel {f} -> {len(df)} linhas")
        except Exception as e:
            logger.warning(f"Falha ao parsear {f}: {e}")

    if not parts:
        raise RuntimeError("Nenhuma tabela válida encontrada nos .xlsx informados")

    out = pd.concat(parts, ignore_index=True)
    out.to_parquet(output_path, index=False)
    logger.info(f"Salvo L1_tidy Excel em {output_path} ({len(out)} linhas)")
    return out
    logger.info(f"Salvo L1_tidy Excel em {output_path} ({len(out)} linhas)")
    return out
