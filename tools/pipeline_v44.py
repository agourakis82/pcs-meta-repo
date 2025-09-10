#!/usr/bin/env python3
"""
PCS v4.4 Orchestrator (tools/pipeline_v44.py)

Runs the non-breaking, idempotent v4.4 pipeline with modal split (RT/EEG),
multilingual KEC (placeholders), integration, models, and figures. Produces a
summary JSON under reports/ for auditability.

Safe to run under CI without access to raw data: creates expected structure and
placeholder artifacts only.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Dict


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


def _ensure_dirs() -> None:
    for d in [
        ROOT / 'data' / 'L1_tidy' / 'zuco_rt',
        ROOT / 'data' / 'L1_tidy' / 'geco_rt',
        ROOT / 'data' / 'L1_tidy' / 'onestop_rt',
        ROOT / 'data' / 'L1_tidy' / 'zuco_eeg',
        ROOT / 'data' / 'L1_tidy' / 'derco_eeg',
        ROOT / 'data' / 'L1_tidy' / 'lpp_eeg',
        ROOT / 'data' / 'L2_derived' / 'kec',
        ROOT / 'data' / 'processed' / 'v4.4' / 'integration',
        ROOT / 'data' / 'processed' / 'v4.4' / 'models',
        ROOT / 'figures' / 'v4.4',
        REPORTS,
    ]:
        d.mkdir(parents=True, exist_ok=True)


def _touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch()


def run_step(step: str) -> None:
    # Reuse the dispatcher in scripts/swow_zuco_pipeline.py
    sys.path.insert(0, str(ROOT))
    from scripts.swow_zuco_pipeline import run_step as _run

    _run(step, datasets=None)


def compile_kec() -> None:
    # Call the CLI function directly
    sys.path.insert(0, str(ROOT))
    from src.cli.kec_compile import main as kec_main

    kec_main(["--lang", "en,es,nl,zh", "--step", "all", "--resume"])  # type: ignore[arg-type]


def make_figures() -> None:
    sys.path.insert(0, str(ROOT))
    from src.figures.make_figures import main as figs_main

    figs_main(["--version", "v4.4"])  # type: ignore[arg-type]


def list_created() -> Dict[str, list]:
    def has(p: str) -> bool:
        return (ROOT / p).exists()

    files = [
        "data/L1_tidy/zuco_rt/word_events_rt.parquet",
        "data/L1_tidy/geco_rt/word_events_rt.parquet",
        "data/L1_tidy/onestop_rt/word_events_rt.parquet",
        "data/L1_tidy/zuco_eeg/word_events_eeg.parquet",
        "data/L1_tidy/derco_eeg/word_events_eeg.parquet",
        "data/L1_tidy/lpp_eeg/word_events_eeg.parquet",
        *[f"data/L2_derived/kec/{lang}/{f}" for lang in ("en","es","nl","zh") for f in (
            "entropy.parquet","curvature.parquet","coherence.parquet","components.parquet","edges.parquet","kec_nodes.parquet"
        )],
        "data/processed/v4.4/integration/zuco_kec_rt.parquet",
        "data/processed/v4.4/integration/zuco_kec_eeg.parquet",
        "data/processed/v4.4/integration/zuco_kec_merged.parquet",
        "data/processed/v4.4/models/models_reading_coeffs.csv",
        "figures/v4.4/F1_mean_spike_delta_kec_en.png",
        "figures/v4.4/F2_reading_vs_KEC.png",
        "figures/v4.4/F3_EEG_vs_KEC.png",
    ]
    present = [p for p in files if has(p)]
    missing = [p for p in files if not has(p)]
    return {"present": present, "missing": missing}


def main() -> int:
    _ensure_dirs()

    # Steps
    run_step("tidy_rt")
    run_step("tidy_eeg")
    compile_kec()
    run_step("integrate")
    run_step("models")
    make_figures()

    # Summary
    summary = {
        "pipeline": "v4.4",
        "env": {
            "python": sys.version.split()[0],
            "cwd": str(ROOT),
        },
        "artifacts": list_created(),
    }
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "pipeline_v44_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

