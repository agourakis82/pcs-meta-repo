#!/usr/bin/env python3
"""SWOW-ZuCo Pipeline v4.4 - Modal split & multilingual KEC"""

import argparse
import json
import logging
import os
import sys
import unicodedata
from datetime import datetime
from math import sqrt
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import yaml
from pandas import DataFrame

# Prefer precise stats if available
try:  # lightweight optional import
    from scipy.stats import spearmanr as _scipy_spearmanr  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    _scipy_spearmanr = None  # type: ignore

# Optional: statsmodels for mixed-effects models
try:  # pragma: no cover - optional dependency
    import statsmodels.formula.api as smf  # type: ignore
except Exception:  # noqa: BLE001
    smf = None  # type: ignore

# Optional: KenLM for surprisal
try:  # pragma: no cover - optional dependency
    import kenlm as _kenlm  # type: ignore
except Exception:  # noqa: BLE001
    _kenlm = None  # type: ignore

try:
    # Prefer stdlib; avoid adding external deps
    import urllib.request as _url
except Exception:  # pragma: no cover
    _url = None  # type: ignore

# Ensure src is on path for imports (before importing from src.*)
_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC_DIR = _REPO_ROOT / "src"
for _p in (str(_SRC_DIR), str(_REPO_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from src.datasets.excel_rt_loader import load_excel_rt  # noqa: E402
from src.datasets.placeholders import (  # noqa: E402
    load_derco_eeg,
    load_geco_et,
    load_lpp_eeg,
    load_onestop_et,
)
from src.datasets.zuco_eeg_loader import load_zuco_eeg  # noqa: E402
from src.datasets.zuco_working_loader import load_zuco_rt  # noqa: E402

scripts_dir = Path(__file__).parent
data_dir = _REPO_ROOT / "data"

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_config() -> Dict[str, Any]:
    """Load configuration from YAML files"""
    config_dir = Path(__file__).parent.parent / "config"

    # Load data roots
    with open(config_dir / "data_root.yaml") as f:
        data_config = yaml.safe_load(f)

    # Load datasets config
    with open(config_dir / "datasets.yaml") as f:
        datasets_config = yaml.safe_load(f)

    # Resolve data root paths
    data_root = data_config.get("data_root", "/mnt/FASTDATA")

    # Create resolved paths
    resolved_data_config: Dict[str, Any] = {}
    for key, path_template in data_config.items():
        if isinstance(path_template, str) and "{data_root}" in path_template:
            resolved_data_config[key] = path_template.format(data_root=data_root)
        else:
            resolved_data_config[key] = path_template

    # Inject canonical defaults if missing
    canonical_defaults = {
        "L1_tidy": "data/L1_tidy",
        "L2_derived": "data/L2_derived",
        "processed": "data/processed",
        "reports": "reports",
    }
    for k, v in canonical_defaults.items():
        if k not in resolved_data_config:
            resolved_data_config[k] = v

    return {"data": resolved_data_config, "datasets": datasets_config}


def tidy_rt_datasets(datasets: List[str], config: Dict[str, Any]) -> None:
    """Process RT/ET datasets to L1 tidy format"""
    logger.info(f"Processing RT datasets: {datasets}")

    # Establish local paths (no reliance on outer scope mutation)
    repo_root = Path(__file__).resolve().parents[1]
    data_dir_local = repo_root / "data"

    def _resolve_raw_dir(ds_key: str, default_sub: str) -> Path:
        # 1) try config raw_dir
        cfg = config["datasets"].get("datasets_rt", {}).get(ds_key, {})
        raw_dir_cfg = cfg.get("raw_dir")
        candidates: List[Path] = []
        if raw_dir_cfg:
            candidates.append(Path(raw_dir_cfg))
        # 2) prefer data/raw_public/{sub}
        candidates.append(repo_root / f"data/raw_public/{default_sub}")
        # 3) fallback scripts/data/raw_public/{sub}
        candidates.append(repo_root / f"scripts/data/raw_public/{default_sub}")
        for c in candidates:
            if c.exists():
                return c
        return candidates[0]

    for dataset in datasets:
        # Check in datasets_rt section
        if (
            "datasets_rt" in config["datasets"]
            and dataset in config["datasets"]["datasets_rt"]
        ):
            dataset_config = config["datasets"]["datasets_rt"][dataset]
        else:
            logger.warning(f"Dataset {dataset} not found in datasets_rt config")
            continue

        if dataset_config.get("modality") not in ["eye-tracking"]:
            logger.warning(f"Dataset {dataset} is not RT/ET, skipping")
            continue

        logger.info(f"Processing {dataset}")

        df = None
        try:
            if dataset == "zuco_rt":
                raw_dir = _resolve_raw_dir("zuco_rt", "zuco")
                out_path = data_dir_local / "L1_tidy/zuco_rt/word_events_rt.parquet"
                df = load_zuco_rt(raw_dir, out_path)
            elif dataset == "zuco_eeg":  # allow EEG in same function if requested
                raw_dir = _resolve_raw_dir("zuco_eeg", "zuco")
                out_path = data_dir_local / "L1_tidy/zuco_eeg/word_events_eeg.parquet"
                df = load_zuco_eeg(raw_dir, out_path)
            elif dataset == "geco_et":
                raw_dir = _resolve_raw_dir("geco_et", "geco")
                out_path = data_dir_local / "L1_tidy/geco_et/word_events_rt.parquet"
                df = load_geco_et(raw_dir, out_path)
            elif dataset == "onestop_et":
                raw_dir = _resolve_raw_dir("onestop_et", "onestop")
                out_path = data_dir_local / "L1_tidy/onestop_et/word_events_rt.parquet"
                df = load_onestop_et(raw_dir, out_path)
            elif dataset == "excel_custom_rt":
                # Excel-based RT/ET ingestion from user-provided .xlsx files
                raw_dir = _resolve_raw_dir("excel_custom_rt", "excel_custom")
                out_path = (
                    data_dir_local / "L1_tidy/excel_custom_rt/word_events_rt.parquet"
                )
                df = load_excel_rt(raw_dir, out_path)
            else:
                logger.warning("Nenhum loader para dataset %s" % dataset)
        except Exception as e:  # noqa: BLE001
            logger.error("Falha ao processar %s: %s" % (dataset, e))

        # Log de sucesso
        if df is not None:
            logger.info("Successfully processed %s: %d records" % (dataset, len(df)))


def tidy_eeg_datasets(
    datasets: List[str], config: Dict[str, Any]
) -> None:  # assinatura corrigida
    """Process EEG datasets to L1 tidy format"""
    logger.info(f"Processing EEG datasets: {datasets}")

    if not datasets:
        logger.warning("No EEG datasets provided")
        return
    repo_root = Path(__file__).resolve().parents[1]

    def _resolve_raw_dir_eeg(ds_key: str, default_sub: str) -> Path:
        cfg = config["datasets"].get("datasets_eeg", {}).get(ds_key, {})
        raw_dir_cfg = cfg.get("raw_dir")
        candidates: List[Path] = []
        if raw_dir_cfg:
            candidates.append(Path(raw_dir_cfg))
        candidates.append(repo_root / f"data/raw_public/{default_sub}")
        candidates.append(repo_root / f"scripts/data/raw_public/{default_sub}")
        for c in candidates:
            if c.exists():
                return c
        return candidates[0]

    for dataset in datasets:
        # Similar lookup to RT sections but in datasets_eeg
        if (
            "datasets_eeg" not in config["datasets"]
            or dataset not in config["datasets"]["datasets_eeg"]
        ):
            logger.warning(f"Dataset {dataset} not found in datasets_eeg config")
            continue
        dataset_config = config["datasets"]["datasets_eeg"][dataset]
        if dataset_config.get("modality") != "EEG":
            logger.warning(f"Dataset {dataset} is not EEG, skipping")
            continue

        logger.info(f"Processing {dataset}")

        # Prefer config; fallback to known canonical locations
        if dataset == "zuco_eeg":
            raw_dir = _resolve_raw_dir_eeg("zuco_eeg", "zuco")
        elif dataset == "derco_eeg":
            raw_dir = _resolve_raw_dir_eeg("derco_eeg", "derco")
        elif dataset == "lpp_eeg":
            raw_dir = _resolve_raw_dir_eeg("lpp_eeg", "lpp")
        else:
            raw_dir = Path(dataset_config["raw_dir"])  # fallback
        out_path = Path(dataset_config["processed_dir"]) / "word_events_eeg.parquet"
        out_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            if dataset == "zuco_eeg":
                df = load_zuco_eeg(raw_dir, out_path)
            elif dataset == "derco_eeg":
                df = load_derco_eeg(raw_dir, out_path)
            elif dataset == "lpp_eeg":
                df = load_lpp_eeg(raw_dir, out_path)
            else:
                logger.warning(f"No loader for dataset {dataset}")
                continue
            logger.info(f"Successfully processed {dataset}: {len(df)} records")
        except Exception as e:  # noqa: BLE001
            logger.error(f"Failed to process {dataset}: {e}")


def integrate_kec_datasets(config: Dict[str, Any]) -> None:
    """Join KEC metrics with processed datasets"""
    logger.info("Integrating KEC with datasets")

    # Load KEC data for all languages
    kec_data: Dict[str, DataFrame] = {}
    kec_base = Path(config["data"]["L2_derived"]) / "kec"
    reports_dir = Path(config["data"]["reports"]) / "v4.4"
    reports_dir.mkdir(parents=True, exist_ok=True)
    provenance_inputs: List[str] = []
    provenance_outputs: List[str] = []
    # Methods summary (for memory logging)
    methods_summary: List[str] = [
        (
            "KEC merge: canonical columns [word, entropy, curvature, coherence], "
            "with components prefixed as comp_* and deduplicated per word."
        ),
        (
            "RT join: per-language join_key; en uses first alphabetical "
            "sequence (>=2 chars); others use lowercase word."
        ),
        (
            "OneStop ET: auto-select text column (word/token/word_form/orth) if "
            "'word' is mostly bracket markers; drop empty tokens after "
            "normalization."
        ),
        (
            "KEC dedup by join_key before merge to avoid row explosion; RT "
            "outputs also saved with _kec_rt alias for coverage."
        ),
    ]

    for lang in ["en", "es", "nl", "zh"]:
        lang_dir = kec_base / lang
        if not lang_dir.exists():
            logger.warning(f"KEC data for {lang} not found at {lang_dir}")
            continue

        try:
            # Load all KEC components
            kec_files = {
                "entropy": lang_dir / "entropy.parquet",
                "curvature": lang_dir / "curvature.parquet",
                "coherence": lang_dir / "coherence.parquet",
                "components": lang_dir / "components.parquet",
            }

            kec_dfs: Dict[str, DataFrame] = {}
            for name, path in kec_files.items():
                if path.exists():
                    kec_dfs[name] = pd.read_parquet(path)
                    provenance_inputs.append(str(path))

            if kec_dfs:
                # Build a clean KEC table with canonical metric columns
                base_cols = ["word", "entropy", "out_degree", "total_weight"]
                if "entropy" in kec_dfs:
                    ent = kec_dfs["entropy"][
                        [c for c in base_cols if c in kec_dfs["entropy"].columns]
                    ]
                else:
                    # Fallback empty frame if missing
                    ent = pd.DataFrame(columns=["word", "entropy"]).astype(
                        {"word": "string"}
                    )

                merged = ent
                if "curvature" in kec_dfs:
                    curv = kec_dfs["curvature"]
                    keep = [c for c in ["word", "curvature"] if c in curv.columns]
                    if keep:
                        merged = merged.merge(curv[keep], on="word", how="outer")
                if "coherence" in kec_dfs:
                    coh = kec_dfs["coherence"]
                    keep = [c for c in ["word", "coherence"] if c in coh.columns]
                    if keep:
                        merged = merged.merge(coh[keep], on="word", how="outer")

                # Optionally, attach components with a prefix to avoid collisions
                if "components" in kec_dfs:
                    comps = kec_dfs["components"].copy()
                    if "word" in comps.columns:
                        # reduce to 1 row per word to avoid duplication explosion
                        comps = comps.drop_duplicates(subset=["word"])  # 1 per word
                        other_cols = [c for c in comps.columns if c != "word"]
                        comps = comps.rename(
                            columns={c: f"comp_{c}" for c in other_cols}
                        )
                        merged = merged.merge(comps, on="word", how="left")

                kec_data[lang] = merged
                logger.info(
                    "Loaded KEC for %s: %d words; cols=%s",
                    lang,
                    len(merged),
                    list(merged.columns),
                )

        except Exception as e:
            logger.error(f"Failed to load KEC for {lang}: {e}")

    # Process each dataset type
    integration_dir = Path(config["data"]["processed"]) / "v4.4" / "integration"
    integration_dir.mkdir(parents=True, exist_ok=True)

    # Small helper: pick first alphabetical token from regex findall
    def _first_alpha_token(obj: object) -> str:
        try:
            if isinstance(obj, (list, tuple)) and obj:
                return str(obj[0])
        except Exception:
            return ""
        return ""

    def _ascii_fold(s: str) -> str:
        try:
            return (
                unicodedata.normalize("NFKD", s)
                .encode("ascii", "ignore")
                .decode("ascii")
            )
        except Exception:
            return s

    def _normalize_join_series(series: pd.Series, lang: str) -> pd.Series:
        series = series.astype(str).str.strip().str.lower()
        if lang == "en":
            return series.str.findall(r"[a-z]{2,}").apply(_first_alpha_token)
        if lang in ("es", "nl"):
            return (
                series.apply(_ascii_fold)
                .str.findall(r"[a-z]{2,}")
                .apply(_first_alpha_token)
            )
        # default (e.g., zh): exact lowercased word
        return series

    # RT datasets
    for dataset in ["zuco_rt", "geco_et", "onestop_et", "excel_custom_rt"]:
        l1_path = Path(config["data"]["L1_tidy"]) / dataset / "word_events_rt.parquet"
        if not l1_path.exists():
            logger.warning(f"L1 data not found: {l1_path}")
            continue

        try:
            df_rt: DataFrame = pd.read_parquet(l1_path)

            # Dataset-specific token normalization to improve KEC matching
            # Only for OneStop (English); removes bracketed markers and
            # non-alpha chars
            if dataset == "onestop_et":
                df_rt = df_rt.copy()
                # Pick best available text column (fallback if 'word' is mostly markers)
                candidates = [
                    "word",
                    "token",
                    "word_form",
                    "orth",
                    "WORD",
                    "Word",
                ]
                text_col = next((c for c in candidates if c in df_rt.columns), "word")

                # If using 'word', detect if mostly bracket markers and switch
                if text_col == "word":
                    sample = (
                        df_rt[text_col]
                        .astype(str)
                        .head(2000)
                        .str.contains(r"^\[[^\]]*\]$", regex=True)
                    )
                    if sample.size and sample.mean() > 0.8:
                        alt = next(
                            (
                                c
                                for c in ["token", "word_form", "orth"]
                                if c in df_rt.columns
                            ),
                            None,
                        )
                        if alt:
                            text_col = alt
                            logger.info(
                                (
                                    "onestop_et: switching text column to '%s' due to "
                                    "bracket markers"
                                ),
                                text_col,
                            )

                # Build normalized join key from chosen text column
                join = (
                    df_rt[text_col]
                    .astype(str)
                    .str.lower()
                    .str.findall(r"[a-z]{2,}")
                    .apply(_first_alpha_token)
                )
                df_rt["join_key"] = join
                # Drop empty tokens after normalization
                before = len(df_rt)
                df_rt = df_rt[df_rt["join_key"] != ""].copy()
                dropped = before - len(df_rt)
                if dropped:
                    logger.info(
                        "onestop_et: dropped %d rows with empty normalized tokens",
                        dropped,
                    )
            else:
                # For other RT datasets: start lowercased; refine per-language below
                df_rt = df_rt.copy()
                df_rt["join_key"] = df_rt["word"].astype(str).str.lower()

            # Join with KEC
            dfs_by_lang: List[DataFrame] = []
            for lang, kec_df in kec_data.items():
                mask = df_rt["lang"] == lang  # type: ignore[index]
                if mask.any():  # type: ignore[call-arg]
                    # Normalize both sides for join per language
                    k = kec_df.copy()
                    df_lang_pre = df_rt[mask].copy()  # type: ignore[index]
                    if lang == "en":
                        k["join_key"] = (
                            k["word"]
                            .astype(str)
                            .str.lower()
                            .str.findall(r"[a-z]{2,}")
                            .apply(_first_alpha_token)
                        )
                        if "join_key" not in df_lang_pre.columns or (
                            dataset != "onestop_et"
                        ):
                            df_lang_pre["join_key"] = _normalize_join_series(
                                df_lang_pre["word"], lang
                            )
                    elif lang in ("es", "nl"):
                        k["join_key"] = _normalize_join_series(k["word"], lang)
                        df_lang_pre["join_key"] = _normalize_join_series(
                            df_lang_pre["word"], lang
                        )
                    else:
                        k["join_key"] = k["word"].astype(str).str.lower()
                        df_lang_pre["join_key"] = (
                            df_lang_pre["word"].astype(str).str.lower()
                        )
                    # Reduce KEC to one row per join_key to avoid row explosion
                    k = k.drop_duplicates(subset=["join_key"])  # 1 per join_key
                    # Perform left join on normalized key, keep original word
                    df_lang: DataFrame = df_lang_pre.merge(
                        k.drop(columns=["word"], errors="ignore"),
                        on="join_key",
                        how="left",
                        suffixes=("", "_kec"),
                    )
                    dfs_by_lang.append(df_lang)  # type: ignore[arg-type]
                    logger.info("Integrated %d %s records with KEC", len(df_lang), lang)

            # Also include any languages not in KEC
            for lang in df_rt["lang"].unique():  # type: ignore[index]
                if lang not in kec_data:
                    mask = df_rt["lang"] == lang  # type: ignore[index]
                    df_lang = df_rt[mask].copy()  # type: ignore[index]
                    dfs_by_lang.append(df_lang)  # type: ignore[arg-type]
                    logger.info(
                        "Added %d %s records without KEC", int(len(df_lang)), lang
                    )

            if dfs_by_lang:
                df_integrated = pd.concat(dfs_by_lang, ignore_index=True)
            else:
                df_integrated = df_rt.copy()

            # Save integrated data (preserve current naming) and also write a
            # standardized alias with suffix _kec_rt to improve downstream
            # coverage/reporting.
            output_path = (
                integration_dir / f"{dataset.replace('_rt', '_kec_rt')}.parquet"
            )
            # Drop helper join key before saving
            if "join_key" in df_integrated.columns:
                df_integrated = df_integrated.drop(columns=["join_key"])  # type: ignore[assignment]
            if len(df_integrated) > 0:
                df_integrated.to_parquet(output_path, index=False)
                logger.info(f"Saved integrated RT data: {output_path}")
                provenance_outputs.append(str(output_path))
                provenance_inputs.append(str(l1_path))
            else:
                logger.info(
                    (
                        "Skipped saving empty integrated RT for %s (no valid "
                        "tokens after filtering)"
                    ),
                    dataset,
                )

            # If dataset name did not end with _rt (e.g., geco_et, onestop_et),
            # also emit an alias ending with _kec_rt to standardize filenames used
            # by coverage scanners and downstream consumers.
            if not dataset.endswith("_rt") and len(df_integrated) > 0:
                alias_name = f"{dataset}_kec_rt.parquet"
                alias_path = integration_dir / alias_name
                if alias_path != output_path:
                    try:
                        df_integrated.to_parquet(alias_path, index=False)
                        logger.info("Saved RT alias for coverage: %s", alias_path)
                        provenance_outputs.append(str(alias_path))
                    except Exception as e:  # noqa: BLE001
                        logger.warning(
                            f"Failed to write RT alias {alias_path.name}: {e}"
                        )

        except Exception as e:
            logger.error(f"Failed to integrate {dataset}: {e}")

    # EEG datasets
    for dataset in ["zuco_eeg", "derco_eeg", "lpp_eeg"]:
        l1_path = Path(config["data"]["L1_tidy"]) / dataset / "word_events_eeg.parquet"
        if not l1_path.exists():
            logger.warning(f"L1 data not found: {l1_path}")
            continue

        try:
            df_eeg: DataFrame = pd.read_parquet(l1_path)

            # Join with KEC
            dfs_by_lang: List[DataFrame] = []
            for lang, kec_df in kec_data.items():
                mask = df_eeg["lang"] == lang  # type: ignore[index]
                if mask.any():  # type: ignore[call-arg]
                    df_lang: DataFrame = df_eeg[mask].merge(  # type: ignore[index]
                        kec_df, on="word", how="left", suffixes=("", "_kec")
                    )
                    dfs_by_lang.append(df_lang)  # type: ignore[arg-type]

            # Also include any languages not in KEC
            for lang in df_eeg["lang"].unique():  # type: ignore[index]
                if lang not in kec_data:
                    mask = df_eeg["lang"] == lang  # type: ignore[index]
                    df_lang = df_eeg[mask].copy()  # type: ignore[index]
                    dfs_by_lang.append(df_lang)  # type: ignore[arg-type]

            if dfs_by_lang:
                df_integrated = pd.concat(dfs_by_lang, ignore_index=True)
            else:
                df_integrated = df_eeg.copy()

            # Save integrated data
            output_path = (
                integration_dir / f"{dataset.replace('_eeg', '_kec_eeg')}.parquet"
            )
            df_integrated.to_parquet(output_path, index=False)
            logger.info(f"Saved integrated EEG data: {output_path}")
            provenance_outputs.append(str(output_path))
            provenance_inputs.append(str(l1_path))

        except Exception as e:
            logger.error(f"Failed to integrate {dataset}: {e}")

    # Create compatibility merged view (ZuCo only)
    try:
        zuco_rt_path = integration_dir / "zuco_kec_rt.parquet"
        zuco_eeg_path = integration_dir / "zuco_kec_eeg.parquet"

        if zuco_rt_path.exists() and zuco_eeg_path.exists():
            df_rt = pd.read_parquet(zuco_rt_path)
            df_eeg = pd.read_parquet(zuco_eeg_path)

            # Inner join on key columns
            merge_cols = [
                "lang",
                "subject_id",
                "task_id",
                "doc_id",
                "sent_id",
                "word_id",
                "word",
            ]
            df_merged = df_rt.merge(
                df_eeg, on=merge_cols, how="inner", suffixes=("_rt", "_eeg")
            )

            merged_path = integration_dir / "zuco_kec_merged.parquet"
            df_merged.to_parquet(merged_path, index=False)
            logger.info(f"Saved merged compatibility view: {merged_path}")

    except Exception as e:
        logger.error(f"Failed to create merged view: {e}")

    # Coverage report: proportion of tokens with non-null KEC metrics (RT + EEG)
    coverage_rows: List[Dict[str, object]] = []
    try:
        for f in list(integration_dir.glob("*kec_rt.parquet")) + list(
            integration_dir.glob("*kec_eeg.parquet")
        ):
            df = pd.read_parquet(f)
            total = len(df)
            for metric in ["entropy", "curvature", "coherence"]:
                if metric in df.columns:
                    non_null = int(df[metric].notna().sum())
                    pct = (non_null / total * 100) if total else 0.0
                    coverage_rows.append(
                        {
                            "file": f.name,
                            "metric": metric,
                            "non_null": non_null,
                            "total": total,
                            "pct": pct,
                        }
                    )
        cov_df = pd.DataFrame(coverage_rows)
        cov_out = reports_dir / "kec_coverage_v4.4.csv"
        cov_df.to_csv(cov_out, index=False)
        logger.info(f"Saved coverage report: {cov_out}")
        for row in coverage_rows:
            logger.info(
                "KEC coverage %s %s: %d/%d (%.1f%%)"
                % (
                    row["file"],
                    row["metric"],
                    row["non_null"],
                    row["total"],
                    row["pct"],
                )
            )
    except Exception as e:  # noqa: BLE001
        logger.warning(f"Coverage report failed: {e}")

    # Provenance summary
    try:
        prov = {
            "pipeline": "SWOW-ZuCo v4.4 integrate",
            "version": "v4.4",
            "inputs": sorted(set(provenance_inputs)),
            "outputs": sorted(set(provenance_outputs)),
        }
        prov_out = reports_dir / "provenance_integration_v4.4.yaml"
        with open(prov_out, "w") as f:
            yaml.safe_dump(prov, f, sort_keys=False)
        logger.info(f"Saved provenance: {prov_out}")
    except Exception as e:  # noqa: BLE001
        logger.warning(f"Provenance write failed: {e}")

    # Memory log: append a human-friendly record of this integration run
    try:
        _append_integration_memory(
            reports_dir=reports_dir,
            methods_summary=methods_summary,
            coverage_rows=coverage_rows,
            outputs=provenance_outputs,
        )
    except Exception as e:  # noqa: BLE001
        logger.warning(f"Memory log write failed: {e}")

    # Also try to feed MCP Extended Memory API (optional, env-controlled)
    try:
        _post_integration_memory_to_mcp(
            methods_summary=methods_summary,
            coverage_rows=coverage_rows,
            outputs=provenance_outputs,
            step="integrate",
            version="v4.4",
        )
    except Exception as e:  # Extra safety; helper already guards exceptions
        logger.warning(f"MCP memory feed failed: {e}")


def _append_integration_memory(
    reports_dir: Path,
    methods_summary: List[str],
    coverage_rows: List[Dict[str, object]],
    outputs: List[str],
) -> None:
    """Append a persistent memory record for the integration run (MD + JSONL)."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    md_path = reports_dir / "integration_memory.md"
    jl_path = reports_dir / "integration_memory.jsonl"

    # Markdown entry
    lines: List[str] = []
    lines.append(f"\n### {ts} — integrate")
    lines.append("\nMétodos utilizados:")
    for m in methods_summary:
        lines.append(f"- {m}")
    if outputs:
        lines.append("\nArtefatos gerados:")
        for o in sorted(set(outputs)):
            lines.append(f"- {o}")
    if coverage_rows:
        # Compact snapshot (primeiras 10 linhas)
        lines.append("\nSnapshot de cobertura (top 10):")
        for row in coverage_rows[:10]:
            lines.append(
                (
                    f"- {row.get('file')} {row.get('metric')}: "
                    f"{row.get('non_null')}/{row.get('total')} "
                    f"({row.get('pct'):.1f}%)"
                )
            )
    with open(md_path, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    # JSONL entry
    try:
        import json

        rec = {
            "timestamp": ts,
            "step": "integrate",
            "methods": methods_summary,
            "outputs": sorted(set(outputs)),
            "coverage": coverage_rows[:50],  # bound size
        }
        with open(jl_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception as e:  # noqa: BLE001
        logger.warning(f"JSONL memory write failed: {e}")


def _post_integration_memory_to_mcp(
    methods_summary: List[str],
    coverage_rows: List[Dict[str, object]],
    outputs: List[str],
    step: str = "integrate",
    version: str = "v4.4",
) -> None:
    """Optionally POST a compact memory record to the local MCP Extended Memory API.

    Behavior:
    - Attempts to POST to /memory/store/project on the RAG++ web server.
    - Controlled via env MCP_FEED (defaults to on). Set MCP_FEED=0 to disable.
    - Base URL from RAG_BASE_URL or RAG_HOST/RAG_PORT (defaults http://127.0.0.1:8000).
    - Fails silently with a warning; never raises.
    """
    try:
        if str(os.getenv("MCP_FEED", "1")).strip().lower() in (
            "0",
            "false",
            "no",
        ):  # opt-out
            logger.info("MCP memory feed disabled (MCP_FEED=0)")
            return

        if _url is None:
            logger.warning("urllib not available; skipping MCP memory POST")
            return

        base_url = os.getenv("RAG_BASE_URL")
        if not base_url:
            host = os.getenv("RAG_HOST", "127.0.0.1").strip()
            port = os.getenv("RAG_PORT", "8000").strip()
            scheme = os.getenv("RAG_SCHEME", "http").strip()
            base_url = f"{scheme}://{host}:{port}"
        endpoint = f"{base_url}/memory/store/project"

        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Build a concise content string for human recall
        cov_lines: List[str] = []
        for row in coverage_rows[:10]:
            try:
                cov_lines.append(
                    (
                        f"- {row.get('file')} {row.get('metric')}: "
                        f"{row.get('non_null')}/{row.get('total')} "
                        f"({row.get('pct'):.1f}%)"
                    )
                )
            except Exception:
                # Fallback if fields missing
                cov_lines.append(f"- {row}")
        content_lines: List[str] = []
        content_lines.append(f"[{ts}] step={step} version={version}")
        content_lines.append("Methods:")
        if methods_summary:
            content_lines.extend(f"- {m}" for m in methods_summary)
        else:
            content_lines.append("(none)")
        if cov_lines:
            content_lines.append("Coverage (top10):")
            content_lines.extend(cov_lines)
        content = "\n".join(content_lines)

        payload = {
            "project_name": os.getenv("PROJECT_NAME", "pcs-meta-repo"),
            "context_type": f"{step}_memory",
            "content": content,
            "metadata": {
                "step": step,
                "version": version,
                "timestamp": ts,
                "outputs": sorted(set(outputs)),
                "coverage": coverage_rows[:50],
                "tags": ["integration", version, step],
            },
        }

        data = json.dumps(payload).encode("utf-8")  # type: ignore[name-defined]
        req = _url.Request(  # type: ignore[union-attr]
            endpoint,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with _url.urlopen(req, timeout=float(os.getenv("MCP_TIMEOUT", "3"))):  # type: ignore[union-attr]
            logger.info("Posted integration memory to MCP: %s", endpoint)
    except Exception as e:  # noqa: BLE001
        # Be quiet in CI/offline; only warn once per run context
        logger.warning(f"MCP memory POST failed: {e}")


def run_models_rt(config: Dict[str, Any]) -> None:
    """Run RT prediction models"""
    logger.info(
        "Running RT/ET models: Spearman corr (exact if SciPy) with per-dataset FDR"
    )

    reports_dir = Path(config["data"]["reports"]) / "v4.4"
    reports_dir.mkdir(parents=True, exist_ok=True)
    integration_dir = Path(config["data"]["processed"]) / "v4.4" / "integration"

    def _is_numeric_series(s: pd.Series) -> bool:
        return pd.api.types.is_numeric_dtype(s)

    def _candidate_rt_cols(df: DataFrame) -> List[str]:
        # Heuristic: typical RT/ET duration columns
        candidates_patterns = [
            "rt",
            "reaction",
            "response",
            "latency",
            "time",
            "duration",
            "gaze",
            "fix",
            "first_pass",
            "go_past",
            "trt",
        ]
        avoid = set(
            [
                "length",
                "position",
                "word_id",
                "sent_id",
                "doc_id",
                "subject_id",
                "task_id",
                "entropy",
                "curvature",
                "coherence",
                "out_degree",
                "total_weight",
            ]
        )
        cols: List[str] = []
        for c in df.columns:
            lc = str(c).lower()
            if c in avoid:
                continue
            if any(pat in lc for pat in candidates_patterns) and _is_numeric_series(
                df[c]
            ):
                if df[c].nunique(dropna=True) >= 10:
                    cols.append(c)
        return cols

    def _rank_corr_and_p(x: pd.Series, y: pd.Series) -> Tuple[float, float, int]:
        """Compute Spearman correlation and p-value.

        - Uses SciPy's exact method if available.
        - Falls back to Pearson on ranks with normal approx p-value.
        """
        s = pd.concat([x, y], axis=1).dropna()
        n = len(s)
        if n < 3:
            return (np.nan, np.nan, n)
        if _scipy_spearmanr is not None:
            try:
                r, p = _scipy_spearmanr(s.iloc[:, 0], s.iloc[:, 1])  # type: ignore[misc]
                return (float(r), float(p), n)
            except Exception:
                pass
        # Fallback: Pearson on ranks + normal approx p
        xr = s.iloc[:, 0].rank(method="average")
        yr = s.iloc[:, 1].rank(method="average")
        r = np.corrcoef(xr, yr)[0, 1]
        if np.isfinite(r) and abs(r) < 1 and n > 3:
            t = r * sqrt((n - 2) / max(1e-12, (1 - r * r)))
            try:
                from math import erf

                z = abs(t)
                p = 2 * (1 - 0.5 * (1 + erf(z / sqrt(2))))
            except Exception:
                p = np.nan
        else:
            p = np.nan
        return (float(r), float(p), n)

    def _bh_fdr(pvals: List[Optional[float]]) -> List[Optional[float]]:
        """Benjamini-Hochberg FDR, stable and NaN-aware."""
        indexed = []
        for i, p in enumerate(pvals):
            if p is None or not np.isfinite(p):
                continue
            indexed.append((i, max(1e-300, float(p))))  # clamp tiny p
        if not indexed:
            return [None for _ in pvals]
        indexed.sort(key=lambda t: t[1])
        m = len(indexed)
        qvals = [None for _ in pvals]
        prev_q = 1.0
        for rank, (i, p) in enumerate(indexed, start=1):
            q = min(prev_q, p * m / rank)
            qvals[i] = q
            prev_q = q
        return qvals

    def _apply_fdr_per_group(
        rows: List[Dict[str, Any]], group_key: str = "file"
    ) -> None:
        """Apply BH-FDR per dataset/file family in-place."""
        # Group row indices by key
        groups: Dict[str, List[int]] = {}
        for idx, row in enumerate(rows):
            k = str(row.get(group_key, ""))
            groups.setdefault(k, []).append(idx)
        # Compute per-group q-values
        for k, idxs in groups.items():
            pvals = [rows[i].get("p") for i in idxs]
            qvals = _bh_fdr(
                [
                    float(p) if (p is not None and np.isfinite(p)) else None
                    for p in pvals
                ]
            )
            for i, q in zip(idxs, qvals):
                rows[i]["q_fdr"] = q

    rows: List[Dict[str, Any]] = []
    methods: List[str] = [
        (
            "Per-dataset Spearman rank correlation (SciPy exact when available) "
            "between RT/ET measures and KEC metrics (entropy, curvature, coherence)."
        ),
        (
            "Multiple DVs auto-detected via column name heuristics (rt, gaze, "
            "fix, duration, trt)."
        ),
        ("BH-FDR correction applied per dataset/file family."),
        (
            "Controls not included in correlation; advise using mixed models "
            "separately if needed."
        ),
    ]

    for f in integration_dir.glob("*_kec_rt.parquet"):
        try:
            df = pd.read_parquet(f)
        except Exception as e:
            logger.warning("Failed to read %s: %s", f.name, e)
            continue
        if len(df) == 0:
            continue
        # prepare covariates
        if "length" not in df.columns:
            try:
                df["length"] = df["word"].astype(str).str.len()
            except Exception:
                df["length"] = np.nan
        dv_cols = _candidate_rt_cols(df)
        if not dv_cols:
            logger.info("No RT/ET DV detected in %s; skipping", f.name)
            continue
        metrics = [c for c in ["entropy", "curvature", "coherence"] if c in df.columns]
        if not metrics:
            logger.info("No KEC metrics found in %s; skipping", f.name)
            continue
        for dv in dv_cols:
            for mcol in metrics:
                r, p, n = _rank_corr_and_p(df[dv], df[mcol])
                rows.append(
                    {
                        "file": f.name,
                        "dataset": f.stem.replace("_kec_rt", ""),
                        "dv": dv,
                        "metric": mcol,
                        "n": n,
                        "r_spearman": r,
                        "p": p,
                        "method": "spearman",
                    }
                )

    # Apply FDR per file/dataset family and also per (file,dv)
    if rows:
        _apply_fdr_per_group(rows, group_key="file")
        groups2: Dict[Tuple[str, str], List[int]] = {}
        for idx, row in enumerate(rows):
            k2 = (str(row.get("file", "")), str(row.get("dv", "")))
            groups2.setdefault(k2, []).append(idx)
        for _, idxs in groups2.items():
            pvals2: List[Optional[float]] = []
            for i in idxs:
                p = rows[i].get("p")
                pvals2.append(float(p) if (p is not None and np.isfinite(p)) else None)
            qvals2 = _bh_fdr(pvals2)
            for i, q in zip(idxs, qvals2):
                rows[i]["q_fdr_by_dv"] = q

    # Save CSV summary
    out_csv = reports_dir / "models_rt_summary_v4.4.csv"
    try:
        pd.DataFrame(rows).to_csv(out_csv, index=False)
        logger.info("Saved RT/ET models summary: %s", out_csv)
    except Exception as e:
        logger.warning("Failed to write RT models summary: %s", e)

    # Memory log and MCP posting
    try:
        _append_step_memory(
            reports_dir=reports_dir,
            step="models_rt",
            methods_summary=methods,
            results_rows=rows[:50],
            outputs=[str(out_csv)],
        )
    except Exception as e:
        logger.warning("Models RT memory log failed: %s", e)
    try:
        _post_integration_memory_to_mcp(
            methods_summary=methods,
            coverage_rows=rows[:50],  # reuse structure field for brevity
            outputs=[str(out_csv)],
            step="models_rt",
            version="v4.4",
        )
    except Exception as e:
        logger.warning("Models RT MCP feed failed: %s", e)


def run_models_eeg(config: Dict[str, Any]) -> None:
    """Run EEG prediction models"""
    logger.info(
        "Running EEG models: Spearman corr (exact if SciPy) with per-dataset FDR"
    )

    reports_dir = Path(config["data"]["reports"]) / "v4.4"
    reports_dir.mkdir(parents=True, exist_ok=True)
    integration_dir = Path(config["data"]["processed"]) / "v4.4" / "integration"

    def _eeg_dv_cols(df: DataFrame) -> List[str]:
        cols: List[str] = []
        for c in df.columns:
            lc = str(c).lower()
            if lc.startswith("eeg_") or any(
                b in lc for b in ["theta", "alpha", "beta", "gamma"]
            ):
                if pd.api.types.is_numeric_dtype(df[c]):
                    cols.append(c)
        return cols

    def _rank_corr_and_p(x: pd.Series, y: pd.Series) -> Tuple[float, float, int]:
        s = pd.concat([x, y], axis=1).dropna()
        n = len(s)
        if n < 3:
            return (np.nan, np.nan, n)
        if _scipy_spearmanr is not None:
            try:
                r, p = _scipy_spearmanr(s.iloc[:, 0], s.iloc[:, 1])  # type: ignore[misc]
                return (float(r), float(p), n)
            except Exception:
                pass
        xr = s.iloc[:, 0].rank(method="average")
        yr = s.iloc[:, 1].rank(method="average")
        r = np.corrcoef(xr, yr)[0, 1]
        if np.isfinite(r) and abs(r) < 1 and n > 3:
            t = r * sqrt((n - 2) / max(1e-12, (1 - r * r)))
            try:
                from math import erf

                z = abs(t)
                p = 2 * (1 - 0.5 * (1 + erf(z / sqrt(2))))
            except Exception:
                p = np.nan
        else:
            p = np.nan
        return (float(r), float(p), n)

    def _bh_fdr(pvals: List[Optional[float]]) -> List[Optional[float]]:
        indexed = []
        for i, p in enumerate(pvals):
            if p is None or not np.isfinite(p):
                continue
            indexed.append((i, max(1e-300, float(p))))
        if not indexed:
            return [None for _ in pvals]
        indexed.sort(key=lambda t: t[1])
        m = len(indexed)
        qvals = [None for _ in pvals]
        prev_q = 1.0
        for rank, (i, p) in enumerate(indexed, start=1):
            q = min(prev_q, p * m / rank)
            qvals[i] = q
            prev_q = q
        return qvals

    rows: List[Dict[str, Any]] = []
    methods: List[str] = [
        (
            "Per-dataset Spearman rank correlation (SciPy exact when available) "
            "between EEG band power and KEC metrics (entropy, curvature, coherence)."
        ),
        (
            "EEG DVs auto-detected via columns starting with 'eeg_' or "
            "containing theta/alpha/beta/gamma."
        ),
        ("BH-FDR correction applied per dataset/file family."),
    ]

    for f in integration_dir.glob("*_kec_eeg.parquet"):
        try:
            df = pd.read_parquet(f)
        except Exception as e:
            logger.warning("Failed to read %s: %s", f.name, e)
            continue
        if len(df) == 0:
            continue
        dv_cols = _eeg_dv_cols(df)
        metrics = [c for c in ["entropy", "curvature", "coherence"] if c in df.columns]
        if not dv_cols or not metrics:
            logger.info("No EEG DVs or KEC metrics in %s; skipping", f.name)
            continue
        for dv in dv_cols:
            for mcol in metrics:
                r, p, n = _rank_corr_and_p(df[dv], df[mcol])
                rows.append(
                    {
                        "file": f.name,
                        "dataset": f.stem.replace("_kec_eeg", ""),
                        "dv": dv,
                        "metric": mcol,
                        "n": n,
                        "r_spearman": r,
                        "p": p,
                        "method": "spearman",
                    }
                )

    if rows:
        # Apply per-file FDR and per (file,dv)
        groups: Dict[str, List[int]] = {}
        for idx, row in enumerate(rows):
            k = str(row.get("file", ""))
            groups.setdefault(k, []).append(idx)
        for _, idxs in groups.items():
            pvals: List[Optional[float]] = []
            for i in idxs:
                p = rows[i].get("p")
                pvals.append(float(p) if (p is not None and np.isfinite(p)) else None)
            qvals = _bh_fdr(pvals)
            for i, q in zip(idxs, qvals):
                rows[i]["q_fdr"] = q

        groups2: Dict[Tuple[str, str], List[int]] = {}
        for idx, row in enumerate(rows):
            k2 = (str(row.get("file", "")), str(row.get("dv", "")))
            groups2.setdefault(k2, []).append(idx)
        for _, idxs in groups2.items():
            pvals2: List[Optional[float]] = []
            for i in idxs:
                p = rows[i].get("p")
                pvals2.append(float(p) if (p is not None and np.isfinite(p)) else None)
            qvals2 = _bh_fdr(pvals2)
            for i, q in zip(idxs, qvals2):
                rows[i]["q_fdr_by_dv"] = q


def run_surprisal(config: Dict[str, Any]) -> None:
    """Compute per-token surprisal for integrated RT datasets.

    Strategy:
    - If KenLM is available and KENLM_MODEL_{LANG} is set, compute sentence-
      conditioned surprisal with stateful scoring.
        - Optionally, if TRF_SURPRISAL=1 and transformers are available, compute
            transformer-based surprisal ('surprisal_trf') via a local HuggingFace
            model (per-sentence forward, token-level logprobs aggregated to words).
        - Else, compute a unigram proxy surprisal: -log2((count+1)/(N+V)).
        Saves back to the same parquet files by adding a 'surprisal' column and,
        when enabled, a 'surprisal_trf' column.
    """
    logger.info("Computing surprisal for integrated RT datasets")

    integration_dir = Path(config["data"]["processed"]) / "v4.4" / "integration"

    # Load KenLM models per language if available
    kenlm_models: Dict[str, Any] = {}
    if _kenlm is not None:
        for lang in ("en", "nl", "es", "zh"):
            env_key = f"KENLM_MODEL_{lang.upper()}"
            path = os.getenv(env_key)
            if path and Path(path).exists():
                try:
                    kenlm_models[lang] = _kenlm.Model(path)
                    logger.info("Loaded KenLM model for %s from %s", lang, path)
                except Exception as e:  # noqa: BLE001
                    logger.warning("Failed to load KenLM for %s: %s", lang, e)

    def _pos_col(df: DataFrame) -> Optional[str]:
        for c in ["word_pos", "word_position", "position", "word_id", "token_id"]:
            if c in df.columns and pd.api.types.is_numeric_dtype(df[c]):
                return c
        return None

    def _sentence_keys(df: DataFrame) -> List[str]:
        keys: List[str] = []
        for c in ["subject_id", "doc_id", "sent_id", "sentence_id", "trial_id"]:
            if c in df.columns:
                keys.append(c)
        # Require at least one boundary; else single group
        return keys if keys else []

    def _normalize_word_series(s: pd.Series, lang: str) -> pd.Series:
        s = s.astype(str).str.strip().str.lower()
        if lang in ("en", "es", "nl"):
            return (
                s.apply(
                    lambda x: unicodedata.normalize("NFKD", x)
                    .encode("ascii", "ignore")
                    .decode("ascii")
                )
                .str.findall(r"[a-z]{2,}")
                .apply(lambda xs: xs[0] if xs else "")
            )
        return s

    def _surprisal_unigram(df: DataFrame) -> pd.Series:
        # Laplace-smoothed unigram surprisal by language within file
        w = df["word"].astype(str).str.lower()
        counts = w.value_counts()
        N = float(len(w))
        V = float(len(counts))
        probs = (w.map(counts).astype(float) + 1.0) / max(1.0, (N + V))
        with np.errstate(divide="ignore"):
            return -np.log2(probs)

    def _surprisal_kenlm(df: DataFrame, lang: str) -> pd.Series:
        model = kenlm_models.get(lang)
        if model is None:
            return _surprisal_unigram(df)
        pos = _pos_col(df)
        keys = _sentence_keys(df)
        if not keys:
            # fall back to a single stream
            giter = [(None, df.copy())]
        else:
            giter = df.groupby(keys, dropna=False)
        out = np.full(len(df), np.nan, dtype=float)
        # stable index order
        for _, g in giter:
            gg = g.copy()
            if pos and pos in gg.columns:
                gg = gg.sort_values(pos)
            words = _normalize_word_series(gg["word"], lang).tolist()
            idxs = gg.index.to_list()
            # stateful scoring
            try:
                state = _kenlm.State()
                model.BeginSentenceWrite(state)
                for i, w in enumerate(words):
                    state2 = _kenlm.State()
                    lp10 = model.BaseScore(state, w or "<unk>", state2)
                    # surprisal bits = -log2 p = -log10 p / log10(2)
                    sp = -lp10 / np.log10(2.0)
                    out[list(range(len(out)))[idxs[i]]] = float(sp)
                    state = state2
            except Exception:
                # fallback to unigram for this group
                out[idxs] = _surprisal_unigram(gg).to_numpy()
        return pd.Series(out, index=df.index)

    # Optional: transformer-based surprisal using HuggingFace (disabled by default)
    def _surprisal_transformer(df: DataFrame, lang: str) -> Optional[pd.Series]:
        """Compute per-word surprisal (bits) with a local HF causal LM.

        Environment:
        - TRF_SURPRISAL=1 to enable (default off)
        - TRF_MODEL_ID (e.g., 'gpt2')
        - TRF_DEVICE ('cuda' or 'cpu')
        - TRF_MAX_TOKENS (cap per sentence; default 512)
        """
        try:
            if str(os.getenv("TRF_SURPRISAL", "0")).strip() not in (
                "1",
                "true",
                "True",
            ):
                return None
            # Lazy import to keep dependency optional
            import torch  # type: ignore
            from transformers import AutoModelForCausalLM, AutoTokenizer  # type: ignore

            model_id = os.getenv("TRF_MODEL_ID", "gpt2").strip()
            device = os.getenv(
                "TRF_DEVICE",
                ("cuda" if torch.cuda.is_available() else "cpu"),
            )
            max_toks = int(os.getenv("TRF_MAX_TOKENS", "512"))

            tokenizer = AutoTokenizer.from_pretrained(model_id)
            # Ensure no BOS/EOS added automatically for causal LMs
            kwargs = {"device_map": None}
            model = AutoModelForCausalLM.from_pretrained(
                model_id,
                torch_dtype=None,
                low_cpu_mem_usage=True,
                **kwargs,
            )
            model.eval()
            model.to(device)

            keys = _sentence_keys(df)
            pos = _pos_col(df)
            if not keys:
                groups = [(None, df.copy())]
            else:
                groups = list(df.groupby(keys, dropna=False))

            out = np.full(len(df), np.nan, dtype=float)

            def _word_char_spans(words: List[str]) -> List[Tuple[int, int]]:
                spans: List[Tuple[int, int]] = []
                cur = 0
                for w in words:
                    start = cur
                    end = start + len(w)
                    spans.append((start, end))
                    cur = end + 1  # plus one space
                return spans

            with torch.no_grad():
                for _, g in groups:
                    gg = g.copy()
                    if pos and pos in gg.columns:
                        gg = gg.sort_values(pos)
                    words = _normalize_word_series(gg["word"], lang).tolist()
                    # Build sentence as space-joined words
                    sent = " ".join(words)
                    if not sent:
                        continue
                    enc = tokenizer(
                        sent,
                        return_tensors="pt",
                        add_special_tokens=False,
                        return_offsets_mapping=True,
                    )
                    input_ids = enc["input_ids"].to(device)
                    # Cap very long sequences
                    if input_ids.shape[1] > max_toks:
                        input_ids = input_ids[:, :max_toks]
                    # Forward
                    out_logits = model(input_ids).logits  # [1, L, V]
                    # Shift for next-token prediction
                    log_probs = out_logits.log_softmax(dim=-1)
                    # Gather token log probs at positions 1..L-1
                    tok_ids = input_ids[:, 1:]
                    tok_lp = torch.gather(
                        log_probs[:, :-1, :],
                        2,
                        tok_ids.unsqueeze(-1),
                    ).squeeze(-1)  # [1, L-1]
                    # Map tokens to words via offsets
                    offsets = enc.get("offset_mapping")
                    if offsets is None:
                        # Without offsets, fallback to unigram for this group
                        vals = _surprisal_unigram(gg).to_numpy()
                        out[gg.index.to_numpy()] = vals
                        continue
                    offsets = offsets[0].tolist()
                    word_spans = _word_char_spans(words)
                    # token positions we kept (consider cap)
                    kept = min(len(offsets), int(tok_lp.shape[1]) + 1)
                    # Accumulate per word sum of -log2 p(token)
                    w_bits = [0.0 for _ in words]
                    for ti in range(1, kept):  # skip token 0 (no previous token)
                        o = offsets[ti]
                        if o is None or o == (None, None):
                            continue
                        t_start = int(o[0])
                        # find word whose span covers token start
                        # naive linear scan; sentences are short
                        wi = None
                        for idx_w, (ws, we) in enumerate(word_spans):
                            if ws <= t_start < we:
                                wi = idx_w
                                break
                        if wi is None:
                            continue
                        lp = float(tok_lp[0, ti - 1].detach().cpu())
                        # surprisal bits = -log2 p
                        w_bits[wi] += -lp / np.log(2.0)
                    # Write back to rows
                    idxs = gg.index.to_list()
                    for i_local, idx_row in enumerate(idxs):
                        if i_local < len(w_bits):
                            out[list(range(len(out)))[idx_row]] = float(w_bits[i_local])

            return pd.Series(out, index=df.index)
        except Exception as e:  # noqa: BLE001
            logger.info("Transformer surprisal disabled or failed: %s", e)
            return None

    changed: List[str] = []
    for f in integration_dir.glob("*_kec_rt.parquet"):
        try:
            df = pd.read_parquet(f)
        except Exception as e:  # noqa: BLE001
            logger.warning("Failed to read %s: %s", f.name, e)
            continue
        if len(df) == 0 or "word" not in df.columns:
            continue
        # language heuristic
        lang = None
        if "lang" in df.columns:
            vals = df["lang"].dropna().astype(str).unique()
            lang = vals[0] if len(vals) == 1 else None
        if lang is None:
            # infer by dataset name
            ln = f.name.lower()
            if "geco" in ln:
                lang = "nl"
            elif "onestop" in ln or "zuco" in ln:
                lang = "en"
        lang = (lang or "en").lower()
        # choose path
        if lang in kenlm_models:
            s = _surprisal_kenlm(df, lang)
        else:
            s = _surprisal_unigram(df)
        df["surprisal"] = pd.to_numeric(s, errors="coerce")
        # Optional transformer surprisal
        s_trf = _surprisal_transformer(df, lang)
        if s_trf is not None:
            df["surprisal_trf"] = pd.to_numeric(s_trf, errors="coerce")
        try:
            df.to_parquet(f, index=False)
            changed.append(f.name)
            logger.info("Wrote surprisal into %s (%d rows)", f.name, len(df))
        except Exception as e:  # noqa: BLE001
            logger.warning("Failed to write surprisal to %s: %s", f.name, e)

    reports_dir = Path(config["data"]["reports"]) / "v4.4"
    try:
        _append_step_memory(
            reports_dir=reports_dir,
            step="surprisal",
            methods_summary=[
                (
                    "KenLM per-token surprisal when available; transformer surprisal "
                    "when TRF_SURPRISAL=1; unigram proxy otherwise"
                ),
                (
                    "KenLM: sentence-conditioned stateful scoring; Transformer: per-"
                    "sentence forward with token logprobs aggregated to words; bits "
                    "as units"
                ),
            ],
            results_rows=[{"file": n} for n in changed][:50],
            outputs=[str(integration_dir / name) for name in changed],
        )
    except Exception as e:  # noqa: BLE001
        logger.warning("Surprisal memory log failed: %s", e)
    try:
        _post_integration_memory_to_mcp(
            methods_summary=[
                (
                    "KenLM per-token surprisal; optional Transformer surprisal "
                    "(TRF_SURPRISAL=1); unigram proxy otherwise"
                )
            ],
            coverage_rows=[{"file": n} for n in changed][:50],
            outputs=[str(integration_dir / name) for name in changed],
            step="surprisal",
            version="v4.4",
        )
    except Exception as e:  # noqa: BLE001
        logger.warning("Surprisal MCP feed failed: %s", e)


def run_models_mixed(config: Dict[str, Any]) -> None:
    """Run mixed-effects models for GECO and ZuCo with controls and random effects.

    Predictors: KEC metrics + controls (length, position, frequency, surprisal*).
    Random intercepts for subject; item variance component when feasible. Sampling
    cap per fit via env MIXED_MAX_N (default 15000).

    * Surprisal control preference: surprisal_trf (if computed) else surprisal.
    """

    if smf is None:
        logger.warning("statsmodels not available; skipping mixed models")
        return

    reports_dir = Path(config["data"]["reports"]) / "v4.4"
    reports_dir.mkdir(parents=True, exist_ok=True)
    integration_dir = Path(config["data"]["processed"]) / "v4.4" / "integration"

    candidates = [
        integration_dir / "geco_et_kec_rt.parquet",
        integration_dir / "zuco_kec_rt.parquet",
    ]

    def _detect_subject_col(df: DataFrame) -> Optional[str]:
        for c in ["subject_id", "participant", "subj", "subject"]:
            if c in df.columns:
                return c
        return None

    def _detect_position_col(df: DataFrame) -> Optional[str]:
        # Prefer numeric position-like columns
        for c in ["word_pos", "word_position", "position", "word_id"]:
            if c in df.columns and pd.api.types.is_numeric_dtype(df[c]):
                return c
        # if none numeric, try to coerce 'word_id' if present
        if "word_id" in df.columns:
            try:
                coerced = pd.to_numeric(df["word_id"], errors="coerce")
                if coerced.notna().any():
                    df["word_id"] = coerced
                    return "word_id"
            except Exception:
                pass
        return None

    def _detect_freq_col(df: DataFrame) -> Optional[str]:
        for c in df.columns:
            lc = str(c).lower()
            if "freq" in lc and pd.api.types.is_numeric_dtype(df[c]):
                return c
        return None

    def _ensure_controls(df: DataFrame) -> DataFrame:
        d = df.copy()
        if "length" not in d.columns:
            try:
                d["length"] = d["word"].astype(str).str.len()
            except Exception:
                d["length"] = np.nan
        # frequency fallback
        if _detect_freq_col(d) is None and "word" in d.columns:
            try:
                vc = d["word"].astype(str).value_counts()
                d = d.join(vc.rename("freq_local"), on="word")
            except Exception:
                d["freq_local"] = np.nan
        return d

    def _dv_candidates(df: DataFrame) -> List[str]:
        preferred = ["first_pass", "go_past", "trt", "gaze", "gaze_ms"]
        out: List[str] = []
        for p in preferred:
            if p in df.columns and pd.api.types.is_numeric_dtype(df[p]):
                out.append(p)
        if not out:
            pats = ["rt", "gaze", "fix", "duration", "trt"]
            for c in df.columns:
                lc = str(c).lower()
                if any(p in lc for p in pats) and pd.api.types.is_numeric_dtype(df[c]):
                    if df[c].nunique(dropna=True) >= 10:
                        out.append(c)
        return out[:3]

    rows: List[Dict[str, Any]] = []
    methods: List[str] = [
        (
            "Mixed-effects models: DV ~ KEC + length + position + frequency + "
            "surprisal?; random intercepts for subject; item variance component "
            "when possible."
        ),
        (
            "Controls included: length (token length), optional position and "
            "frequency (auto-detected or fallback local frequency), plus surprisal "
            "(surprisal_trf if available else surprisal)."
        ),
        ("Benjamini-Hochberg FDR applied per dataset/file and per (file, DV)."),
    ]
    max_n = int(os.getenv("MIXED_MAX_N", "15000"))

    def _ols_coef_and_se(
        y: np.ndarray, X: np.ndarray, col_index: int
    ) -> Tuple[float, float]:
        """Compute OLS coefficient and standard error for column at col_index.

        Uses normal equations with pseudo-inverse for stability. Returns (beta, se).
        If computation fails or df <= p, returns (nan, nan).
        """
        try:
            n, p = X.shape
            if n <= p + 1:
                return (float("nan"), float("nan"))
            XtX = X.T @ X
            try:
                XtX_inv = np.linalg.pinv(XtX)
            except Exception:
                return (float("nan"), float("nan"))
            beta = XtX_inv @ (X.T @ y)
            y_hat = X @ beta
            resid = y - y_hat
            dof = max(1, n - p)
            s2 = float((resid.T @ resid) / dof)
            var_beta = s2 * XtX_inv
            b = float(beta[col_index])
            se = float(np.sqrt(max(0.0, var_beta[col_index, col_index])))
            if not np.isfinite(b) or not np.isfinite(se):
                return (float("nan"), float("nan"))
            return (b, se)
        except Exception:
            return (float("nan"), float("nan"))

    def _meta_random_effects(
        betas: List[float], ses: List[float]
    ) -> Tuple[float, float, int, float]:
        """DerSimonian-Laird random-effects meta-analysis.

        Returns (beta_RE, se_RE, k, tau2). Filters out NaNs and zero SEs.
        """
        vals = [
            (b, s)
            for b, s in zip(betas, ses)
            if np.isfinite(b) and np.isfinite(s) and s > 0
        ]
        k = len(vals)
        if k == 0:
            return (float("nan"), float("nan"), 0, float("nan"))
        b_arr = np.array([b for b, _ in vals], dtype=float)
        s_arr = np.array([s for _, s in vals], dtype=float)
        w = 1.0 / (s_arr**2)
        w_sum = float(w.sum())
        beta_fe = float((w * b_arr).sum() / max(1e-12, w_sum))
        Q = float((w * (b_arr - beta_fe) ** 2).sum())
        df_k = max(1, k - 1)
        C = w_sum - float(((w**2).sum()) / max(1e-12, w_sum))
        tau2 = max(0.0, (Q - df_k) / max(1e-12, C))
        w_star = 1.0 / (s_arr**2 + tau2)
        w_star_sum = float(w_star.sum())
        beta_re = float((w_star * b_arr).sum() / max(1e-12, w_star_sum))
        se_re = float(np.sqrt(1.0 / max(1e-12, w_star_sum)))
        return (beta_re, se_re, k, tau2)

    for f in candidates:
        if not f.exists():
            continue
        try:
            df = pd.read_parquet(f)
        except Exception as e:  # noqa: BLE001
            logger.warning("Failed to read %s: %s", f.name, e)
            continue
        if len(df) == 0:
            continue
        is_geco = "geco" in f.name.lower()
        if is_geco and os.getenv("MIXED_INCLUDE_GECO", "0") != "1":
            logger.info(
                "Skipping GECO in mixed models (set MIXED_INCLUDE_GECO=1 to include)"
            )
            continue
        # If no clear DV columns (e.g., GECO time-sampled rows), aggregate to per-word
        tmp_check = df.copy()
        subj_col = _detect_subject_col(tmp_check)
        dv_probe = _dv_candidates(tmp_check)
        if (
            not dv_probe
            and {
                "timestamp",
                "fixation_duration",
                "word",
            }.issubset(set(tmp_check.columns))
            and subj_col is not None
        ):
            try:
                group_cols = [subj_col]
                group_cols += [
                    c
                    for c in [
                        "doc_id",
                        "sent_id",
                        "word_id",
                        "word",
                    ]
                    if c in tmp_check.columns
                ]
                # aggregate per word: total gaze in ms and average KEC metrics
                agg_parts: Dict[str, str] = {}
                if "fixation_duration" in tmp_check.columns:
                    agg_parts["fixation_duration"] = "sum"
                for mc in ["entropy", "curvature", "coherence"]:
                    if mc in tmp_check.columns:
                        agg_parts[mc] = "mean"
                agg = (
                    tmp_check.groupby(group_cols, dropna=False)
                    .agg(agg_parts)
                    .reset_index()
                )
                if "fixation_duration" in agg.columns:
                    agg["gaze_ms"] = agg["fixation_duration"].astype(float)
                    agg = agg.drop(columns=["fixation_duration"])
                df = agg
                logger.info(
                    "Derived per-word GECO measures: %d rows with gaze_ms",
                    int(len(df)),
                )
            except Exception as e:  # noqa: BLE001
                logger.info(
                    (
                        "GECO aggregation fallback failed in %s: %s; "
                        "proceeding with original"
                    ),
                    f.name,
                    e,
                )

        df = _ensure_controls(df)
        subj_col = _detect_subject_col(df)
        if subj_col is None:
            logger.info("No subject column in %s; skipping mixed models", f.name)
            continue
        pos_col = _detect_position_col(df)
        freq_col = _detect_freq_col(df) or (
            "freq_local" if "freq_local" in df.columns else None
        )
        dvs = _dv_candidates(df)
        metrics = [c for c in ["entropy", "curvature", "coherence"] if c in df.columns]
        if not dvs or not metrics:
            logger.info("No DVs or KEC metrics in %s; skipping", f.name)
            continue

        # prepare item id (word as item)
        if "word" in df.columns:
            df["item_word"] = df["word"].astype(str)
        elif "word_id" in df.columns:
            df["item_word"] = df["word_id"].astype(str)
        else:
            df["item_word"] = "item"

        def _numeric_controls_list(
            base_df: DataFrame, base_controls: List[str]
        ) -> List[str]:
            out: List[str] = []
            for c in base_controls:
                if c in base_df.columns and pd.api.types.is_numeric_dtype(base_df[c]):
                    out.append(c)
            return out

        for dv in dvs:
            for mcol in metrics:
                controls_base: List[str] = ["length"]
                # Prefer transformer surprisal if present
                if "surprisal_trf" in df.columns:
                    controls_base.append("surprisal_trf")
                elif "surprisal" in df.columns:
                    controls_base.append("surprisal")
                if pos_col:
                    controls_base.append(pos_col)
                if freq_col:
                    controls_base.append(freq_col)
                # Keep only numeric controls to avoid casting errors
                controls = _numeric_controls_list(df, controls_base)

                if is_geco and os.getenv("MIXED_GECO_META", "1") == "1":
                    # Full-data subject-level OLS + random-effects meta-analysis (DL)
                    needed = [dv, mcol, subj_col] + controls
                    tmp_all = df[needed].dropna()
                    if len(tmp_all) < 200:
                        continue
                    betas: List[float] = []
                    ses: List[float] = []
                    n_subj_used = 0
                    # design labels (unused, kept here for clarity)
                    # p_cols = ["intercept", mcol] + [c for c in controls]
                    for sid, g in tmp_all.groupby(subj_col):
                        g = g.dropna()
                        if len(g) < (2 + len(controls)):
                            continue
                        # Design matrix with intercept
                        X_list = [
                            np.ones(len(g), dtype=float),
                            g[mcol].astype(float).to_numpy(),
                        ]
                        for c in controls:
                            X_list.append(g[c].astype(float).to_numpy())
                        X = np.vstack(X_list).T
                        y = g[dv].astype(float).to_numpy()
                        b, s = _ols_coef_and_se(y, X, col_index=1)  # mcol at idx 1
                        if np.isfinite(b) and np.isfinite(s) and s > 0:
                            betas.append(b)
                            ses.append(s)
                            n_subj_used += 1
                    beta_re, se_re, k, tau2 = _meta_random_effects(betas, ses)
                    if (
                        k == 0
                        or not np.isfinite(beta_re)
                        or not np.isfinite(se_re)
                        or se_re <= 0
                    ):
                        continue
                    z = beta_re / se_re
                    # two-sided normal p-value
                    from math import erf

                    p_val = float(2 * (1 - 0.5 * (1 + erf(abs(z) / np.sqrt(2)))))
                    rows.append(
                        {
                            "file": f.name,
                            "dataset": f.stem.replace("_kec_rt", ""),
                            "dv": dv,
                            "metric": mcol,
                            "term": mcol,
                            "n": int(len(tmp_all)),
                            "coef_metric": float(beta_re),
                            "coef": float(beta_re),
                            "|coef|": (
                                abs(float(beta_re)) if np.isfinite(beta_re) else np.nan
                            ),
                            "se_metric": float(se_re),
                            "z_approx": float(z),
                            "p": p_val,
                            "converged": True,
                            "controls": ",".join(controls),
                            "random_effects": (
                                f"meta(DL) over subjects k={k}, tau2={tau2:.4g}"
                            ),
                            "method": "meta_subjects",
                        }
                    )
                    continue

                # MixedLM path with sampling caps (non-GECO or explicitly requested)
                cols_needed = [dv, mcol, subj_col, "item_word", "length"]
                for c in controls:
                    if c not in cols_needed:
                        cols_needed.append(c)
                tmp = df[cols_needed].dropna()
                if len(tmp) < 200:
                    continue
                # Per-dataset cap (tighter for GECO)
                max_n_local = max_n
                if is_geco:
                    max_n_local = min(max_n, int(os.getenv("MIXED_MAX_N_GECO", "4000")))
                if len(tmp) > max_n_local:
                    tmp = tmp.sample(max_n_local, random_state=42)
                # Downcast to reduce memory
                for col in tmp.columns:
                    if pd.api.types.is_float_dtype(tmp[col]):
                        tmp[col] = tmp[col].astype("float32")

                rhs = " + ".join([mcol] + controls)
                formula = f"{dv} ~ {rhs}"

                converged = False
                p_val = np.nan
                coef = np.nan
                se = np.nan
                stat = np.nan
                # For very large N, prefer subject-only to reduce memory
                large_n = is_geco or (len(tmp) > 20000)
                if large_n:
                    method_note = "subject-only (large-N)"
                    try:
                        model = smf.mixedlm(
                            formula,
                            data=tmp,
                            groups=tmp[subj_col],
                        )
                        res = model.fit(method="lbfgs", maxiter=200)
                        converged = bool(getattr(res, "converged", False))
                        params = res.params
                        bse = res.bse
                        if mcol in params and mcol in bse:
                            coef = float(params[mcol])
                            se = float(bse[mcol])
                            if se > 0:
                                stat = coef / se
                            from math import erf

                            p_val = float(
                                2 * (1 - 0.5 * (1 + erf(abs(stat) / np.sqrt(2))))
                            )
                    except Exception as e2:  # noqa: BLE001
                        method_note = f"failed: {e2.__class__.__name__}"
                else:
                    method_note = "subject + item(vc)"
                    try:
                        model = smf.mixedlm(
                            formula,
                            data=tmp,
                            groups=tmp[subj_col],
                            vc_formula={"item": "0 + C(item_word)"},
                        )
                        res = model.fit(method="lbfgs", maxiter=200)
                        converged = bool(getattr(res, "converged", False))
                        params = res.params
                        bse = res.bse
                        if mcol in params and mcol in bse:
                            coef = float(params[mcol])
                            se = float(bse[mcol])
                            if se > 0:
                                stat = coef / se
                            # Wald z approx to p
                            from math import erf

                            p_val = float(
                                2 * (1 - 0.5 * (1 + erf(abs(stat) / np.sqrt(2))))
                            )
                    except Exception as e:  # noqa: BLE001
                        method_note = f"fallback-subject-only ({e.__class__.__name__})"
                        try:
                            model = smf.mixedlm(
                                formula,
                                data=tmp,
                                groups=tmp[subj_col],
                            )
                            res = model.fit(method="lbfgs", maxiter=200)
                            converged = bool(getattr(res, "converged", False))
                            params = res.params
                            bse = res.bse
                            if mcol in params and mcol in bse:
                                coef = float(params[mcol])
                                se = float(bse[mcol])
                                if se > 0:
                                    stat = coef / se
                                from math import erf

                                p_val = float(
                                    2 * (1 - 0.5 * (1 + erf(abs(stat) / np.sqrt(2))))
                                )
                        except Exception as e2:  # noqa: BLE001
                            method_note = f"failed: {e2.__class__.__name__}"

                rows.append(
                    {
                        "file": f.name,
                        "dataset": f.stem.replace("_kec_rt", ""),
                        "dv": dv,
                        "metric": mcol,
                        "term": mcol,
                        "n": int(len(tmp)),
                        "coef_metric": coef,
                        "coef": coef,
                        "|coef|": (abs(coef) if np.isfinite(coef) else np.nan),
                        "se_metric": se,
                        "z_approx": stat,
                        "p": p_val,
                        "converged": converged,
                        "controls": ",".join(controls),
                        "random_effects": method_note,
                        "method": "mixedlm",
                    }
                )

    # Apply FDR per file and per (file, dv)
    def _bh_fdr_mix(pvals: List[Optional[float]]) -> List[Optional[float]]:
        indexed: List[Tuple[int, float]] = []
        for i, p in enumerate(pvals):
            if p is None or not np.isfinite(p):
                continue
            indexed.append((i, max(1e-300, float(p))))
        if not indexed:
            return [None for _ in pvals]
        indexed.sort(key=lambda t: t[1])
        m = len(indexed)
        qvals: List[Optional[float]] = [None for _ in pvals]
        prev_q = 1.0
        for rank, (i, p) in enumerate(indexed, start=1):
            q = min(prev_q, p * m / rank)
            qvals[i] = q
            prev_q = q
        return qvals

    if rows:
        # Per-file
        groups: Dict[str, List[int]] = {}
        for idx, row in enumerate(rows):
            k = str(row.get("file", ""))
            groups.setdefault(k, []).append(idx)
        for _, idxs in groups.items():
            pvals: List[Optional[float]] = []
            for i in idxs:
                p = rows[i].get("p")
                pvals.append(float(p) if (p is not None and np.isfinite(p)) else None)
            qvals = _bh_fdr_mix(pvals)
            for i, q in zip(idxs, qvals):
                rows[i]["q_fdr"] = q

        # Per (file, dv)
        groups2: Dict[Tuple[str, str], List[int]] = {}
        for idx, row in enumerate(rows):
            k2 = (str(row.get("file", "")), str(row.get("dv", "")))
            groups2.setdefault(k2, []).append(idx)
        for _, idxs in groups2.items():
            pvals2: List[Optional[float]] = []
            for i in idxs:
                p = rows[i].get("p")
                pvals2.append(float(p) if (p is not None and np.isfinite(p)) else None)
            qvals2 = _bh_fdr_mix(pvals2)
            for i, q in zip(idxs, qvals2):
                rows[i]["q_fdr_by_dv"] = q

    out_csv = reports_dir / "models_mixed_summary_v4.4.csv"
    try:
        pd.DataFrame(rows).to_csv(out_csv, index=False)
        logger.info("Saved Mixed Models summary: %s", out_csv)
    except Exception as e:  # noqa: BLE001
        logger.warning("Failed to write Mixed Models summary: %s", e)

    try:
        _append_step_memory(
            reports_dir=reports_dir,
            step="models_mixed",
            methods_summary=methods,
            results_rows=rows[:50],
            outputs=[str(out_csv)],
        )
    except Exception as e:  # noqa: BLE001
        logger.warning("Models Mixed memory log failed: %s", e)
    try:
        _post_integration_memory_to_mcp(
            methods_summary=methods,
            coverage_rows=rows[:50],
            outputs=[str(out_csv)],
            step="models_mixed",
            version="v4.4",
        )
    except Exception as e:  # noqa: BLE001
        logger.warning("Models Mixed MCP feed failed: %s", e)

    # Done


def _append_step_memory(
    reports_dir: Path,
    step: str,
    methods_summary: List[str],
    results_rows: List[Dict[str, Any]],
    outputs: List[str],
) -> None:
    """Generic memory appender for steps other than integrate (MD + JSONL)."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    md_path = reports_dir / "integration_memory.md"
    jl_path = reports_dir / "integration_memory.jsonl"

    lines: List[str] = []
    lines.append(f"\n### {ts} — {step}")
    lines.append("\nMétodos utilizados:")
    for m in methods_summary:
        lines.append(f"- {m}")
    if outputs:
        lines.append("\nArtefatos gerados:")
        for o in sorted(set(outputs)):
            lines.append(f"- {o}")
    if results_rows:
        lines.append("\nSnapshot de resultados (top 10):")
        for row in results_rows[:10]:
            try:
                lines.append(
                    (
                        f"- {row.get('file')} {row.get('dv')}~{row.get('metric')}: "
                        f"r={row.get('r_spearman'):.3f}, p={row.get('p')}, "
                        f"q={row.get('q_fdr')} (n={row.get('n')})"
                    )
                )
            except Exception:
                lines.append(f"- {row}")
    with open(md_path, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    try:
        rec = {
            "timestamp": ts,
            "step": step,
            "methods": methods_summary,
            "outputs": sorted(set(outputs)),
            "results": results_rows[:50],
        }
        with open(jl_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception as e:
        logger.warning("JSONL step memory write failed: %s", e)


def main():
    parser = argparse.ArgumentParser(description="SWOW-ZuCo Pipeline v4.4")
    parser.add_argument(
        "--step",
        choices=[
            "tidy_rt",
            "tidy_eeg",
            "integrate",
            "surprisal",
            "models_rt",
            "models_eeg",
            "models",
            "models_mixed",
        ],
        required=True,
        help="Pipeline step to run",
    )
    parser.add_argument(
        "--datasets", help="Comma-separated list of datasets (for tidy steps)"
    )

    args = parser.parse_args()

    try:
        config = load_config()

        if args.step == "tidy_rt":
            if not args.datasets:
                logger.error("--datasets required for tidy_rt")
                sys.exit(1)
            tidy_rt_datasets(args.datasets.split(","), config)

        elif args.step == "tidy_eeg":
            if not args.datasets:
                logger.error("--datasets required for tidy_eeg")
                sys.exit(1)
            tidy_eeg_datasets(args.datasets.split(","), config)

        elif args.step == "integrate":
            integrate_kec_datasets(config)

        elif args.step == "surprisal":
            run_surprisal(config)

        elif args.step == "models_rt":
            run_models_rt(config)

        elif args.step == "models_eeg":
            run_models_eeg(config)

        elif args.step == "models":
            run_models_rt(config)
            run_models_eeg(config)

        elif args.step == "models_mixed":
            run_models_mixed(config)

        logger.info(f"Pipeline step '{args.step}' completed successfully")

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
