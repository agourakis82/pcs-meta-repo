# PCS‑HELIO v4.3 — Notebook Style & Execution Guide

This repository enforces a unified, auditable notebook structure:

- IMRaD sections (Intro/Methods/Results/Discussion).
- Run Modes: `RUN_MODE in {'sample','full'}`; `sample` must always run without crashes (use synthetic mini‑data if raw are absent).
- Preflight cell: environment versions and required folders.
- QA cell: assertions on shapes, required columns, coverage.
- Outputs: write deterministic CSV/JSON/PNGs to `data/processed/**`, `reports/**`, `figures/metrics/**`.
- Visual: load `notebooks/_style.css`; add captions to figures.

## Acceptance tests

- Each notebook prints a short contract summary.
- Saving cells write a small manifest JSON (hashes, row counts).
- CI executes notebooks in `sample` mode and uploads artifacts.

