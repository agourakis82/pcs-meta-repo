# PCS-Meta-Repo — Governance v4.4 (Definitive)

## Goal
Deliver auditable, reproducible, and publish-ready governance (Q1–Q11) linking repository curation to the scientific pipeline (SWOW → KEC → EEG/ET).

## Canonical Structure (target)

```
/docs                Documentation (guides, policies, runbooks)
/src                 Code (cli/, datasets/, kec/, pipeline/, models/, figures/, utils/, pcs_toolbox/)
/scripts             Automation (fetch_data.sh, compute_checksums.py, swow_zuco_pipeline.py, r_mixedlm_check.R)
/notebooks           01_swow_loader → 02_zuco_loader → 03_ag5_metrics (and friends)
/data
  /L0_raw            Local raw (unversioned) OR /data/raw_public (when license allows)
  /L1_tidy           Clean/tidy data
  /L2_derived/kec/<lang>/ entropy.parquet, curvature.parquet, coherence.parquet, components.parquet, edges.parquet, kec_nodes.parquet
/data/processed/v4.4/{kec,zuco,external,integration,models}
/figures/v4.4        F1–F3 + subfolders (kec_distributions/, integration/, supplementary/, corrected/)
/reports             QA (lint, linkcheck, inventory, provenance, models, notebooks)
/tools               Linters, verifiers, curation plans
```

## Policies
- Raw data never redistributed (keep under /data/L0_raw or /data/raw_public per license).
- Reproducibility: fixed seeds, pinned versions, single runbook.
- Provenance: SHA-256, sizes, sources in `reports/provenance/*.yaml` + top-level `PROVENANCE.yaml`.
- Naming/structure: follow tree above; kebab-case for files, snake_case for code.
- Curation: full inventory + file classification + move/delete/quarantine plans; no synthetic artifacts in release.
- Publication: `CITATION.cff`, `metadata.yaml`, `.zenodo.json`; semantic tag (`v4.4.x`), updated badges, version DOI.

## RACI & Quality Gates (Q1–Q11)
- Roles: PI, Maintainer, Contributor, Reviewer.
- Flow: curation → local QA → tag/DOI → badges + attach reports (no raw).
- QGs (abbrev.): Q1 scope, Q2 data, Q3 code, Q4 numerics, Q5 provenance, Q6 reproducibility, Q7 governance, Q8 ethics/licensing, Q9 CI/QA, Q10 docs, Q11 agentic patterns.

