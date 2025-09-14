#!/usr/bin/env python3
"""
Gera um manifesto dos dados processados (v4.4):
- L1_tidy por dataset
- L2_derived/Kec por idioma
- processed/v4.4/integration
- SWOW L1 CSVs

Saídas:
- reports/v4.4/manifest_v4.4.csv
- reports/v4.4/manifest_v4.4.yaml

Notas:
- Tenta contar linhas com pandas quando viável; em falha, registra
    apenas tamanho e erro.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import yaml


def _rows_parquet(p: Path) -> int | str:
    try:
        return len(pd.read_parquet(p))
    except Exception as e:  # noqa: BLE001
        return f"ERR:{e}"  # muito grande ou lib ausente


def _rows_csv(p: Path) -> int | str:
    try:
        # leitura rápida só para contar
        return sum(1 for _ in p.open("r", encoding="utf-8", errors="ignore")) - 1
    except Exception as e:  # noqa: BLE001
        return f"ERR:{e}"


def gather_manifest(repo_root: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []

    def add_entry(path: Path, kind: str, dataset: str, note: str = "") -> None:
        exists = path.exists()
        size = os.path.getsize(path) if exists else 0
        mtime = (
            time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(path.stat().st_mtime))
            if exists
            else ""
        )
        count: int | str = ""
        if exists:
            if path.suffix == ".parquet":
                count = _rows_parquet(path)
            elif path.suffix == ".csv":
                count = _rows_csv(path)
        rows.append(
            {
                "kind": kind,
                "dataset": dataset,
                "rel_path": (
                    str(path.relative_to(repo_root))
                    if path.is_absolute()
                    else str(path)
                ),
                "exists": exists,
                "size_bytes": size,
                "rows": count,
                "modified": mtime,
                "note": note,
            }
        )

    data = repo_root / "data"
    reports = repo_root / "reports" / "v4.4"
    reports.mkdir(parents=True, exist_ok=True)

    # L1_tidy
    l1 = data / "L1_tidy"
    l1_targets = {
        "zuco_rt": l1 / "zuco_rt/word_events_rt.parquet",
        "geco_et": l1 / "geco_et/word_events_rt.parquet",
        "onestop_et": l1 / "onestop_et/word_events_rt.parquet",
        "zuco_eeg": l1 / "zuco_eeg/word_events_eeg.parquet",
        "derco_eeg": l1 / "derco_eeg/word_events_eeg.parquet",
        "lpp_eeg": l1 / "lpp_eeg/word_events_eeg.parquet",
    }
    for ds, p in l1_targets.items():
        add_entry(p, kind="L1_tidy", dataset=ds)

    # SWOW L1 CSVs
    swow = l1 / "swow"
    for lang in ["en", "es", "nl", "zh"]:
        add_entry(swow / f"swow_{lang}.csv", kind="SWOW_L1", dataset=f"swow_{lang}")

    # L2_derived/Kec
    l2 = data / "L2_derived" / "kec"
    for lang in ["en", "es", "nl", "zh"]:
        base = l2 / lang
        for name in [
            "edges.parquet",
            "entropy.parquet",
            "curvature.parquet",
            "coherence.parquet",
            "components.parquet",
            "kec_nodes.parquet",
        ]:
            add_entry(base / name, kind="L2_kec", dataset=f"kec_{lang}")

    # processed/integration
    integration = data / "processed" / "v4.4" / "integration"
    if integration.exists():
        for p in sorted(integration.glob("*.parquet")):
            add_entry(p, kind="integration", dataset=p.stem)

    return rows


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    rows = gather_manifest(repo_root)
    df = pd.DataFrame(rows)
    csv_out = repo_root / "reports/v4.4/manifest_v4.4.csv"
    yaml_out = repo_root / "reports/v4.4/manifest_v4.4.yaml"
    df.to_csv(csv_out, index=False)
    with open(yaml_out, "w", encoding="utf-8") as f:
        yaml.safe_dump(rows, f, sort_keys=False, allow_unicode=True)
    print(f"Saved: {csv_out}")
    print(f"Saved: {yaml_out}")


if __name__ == "__main__":
    sys.exit(main())
