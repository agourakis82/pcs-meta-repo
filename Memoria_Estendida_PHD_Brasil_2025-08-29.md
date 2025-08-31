---
title: "Extended Memory — PhD & Publication Plan (Brazil)"
subtitle: "Fractal Entropy — Computational–Symbolic Psychiatry (PCS)"
author:
  - name: "Demetrios Agourakis"
    orcid: "0000-0002-8596-5097"
    email: "demetrios@agourakis.med.br"
affiliations:
  - "PUC-SP — Graduate Program in Biomaterials & Regenerative Medicine (PPGBMR)"
  - "Faculdade São Leopoldo Mandic — Medicine"
version: "v2025.08.29 (PCS v4.3)"
date: "29 Aug 2025"
license: "CC BY 4.0"
doi: "TBD (Zenodo release for v4.3)"
keywords: ["Computational-Symbolic Psychiatry", "Fractal Entropy", "Semantic Manifolds", "SWOW", "ZuCo", "Cognitive Topology", "AG5/KEC", "HELIO exposure"]
language: "en"
---

> **Versioning Policy (clarification).**
> • **Release (documents):** vMAJOR.MINOR = **v4.3** for this snapshot; previous = **v4.2** (2025‑08‑17).
> • **Calendar tag:** vYYYY.MM.DD = **v2025.08.28**.
> • **Software modules (toolbox):** independent **SemVer** (e.g., **v0.2.0**). Toolbox version numbers do **not** reflect the document release.

---

---

## Executive Summary

This document consolidates **Version 4.3** of the project's extended memory. It unifies
the *clinical-computational bridge* between **Biomaterials & Regenerative Medicine**
(PUC‑SP) and **Computational–Symbolic Psychiatry (PCS)**, and sets a single source of
truth for editorial strategy, data pipelines, governance, and scientific outreach. All
content is curated for reproducibility, licensing clarity (CC BY 4.0), and *auditability*
according to **Quality Gates Q1–Q10**.

**Impact in one paragraph.** We formalise an interpretable, entropy‑driven framework
that maps symbolic cognition onto manifold topology, leveraging public datasets (e.g.,
SWOW, ZuCo) to derive state metrics (**AG5/KEC**: transition entropy, local/meso
curvature, coherence) and testable inferences (SEA/VAR/ARIMAX). We explicitly
distinguish **evidence vs. plausibility vs. speculation**, integrate clinical‑cultural
lenses (CFI/DSM‑5), and deliver an IMRaD‑ready path to Q1 submissions, with a 12‑month
PhD roadmap and a 24‑month master's timeline harmonised under the PCS governance.

---

## 1) SCOPE — Objective, Variables, Windows, Corpus, Output, Contract

**Objective.** Establish a reproducible bridge from *HELIO exposure* → **AG5/KEC
state metric** → *SEA/VAR inference* → *ZuCo validation* → *IMRaD/toolbox*, with
clinical‑cultural interpretation.

**Primary variables.**

- *HELIO exposure:* Kp, Dst, Bz, V_sw, F10.7 (DONKI/NOAA as public sources; no
  private data).
- *State metrics (AG5/KEC):* transition entropy, local & mesoscopic curvature,
  coherence (lexico‑semantic graphs).
- *Cognitive validation:* ZuCo EEG/ET features (word/sentence‑level); eye‑tracking
  metrics (FFD, GD, TRT, GPT).
- *Semantic substrate:* SWOW association networks by language (EN first; extended
  later).

**Time windows.** Standard **−3…+3 days** around Kp ≥ 5 storms (SEA A1), plus mixed
windows for placebo/falsification.

**Corpus (public).** SWOW (EN; later RP/ES), ZuCo 1.0/2.0 (EEG+ET),
Wikipedia‑derived sentences (as present in ZuCo).

**Output language.** English (native quality) for all artifacts; Portuguese only for administrative dialogue.

**Delivery contract.** All releases must include: (1) Executive Summary; (2) Technical Core; (3) References (Vancouver);
(4) Artifacts list; (5) Actionables + Limitations; (6) Next Steps (48h/7d/10w); (7) Assumptions Log + Quality Gates.

---

## 2) DESIGN — SEA/VAR/ARIMAX; Controls; Falsifications

