#!/usr/bin/env python3
from pathlib import Path
import time


def main():
    base_dir = Path(__file__).resolve().parents[1]
    results_dir = base_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    # Create a stub alignment output
    alignment_text = (
        "Aligned ZuCo (stub): fixation-locked theta/alpha and "
        "sentence-level reading cost.\n"
    )
    (results_dir / "zuco_alignment_stub.txt").write_text(
        alignment_text,
        encoding="utf-8",
    )

    ts = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    msg = f"Alignment (stub) completed at {ts}.\n"
    (results_dir / "align_zuco.log").write_text(
        msg,
        encoding="utf-8",
    )

    print("[OK] align_zuco.py: stub alignment outputs written to results/.")


if __name__ == "__main__":
    main()
