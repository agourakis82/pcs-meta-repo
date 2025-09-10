#!/usr/bin/env python3
"""
KEC Compiler CLI (v4.4-ready)

Multilingual SWOW → KEC artifacts compiler with resumable steps and GPU hinting.
This is a lightweight CLI wrapper that orchestrates per-language builds.
It creates the expected folder structure and status files; replace stubs with
real computations in your environment with data access.

Author: PCS-HELIO Team (MIT)
"""
from __future__ import annotations

import argparse, json, time
from pathlib import Path
from typing import List


ARTIFACTS = [
    "entropy.parquet",
    "curvature.parquet",
    "coherence.parquet",
    "components.parquet",
    "edges.parquet",
    "kec_nodes.parquet",
]


def _ensure(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def compile_lang(lang: str, out_base: Path, step: str, resume: bool = True) -> dict:
    out_dir = out_base / lang
    _ensure(out_dir)
    status = out_dir / ".status.json"
    info = {"lang": lang, "step": step, "ts_start": time.time()}
    # Stub: just create touch files to mark presence without distributing data
    if step in ("build", "all"):
        pass
    if step in ("entropy", "all"):
        (out_dir / "entropy.parquet").touch()
    if step in ("curvature", "all"):
        (out_dir / "curvature.parquet").touch()
    if step in ("coherence", "all"):
        (out_dir / "coherence.parquet").touch()
    if step in ("compose", "all"):
        for f in ("components.parquet", "edges.parquet", "kec_nodes.parquet"):
            (out_dir / f).touch()
    info["ts_end"] = time.time()
    info["artifacts"] = [p for p in ARTIFACTS if (out_dir / p).exists()]
    status.write_text(json.dumps(info, indent=2), encoding="utf-8")
    return info


def main(argv: List[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Compile multilingual KEC artifacts")
    ap.add_argument("--lang", required=True, help="comma-separated languages, e.g., en,es,nl,zh")
    ap.add_argument("--step", default="all", choices=["build","entropy","curvature","coherence","compose","all"])
    ap.add_argument("--device", default="auto", choices=["auto","cpu","cuda"], help="device hint")
    ap.add_argument("--resume", action="store_true", help="resume from .status.json")
    ap.add_argument("--out", default="data/L2_derived/kec", help="output base directory")
    args = ap.parse_args(argv)

    out_base = Path(args.out)
    _ensure(out_base)
    langs = [s.strip() for s in args.lang.split(",") if s.strip()]
    results = []
    for lang in langs:
        results.append(compile_lang(lang, out_base, args.step, resume=args.resume))
    print(json.dumps({"status": "ok", "results": results}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