**A1 SEA (event study).** ΔKEC around storms (Kp≥5) within −3…+3d; controls for
seasonality, topic, latitude; placebo windows. Primary outcome: mean ΔKEC (CI),
FDR‑adjusted p‑values; figure: *Mean Storm ΔKEC*.

**A2 VAR/ARIMAX.** Shock‑response IRFs for AG5/KEC ↔ exposure; heterogeneity by
lexical domains, register and language. Robust SEs, HAC corrections; sensitivity to
lag length (AIC/BIC), rolling windows.

**A3 ZuCo validation.** Hypothesis: reading cost (EEG/ET) tracks local AG5;
*prediction:* higher AG5 curvature/coherence aligns with reduced reading cost
under specific linguistic regimes; cross‑validate across ZuCo 1.0/2.0 tasks
(NR vs. TSR).

**Controls.** Seasonality; topic composition; sentence length; word frequency;
morphological complexity; subject reading speed (ZuCo).

**Falsifications.** (i) Implausible lags; (ii) label permutation; (iii) null graph
ablations; (iv) shuffled semantic edges; (v) non‑storm windows.

---

## 3) EXECUTION — Steps, Premises, Artifacts, Versions & Seeds

**E1 Data Provenance (public only).**

- SWOW (EN): lexical association matrices → graph construction
  (undirected/weighted); per‑language isolation.
- ZuCo 1.0/2.0: EEG/ET alignment; fixation‑locked features; frequency bands
  (theta/alpha/beta/gamma) with Hilbert envelopes.
- HELIO exposure: public indices (Kp, Dst, Bz, V_sw, F10.7) via official
  repositories; pinned snapshots at release.

**E2 Feature Engineering.**

- AG5/KEC: transition entropy (Markovised walk), local/meso curvature
  (Ollivier‑Ricci/Forman‑Ricci variants), coherence (community‑consistent
  embedding proximity).
- Reading cost: FFD, SFD, GD, TRT, GPT; per‑band EEG power; omission rates;
  regressions.

**E3 Models.**

- SEA with bootstrapped CIs (>= 2000 resamples); FDR (Benjamini–Hochberg).
- VAR/ARIMAX with exogenous HELIO; IRFs ±95% CIs; stability checks (roots inside
  unit circle).
- Cross‑mapping: regress ZuCo features on AG5/KEC with lexical controls
  (frequency, length, surprisal proxies).

**E4 Reproducibility.** Random seeds pinned; conda/uv environment file;
`provenance.yaml`; hashes for raw/public inputs; LICENSE (CC BY 4.0) and code
MIT where applicable.

**Artifacts (v4.3).** README, this Extended Memory, CHANGELOG, metadata.yaml,
zenodo.json, CITATION.cff; onboarding guides; NIT (linter, linkcheck,
inventory).

---

## 4) QUALITY — Limits, Biases, CIs, FDR, Robustness

- **Bias & WEIRD:** SWOW/ZuCo are predominantly WEIRD contexts; explicit note
  in all results.
- **Language scope:** Initial EN focus; avoid overclaiming cross‑lingual
  generality until RP/ES modules pass GW/Procrustes checks.
- **Confounding:** Topic/length/frequency rigorously controlled; storm‑window
  placebos required.
- **Uncertainty:** Report 95% CIs; bootstrap for SEA; robust SEs for VAR/ARIMAX;
  FDR across families of tests.
- **Ablations:** Shuffle edges; null graphs; randomised windows.
- **Ethics:** No PII; public datasets only; license compliance; no clinical
  diagnostic claims.

---

## 5) DELIVERY — IMRaD / Tech‑Note / Toolbox & Q‑Gates

- **Primary IMRaD target:** *Nature Human Behaviour* (derivative path); maintain
  neutral claims; emphasise interpretability and public data.
- **Toolbox:** metrics (AG5/KEC), SEA scripts, VAR/ARIMAX, ZuCo mapping
  utilities; documented with examples.
- **Quality Gates (Q1–Q10):** Technical accuracy; evidence vs plausibility vs
  speculation; consistent terminology; editorial structure; reproducibility;
  explicit limitations; actionable DoD; impact strategy; legal‑ethical
  compliance; alignment to PCS Supreme Goal.

---

