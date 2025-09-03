#!/usr/bin/env python3
from pathlib import Path
import time
import sys


def main():
    base_dir = Path(__file__).resolve().parents[1]
    repo_root = Path(__file__).resolve().parents[2]
    results_dir = base_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    # Allow importing toolbox from src/
    sys.path.insert(0, str(repo_root / "src"))
    from pcs_toolbox import zuco  # type: ignore

    # Run loader and write processed outputs under data/processed + reports
    merged, qa = zuco.load_all(write_outputs=True)

    # Write a light alignment artifact for the hub
    out_csv = results_dir / "zuco_aligned.csv"
    merged.to_csv(out_csv, index=False)

    ts = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    n_rows = merged.shape[0]
    n_subj = merged['Subject'].nunique(dropna=True) if 'Subject' in merged else 0
    msg = (
        f"Alignment completed at {ts}.\n"
        f"Rows={n_rows} Subjects={n_subj}\n"
    )
    (results_dir / "align_zuco.log").write_text(
        msg,
        encoding="utf-8",
    )

    print(f"[OK] align_zuco.py: wrote {out_csv}")


if __name__ == "__main__":
    main()
