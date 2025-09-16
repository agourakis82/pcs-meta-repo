# KEC Pipeline (SWOW) — GPU-Optional, Resumable, Audited

This document summarizes how to run the KEC pipeline (K=Entropy, E=Curvature, C=Coherence) on SWOW in EN/ES/NL/ZH.

## Quick Start

- Ensure data CSVs are in `data/raw_public/swow/<lang>/` per `config/swow.yaml`.
- Optional GPU prep (CUDA 12.x): install CuPy + RAPIDS (cudf/cugraph) and export `LD_LIBRARY_PATH`.
- Run per language:

```
python -m src.cli.kec_compile --lang en --step all --device auto
python -m src.cli.kec_compile --lang es --step all --device auto
python -m src.cli.kec_compile --lang nl --step all --device auto
python -m src.cli.kec_compile --lang zh --step all --device auto
```

- Or Make targets:

```
make kec-en
make kec-es
make kec-nl
make kec-zh
make kec-all
```

## GPU

- Device selection: `--device auto|cpu|cuda` (auto prefers CUDA if available).
- Entropy uses CuPy when available. Coherence (communities) uses cuGraph; embeddings use fastnode2vec or spectral if node2vec GPU is unavailable.

## Resume & Artifacts

Each step writes Parquet and skips recomputation if outputs are newer than inputs:

```
data/L2_derived/kec/<lang>/
  edges.parquet
  entropy.parquet
  curvature.parquet
  coherence.parquet
  kec_nodes.parquet
reports/kec/
  kec_<lang>.log
  summary_<lang>.json
```

Use `--force` to recompute fresh.

## Parameters

Edit `config/swow.yaml`:
- Entropy smoothing: `teleport` or `selfloop`, `epsilon`.
- Curvature: `forman` (fast), optional Ollivier sample for QC.
- Embeddings: `method`, `dim`, `walk_len`, `walks_per_node`.
- Communities: `method_gpu=louvain`, `method_cpu=leiden`.
- Compose: weights `K/E/C`, `zscore`.

## Monitoring

- Live logs: `tail -f reports/kec/kec_<lang>.run.log` or `kec_<lang>.coh.run.log`.
- Status helper: `scripts/kec_status.sh` prints PIDs, artifact presence and last log lines.

## Quality Gates

- Full graph for K (directed), E and C (undirected projection). No SCC-only by default; GWCC used only to speed community detection & embeddings.
- Deterministic seeds; metadata logged to summaries.

