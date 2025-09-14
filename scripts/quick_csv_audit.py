#!/usr/bin/env python3
"""
Quick CSV Audit (v4.4)

Scans key CSV outputs under ./data for basic quality checks and writes a concise
Markdown report to ./reports/csv_audit_report.md (or --out path).

Checks (sample-based):
- File size and total line count (wc -l)
- Presence of key columns (KEC/EEG/RT/IDs)
- Non-null coverage for key columns
- Basic numeric stats (min/median/max, p1/p99) for key numeric columns
- Simple plausibility hints for reading-time columns

Usage:
  python scripts/quick_csv_audit.py --out reports/csv_audit_report.md
"""

from __future__ import annotations

import argparse
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict

import pandas as pd


KEY_NUM_COLS = [
    # KEC
    "entropy", "curvature", "coherence",
    # EEG
    "eeg_metric", "theta", "alpha", "beta",
    # RT
    "fixation_duration", "ffd_ms", "gd_ms", "trt_ms", "nfix",
]

KEY_ID_COLS = ["subject_id", "doc_id", "sent_id", "word_id", "word", "lang", "dataset"]


@dataclass
class FileAudit:
    path: Path
    size_mb: float
    total_lines: int
    present_cols: List[str]
    coverage: Dict[str, float]
    stats: Dict[str, Dict[str, float]]
    notes: List[str]


def line_count(path: Path) -> int:
    try:
        out = subprocess.check_output(["wc", "-l", str(path)], text=True).strip()
        return int(out.split()[0])
    except Exception:
        return -1


def audit_csv(path: Path, sample_rows: int = 100_000) -> FileAudit:
    size_mb = path.stat().st_size / (1024 * 1024)
    total_lines = line_count(path)
    notes: List[str] = []

    try:
        df = pd.read_csv(path, nrows=sample_rows)
    except Exception as e:
        return FileAudit(path, size_mb, total_lines, [], {}, {}, [f"read error: {e}"])

    present_cols = [c for c in KEY_NUM_COLS + KEY_ID_COLS if c in df.columns]

    coverage: Dict[str, float] = {}
    for c in present_cols:
        coverage[c] = float(df[c].notna().mean()) if c in df.columns else 0.0

    stats: Dict[str, Dict[str, float]] = {}
    for c in KEY_NUM_COLS:
        if c in df.columns:
            s = pd.to_numeric(df[c], errors="coerce")
            if s.notna().any():
                q = s.quantile([0.01, 0.5, 0.99])
                stats[c] = {
                    "min": float(s.min()),
                    "p01": float(q.loc[0.01]),
                    "median": float(q.loc[0.5]),
                    "p99": float(q.loc[0.99]),
                    "max": float(s.max()),
                }

    # Simple plausibility hints for RT
    def _hint_rt(col: str, low: float, high: float):
        if col not in df.columns:
            return
        s = pd.to_numeric(df[col], errors="coerce")
        nn = s.notna().sum()
        if nn == 0:
            return
        frac_low = float((s < low).sum()) / nn
        frac_high = float((s > high).sum()) / nn
        if frac_low > 0.2:
            notes.append(f"{col}: {frac_low:.0%} abaixo de {low}ms (verificar escala)")
        if frac_high > 0.2:
            notes.append(f"{col}: {frac_high:.0%} acima de {high}ms (outliers/escala)")

    _hint_rt("ffd_ms", 50, 800)
    _hint_rt("gd_ms", 80, 1200)
    _hint_rt("trt_ms", 120, 2000)

    return FileAudit(path, size_mb, total_lines, present_cols, coverage, stats, notes)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="reports/csv_audit_report.md")
    args = ap.parse_args()

    root = Path.cwd()
    targets = []
    # Prioridade: outputs integrados e KEC derivados
    targets += list((root / "data" / "processed").rglob("*.csv"))
    # Limitar para não explodir o relatório
    targets = sorted(set(targets))

    out_path = root / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)

    rows: List[str] = []
    rows.append("# CSV Audit (v4.4)\n")
    rows.append("Arquivo | Tamanho (MB) | Linhas | Colunas‑chave | Cobertura (amostra) | Notas")
    rows.append("--- | ---:| ---:| --- | --- | ---")

    for p in targets:
        audit = audit_csv(p)
        cols_str = ", ".join(audit.present_cols) if audit.present_cols else "—"
        cov_parts = []
        for c in audit.present_cols:
            cov_parts.append(f"{c}:{audit.coverage.get(c,0.0)*100:.0f}%")
        cov_str = ", ".join(cov_parts) if cov_parts else "—"
        note = "; ".join(audit.notes) if audit.notes else ""
        rows.append(
            f"`{p}` | {audit.size_mb:.1f} | {audit.total_lines} | {cols_str} | {cov_str} | {note}"
        )

        # Append stats block
        if audit.stats:
            rows.append("<details><summary>Stats (amostra)</summary>")
            rows.append("")
            rows.append("coluna | min | p01 | mediana | p99 | max")
            rows.append("---|---:|---:|---:|---:|---:")
            for c, s in audit.stats.items():
                rows.append(
                    f"{c} | {s['min']:.3g} | {s['p01']:.3g} | {s['median']:.3g} | {s['p99']:.3g} | {s['max']:.3g}"
                )
            rows.append("")
            rows.append("</details>")

    out_path.write_text("\n".join(rows), encoding="utf-8")
    print(f"[audit] wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

