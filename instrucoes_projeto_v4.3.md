# Project Instructions — v4.3 (Symbolic First)

**Repository standard:** canonical, auditable,
public data only, no broken links.
**Tags:** [Mestrado] · [Symbolic Area] · [Infrastructure]
**Owner:** Demetrios Agourakis (ORCID 0000-0002-8596-5097)
**Concept DOI:** 10.5281/zenodo.16533374

---

## 0) Purpose & Non‑negotiables

This document operationalizes v4.3 for **Phase S1 — Symbolic Area First**.
The **HELIO module is explicitly deferred** to a later phase (H1).
- Safety, accuracy, traceability > convenience. No PII; public datasets only.
- Reproducibility: fixed seeds, pinned envs,
`provenance.yaml`, inventory & link‑check reports.
- **Quality Gates (Q1–Q10)** enforced for every deliverable; CI checks must pass
  prior to release.

**Out of Scope (deferred):** HELIO, geomagnetic exposures, SEA/VAR event‑study. Keep placeholders only in roadmap.

---

## 1) Scope — Symbolic Manifolds & Public Neurophysiology

**Objective.** Build the symbolic manifold and **KEC** (symbolic state metric) from public
language graphs (SWOW), then validate associations with **ZuCo** (eye‑tracking + EEG).
**Outputs.** (i) Preprint + Overleaf IMRaD; (ii) Toolbox v0.1 for KEC; (iii) Figures &
notebooks reproducible; (iv) Zenodo version DOI; (v) Dissertation‑ready figures.

---

## 2) Roles & Governance

- **Contributor (Data Science & AI):** Dionisio Chiuratto Agourakis — methods,
  modeling, reproducibility.
- **PI/Author:** Demetrios — scientific direction, writing, final approvals.
- **Infra:** repo curation, lints, linkcheck, metadata (`CITATION.cff`,
  `zenodo.json`, `metadata.yaml`).
- **Quality:** apply **Q1–Q10** (technical accuracy; up‑to‑date sources;
  terminology; IMRaD; reproducibility; limitations & bias; actionables;
  impact/toolbox; ethics/legal; alignment to the Supreme Goal).

**Licensing.** Text CC BY 4.0; code MIT. Include LICENSE & CITATION.

---

## 3) Canonical Repository Layout & Conventions

```text
/docs               policies, guides, inventory, methods
/src                library code (packaged later)
/notebooks          reproducible (versioned) notebooks
/data
  /raw_public
    /swow/<lang>/   raw SWOW exports per language
    /zuco/v1/       ZuCo 1.0 raw structure
    /zuco/v2/       ZuCo 2.0 raw structure
  /processed        deterministic derivatives
/figures            manuscript-ready figures
/manuscripts        Overleaf-ready IMRaD, submissions
/reports            lint, inventory, linkcheck, QA JSONs
/tools              repo_lint.py, linkcheck configs
```

**Naming:** kebab‑case for files; snake_case for code.
**Commits:** conventional commits; tag releases `vX.Y.Z`.
**Checks:** `repo_lint.py` + markdown linkcheck must be clean before merging.

---

## 4) Data Provenance (Public Only)

### 4.1 SWOW (Small World of Words)

- **Use:** build language‑specific association graphs; compute **KEC** (entropy, curvature, coherence).
- **Provenance:** document source URL & license; store raw under `/data/raw_public/swow/<lang>/`.

### 4.2 ZuCo 1.0 / 2.0

- **Use:** EEG + eye‑tracking during sentence reading; fixation‑aligned EEG features; reading‑cost metrics (FFD, GD, TRT, GPT).
- **Provenance:** retain original file structure; conversions scripted; no subject PII.
- **Controls:** lexical frequency/length, word position, sentence length, syntactic depth (optional).

**ETL Rules:**

1) never edit raw files;
2) normalize into tidy tables (CSV/Parquet);
3) hash & size checks (SHA‑256);
4) record `provenance.yaml` (source, checksum, scripts, versions).

**Example `provenance.yaml` stub:**

```yaml
dataset: zuco_v2
source_url: https://osf.io/ (provider link)
license: CC BY-NC-SA 4.0 (verify upstream)
ingest_date: 2025-08-29
raw_dir: data/raw_public/zuco/v2
checksums:
  - file: S01.mat
    sha256: <hash>
scripts:
  - notebooks/02_zuco_loader.ipynb
  - src/zuco/convert_mat_to_tidy.py
```

```yaml
dataset: zuco_v2
source_url: https://osf.io/ (provider link)
license: CC BY-NC-SA 4.0 (verify upstream)
ingest_date: 2025-08-29
raw_dir: data/raw_public/zuco/v2
checksums:
  - file: S01.mat
    sha256: <hash>
scripts:
  - notebooks/02_zuco_loader.ipynb
  - src/zuco/convert_mat_to_tidy.py
```