## 6) Editorial & Publication Strategy

- **Q1 Path:** NHB derivative (manifold + cognitive topology); Scientific Reports
  companion (methods/toolbox); OSF/Zenodo mirrored with DOIs.
- **Badges:** ORCID, DOI, License, Reproducibility.
- **Repository hygiene:** linter, linkcheck, curated inventory; no broken links
  policy.

---

## 7) Scientific Outreach (Marketing)

- **LinkedIn/ResearchGate:** monthly micro‑summaries (figures + one key metric);
  DOI back‑references.
- **Pre‑pitches to PIs:** concise 1‑pager, neutral tone; stress data‑public
  reproducibility; invite methodological critique.
- **Talks/Workshops:** focus on interpretability and clinical‑cultural alignment
  (CFI).

---

## 8) Governance & NIT (Non‑Idiot Tooling)

- **Repo linter:** presence & structure checks; LICENSE/CITATION/CHANGELOG;
  required folders; JSON report under `/reports/`.
- **Linkcheck:** relative links in `.md`; exit code 0 gate.
- **Inventory:** CSV/JSON with name/hash/size; duplicates flagged; pinned in
  `/docs/inventory/`.
- **PR Template:** linter + linkcheck + CHANGELOG update required before merge.

---

## 9) Clinical‑Cultural Bridge (High‑Level Summary)

A third‑person neuropsychological synthesis is maintained for *psychiatric safety
and pedagogy*. No PII is stored; recommendations for **Marina (neuropsychology)**
and **Renata (psychiatry)** focus on: metacognitive training; task‑switching
hygiene; minimising cognitive blunting pharmacology; risk monitoring (existential
depression/underachievement); supervised neuromodulation when indicated.

---

## References (Vancouver)

1. Hollenstein N, et al. ZuCo: A simultaneous EEG and eye‑tracking resource for
   natural sentence reading. *Sci Data*. 2018.
2. Hollenstein N, et al. ZuCo 2.0: Physiological recordings during natural
   reading and annotation. *LREC*. 2020.
3. De Deyne S, et al. The Small World of Words English word association norms.
   *Behav Res Methods*. 2019.
4. Dimigen O, et al. Coregistration of eye movements and EEG in natural reading.
   *J Exp Psychol Gen*. 2011.
5. Benjamini Y, Hochberg Y. Controlling the false discovery rate. *J R Stat Soc B*. 1995.
6. Ollivier Y. Ricci curvature of Markov chains on metric spaces. *J Funct Anal*.
   2009.
7. Forman R. Bochner’s method for cell complexes. *Discrete Comput Geom*. 2003.
8. Poldrack RA, et al. Transparent and reproducible neuroimaging. *Nat Rev
   Neurosci*. 2017.

---

## Artifacts (this release)

- This file: **Memoria_Estendida_PHD_Brasil_2025-08-29.md** (v2025.08.29).
- **README_v4.3.md** — curated repository overview.
- **CHANGELOG_v4.3.md** — formal change entry.
- **metadata_v4.3.yaml** — release metadata.
- **zenodo_v4.3.json** — Zenodo deposition metadata.
- **CITATION_v4.3.cff** — citation file for this snapshot.

---

## Actionables + Limitations

**Actionables (immediate):** run linter/linkcheck; generate `/reports/*.json`; pin
HELIO snapshots; open pre‑pitch round with 3 PIs.
**Limitations:** language WEIRDness; EN‑only validation at this stage; HELIO–cognition links remain exploratory (labelled as *plausibility*).

---

## Next Steps

**48h:** run NIT suite; tag Git release; prepare Overleaf skeleton with figures
placeholders.
**7d:** SEA results (bootstrapped CIs); preliminary ZuCo regressions with lexical
controls; draft IMRaD methods.
**10w:** Full VAR/ARIMAX with IRFs; cross‑lingual SWOW module; preprint + toolbox
v0.2; journal submission.

---

## Assumptions Log + QUALITY GATES (Q1–Q10)

- **Assumptions:** public‑only data; EN first; interpretability > brute accuracy;
  clinical framing is R&D, not diagnosis.
- **Q‑Gates:** all 10 gates must be ticked before submission; any failure blocks
  the release (see `QUALITY_GATES.md`).
