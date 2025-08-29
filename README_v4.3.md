# Fractal Entropy — Computational–Symbolic Psychiatry (PCS)

**Owner:** Demetrios Agourakis · ORCID 0000-0002-8596-5097 · <demetrios@agourakis.med.br>
**Current snapshot:** v2025.08.29 (PCS v4.3) · **Date:** 29 Aug 2025
**License:** CC BY 4.0

> Canonical, auditable structure prioritising public data and full reproducibility.

## Repository Structure (canonical)

```bash
/docs               → policies, guides, inventory, methods
/src                → source code (to be packaged)
/notebooks          → reproducible notebooks (versioned)
/data
  /raw_public       → unchanged public datasets
  /processed        → reproducible derivatives
/figures            → manuscript-ready figures
/manuscripts        → IMRaD, Overleaf templates, submissions
/reports            → linter, inventory, linkcheck outputs
/tools              → repo_lint.py, linkcheck, helpers
```

## What's in v4.3

- **Extended Memory:** `Memoria_Estendida_PHD_Brasil_2025-08-29.md` (single source
  of truth; governance; editorial plan).
- **Metadata:** `metadata_v4.3.yaml`, `zenodo_v4.3.json`, `CITATION_v4.3.cff`.
- **Quality Gates:** Q1–Q10 enforced at release.
- **NIT:** linter, linkcheck, inventory (no-broken-links policy).

## How to Cite

See `CITATION_v4.3.cff`. DOI will be minted on Zenodo upon deposition of this snapshot.

## Getting Started

1. Run `tools/repo_lint.py` and linkcheck (exit code must be 0).
2. Open notebooks under `/notebooks` (environment pinned).
3. For IMRaD, use the Overleaf skeleton provided in `/manuscripts`.

## Ethics & Legal

- Public datasets only; zero PII.
- CC BY 4.0 for text/figures; MIT for code (unless stated).
- Clinical content is **R&D**; **not** diagnostic guidance.

## Versioning

- **Release (documents):** **v4.3** (this snapshot). Previous: **v4.2** (17 Aug 2025).
- **Calendar tag:** **v2025.08.29** (document header in Extended Memory).
- **Software modules:** independent **SemVer** (e.g., Toolbox **v0.2.0**). Toolbox
  version numbers are **independent** from the document release.