```yaml
version_pins:
  python: "3.11"
  packages:
    numpy: "1.26.*"
    pandas: "2.2.*"
```

---

## 5) Symbolic State Metric — **KEC**

**Components:** (i) transition entropy; (ii) local curvature (Ollivier‑Ricci/Forman variants); (iii) meso‑coherence.
```

---

## 5) Symbolic State Metric — **KEC**

**Inputs:** SWOW graphs; tokenized stimuli; mapping tables.
**Components:** (i) transition entropy; (ii) local curvature (Ollivier‑Ricci/Forman variants); (iii) meso‑coherence (community‑aware).
**Ablations:** edge shuffles; degree‑preserving randomization; vocabulary subsampling.
**Uncertainty:** bootstrap CIs; robust SEs clustered by sentence/subject when mapped to ZuCo.

**Deliverables:** metric tables under `/data/processed/kec/` + plots under `/figures/metrics/`.

---

## 6) Validation on ZuCo (Symbolic ↔ Neurophysiology)

- **Models:** reading‑cost metrics and band‑limited EEG power ~ local **KEC** at fixation times.
- **Covariates:** lexical frequency/length, surprisal (optional), position; random effects for subject/sentence if needed.
- **Figures:**
  - **F1** — KEC distributions and layout diagnostics (per language).
  - **F2** — Reading‑cost vs KEC (partial effects).
  - **F3** — EEG band power vs KEC (per‑subject panels).
  - **F4** — Cross‑lingual residuals (Procrustes/MUSE) when multi‑language SWOW is added.

---

## 7) Notebooks Plan (v0.1)
1. `01_swow_loader.ipynb` — ingest, graph build, sanity checks.
2. `02_kec_metrics.ipynb` — entropy/curvature/coherence, ablations, CIs.
3. `03_zuco_loader.ipynb` — ET/EEG features, alignment, tidy exports.
4. `04_zuco_models.ipynb` — reading‑cost & EEG ~ KEC, model outputs.
5. `05_cultural_residuals.ipynb` — optional cross‑lingual alignment and residuals.

**Output contracts:** CSV/Parquet tables + PNG/SVG under `/figures/`.

---

## 8) Manuscripts & References
- **Primary:** Overleaf IMRaD (skeleton supplied), Vancouver style, Better BibTeX export to `manuscripts/references.bib`.
- **Sections:** Abstract, Introduction, Methods (KEC, data, models), Results (F1–F4), Discussion, Limitations, Ethics, Data/Code availability.

---

## 9) Releases & DOIs
**Concept DOI:** 10.5281/zenodo.16533374 (keep).
**Version DOI procedure:**
1) Create Git tag `v4.3`;
2) Archive release → Zenodo (link GitHub);
3) Capture badge;
4) Update README & `CITATION.cff`.
**Reports:** attach `/reports/*` and inventory hashes to the release.

---

## 10) 48h / 7d / 10w Checklists & Acceptance Criteria

**48h.**

- [ ] Commit this file `docs/instrucoes_projeto_v4.3.md`.
- [ ] Add notebooks 01–03 with stubs & IO contracts.
- [ ] Push Overleaf `preprint_skeleton.tex`; compile.

**Acceptance:** lints pass; linkcheck=0 broken; README badges OK.

**7d.**

- [ ] Figures F1–F3; Methods drafted; toolbox v0.1.

**Acceptance:** rerun notebooks end‑to‑end; artifacts reproducible.

**10w.**

- [ ] Full cultural residuals; Discussion/Limitations; preprint ready.

**Acceptance:** Quality Gates Q1–Q10 satisfied; Zenodo DOI minted.

---

## 11) Ethics & Limitations

- Public datasets only; no diagnosis; research‑only.
- WEIRD bias in SWOW/ZuCo; discuss generalizability.
- Graph sampling impacts KEC; mitigate with ablations and sensitivity.

---

## 12) Reproducibility & QA

- **Seeds:** fixed; logged in `reports/run_meta.json`.
- **Env:** `environment.yml` + exact versions; freeze on release.
- **Tests:** unit tests for loaders/metrics; figure hash checks; CI must be green.
- **Inventory:** `/reports/inventory.json` (name, size, SHA‑256) + duplicates table.

---

## 13) Appendix — Commands & Templates
- **Build figures:** run notebooks 01→05; outputs saved under `/figures/*`.
- **Overleaf:** load `manuscripts/preprint_skeleton.tex`; ensure `references.bib` synced (Zotero).
- **Citations:** Vancouver numeric; every non‑obvious claim must have a primary source.
