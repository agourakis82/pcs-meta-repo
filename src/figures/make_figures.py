#!/usr/bin/env python3
"""
Figures generation stubs for v4.4
Creates expected figure files with minimal placeholders to support CI/QA.
Replace stub content with actual plotting when data is available.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import matplotlib.pyplot as plt


def _ensure(p: Path):
    p.mkdir(parents=True, exist_ok=True)


def _save_placeholder(path: Path, title: str):
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.axis('off')
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def make(version: str, compat: bool = False):
    base = Path('figures') / version
    _ensure(base)
    _ensure(base / 'kec_distributions')
    _save_placeholder(base / 'F1_mean_spike_delta_kec_en.png', 'F1 KEC distributions (placeholder)')
    _save_placeholder(base / 'F2_reading_vs_KEC.png', 'F2 Reading vs KEC (placeholder)')
    _save_placeholder(base / 'F3_EEG_vs_KEC.png', 'F3 EEG vs KEC (placeholder)')


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--version', default='v4.4')
    ap.add_argument('--compat', action='store_true')
    args = ap.parse_args(argv)
    make(args.version, args.compat)
    print(f"[figures] generated placeholders under figures/{args.version}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

