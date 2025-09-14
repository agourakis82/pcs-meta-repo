"""SWOW real dataset loader (multilíngue) v4.4

Suporte a formatos reais encontrados no repositório:

EN:
    SWOW-EN.complete.20180827.csv (colunas contém cue, R1Raw/R1 etc.)
ES (SWOWRP):
    SWOWRP.raw.20220426.csv (cue, R1,R2,R3)
NL (Dutch 2012):
    associationData.csv (separador ';', cue, asso1..asso3)
ZH:
    SWOWZH.raw.20230424.csv (cue, R1Raw..R3Raw)

Processo:
    1. Detecta coluna de cue.
    2. Detecta colunas de respostas (prioridade R1,R2,R3 > R1Raw.. > asso1.. > fallback)
    3. Gera linhas (cue, response, weight=1, lang) removendo vazios ou placeholders.
    4. Agrega duplicatas somando weight.

Referência: De Deyne et al. (2019) Small World of Words (doi:10.1038/s41597-019-0224-1).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable, List

import pandas as pd

logger = logging.getLogger(__name__)


def _candidate_columns(df: pd.DataFrame, names: Iterable[str]) -> List[str]:
    lower_map = {c.lower(): c for c in df.columns}
    found: List[str] = []
    for n in names:
        if n.lower() in lower_map:
            found.append(lower_map[n.lower()])
    return found


def _extract_edges(df: pd.DataFrame) -> pd.DataFrame:
    """Extrai edges (cue,response) de formatos suportados."""
    cue_cols = _candidate_columns(df, ["cue", "stimulus"])
    if not cue_cols:
        raise ValueError("Não encontrou coluna 'cue' ou 'stimulus'")
    cue_col = cue_cols[0]

    priority_groups = [
        ["R1", "R2", "R3"],
        ["R1Raw", "R2Raw", "R3Raw"],
        ["asso1", "asso2", "asso3"],
    ]
    responses: List[str] = []
    avail_lower = {c.lower(): c for c in df.columns}
    for group in priority_groups:
        group_found = [
            avail_lower[g.lower()] for g in group if g.lower() in avail_lower
        ]
        if len(group_found) >= 2:
            responses = group_found
            break
    # fallback genérico
    if not responses:
        generic_set = {
            "r1",
            "r2",
            "r3",
            "r1raw",
            "r2raw",
            "r3raw",
            "asso1",
            "asso2",
            "asso3",
        }
        generic = [c for c in df.columns if c.lower() in generic_set]
        responses = generic
    if not responses:
        raise ValueError("Não encontrou colunas de respostas (R1/R2/...)")

    melted = df.melt(
        id_vars=[cue_col],
        value_vars=responses,
        var_name="resp_col",
        value_name="response",
    )
    # limpeza
    melted["response"] = (
        melted["response"]
        .astype(str)
        .str.strip()
        .str.replace("\u200b", "", regex=False)
    )
    invalid = {"", "na", "none", "nan", "no", "não", "没有了"}
    melted = melted[~melted["response"].str.lower().isin(invalid)]
    melted = melted[melted["response"].str.len() > 0]
    melted = melted.rename(columns={cue_col: "cue"})
    melted["cue"] = melted["cue"].astype(str).str.strip()
    melted = melted[melted["cue"] != ""]
    melted["weight"] = 1
    grouped = (
        melted[["cue", "response", "weight"]]
        .groupby(["cue", "response"], as_index=False)["weight"]
        .sum()
    )
    return grouped


def load_swow_language(raw_lang_dir: Path, lang: str) -> pd.DataFrame:
    if not raw_lang_dir.exists():
        logger.warning(f"Diretório SWOW ausente para {lang}: {raw_lang_dir}")
        # Fallback diretórios alternativos conhecidos
        alt_map = {
            "es": Path("data/es/raw"),
            "nl": Path("data/nl/raw"),
            "zh": Path("data/zh/raw/SWOW-ZH24"),
        }
        alt_dir = alt_map.get(lang)
        if alt_dir and alt_dir.exists():
            raw_lang_dir = alt_dir
            logger.info(f"Usando fallback para {lang}: {raw_lang_dir}")
        else:
            return pd.DataFrame(columns=["cue", "response", "weight", "lang"])

    patterns_map = {
        "en": ["SWOW-EN.complete", "SWOW-EN.R100", "SWOW-EN"],
        "es": ["SWOWRP.raw", "SWOWRP.R70", "SWOWRP.spellchecked"],
        "nl": ["associationData"],
        "zh": ["SWOWZH.raw", "SWOWZH.R55"],
        "pt": ["swow_pt"],  # placeholder
    }

    files: List[Path] = []
    for patt in patterns_map.get(lang, []):
        files.extend(raw_lang_dir.rglob(f"{patt}*.csv"))
    if not files:
        files = list(raw_lang_dir.glob("*.csv")) + list(raw_lang_dir.glob("*.tsv"))
    if not files:
        # Tentativa secundária: fallback se ainda não testado
        alt_map = {
            "es": Path("data/es/raw"),
            "nl": Path("data/nl/raw"),
            "zh": Path("data/zh/raw/SWOW-ZH24"),
        }
        alt_dir = alt_map.get(lang)
        if alt_dir and alt_dir.exists() and alt_dir != raw_lang_dir:
            logger.info(f"Re-tentando {lang} em fallback {alt_dir}")
            raw_lang_dir = alt_dir
            for patt in patterns_map.get(lang, []):
                files.extend(raw_lang_dir.rglob(f"{patt}*.csv"))
            if not files:
                files = list(raw_lang_dir.glob("*.csv"))
        if not files:
            logger.warning(f"Sem arquivos SWOW para {lang} em {raw_lang_dir}")
            return pd.DataFrame(columns=["cue", "response", "weight", "lang"])

    parts: List[pd.DataFrame] = []
    for f in files:
        try:
            # Detecta separador ';' (caso NL) vs ','
            head_text = f.read_text(encoding="utf-8", errors="ignore")[:200]
            sep = ";" if head_text.count(";") > head_text.count(",") else ","
            df = pd.read_csv(f, sep=sep, low_memory=False)
            edges = _extract_edges(df)
            parts.append(edges)
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Falha lendo {f.name}: {e}")
            continue
    if not parts:
        return pd.DataFrame(columns=["cue", "response", "weight", "lang"])
    out = pd.concat(parts, ignore_index=True)
    out["lang"] = lang
    grouped = out.groupby(["cue", "response", "lang"], as_index=False)["weight"].sum()
    return grouped


def load_swow_all(raw_root: Path, languages: List[str]) -> pd.DataFrame:
    frames: List[pd.DataFrame] = []
    for lang in languages:
        df = load_swow_language(raw_root / lang, lang)
        if not df.empty:
            frames.append(df)
    if not frames:
        return pd.DataFrame(columns=["cue", "response", "weight", "lang"])
    merged = pd.concat(frames, ignore_index=True)
    return merged
