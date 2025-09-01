# Psychiatry & Neuroscience — YEAR 2025 Sweep (RAG‑ready)

This repository contains the **canonical, deduplicated and labeled corpus for 2025**
across psychiatry and neuroscience, plus **RAG‑ready** artifacts.

## Deliverables (canonical filenames)
- `data/processed/2025_sweep/YEAR-2025_psy-neuro_records.jsonl`
- `data/processed/2025_sweep/YEAR-2025_psy-neuro_records.csv`
- `data/processed/2025_sweep/YEAR-2025_active_reading_notes.jsonl`
- `data/processed/2025_sweep/YEAR-2025_chunks.jsonl`
- `data/processed/2025_sweep/YEAR-2025_quality_audit.jsonl`
- `reports/YEAR-2025_top_venues.csv`
- `reports/README_YEAR-2025.md` (coverage, hashes, and instructions)

## Structure (canonical)
/docs  · /src  · /notebooks  · /data/raw_public  · /data/processed/2025_sweep  · /figures  · /manuscripts  · /reports  · /tools

> **Licensing:** Metadata and derived notes (abstracts, QA, triples) are released under **CC BY 4.0**. Code under **MIT**.
> Third‑party metadata remains under original licenses. No paywalled full‑text is redistributed.

## Quick start
1. Load `data/processed/2025_sweep/YEAR-2025_psy-neuro_records.jsonl` for canonical metadata.
2. Index `YEAR-2025_active_reading_notes.jsonl` (QA and concept edges) into your RAG store.
3. Use `YEAR-2025_chunks.jsonl` for semantic retrieval (OA abstracts; extend with OA full text later).
