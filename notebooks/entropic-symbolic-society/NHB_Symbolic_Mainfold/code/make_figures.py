#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Runner to generate all figures headlessly.
- Sets NO_SHOW=1 for child processes
- Calls analyze_swow.py with proper arguments
- Copies outputs into figs_final with canonical names
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FIGS = ROOT / "figs"
FINAL = ROOT / "figs_final"
FINAL.mkdir(exist_ok=True)
PY = sys.executable


def run_script(cmd: list[str]) -> int:
    env = os.environ.copy()
    env["NO_SHOW"] = "1"
    print(">>", " ".join(cmd))
    return subprocess.call(cmd, env=env, cwd=ROOT)


def main():
    steps = [
        [PY, str(ROOT / "plot_symbolic_regimes_map.py")],
        [PY, str(ROOT / "simulate_heatmap.py")],
        [PY, str(ROOT / "simulate_kappa_bifurcation.py")],
        [PY, str(ROOT / "simulate_profiles.py")],
        [PY, str(ROOT / "simulate_trajectory_3D.py")],
        [PY, str(ROOT / "simulate_collapse.py")],
        [PY, str(ROOT / "simulate_collapse_recovery.py")],
    ]
    fail = False
    for cmd in steps:
        rc = run_script(cmd)
        if rc != 0:
            print("ERROR running:", cmd)
            fail = True

    # analyze_swow with args (ajuste o caminho abaixo se preciso)
    graph = ROOT.parent / "results" / "word_network.graphml"
    if graph.exists():
        rc = run_script(
            [
                PY,
                str(ROOT / "analyze_swow.py"),
                "--graph",
                str(graph),
                "--outdir",
                "figs",
                "--base",
                "ext_S3_degree_distribution",
            ]
        )
        if rc != 0:
            fail = True
    else:
        print("WARNING: SWOW graphml not found:", graph)

    mapping = {
        "Fig_symbolic_regimes_map.pdf": "Fig4_symbolic_regimes_map.pdf",
        "Fig_symbolic_heatmap.pdf": "Fig2_entropy_curvature_heatmap.pdf",
        "Fig_kappa_bifurcation.pdf": "Ext_S2_kappa_bifurcation.pdf",
        "Fig_gamma_profiles.pdf": "Ext_S1_regime_profiles.pdf",
        "Fig_trajectory_3D.pdf": "Ext_S4_trajectory_3D.pdf",
        "Fig1_collapse.png": "Ext_S5_collapse.png",
        "Fig2_bifurcation.png": "Ext_S5_bifurcation.png",
        "Fig_collapse_recovery.pdf": "Ext_S6_collapse_recovery.pdf",
        "ext_S3_degree_distribution.pdf": "Ext_S3_degree_distribution.pdf",
    }
    for src, dst in mapping.items():
        s = FIGS / src
        if s.exists():
            shutil.copy2(s, FINAL / dst)
            print("OK:", dst)
        else:
            print("MISSING:", s.name)

    print("Done. Check figs_final/. Fail =", fail)


if __name__ == "__main__":
    main()
