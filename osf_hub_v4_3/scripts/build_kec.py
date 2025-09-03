#!/usr/bin/env python3
from pathlib import Path
import json
import time


def main():
    base_dir = Path(__file__).resolve().parents[1]
    results_dir = base_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    # Write a minimal KEC artifact (stub)
    kec_artifact = {
        "version": "v4.3",
        "source": "SWOW",
        "method": "KEC (stub)",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "note": "This is a stub artifact for pipeline wiring."
    }

    (results_dir / "kec_graph_stub.json").write_text(
        json.dumps(kec_artifact, indent=2), encoding="utf-8"
    )

    (results_dir / "kec_build.log").write_text(
        "Built KEC (stub) from SWOW.\n", encoding="utf-8"
    )

    print("[OK] build_kec.py: stub KEC artifact created in results/.")


if __name__ == "__main__":
    main()

