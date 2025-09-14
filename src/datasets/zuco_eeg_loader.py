#!/usr/bin/env python3
"""
ZuCo EEG data loader (pragmático)

Objetivo imediato: produzir L1 `word_events_eeg.parquet` com chaves
compatíveis ao L1 de RT para permitir o merge ZuCo RT+EEG.

Ordem de preferência:
1) Usar `data/processed/zuco_aligned.csv` (pcs_toolbox.zuco.load_all)
   - Mapear colunas para: subject_id, task_id, doc_id, sent_id, word_id, word,
     eeg_alpha/beta/gamma/theta, length, position, lang
2) Fallback: usar L1 RT (`data/L1_tidy/zuco_rt/word_events_rt.parquet`) para
   replicar chaves e preencher EEG como NaN (mantém merge não-vazio)
"""

import logging
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _from_aligned_csv(repo_root: Path) -> pd.DataFrame:
    """Constrói EEG L1 a partir do `zuco_aligned.csv`, se existir."""
    aligned_csv = repo_root / "data/processed/zuco_aligned.csv"
    if not aligned_csv.exists():
        return pd.DataFrame()
    try:
        df = pd.read_csv(aligned_csv)
    except Exception as e:
        logger.warning(f"Falha ao ler {aligned_csv}: {e}")
        return pd.DataFrame()

    needed = {"Subject", "SentenceID", "w_pos", "token"}
    bands_map = {
        "alpha1": "eeg_alpha",
        "beta1": "eeg_beta",
        "gamma1": "eeg_gamma",
        "theta1": "eeg_theta",
    }
    if not needed.issubset(df.columns):
        logger.warning("Colunas essenciais ausentes no zuco_aligned.csv; ignorando")
        return pd.DataFrame()

    out = pd.DataFrame()
    out["subject_id"] = df["Subject"].astype(str)
    # Para compatibilizar com RT L1 atual (task_id='zuco')
    out["task_id"] = "zuco"
    # doc_id como sent_###
    out["sent_id"] = pd.to_numeric(df["SentenceID"], errors="coerce").astype("Int64")
    out["doc_id"] = out["sent_id"].map(
        lambda x: f"sent_{int(x):03d}" if pd.notna(x) else None
    )
    out["word_id"] = pd.to_numeric(df["w_pos"], errors="coerce").astype("Int64")
    out["word"] = df["token"].astype(str)
    # Mapear bandas
    for src, dst in bands_map.items():
        if src in df.columns:
            out[dst] = pd.to_numeric(df[src], errors="coerce")
        else:
            out[dst] = np.nan
    out["length"] = out["word"].astype(str).map(len)
    out["position"] = out["word_id"]
    out["lang"] = "en"

    # Ordenar/limpar
    cols = [
        "subject_id",
        "task_id",
        "doc_id",
        "sent_id",
        "word_id",
        "word",
        "eeg_alpha",
        "eeg_beta",
        "eeg_gamma",
        "eeg_theta",
        "length",
        "position",
        "lang",
    ]
    out = out[cols].dropna(subset=["sent_id", "word_id", "word"]).reset_index(drop=True)
    logger.info(f"EEG L1 (aligned.csv): {len(out)} linhas")
    return out


def _from_rt_fallback(repo_root: Path) -> pd.DataFrame:
    """Fallback: replica chaves do L1 RT e preenche bandas EEG como NaN."""
    rt_path = repo_root / "data/L1_tidy/zuco_rt/word_events_rt.parquet"
    if not rt_path.exists():
        return pd.DataFrame()
    try:
        rt = pd.read_parquet(rt_path)
    except Exception as e:
        logger.warning(f"Falha ao ler RT L1 {rt_path}: {e}")
        return pd.DataFrame()

    keep = [
        "subject_id",
        "task_id",
        "doc_id",
        "sent_id",
        "word_id",
        "word",
        "length",
        "position",
        "lang",
    ]
    miss = [c for c in keep if c not in rt.columns]
    if miss:
        logger.warning(f"RT L1 sem colunas esperadas: {miss}")
        return pd.DataFrame()

    eeg = rt[keep].copy()
    for c in ["eeg_alpha", "eeg_beta", "eeg_gamma", "eeg_theta"]:
        eeg[c] = np.nan
    # Reordenar
    eeg = eeg[
        [
            "subject_id",
            "task_id",
            "doc_id",
            "sent_id",
            "word_id",
            "word",
            "eeg_alpha",
            "eeg_beta",
            "eeg_gamma",
            "eeg_theta",
            "length",
            "position",
            "lang",
        ]
    ]
    logger.info(f"EEG L1 (fallback RT): {len(eeg)} linhas")
    return eeg


def load_zuco_eeg(raw_dir: Path, output_path: Path) -> pd.DataFrame:
    """Entrada principal do loader de EEG do ZuCo.

    Prioriza conversão de `zuco_aligned.csv`; cai para réplicas do L1 RT
    se necessário.
    """
    # Determinar repo_root de forma robusta: src/datasets/.. -> repo root
    repo_root = Path(__file__).resolve().parents[2]
    # 1) Tentar aligned.csv
    df = _from_aligned_csv(repo_root)
    if df.empty:
        logger.info("Aligned indisponível; usando fallback com RT L1…")
        df = _from_rt_fallback(repo_root)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not df.empty:
        df.to_parquet(output_path, index=False)
        logger.info(f"Salvo EEG L1 em {output_path}")
    else:
        # Último recurso: emitir 0 linhas (evita placeholders desinformativos)
        pd.DataFrame(
            columns=[
                "subject_id",
                "task_id",
                "doc_id",
                "sent_id",
                "word_id",
                "word",
                "eeg_alpha",
                "eeg_beta",
                "eeg_gamma",
                "eeg_theta",
                "length",
                "position",
                "lang",
            ]
        ).to_parquet(output_path, index=False)
        logger.info(f"EEG L1 vazio salvo em {output_path}")
    return df


if __name__ == "__main__":
    repo_root = Path("/home/agourakis82/workspace/pcs-meta-repo")
    out = repo_root / "data/L1_tidy/zuco_eeg/word_events_eeg.parquet"
    df = load_zuco_eeg(repo_root / "scripts/data/raw_public/zuco", out)
    print("rows:", len(df))
